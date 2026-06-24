"""Batch runner for country/profile optimizations without the GUI.

All run settings are hard-coded in the configuration block below. Countries
are still discovered automatically from the subfolders of COUNTRIES_ROOT.

Run:
    python ptx_now/country_profile_runner.py
"""

from __future__ import annotations

import multiprocessing
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROFILE_SUFFIXES = {".csv", ".xlsx", ".xls"}


# ---------------------------------------------------------------------------
# Hard-coded runner configuration
# ---------------------------------------------------------------------------
SETTINGS_YAML = Path(
    r"C:\Users\mt5285\Documents\yamls_hydrogen\hydrogen_all_data.yaml"
)
COUNTRIES_ROOT = Path(r"Z:\weatherOut\weatherOut_Uwe")
WACC_FILE = Path(r"C:\Users\mt5285\Documents\country_specific_wacc.xlsx")
OUTPUT_XLSX = Path(
    r"C:\Users\mt5285\Documents\yamls_hydrogen\country_profile_results.xlsx"
)

SCENARIO_YEAR = 2030
CLUSTER_LENGTH = 168
PROFILE_SUBDIR = Path("Clustered_Profiles") / str(SCENARIO_YEAR) / str(CLUSTER_LENGTH)

SOLVER = "gurobi"
OPTIMIZATION_TYPE: str | None = None
CORES: int | str = "max"
RECURSIVE_PROFILES = False

# None processes every country folder. To restrict the run, use for example:
# COUNTRIES = ["Germany", "France"]
COUNTRIES: list[str] | None = None


@dataclass(frozen=True)
class RunnerConfig:
    settings_yaml: Path
    countries_root: Path
    output_xlsx: Path
    wacc_file: Path | None
    profile_subdir: str | None
    countries: list[str] | None
    recursive_profiles: bool
    solver: str
    optimization_type: str | None
    cores: int


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


def collect_jobs(args: RunnerConfig) -> list[dict[str, Any]]:
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


def _parse_cores(value: int | str) -> int:
    if isinstance(value, str) and value.lower() == "max":
        return max(1, multiprocessing.cpu_count() - 1)

    cores = int(value)
    if cores < 1:
        raise ValueError("CORES must be at least 1 or 'max'.")
    return cores


def build_config() -> RunnerConfig:
    return RunnerConfig(
        settings_yaml=SETTINGS_YAML,
        countries_root=COUNTRIES_ROOT,
        output_xlsx=OUTPUT_XLSX,
        wacc_file=WACC_FILE,
        profile_subdir=str(PROFILE_SUBDIR),
        countries=COUNTRIES,
        recursive_profiles=RECURSIVE_PROFILES,
        solver=SOLVER,
        optimization_type=OPTIMIZATION_TYPE,
        cores=_parse_cores(CORES),
    )


def validate_config(config: RunnerConfig) -> None:
    missing = []
    if not config.settings_yaml.is_file():
        missing.append(f"SETTINGS_YAML does not exist: {config.settings_yaml}")
    if not config.countries_root.is_dir():
        missing.append(f"COUNTRIES_ROOT does not exist: {config.countries_root}")
    if config.wacc_file is not None and not config.wacc_file.is_file():
        missing.append(f"WACC_FILE does not exist: {config.wacc_file}")

    if missing:
        details = "\n".join(f"- {message}" for message in missing)
        raise SystemExit(
            "Please correct the hard-coded configuration at the top of "
            f"country_profile_runner.py:\n{details}"
        )


def main() -> None:
    args = build_config()
    validate_config(args)
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
