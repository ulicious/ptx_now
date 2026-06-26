"""Run country profile optimizations without the GUI.

The runner configuration is intentionally hard-coded below. The workflow is:

1. Discover countries from the direct subfolders of ``COUNTRIES_ROOT``.
2. Load one base YAML into a ``ParameterObject``.
3. Iterate over ``SCENARIO_YEARS``.
4. Read and apply parameters from ``PARAMETERS_XLSX``.
5. Process one country at a time and its profiles in parallel.
6. Save a checkpoint Excel file after every completed country.

Run:
    python ptx_now/country_profile_runner.py
"""

from __future__ import annotations

import json
import multiprocessing
import os
import shutil
import tempfile
import time
import traceback
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_SUFFIXES = {".csv", ".xlsx", ".xls"}
RUNNER_VERSION = "2026-06-26-solver-flow-capacity-check-v3"


# ---------------------------------------------------------------------------
# Hard-coded configuration
# ---------------------------------------------------------------------------
COUNTRIES_ROOT = Path(
    r"/run/user/1000/gvfs/smb-share:server=iipsrv-ss1.iip.kit.edu,"
    r"share=daten$/weatherOut/weatherOut_Uwe"
)
SETTINGS_YAML = Path(
    r"/home/localadmin/Dokumente/ptx_now_data/"
    r"global_hydrogen_case_calculation/hydrogen.yaml"
)
PARAMETERS_XLSX = Path(
    r"/home/localadmin/Dokumente/ptx_now_data/"
    r"global_hydrogen_case_calculation/runner_parameters.xlsx"
)
OUTPUT_DIR = Path(
    r"/home/localadmin/Dokumente/ptx_now_data/"
    r"global_hydrogen_case_calculation/results"
)

SCENARIO_YEARS = (2030, 2040, 2050)
PROFILE_SUBDIR_TEMPLATE = "Clustered_Profiles/{year}/168"

SOLVER = "gurobi"
OPTIMIZATION_TYPE: str | None = "economical"
CORES: int | str = "max"
RECURSIVE_PROFILES = False
PROFILE_COPY_RETRIES = 5
PROFILE_COPY_RETRY_DELAY_SECONDS = 2.0

# None means all discovered country folders.
COUNTRIES: list[str] | None = None

COUNTRIES_SHEET = "countries"
PARAMETERS_SHEET = "parameters"
PROGRESS_FILE_NAME = "runner_progress.json"

# Country folders are mapped to the parameter geographies below. Exact
# geographies such as China or India take precedence over broad regions.
EUROPE_COUNTRIES = {
    "Albania",
    "Austria",
    "Belarus",
    "Belgium",
    "Bosnia and Herzegovina",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Iceland",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Moldova",
    "Montenegro",
    "Netherlands",
    "North Macedonia",
    "Norway",
    "Poland",
    "Portugal",
    "Romania",
    "Serbia",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
    "Switzerland",
    "Turkey",
    "Ukraine",
    "United Kingdom",
}
MIDDLE_EAST_COUNTRIES = {
    "Bahrain",
    "Iran",
    "Iraq",
    "Israel",
    "Jordan",
    "Kuwait",
    "Lebanon",
    "Oman",
    "Qatar",
    "Saudi Arabia",
    "Syria",
    "United Arab Emirates",
    "Yemen",
}
AFRICA_COUNTRIES = {
    "Algeria",
    "Angola",
    "Benin",
    "Botswana",
    "Burkina Faso",
    "Burundi",
    "Cameroon",
    "Central African Republic",
    "Chad",
    "Comoros",
    "Democratic Republic of the Congo",
    "Djibouti",
    "Egypt",
    "Equatorial Guinea",
    "Eritrea",
    "Eswatini",
    "Ethiopia",
    "Gabon",
    "Gambia",
    "Ghana",
    "Guinea",
    "Guinea-Bissau",
    "Ivory Coast",
    "Kenya",
    "Lesotho",
    "Liberia",
    "Libya",
    "Madagascar",
    "Malawi",
    "Mali",
    "Mauritania",
    "Morocco",
    "Mozambique",
    "Namibia",
    "Niger",
    "Nigeria",
    "Republic of the Congo",
    "Rwanda",
    "Senegal",
    "Sierra Leone",
    "Somalia",
    "South Africa",
    "South Sudan",
    "Sudan",
    "Tanzania",
    "Togo",
    "Tunisia",
    "Uganda",
    "Western Sahara",
    "Zambia",
    "Zimbabwe",
}
LATIN_AMERICA_COUNTRIES = {
    "Argentina",
    "Belize",
    "Bolivia",
    "Chile",
    "Colombia",
    "Costa Rica",
    "Cuba",
    "Dominican Republic",
    "Ecuador",
    "El Salvador",
    "Guatemala",
    "Guyana",
    "Haiti",
    "Honduras",
    "Jamaica",
    "Mexico",
    "Nicaragua",
    "Panama",
    "Paraguay",
    "Peru",
    "Puerto Rico",
    "Suriname",
    "Uruguay",
    "Venezuela",
}
ASIA_OCEANIA_COUNTRIES = {
    "Afghanistan",
    "Armenia",
    "Australia",
    "Azerbaijan",
    "Bangladesh",
    "Bhutan",
    "Brunei",
    "Cambodia",
    "Georgia",
    "Indonesia",
    "Kazakhstan",
    "Kyrgyzstan",
    "Laos",
    "Malaysia",
    "Mongolia",
    "Myanmar",
    "Nepal",
    "New Zealand",
    "North Korea",
    "Pakistan",
    "Papua New Guinea",
    "Philippines",
    "South Korea",
    "Sri Lanka",
    "Tajikistan",
    "Thailand",
    "Turkmenistan",
    "Uzbekistan",
    "Vietnam",
}
COUNTRY_REGION_ALIASES = {
    "Brazil": "Brazil",
    "Canada": "North America",
    "China": "China",
    "People's Republic of China": "China",
    "India": "India",
    "Japan": "Japan",
    "Russia": "Russia",
    "United States": "United States",
    "United States of America": "United States",
}


@dataclass(frozen=True)
class RunnerConfig:
    countries_root: Path
    settings_yaml: Path
    parameters_xlsx: Path
    output_dir: Path
    scenario_years: tuple[int, ...]
    profile_subdir_template: str
    solver: str
    optimization_type: str | None
    cores: int
    recursive_profiles: bool
    countries: list[str] | None


