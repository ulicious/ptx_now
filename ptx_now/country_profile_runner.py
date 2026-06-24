"""Batch runner for country/profile optimizations without the GUI.

Countries are discovered from the subfolders of --countries-root. No hard-coded
country list is needed.

Example:
    python ptx_now/country_profile_runner.py \
        --settings-yaml ptx_now/data/hydrogen_parameters.yaml \
        --countries-root D:/weatherOut_Uwe \
        --profile-subdir Clustered_Profiles/2030/168 \
        --wacc-file D:/country_specific_wacc.xlsx \
        --output-xlsx D:/results/country_profile_results.xlsx
"""

from __future__ import annotations

import argparse
import multiprocessing
import os
from pathlib import Path
from typing import Any


PROFILE_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _normalise_folder(path: Path) -> str:
    """Return a path string that works with the project's string concatenation."""
    return str(path.resolve()) + os.sep


def _load_case_data(settings_yaml: Path) -> dict[str, Any]:
    import yaml

    with settings_yaml.open("r", encoding="utf-8") as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def _build_pm_object(settings_yaml: Path, profile_dir: Path, profile_file: str, wacc: float | None) -> Any:
    from _helper_optimization import clone_components_which_use_parallelization
    from _load_projects import load_project
    from object_framework import ParameterObject

    case_data = _load_case_data(settings_yaml)
    pm_object = ParameterObject("parameter", integer_steps=10, path_data=_normalise_folder(profile_dir))
    pm_object = load_project(pm_object, case_data)
    pm_object.set_path_data(_normalise_folder(profile_dir))
    pm_object.set_profile_data(profile_file)

    if wacc is not None:
        pm_object.set_wacc(wacc)

    return clone_components_which_use_parallelization(pm_object)


def _model_class_for_solver(solver: str):
    if solver.lower() == "gurobi":
        from optimization_gurobi_model import OptimizationGurobiModel

        return OptimizationGurobiModel

    from optimization_pyomo_model import OptimizationPyomoModel

    return OptimizationPyomoModel


def _component_rows(pm_object: Any, country: str, profile: str) -> list[dict[str, Any]]:
    rows = []
    for component in pm_object.get_final_components_objects():
        rows.append(
            {
                "country": country,
                "profile": profile,
                "component": component.get_name(),
                "component_type": component.get_component_type(),
                "capacity": component.get_fixed_capacity(),
                "investment": component.get_investment(),
                "annualized_investment": component.get_annualized_investment(),
                "fixed_costs": component.get_total_fixed_costs(),
                "variable_costs": component.get_total_variable_costs(),
                "total_costs": component.get_total_costs(),
            }
        )
    return rows


def _optimization_status(optimization_problem: Any) -> tuple[bool, str]:
    status = getattr(optimization_problem, "status", None)
    if status is not None:
        return status == 2, str(status)

    results = getattr(optimization_problem, "results", None)
    if results is None:
        return False, "unknown"

    solver_status = str(results.solver.status).lower()
    termination = str(results.solver.termination_condition).lower()
    return solver_status == "ok" and termination == "optimal", f"{solver_status}_{termination}"


def _run_single_profile(args: dict[str, Any]) -> dict[str, Any]:
    country = args["country"]
    profile = args["profile"]
    wacc = args["wacc"]

    try:
        from _transfer_results_to_parameter_object import _transfer_results_to_parameter_object

        pm_object = _build_pm_object(
            settings_yaml=args["settings_yaml"],
            profile_dir=args["profile_dir"],
            profile_file=profile,
            wacc=wacc,
        )
        pm_object.set_solver(args["solver"])
        if args["optimization_type"]:
            pm_object.set_optimization_type(args["optimization_type"])
        if pm_object.get_optimization_type() not in {"economical", "ecological"}:
            raise ValueError(
                "country_profile_runner supports direct 'economical' or 'ecological' runs. "
                "Multiobjective runs need an epsilon-selection workflow."
            )

        optimization_model = _model_class_for_solver(args["solver"])
        optimization_problem = optimization_model(pm_object, args["solver"])
        optimization_problem.prepare(optimization_type=pm_object.get_optimization_type())
        optimization_problem.optimize()

        is_optimal, status = _optimization_status(optimization_problem)
        economic_objective = getattr(
            optimization_problem,
            "economic_objective_function_value",
            optimization_problem.objective_function_value,
        )
        ecologic_objective = getattr(optimization_problem, "ecologic_objective_function_value", None)

        if not is_optimal:
            return {
                "run": {
                    "country": country,
                    "profile": profile,
                    "wacc": wacc,
                    "status": f"not_optimal_{status}",
                    "economic_objective": economic_objective,
                    "ecologic_objective": ecologic_objective,
                    "total_costs": None,
                },
                "components": [],
                "error": None,
            }

        pm_object.set_objective_function_value(optimization_problem.objective_function_value)
        pm_object.set_instance(optimization_problem.instance)
        _transfer_results_to_parameter_object(pm_object, optimization_problem.model_type)

        component_rows = _component_rows(pm_object, country, profile)
        run_row = {
            "country": country,
            "profile": profile,
            "wacc": wacc,
            "status": "optimal",
            "economic_objective": economic_objective,
            "ecologic_objective": ecologic_objective,
            "total_costs": sum(row["total_costs"] for row in component_rows),
        }

        for row in component_rows:
            prefix = row["component"]
            run_row[f"{prefix}_capacity"] = row["capacity"]
            run_row[f"{prefix}_total_costs"] = row["total_costs"]

        return {"run": run_row, "components": component_rows, "error": None}

    except Exception as exc:  # noqa: BLE001 - batch runs should keep going and report the failing case.
        return {
            "run": {
                "country": country,
                "profile": profile,
                "wacc": wacc,
                "status": "failed",
                "economic_objective": None,
                "ecologic_objective": None,
                "total_costs": None,
            },
            "components": [],
            "error": {"country": country, "profile": profile, "error": repr(exc)},
        }


