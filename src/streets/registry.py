"""Registry of Czech municipalities (RÚIAN + ČSÚ), migrated from the GeoGram_sufix-ice project.

Used to disambiguate settlement names before querying OSM (multiple
municipalities can share a name — e.g. several villages named "Lhota") and
to attach population/district/region metadata to the sample.
"""

from pathlib import Path

import pandas as pd

EXTERNAL_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "geogram"


def load_ui_obec(path: Path) -> pd.DataFrame:
    """Load UI_OBEC.csv (RÚIAN municipality register)."""
    df = pd.read_csv(path, sep=";", encoding="cp1250")
    return df.rename(columns={
        "KOD": "code",
        "NAZEV": "name",
        "OKRES_KOD": "district_code",
        "STATUS_KOD": "status_code",
    })


def load_ui_okres(path: Path) -> pd.DataFrame:
    """Load UI_OKRES.csv, mapping district codes to names."""
    df = pd.read_csv(path, sep=";", encoding="cp1250")
    return df.rename(columns={
        "KOD": "district_code",
        "NAZEV": "district_name",
        "VUSC_KOD": "region_code",
    })[["district_code", "district_name", "region_code"]]


def load_ui_vusc(path: Path) -> pd.DataFrame:
    """Load UI_VUSC.csv, mapping region codes to names."""
    df = pd.read_csv(path, sep=";", encoding="cp1250")
    return df.rename(columns={
        "KOD": "region_code",
        "NAZEV": "region_name",
    })[["region_code", "region_name"]]


def load_population(path: Path) -> pd.DataFrame:
    """Load ČSÚ population-by-municipality Excel export."""
    df = pd.read_excel(path, sheet_name="List1", skiprows=4)
    df.columns = [
        "district_code", "municipality_code", "municipality_name",
        "population_total", "population_men", "population_women",
        "avg_age_total", "avg_age_men", "avg_age_women",
    ]
    df = df.dropna(subset=["municipality_code"])
    df["municipality_code"] = df["municipality_code"].astype("Int64")
    return df


def load_coordinates(path: Path) -> pd.DataFrame:
    """Load municipality centroid coordinates."""
    df = pd.read_csv(path, encoding="utf-8")
    df = df.rename(columns={
        "Kód obce": "municipality_code",
        "Latitude": "latitude",
        "Longitude": "longitude",
    })[["municipality_code", "latitude", "longitude"]]
    df = df.drop_duplicates(subset="municipality_code")
    df["municipality_code"] = df["municipality_code"].astype("Int64")
    return df


def load_all_municipalities(data_dir: Path = EXTERNAL_DIR) -> pd.DataFrame:
    """Build the full, denormalized table of all ~6,259 Czech municipalities."""
    obec = load_ui_obec(data_dir / "UI_OBEC.csv")
    okres = load_ui_okres(data_dir / "UI_OKRES.csv")
    vusc = load_ui_vusc(data_dir / "UI_VUSC.csv")

    df = obec.merge(okres, on="district_code", how="left")
    df = df.merge(vusc, on="region_code", how="left")

    population = load_population(data_dir / "pocty_obyvatel" / "1300722503.xlsx")
    pop_subset = population[["municipality_code", "population_total", "population_men", "population_women", "avg_age_total"]]
    df = df.merge(pop_subset, left_on="code", right_on="municipality_code", how="left")
    df = df.drop(columns=["municipality_code"], errors="ignore")

    coordinates = load_coordinates(data_dir / "33bcdd-souradnice-mest-3d4b1fd" / "souradnice.csv")
    df = df.merge(coordinates, left_on="code", right_on="municipality_code", how="left")
    df = df.drop(columns=["municipality_code"], errors="ignore")

    columns = [
        "code", "name", "district_code", "district_name", "region_code", "region_name",
        "status_code", "population_total", "population_men", "population_women",
        "avg_age_total", "latitude", "longitude",
    ]
    df = df[columns].sort_values(by=["region_code", "district_code", "name"]).reset_index(drop=True)
    return df


def find_municipality(df: pd.DataFrame, name: str, district_hint: str | None = None) -> pd.DataFrame:
    """Look up a municipality by name; narrow by district_name if the name is ambiguous."""
    matches = df[df["name"] == name]
    if district_hint is not None:
        matches = matches[matches["district_name"] == district_hint]
    return matches