@dataclass(frozen=True)
class CountrySettings:
    country: str
    region: str
    wacc: float | None


class OptimizationNotOptimalError(RuntimeError):
    def __init__(
        self,
        year: int,
        country: str,
        profile: str,
        reason: str,
        raw_status: str,
    ) -> None:
        self.year = year
        self.country = country
        self.profile = profile
        self.reason = reason
        self.raw_status = raw_status
        super().__init__(year, country, profile, reason, raw_status)

    def __str__(self) -> str:
        return (
            "Optimization aborted because no optimal solution was found: "
            f"year={self.year}, country={self.country}, "
            f"profile={self.profile}, reason={self.reason}, "
            f"solver_status={self.raw_status}"
        )


class ProfileOptimizationError(RuntimeError):
    def __init__(
        self,
        year: int,
        country: str,
        region: str,
        profile: str,
        profile_path: str,
        exception_type: str,
        detail: str,
        traceback_text: str,
    ) -> None:
        self.year = year
        self.country = country
        self.region = region
        self.profile = profile
        self.profile_path = profile_path
        self.exception_type = exception_type
        self.detail = detail
        self.traceback_text = traceback_text
        super().__init__(
            year,
            country,
            region,
            profile,
            profile_path,
            exception_type,
            detail,
            traceback_text,
        )

    def __str__(self) -> str:
        return (
            "Optimization aborted because the profile run failed: "
            f"year={self.year}, country={self.country}, "
            f"profile={self.profile}, profile_path={self.profile_path}, "
            f"exception={self.exception_type}, detail={self.detail}\n"
            f"Traceback:\n{self.traceback_text}"
        )


def _normalise_folder(path: Path) -> str:
    return str(path.resolve()) + os.sep


def _parse_cores(value: int | str) -> int:
    if isinstance(value, str) and value.lower() == "max":
        return max(1, multiprocessing.cpu_count() - 1)

    cores = int(value)
    if cores < 1:
        raise ValueError("CORES must be at least 1 or 'max'.")
    return cores


def build_config() -> RunnerConfig:
    return RunnerConfig(
        countries_root=COUNTRIES_ROOT,
        settings_yaml=SETTINGS_YAML,
        parameters_xlsx=PARAMETERS_XLSX,
        output_dir=OUTPUT_DIR,
        scenario_years=SCENARIO_YEARS,
        profile_subdir_template=PROFILE_SUBDIR_TEMPLATE,
        solver=SOLVER,
        optimization_type=OPTIMIZATION_TYPE,
        cores=_parse_cores(CORES),
        recursive_profiles=RECURSIVE_PROFILES,
        countries=COUNTRIES,
    )


def validate_config(config: RunnerConfig) -> None:
    missing = []
    if not config.countries_root.is_dir():
        missing.append(f"COUNTRIES_ROOT does not exist: {config.countries_root}")
    if not config.settings_yaml.is_file():
        missing.append(f"SETTINGS_YAML does not exist: {config.settings_yaml}")
    if not config.parameters_xlsx.is_file():
        missing.append(f"PARAMETERS_XLSX does not exist: {config.parameters_xlsx}")

    if missing:
        details = "\n".join(f"- {message}" for message in missing)
        raise SystemExit(
            "Please correct the hard-coded configuration at the top of "
            f"country_profile_runner.py:\n{details}"
        )


def _load_case_data(settings_yaml: Path) -> dict[str, Any]:
    import yaml

    with settings_yaml.open("r", encoding="utf-8") as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def _build_base_parameter_object(config: RunnerConfig) -> Any:
    from _load_projects import load_project
    from object_framework import ParameterObject

    case_data = _load_case_data(config.settings_yaml)
    pm_object = ParameterObject(
        "parameter",
        integer_steps=10,
        path_data=_normalise_folder(config.countries_root),
    )
    pm_object = load_project(pm_object, case_data)
    pm_object.set_solver(config.solver)
    if config.optimization_type:
        pm_object.set_optimization_type(config.optimization_type)
    return pm_object


def _is_active(value: Any) -> bool:
    if value is None:
        return True
    try:
        import pandas as pd

        if pd.isna(value):
            return True
    except TypeError:
        pass
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "nein", "inactive"}
    return bool(value)


def _read_parameter_workbook(path: Path) -> tuple[Any, Any]:
    import pandas as pd

    countries = pd.read_excel(path, sheet_name=COUNTRIES_SHEET)
    parameter_matrix = pd.read_excel(path, sheet_name=PARAMETERS_SHEET)

    country_required = {"country", "region", "wacc"}
    parameter_required = {
        "country_or_region",
        "technology",
        "parameter",
        *[str(year) for year in SCENARIO_YEARS],
    }
    missing_country = country_required - set(countries.columns)
    parameter_matrix.columns = [
        str(column).strip() for column in parameter_matrix.columns
    ]
    missing_parameter = parameter_required - set(parameter_matrix.columns)
    if missing_country:
        raise ValueError(
            f"Sheet '{COUNTRIES_SHEET}' is missing columns: "
            f"{sorted(missing_country)}"
        )
    if missing_parameter:
        raise ValueError(
            f"Sheet '{PARAMETERS_SHEET}' is missing columns: "
            f"{sorted(missing_parameter)}"
        )

    if "active" in countries.columns:
        countries = countries[countries["active"].map(_is_active)]
    if "active" in parameter_matrix.columns:
        parameter_matrix = parameter_matrix[
            parameter_matrix["active"].map(_is_active)
        ]

    countries = countries.copy()
    parameter_matrix = parameter_matrix.copy()
    countries["country"] = countries["country"].astype(str).str.strip()
    countries["region"] = countries["region"].astype(str).str.strip()

    parameter_matrix["country_or_region"] = (
        parameter_matrix["country_or_region"]
        .fillna("Global")
        .astype(str)
        .str.strip()
    )
    parameter_matrix["technology"] = (
        parameter_matrix["technology"].astype(str).str.strip()
    )
    parameter_matrix["parameter"] = (
        parameter_matrix["parameter"].astype(str).str.strip()
    )

    parameters = parameter_matrix.melt(
        id_vars=[
            column
            for column in parameter_matrix.columns
            if column not in {str(year) for year in SCENARIO_YEARS}
        ],
        value_vars=[str(year) for year in SCENARIO_YEARS],
        var_name="year",
        value_name="value",
    )
    parameters = parameters[pd.notna(parameters["value"])].copy()
    parameters["year"] = parameters["year"].astype(int)
    parameters["value"] = parameters["value"].astype(float)
    parameters["scope"] = "global"
    parameters["scope_name"] = ""
    geography = parameters["country_or_region"]
    country_names = set(countries["country"])
    region_names = set(countries["region"])
    region_mask = geography.isin(region_names)
    country_mask = geography.isin(country_names) & ~region_mask
    parameters.loc[region_mask, "scope"] = "region"
    parameters.loc[region_mask, "scope_name"] = parameters.loc[
        region_mask, "country_or_region"
    ]
    parameters.loc[country_mask, "scope"] = "country"
    parameters.loc[country_mask, "scope_name"] = parameters.loc[
        country_mask, "country_or_region"
    ]
    unknown_mask = (
        ~geography.str.casefold().eq("global")
        & ~region_mask
        & ~country_mask
    )
    if unknown_mask.any():
        unknown = sorted(set(geography[unknown_mask]))
        raise ValueError(
            "Unknown country_or_region entries in parameters sheet: "
            f"{unknown}. Add them to the countries sheet first."
        )
    parameters["component"] = parameters["technology"].map(
        _component_name_for_technology
    )
    parameters["parameter"] = parameters["parameter"].map(
        _internal_parameter_name
    )

    return countries, parameters