def _read_wacc_table(path: Path | None) -> dict[str, float]:
    if path is None:
        return {}

    import pandas as pd

    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    lower_columns = {str(column).strip().lower(): column for column in df.columns}
    country_column = lower_columns.get("country") or lower_columns.get("land")
    wacc_column = lower_columns.get("wacc")

    if wacc_column is None:
        raise ValueError("WACC-Datei braucht eine Spalte 'WACC'.")

    if country_column is None:
        country_values = df.iloc[:, 0]
    else:
        country_values = df[country_column]

    return {
        str(country).strip(): float(wacc)
        for country, wacc in zip(country_values, df[wacc_column])
        if pd.notna(country) and pd.notna(wacc)
    }


def _country_profile_dir(country_dir: Path, profile_subdir: str | None) -> Path:
    if not profile_subdir:
        return country_dir
    return country_dir / Path(profile_subdir)


def _profile_files(profile_dir: Path, recursive: bool) -> list[str]:
    if recursive:
        files = [path for path in profile_dir.rglob("*") if path.suffix.lower() in PROFILE_SUFFIXES]
        return sorted(str(path.relative_to(profile_dir)) for path in files)

    files = [path.name for path in profile_dir.iterdir() if path.is_file() and path.suffix.lower() in PROFILE_SUFFIXES]
    return sorted(files)


def collect_jobs(args: argparse.Namespace) -> list[dict[str, Any]]:
    wacc_by_country = _read_wacc_table(args.wacc_file)
    country_dirs = [path for path in args.countries_root.iterdir() if path.is_dir()]

    if args.countries:
        selected = set(args.countries)
        country_dirs = [path for path in country_dirs if path.name in selected]

    jobs = []
    for country_dir in sorted(country_dirs, key=lambda path: path.name):
        profile_dir = _country_profile_dir(country_dir, args.profile_subdir)
        if not profile_dir.exists():
            print(f"Skip {country_dir.name}: profile folder not found: {profile_dir}")
            continue

        wacc = wacc_by_country.get(country_dir.name)
        if args.wacc_file and wacc is None:
            print(f"Skip {country_dir.name}: no WACC found")
            continue

        for profile in _profile_files(profile_dir, args.recursive_profiles):
            jobs.append(
                {
                    "settings_yaml": args.settings_yaml,
                    "profile_dir": profile_dir,
                    "profile": profile,
                    "country": country_dir.name,
                    "wacc": wacc,
                    "solver": args.solver,
                    "optimization_type": args.optimization_type,
                }
            )

    return jobs


def write_results(output_xlsx: Path, results: list[dict[str, Any]]) -> None:
    import pandas as pd

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    runs = [result["run"] for result in results]
    components = [row for result in results for row in result["components"]]
    errors = [result["error"] for result in results if result["error"]]

    with pd.ExcelWriter(output_xlsx) as writer:
        pd.DataFrame(runs).to_excel(writer, sheet_name="runs", index=False)
        pd.DataFrame(components).to_excel(writer, sheet_name="components", index=False)
        if errors:
            pd.DataFrame(errors).to_excel(writer, sheet_name="errors", index=False)


def _parse_cores(value: str) -> int:
    if value.lower() == "max":
        return max(1, multiprocessing.cpu_count() - 1)

    cores = int(value)
    if cores < 1:
        raise argparse.ArgumentTypeError("--cores must be at least 1 or 'max'.")
    return cores


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run country/profile optimizations without the GUI.")
    parser.add_argument("--settings-yaml", required=True, type=Path, help="Path to the project YAML.")
    parser.add_argument(
        "--countries-root",
        required=True,
        type=Path,
        help="Folder whose direct subfolders are treated as countries.",
    )
    parser.add_argument("--output-xlsx", required=True, type=Path, help="Central Excel output file.")
    parser.add_argument("--wacc-file", type=Path, help="Excel/CSV with country names and a WACC column.")
    parser.add_argument("--profile-subdir", help="Relative profile folder inside each country folder.")
    parser.add_argument("--countries", nargs="*", help="Optional filter for specific country folder names.")
    parser.add_argument("--recursive-profiles", action="store_true", help="Search profiles below the profile folder.")
    parser.add_argument("--solver", default="gurobi", help="Solver name passed to the project.")
    parser.add_argument("--optimization-type", help="Override optimization type from the YAML.")
    parser.add_argument(
        "--cores",
        type=_parse_cores,
        default=max(1, multiprocessing.cpu_count() - 1),
        help="Number of parallel worker processes, or 'max' for cpu_count - 1.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    jobs = collect_jobs(args)

    if not jobs:
        raise SystemExit("No profile jobs found.")

    print(f"Running {len(jobs)} optimizations on {args.cores} worker(s).")

    if args.cores == 1:
        results = [_run_single_profile(job) for job in jobs]
    else:
        with multiprocessing.Pool(processes=args.cores, maxtasksperchild=1) as pool:
            results = list(pool.imap_unordered(_run_single_profile, jobs))

    write_results(args.output_xlsx, results)
    failed = sum(1 for result in results if result["run"]["status"] == "failed")
    print(f"Wrote {args.output_xlsx}. Failed runs: {failed}.")


if __name__ == "__main__":
    main()