def _component_name_for_technology(technology: str) -> str:
    mapping = {
        "solar": "Solar",
        "wind": "Wind",
        "battery": "Electricity",
        "electricity storage": "Electricity",
        "electrolyzer": "electrolyzer",
        "electrolyser": "electrolyzer",
    }
    return mapping.get(technology.strip().lower(), technology.strip())


def _internal_parameter_name(parameter: str) -> str:
    mapping = {
        "capex": "capex",
        "fom": "fixed_om",
        "fixed om": "fixed_om",
        "fixed_om": "fixed_om",
        "vom": "variable_om",
        "variable om": "variable_om",
        "variable_om": "variable_om",
        "charging efficiency": "charging_efficiency",
        "charging_efficiency": "charging_efficiency",
        "discharging efficiency": "discharging_efficiency",
        "discharging_efficiency": "discharging_efficiency",
        "duration": "ratio_capacity_p",
        "storage duration": "ratio_capacity_p",
        "ratio_capacity_p": "ratio_capacity_p",
        "minimum load": "min_p",
        "min_p": "min_p",
        "maximum load": "max_p",
        "max_p": "max_p",
        "electricity input": "input.Electricity",
        "input.electricity": "input.Electricity",
    }
    return mapping.get(parameter.strip().lower(), parameter.strip())


def _discover_countries(config: RunnerConfig) -> list[Path]:
    country_dirs = [
        path for path in config.countries_root.iterdir() if path.is_dir()
    ]
    if config.countries:
        selected = set(config.countries)
        country_dirs = [path for path in country_dirs if path.name in selected]
    return sorted(country_dirs, key=lambda path: path.name.casefold())


def _country_settings(countries_df: Any, country: str) -> CountrySettings:
    import pandas as pd

    matches = countries_df[countries_df["country"] == country]
    if len(matches) > 1:
        raise ValueError(
            f"Country '{country}' may occur at most once in sheet "
            f"'{COUNTRIES_SHEET}', found {len(matches)} rows."
        )

    available_regions = set(countries_df["region"])
    if len(matches) == 1:
        row = matches.iloc[0]
        region = str(row["region"]).strip()
        wacc = None if pd.isna(row["wacc"]) else float(row["wacc"])
    else:
        region = _infer_parameter_region(country, available_regions)
        region_rows = countries_df[
            (countries_df["country"] == region)
            | (countries_df["region"] == region)
        ]
        region_wacc_values = region_rows["wacc"].dropna()
        wacc = (
            float(region_wacc_values.iloc[0])
            if len(region_wacc_values) > 0
            else None
        )

    return CountrySettings(
        country=country,
        region=region,
        wacc=wacc,
    )


def _infer_parameter_region(
    country: str,
    available_regions: set[str],
) -> str:
    if country in COUNTRY_REGION_ALIASES:
        region = COUNTRY_REGION_ALIASES[country]
    elif country in EUROPE_COUNTRIES:
        region = "European Union"
    elif country in MIDDLE_EAST_COUNTRIES:
        region = "Middle East"
    elif country in AFRICA_COUNTRIES:
        region = "Africa"
    elif country in LATIN_AMERICA_COUNTRIES:
        region = "South & Latin America"
    elif country in ASIA_OCEANIA_COUNTRIES:
        region = "Asia & Oceania"
    else:
        raise ValueError(
            f"No automatic parameter region is defined for country "
            f"'{country}'. Add an exact row to sheet '{COUNTRIES_SHEET}' "
            "or extend the country mapping in country_profile_runner.py."
        )

    if region not in available_regions:
        raise ValueError(
            f"Country '{country}' maps to region '{region}', but that region "
            f"is not present in sheet '{COUNTRIES_SHEET}'."
        )
    return region


def _parameter_rows_for_country(
    parameters_df: Any,
    year: int,
    settings: CountrySettings,
) -> Any:
    year_rows = parameters_df[parameters_df["year"] == year].copy()
    selected = year_rows[
        (year_rows["scope"] == "global")
        | (
            (year_rows["scope"] == "region")
            & (year_rows["scope_name"] == settings.region)
        )
        | (
            (year_rows["scope"] == "country")
            & (year_rows["scope_name"] == settings.country)
        )
    ].copy()

    priority = {"global": 0, "region": 1, "country": 2}
    selected["_priority"] = selected["scope"].map(priority)
    selected = selected.sort_values(
        ["_priority", "component", "parameter"],
        kind="stable",
    )
    selected = selected.drop_duplicates(
        subset=["component", "parameter"],
        keep="last",
    )
    return selected


def _apply_parameter(pm_object: Any, component_name: str, parameter: str, value: float) -> None:
    if component_name == "__project__":
        if parameter != "wacc":
            raise ValueError(f"Unsupported project parameter: {parameter}")
        pm_object.set_wacc(value)
        return

    component = pm_object.get_component(component_name)
    setter_by_parameter = {
        "capex": component.set_capex,
        "fixed_om": component.set_fixed_OM,
        "variable_om": component.set_variable_OM,
    }

    if parameter in setter_by_parameter:
        setter_by_parameter[parameter](value)
    elif parameter == "charging_efficiency":
        component.set_charging_efficiency(value)
    elif parameter == "discharging_efficiency":
        component.set_discharging_efficiency(value)
    elif parameter == "ratio_capacity_p":
        component.set_ratio_capacity_p(value)
    elif parameter == "min_p":
        component.set_min_p(value)
    elif parameter == "max_p":
        component.set_max_p(value)
    elif parameter.startswith("input."):
        commodity = parameter.split(".", 1)[1]
        component.add_input(commodity, value)
    elif parameter.startswith("output."):
        commodity = parameter.split(".", 1)[1]
        component.add_output(commodity, value)
    else:
        raise ValueError(
            f"Unsupported parameter '{parameter}' for component "
            f"'{component_name}'."
        )


def _apply_parameters(pm_object: Any, parameter_rows: Any) -> list[dict[str, Any]]:
    applied = []
    for _, row in parameter_rows.iterrows():
        _apply_parameter(
            pm_object,
            component_name=row["component"],
            parameter=row["parameter"],
            value=float(row["value"]),
        )
        applied.append(
            {
                key: row.get(key)
                for key in [
                    "year",
                    "scope",
                    "scope_name",
                    "component",
                    "parameter",
                    "value",
                    "unit",
                    "source",
                    "note",
                ]
                if key in row.index
            }
        )
    return applied


def _profile_dir(config: RunnerConfig, country_dir: Path, year: int) -> Path:
    relative = config.profile_subdir_template.format(year=year)
    return country_dir / Path(relative)


def _profile_files(profile_dir: Path, recursive: bool) -> list[str]:
    if recursive:
        files = [
            path
            for path in profile_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in PROFILE_SUFFIXES
        ]
        return sorted(str(path.relative_to(profile_dir)) for path in files)

    return sorted(
        path.name
        for path in profile_dir.iterdir()
        if path.is_file() and path.suffix.lower() in PROFILE_SUFFIXES
    )


def _validate_staged_profile(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Staged profile does not exist: {path}")
    if path.stat().st_size == 0:
        raise OSError(f"Staged profile is empty: {path}")

    if path.suffix.lower() == ".xlsx":
        with zipfile.ZipFile(path, "r") as archive:
            corrupt_member = archive.testzip()
            if corrupt_member is not None:
                raise zipfile.BadZipFile(
                    f"Corrupt member '{corrupt_member}' in {path}"
                )


def _copy_profile_with_retries(
    source: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_destination = destination.with_suffix(
        destination.suffix + ".part"
    )
    last_error: Exception | None = None

    for attempt in range(1, PROFILE_COPY_RETRIES + 1):
        try:
            temporary_destination.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)

            source_size_before = source.stat().st_size
            with source.open("rb") as source_file:
                with temporary_destination.open("wb") as destination_file:
                    shutil.copyfileobj(
                        source_file,
                        destination_file,
                        length=1024 * 1024,
                    )
                    destination_file.flush()
                    os.fsync(destination_file.fileno())

            source_size_after = source.stat().st_size
            copied_size = temporary_destination.stat().st_size
            if source_size_before != source_size_after:
                raise OSError(
                    "Source file size changed while it was being copied: "
                    f"{source_size_before} -> {source_size_after}"
                )
            if copied_size != source_size_after:
                raise OSError(
                    f"Incomplete copy: source={source_size_after} bytes, "
                    f"local={copied_size} bytes"
                )

            _validate_staged_profile(temporary_destination)
            os.replace(temporary_destination, destination)
            return

        except Exception as exc:  # noqa: BLE001 - network reads are retried.
            last_error = exc
            temporary_destination.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            if attempt == PROFILE_COPY_RETRIES:
                break

            delay = PROFILE_COPY_RETRY_DELAY_SECONDS * attempt
            print(
                f"Profile copy failed ({attempt}/{PROFILE_COPY_RETRIES}): "
                f"{source}: {type(exc).__name__}: {exc}. "
                f"Retry in {delay:.1f}s."
            )
            time.sleep(delay)

    raise OSError(
        f"Could not create a valid local copy after "
        f"{PROFILE_COPY_RETRIES} attempts: {source}"
    ) from last_error


def _model_class_for_solver(solver: str):
    if solver.lower() == "gurobi":
        from optimization_gurobi_model import OptimizationGurobiModel

        return OptimizationGurobiModel

    from optimization_pyomo_model import OptimizationPyomoModel

    return OptimizationPyomoModel


def _optimization_status(
    optimization_problem: Any,
) -> tuple[bool, str, str]:
    status = getattr(optimization_problem, "status", None)
    if status is not None:
        gurobi_status = {
            1: "loaded",
            2: "optimal",
            3: "infeasible",
            4: "infeasible_or_unbounded",
            5: "unbounded",
            6: "cutoff",
            7: "iteration_limit",
            8: "node_limit",
            9: "time_limit",
            10: "solution_limit",
            11: "interrupted",
            12: "numeric_error",
            13: "suboptimal",
            14: "in_progress",
            15: "user_objective_limit",
            16: "work_limit",
            17: "memory_limit",
        }
        reason = gurobi_status.get(int(status), "unknown")
        return status == 2, reason, f"gurobi_status_{status}"

    results = getattr(optimization_problem, "results", None)
    if results is None:
        return False, "unknown", "unknown"

    solver_status = str(results.solver.status).lower()
    termination = str(results.solver.termination_condition).lower()
    normalized_termination = termination.replace(" ", "_")
    if "infeasibleorunbounded" in normalized_termination.replace("_", ""):
        reason = "infeasible_or_unbounded"
    elif "infeasible" in normalized_termination:
        reason = "infeasible"
    elif "unbounded" in normalized_termination:
        reason = "unbounded"
    elif "timelimit" in normalized_termination.replace("_", ""):
        reason = "time_limit"
    elif normalized_termination == "optimal":
        reason = "optimal"
    else:
        reason = normalized_termination

    return (
        solver_status == "ok" and termination == "optimal",
        reason,
        f"{solver_status}_{termination}",
    )


def _variable_value(variable: Any) -> float:
    value = getattr(variable, "X", None)
    if value is None:
        value = getattr(variable, "value", None)
    if callable(value):
        value = value()
    if value is None:
        raise ValueError(f"Solver variable has no result value: {variable!r}")
    return float(value)


def _solver_nominal_capacity(
    optimization_problem: Any,
    component_name: str,
) -> float:
    nominal_cap = getattr(optimization_problem, "nominal_cap", None)
    if nominal_cap is None:
        instance = getattr(optimization_problem, "instance", None)
        nominal_cap = getattr(instance, "nominal_cap", None)
    if nominal_cap is None:
        raise ValueError("Optimization result has no nominal_cap variable.")
    return _variable_value(nominal_cap[component_name])


def _solver_weighted_flow_sum(
    variable: Any,
    keys: list[tuple[Any, ...]],
    weightings: dict[Any, float],
    cluster_index: int,
) -> float:
    quantity = 0.0
    for key in keys:
        quantity += _variable_value(variable[key]) * weightings[key[cluster_index]]
    return quantity


def _solver_component_output_quantity(
    optimization_problem: Any,
    pm_object: Any,
    component_name: str,
    commodity_names: set[str],
) -> float:
    variable = getattr(
        optimization_problem,
        "mass_energy_component_out_commodities",
        None,
    )
    if variable is None:
        instance = getattr(optimization_problem, "instance", None)
        variable = getattr(instance, "mass_energy_component_out_commodities", None)
    if variable is None:
        return 0.0

    weightings = pm_object.get_weightings_time_series()
    keys = [
        (component_name, commodity_name, cl, t)
        for commodity_name in commodity_names
        for cl in range(pm_object.get_number_clusters())
        for t in range(pm_object.get_covered_period())
    ]
    existing_keys = [key for key in keys if key in variable]
    return _solver_weighted_flow_sum(
        variable,
        existing_keys,
        weightings,
        cluster_index=2,
    )


def _solver_generator_output_quantity(
    optimization_problem: Any,
    pm_object: Any,
    component_name: str,
    commodity_name: str,
) -> float:
    variable = getattr(optimization_problem, "mass_energy_generation", None)
    if variable is None:
        instance = getattr(optimization_problem, "instance", None)
        variable = getattr(instance, "mass_energy_generation", None)
    if variable is None:
        return 0.0

    weightings = pm_object.get_weightings_time_series()
    keys = [
        (component_name, commodity_name, cl, t)
        for cl in range(pm_object.get_number_clusters())
        for t in range(pm_object.get_covered_period())
    ]
    existing_keys = [key for key in keys if key in variable]
    return _solver_weighted_flow_sum(
        variable,
        existing_keys,
        weightings,
        cluster_index=2,
    )


def _run_single_profile(job: dict[str, Any]) -> dict[str, Any]:
    country = job["country"]
    region = job["region"]
    year = job["year"]
    profile = job["profile"]

    try:
        from _helper_optimization import clone_components_which_use_parallelization
        from _transfer_results_to_parameter_object import (
            _transfer_results_to_parameter_object,
        )

        pm_object = clone_components_which_use_parallelization(job["pm_object"])
        pm_object.set_path_data(_normalise_folder(job["profile_dir"]))
        pm_object.set_profile_data(profile)
        pm_object.set_solver(job["solver"])

        optimization_model = _model_class_for_solver(job["solver"])
        optimization_problem = optimization_model(pm_object, job["solver"])
        optimization_problem.prepare(
            optimization_type=pm_object.get_optimization_type()
        )
        try:
            optimization_problem.optimize()
        except Exception as exc:
            is_optimal, reason, raw_status = _optimization_status(
                optimization_problem
            )
            if not is_optimal and raw_status != "unknown":
                raise OptimizationNotOptimalError(
                    year,
                    country,
                    profile,
                    reason,
                    raw_status,
                ) from exc
            raise

        is_optimal, reason, solver_status = _optimization_status(
            optimization_problem
        )
        if not is_optimal:
            raise OptimizationNotOptimalError(
                year,
                country,
                profile,
                reason,
                solver_status,
            )

        economic_objective = getattr(
            optimization_problem,
            "economic_objective_function_value",
            getattr(optimization_problem, "objective_function_value", None),
        )
        ecologic_objective = getattr(
            optimization_problem,
            "ecologic_objective_function_value",
            None,
        )

        base_result = {
            "scenario_year": year,
            "country": country,
            "region": region,
            "profile": profile,
            "wacc": job["wacc"],
            "solver_status": solver_status,
            "economic_objective": economic_objective,
            "ecologic_objective": ecologic_objective,
        }

        pm_object.set_objective_function_value(
            optimization_problem.objective_function_value
        )
        pm_object.set_instance(optimization_problem.instance)
        _transfer_results_to_parameter_object(
            pm_object,
            optimization_problem.model_type,
        )

        produced_by_commodity = {
            commodity.get_name(): commodity.get_produced_quantity()
            for commodity in pm_object.get_final_commodities_objects()
        }
        demanded_production = {
            commodity.get_name(): commodity.get_produced_quantity()
            for commodity in pm_object.get_final_commodities_objects()
            if commodity.is_demanded()
        }
        produced_quantity = sum(demanded_production.values())
        total_costs = economic_objective
        cost_per_produced_unit = (
            total_costs / produced_quantity
            if total_costs is not None and produced_quantity
            else None
        )

        components = []
        capacity_columns = {}
        final_commodity_names = set(produced_by_commodity)
        for component in pm_object.get_final_components_objects():
            component_name = component.get_name()
            solver_capacity = _solver_nominal_capacity(
                optimization_problem,
                component_name,
            )
            capacity_ratio = (
                component.get_capex_ratio()
                if component.get_component_type() == "conversion"
                else 1.0
            )
            reported_capacity = solver_capacity * capacity_ratio
            transferred_capacity = component.get_fixed_capacity()

            if component.get_component_type() == "conversion":
                produced_by_component = _solver_component_output_quantity(
                    optimization_problem,
                    pm_object,
                    component_name,
                    final_commodity_names,
                )
            elif component.get_component_type() == "generator":
                produced_by_component = _solver_generator_output_quantity(
                    optimization_problem,
                    pm_object,
                    component_name,
                    component.get_generated_commodity(),
                )
            else:
                produced_by_component = 0.0

            if produced_by_component > 1e-8 and solver_capacity <= 1e-12:
                raise RuntimeError(
                    "Inconsistent optimization result: component "
                    f"'{component_name}' produced {produced_by_component} "
                    "but its solver nominal capacity is zero."
                )

            component_row = {
                "scenario_year": year,
                "country": country,
                "region": region,
                "profile": profile,
                "component": component_name,
                "component_type": component.get_component_type(),
                "capacity": reported_capacity,
                "solver_capacity": solver_capacity,
                "transferred_capacity": transferred_capacity,
                "solver_output_quantity": produced_by_component,
                "capacity_basis": (
                    component.get_capex_basis()
                    if component.get_component_type() == "conversion"
                    else "native"
                ),
                "investment": component.get_investment(),
                "annualized_investment": component.get_annualized_investment(),
                "fixed_costs": component.get_total_fixed_costs(),
                "variable_costs": component.get_total_variable_costs(),
                "component_total_costs": component.get_total_costs(),
            }
            components.append(component_row)
            capacity_columns[f"capacity_{component_name}"] = reported_capacity

        commodity_columns = {
            f"produced_{name}": quantity
            for name, quantity in produced_by_commodity.items()
        }
        return {
            "result": {
                **base_result,
                "status": "optimal",
                "total_costs": total_costs,
                "produced_quantity": produced_quantity,
                "cost_per_produced_unit": cost_per_produced_unit,
                **commodity_columns,
                **capacity_columns,
            },
            "components": components,
            "error": None,
        }

    except OptimizationNotOptimalError:
        raise
    except ProfileOptimizationError:
        raise
    except Exception as exc:
        retryable_file_error = isinstance(
            exc,
            (OSError, EOFError, zipfile.BadZipFile),
        )
        if retryable_file_error and not job.get("_local_file_retry"):
            safe_country = "".join(
                character if character.isalnum() else "_"
                for character in country
            )
            local_profile_dir = Path(
                tempfile.mkdtemp(
                    prefix=f"ptx_now_retry_{year}_{safe_country}_",
                )
            )
            source_profile = Path(job["profile_dir"]) / profile
            local_profile = local_profile_dir / profile

            print(
                f"Direct server read failed for {source_profile}: "
                f"{type(exc).__name__}: {exc}. "
                f"Retrying with a validated local copy."
            )
            try:
                _copy_profile_with_retries(
                    source=source_profile,
                    destination=local_profile,
                )
                retry_job = dict(job)
                retry_job["profile_dir"] = local_profile_dir
                retry_job["_local_file_retry"] = True
                result = _run_single_profile(retry_job)
            except Exception:
                print(
                    f"Local retry directory retained after failure: "
                    f"{local_profile_dir}"
                )
                raise
            else:
                shutil.rmtree(local_profile_dir)
                print(
                    f"Local retry succeeded for {country}/{profile}"
                )
                return result

        raise ProfileOptimizationError(
            year=year,
            country=country,
            region=region,
            profile=profile,
            profile_path=str(Path(job["profile_dir"]) / profile),
            exception_type=type(exc).__name__,
            detail=repr(exc),
            traceback_text=traceback.format_exc(),
        ) from exc


def _run_country_jobs(jobs: list[dict[str, Any]], cores: int) -> list[dict[str, Any]]:
    if cores == 1:
        return [_run_single_profile(job) for job in jobs]

    with multiprocessing.Pool(
        processes=cores,
        maxtasksperchild=1,
    ) as pool:
        return list(pool.imap_unordered(_run_single_profile, jobs))


def _safe_excel_value(value: Any) -> Any:
    try:
        import pandas as pd

        return None if pd.isna(value) else value
    except TypeError:
        return value


def _normalize_result_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized_record = {}
    for key, value in record.items():
        normalized_key = key
        if key.startswith("capacity__"):
            normalized_key = "capacity_" + key.removeprefix("capacity__")
        elif key.startswith("produced__"):
            normalized_key = "produced_" + key.removeprefix("produced__")
        normalized_record[normalized_key] = value
    return normalized_record


def _records_from_sheet(path: Path, sheet_name: str) -> list[dict[str, Any]]:
    import pandas as pd

    try:
        frame = pd.read_excel(path, sheet_name=sheet_name)
    except ValueError:
        return []
    if frame.empty:
        return []
    records = []
    for record in frame.to_dict(orient="records"):
        normalized_record = _normalize_result_record(record)
        normalized_record = {
            key: _safe_excel_value(value)
            for key, value in normalized_record.items()
        }
        records.append(normalized_record)
    return records


def _load_existing_year_results(
    output_path: Path,
    year: int,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    if not output_path.is_file():
        return [], [], [], []

    results = _records_from_sheet(output_path, "results")
    components = _records_from_sheet(output_path, "components")
    parameters = _records_from_sheet(output_path, "parameters_applied")
    errors = _records_from_sheet(output_path, "errors")

    for sheet_name, records in [
        ("results", results),
        ("components", components),
        ("parameters_applied", parameters),
        ("errors", errors),
    ]:
        wrong_years = {
            int(record["scenario_year"])
            for record in records
            if record.get("scenario_year") is not None
            and int(record["scenario_year"]) != year
        }
        if wrong_years:
            raise ValueError(
                f"Existing sheet '{sheet_name}' in {output_path} contains "
                f"unexpected scenario years: {sorted(wrong_years)}"
            )

    return results, components, parameters, errors


def _progress_path(config: RunnerConfig) -> Path:
    return config.output_dir / PROGRESS_FILE_NAME


def _load_progress(config: RunnerConfig) -> dict[str, Any]:
    path = _progress_path(config)
    if not path.is_file():
        return {"version": 1, "scenario_years": {}}

    with path.open("r", encoding="utf-8") as file:
        progress = json.load(file)
    if progress.get("version") != 1:
        raise ValueError(
            f"Unsupported progress file version in {path}: "
            f"{progress.get('version')}"
        )
    progress.setdefault("scenario_years", {})
    return progress


def _save_progress(config: RunnerConfig, progress: dict[str, Any]) -> None:
    path = _progress_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp.json")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(progress, file, indent=2, ensure_ascii=True)
    os.replace(temporary_path, path)


def _completed_country_records(
    progress: dict[str, Any],
    year: int,
) -> dict[str, Any]:
    year_state = progress.setdefault("scenario_years", {}).setdefault(
        str(year),
        {},
    )
    return year_state.setdefault("completed_countries", {})


def _mark_country_completed(
    config: RunnerConfig,
    progress: dict[str, Any],
    year: int,
    country: str,
    region: str,
    profile_count: int,
    output_path: Path,
) -> None:
    completed = _completed_country_records(progress, year)
    completed[country] = {
        "region": region,
        "profile_count": profile_count,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "output_file": str(output_path),
    }
    _save_progress(config, progress)


def _remove_country_records(
    records: list[dict[str, Any]],
    country: str,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("country") != country
    ]


def _format_output_workbook(path: Path) -> None:
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.table import Table, TableStyleInfo

    workbook = load_workbook(path)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)

    for sheet in workbook.worksheets:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        sheet.sheet_view.showGridLines = False

        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")

        for cell in sheet[1]:
            header = str(cell.value or "").lower()
            if header == "wacc":
                for data_cell in sheet.iter_cols(
                    min_col=cell.column,
                    max_col=cell.column,
                    min_row=2,
                ):
                    for item in data_cell:
                        item.number_format = "0.00%"
            elif (
                "cost" in header
                or "capacity" in header
                or "quantity" in header
                or header in {"economic_objective", "ecologic_objective", "value"}
            ):
                for data_cell in sheet.iter_cols(
                    min_col=cell.column,
                    max_col=cell.column,
                    min_row=2,
                ):
                    for item in data_cell:
                        item.number_format = "#,##0.000000"

        for column_cells in sheet.columns:
            values = [str(cell.value) for cell in column_cells if cell.value is not None]
            width = min(max((len(value) for value in values), default=8) + 2, 42)
            sheet.column_dimensions[column_cells[0].column_letter].width = width

        if sheet.max_row >= 2 and sheet.max_column >= 1:
            table_name = f"tbl_{sheet.title.replace(' ', '_')}"
            table = Table(displayName=table_name[:255], ref=sheet.dimensions)
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium2",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )
            sheet.add_table(table)

    workbook.save(path)


def write_year_results(
    output_path: Path,
    year: int,
    completed_countries: list[str],
    results: list[dict[str, Any]],
    components: list[dict[str, Any]],
    applied_parameters: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    import pandas as pd

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp.xlsx")
    results = [_normalize_result_record(record) for record in results]

    result_base_columns = [
        "scenario_year",
        "country",
        "region",
        "profile",
        "wacc",
        "status",
        "solver_status",
        "economic_objective",
        "ecologic_objective",
        "total_costs",
        "produced_quantity",
        "cost_per_produced_unit",
    ]
    result_extra_columns = sorted(
        {
            key
            for row in results
            for key in row
            if key not in result_base_columns
        }
    )
    results_df = pd.DataFrame(
        results,
        columns=result_base_columns + result_extra_columns,
    )
    components_df = pd.DataFrame(
        components,
        columns=[
            "scenario_year",
            "country",
            "region",
            "profile",
            "component",
            "component_type",
            "capacity",
            "solver_capacity",
            "transferred_capacity",
            "solver_output_quantity",
            "capacity_basis",
            "investment",
            "annualized_investment",
            "fixed_costs",
            "variable_costs",
            "component_total_costs",
        ],
    )
    parameters_df = pd.DataFrame(
        applied_parameters,
        columns=[
            "country",
            "region",
            "wacc",
            "year",
            "scope",
            "scope_name",
            "component",
            "parameter",
            "value",
            "unit",
            "source",
            "note",
        ],
    )
    errors_df = pd.DataFrame(
        errors,
        columns=[
            "scenario_year",
            "country",
            "region",
            "profile",
            "error",
        ],
    )

    summary = pd.DataFrame(
        [
            {"metric": "scenario_year", "value": year},
            {"metric": "last_checkpoint", "value": datetime.now().isoformat(timespec="seconds")},
            {"metric": "countries_completed", "value": len(completed_countries)},
            {"metric": "country_names", "value": ", ".join(completed_countries)},
            {"metric": "profile_runs", "value": len(results_df)},
            {
                "metric": "optimal_runs",
                "value": int((results_df.get("status") == "optimal").sum())
                if not results_df.empty
                else 0,
            },
            {
                "metric": "failed_runs",
                "value": int((results_df.get("status") == "failed").sum())
                if not results_df.empty
                else 0,
            },
        ]
    )

    with pd.ExcelWriter(temporary_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        results_df.to_excel(writer, sheet_name="results", index=False)
        components_df.to_excel(writer, sheet_name="components", index=False)
        parameters_df.to_excel(
            writer,
            sheet_name="parameters_applied",
            index=False,
        )
        errors_df.to_excel(writer, sheet_name="errors", index=False)

    _format_output_workbook(temporary_path)
    os.replace(temporary_path, output_path)


def _applied_rows_with_country(
    applied: list[dict[str, Any]],
    settings: CountrySettings,
) -> list[dict[str, Any]]:
    return [
        {
            "country": settings.country,
            "region": settings.region,
            "wacc": settings.wacc,
            **{key: _safe_excel_value(value) for key, value in row.items()},
        }
        for row in applied
    ]


def run(config: RunnerConfig) -> None:
    countries_df, parameters_df = _read_parameter_workbook(
        config.parameters_xlsx
    )
    country_dirs = _discover_countries(config)
    if not country_dirs:
        raise SystemExit("No country folders found.")

    base_pm_object = _build_base_parameter_object(config)
    progress = _load_progress(config)

    for year in config.scenario_years:
        print(f"\n=== Scenario year {year} ===")
        output_path = config.output_dir / f"country_profile_results_{year}.xlsx"

        (
            year_results,
            year_components,
            year_parameters,
            year_errors,
        ) = _load_existing_year_results(output_path, year)

        logged_completed = _completed_country_records(progress, year)
        resumable_completed = set()
        for country, record in logged_completed.items():
            country_rows = [
                row
                for row in year_results
                if row.get("country") == country
            ]
            country_component_rows = [
                row
                for row in year_components
                if row.get("country") == country
            ]
            expected_profiles = int(record.get("profile_count", 0))
            has_current_capacity_schema = (
                bool(country_component_rows)
                and all(
                    row.get("solver_capacity") is not None
                    and row.get("transferred_capacity") is not None
                    and row.get("solver_output_quantity") is not None
                    for row in country_component_rows
                )
            )
            if (
                country_rows
                and len(country_rows) == expected_profiles
                and has_current_capacity_schema
                and all(
                    row.get("status") == "optimal"
                    for row in country_rows
                )
            ):
                resumable_completed.add(country)
            else:
                print(
                    f"Progress entry for {year}/{country} is not backed by "
                    "a complete optimal result set using the current output "
                    "schema; country will be rerun."
                )

        completed_countries = sorted(resumable_completed)
        if completed_countries:
            print(
                f"Resume {year}: {len(completed_countries)} completed "
                "countries loaded from progress log."
            )

        for country_dir in country_dirs:
            country = country_dir.name

            if country == "00_Information":
                continue
            if country in resumable_completed:
                print(f"{year}: Skip completed country {country}")
                continue

            print(f"{year}: {country}")
            country_successful = False
            completed_profile_count = 0

            # Remove stale rows from an interrupted or previously failed run
            # before recalculating this country.
            year_results = _remove_country_records(year_results, country)
            year_components = _remove_country_records(
                year_components,
                country,
            )
            year_parameters = _remove_country_records(
                year_parameters,
                country,
            )
            year_errors = _remove_country_records(year_errors, country)

            try:
                settings = _country_settings(countries_df, country)
                parameter_rows = _parameter_rows_for_country(
                    parameters_df,
                    year,
                    settings,
                )
                if parameter_rows.empty:
                    raise ValueError(
                        f"No active parameters found for {country}, "
                        f"region {settings.region}, year {year}."
                    )

                country_pm_object = deepcopy(base_pm_object)
                applied = _apply_parameters(
                    country_pm_object,
                    parameter_rows,
                )
                if settings.wacc is not None:
                    country_pm_object.set_wacc(settings.wacc)

                profile_dir = _profile_dir(
                    config,
                    country_dir,
                    year,
                )
                if not profile_dir.is_dir():
                    raise FileNotFoundError(
                        f"Profile directory not found: {profile_dir}"
                    )
                profiles = _profile_files(
                    profile_dir,
                    config.recursive_profiles,
                )
                if not profiles:
                    raise FileNotFoundError(
                        f"No profile files found in {profile_dir}"
                    )

                jobs = [
                    {
                        "pm_object": deepcopy(country_pm_object),
                        "profile_dir": profile_dir,
                        "profile": profile,
                        "country": country,
                        "region": settings.region,
                        "year": year,
                        "wacc": settings.wacc,
                        "solver": config.solver,
                    }
                    for profile in profiles
                ]
                country_results = _run_country_jobs(jobs, config.cores)

                unsuccessful = [
                    result
                    for result in country_results
                    if result.get("result", {}).get("status") != "optimal"
                ]
                if unsuccessful:
                    failed_result = unsuccessful[0]
                    result_row = failed_result.get("result", {})
                    error_row = failed_result.get("error") or {}
                    raise ProfileOptimizationError(
                        year=year,
                        country=country,
                        region=settings.region,
                        profile=str(result_row.get("profile", "unknown")),
                        profile_path=str(
                            profile_dir
                            / str(result_row.get("profile", "unknown"))
                        ),
                        exception_type=str(
                            result_row.get("solver_status", "unknown")
                        ),
                        detail=str(
                            error_row.get(
                                "error",
                                f"Non-optimal result row: {result_row}",
                            )
                        ),
                        traceback_text="No worker traceback was returned.",
                    )

                year_results.extend(
                    result["result"] for result in country_results
                )
                year_components.extend(
                    row
                    for result in country_results
                    for row in result["components"]
                )
                year_errors.extend(
                    result["error"]
                    for result in country_results
                    if result["error"] is not None
                )
                year_parameters.extend(
                    _applied_rows_with_country(applied, settings)
                )
                completed_countries.append(country)
                country_successful = True
                completed_profile_count = len(country_results)

            except OptimizationNotOptimalError as exc:
                year_errors.append(
                    {
                        "scenario_year": exc.year,
                        "country": exc.country,
                        "region": settings.region,
                        "profile": exc.profile,
                        "error": str(exc),
                    }
                )
                write_year_results(
                    output_path=output_path,
                    year=year,
                    completed_countries=completed_countries,
                    results=year_results,
                    components=year_components,
                    applied_parameters=year_parameters,
                    errors=year_errors,
                )
                print(f"\nABORT: {exc}")
                print(f"Checkpoint written before abort: {output_path}")
                raise SystemExit(str(exc)) from exc

            except ProfileOptimizationError as exc:
                year_errors.append(
                    {
                        "scenario_year": exc.year,
                        "country": exc.country,
                        "region": exc.region,
                        "profile": exc.profile,
                        "error": str(exc),
                    }
                )
                write_year_results(
                    output_path=output_path,
                    year=year,
                    completed_countries=completed_countries,
                    results=year_results,
                    components=year_components,
                    applied_parameters=year_parameters,
                    errors=year_errors,
                )
                print(f"\nABORT: {exc}")
                print(f"Checkpoint written before abort: {output_path}")
                raise SystemExit(str(exc)) from exc

            except Exception as exc:  # noqa: BLE001 - checkpoint and continue.
                year_errors.append(
                    {
                        "scenario_year": year,
                        "country": country,
                        "region": None,
                        "profile": None,
                        "error": repr(exc),
                    }
                )
                print(f"Skip {country}: {exc}")

            write_year_results(
                output_path=output_path,
                year=year,
                completed_countries=completed_countries,
                results=year_results,
                components=year_components,
                applied_parameters=year_parameters,
                errors=year_errors,
            )
            print(f"Checkpoint written: {output_path}")
            if country_successful:
                _mark_country_completed(
                    config=config,
                    progress=progress,
                    year=year,
                    country=country,
                    region=settings.region,
                    profile_count=completed_profile_count,
                    output_path=output_path,
                )
                resumable_completed.add(country)
                print(
                    f"Progress logged: year={year}, country={country}, "
                    f"profiles={completed_profile_count}"
                )

        print(f"Final result for {year}: {output_path}")


def main() -> None:
    config = build_config()
    validate_config(config)
    print(
        f"Runner version: {RUNNER_VERSION}\n"
        f"Countries: {config.countries_root}\n"
        f"YAML: {config.settings_yaml}\n"
        f"Parameters: {config.parameters_xlsx}\n"
        f"Years: {config.scenario_years}\n"
        f"Workers per country: {config.cores}"
    )
    run(config)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
