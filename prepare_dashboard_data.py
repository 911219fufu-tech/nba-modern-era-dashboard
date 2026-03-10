"""Reprocess raw NBA game data into a clean team-game dataset for dashboards.

Usage:
    python prepare_dashboard_data.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

INPUT_PATH = Path("game.csv")
OUTPUT_PATH = Path("data/nba_team_game_1999_2023.csv")
REPORT_PATH = Path("data_prep_report.md")

DATE_START = pd.Timestamp("1999-10-01")
DATE_END = pd.Timestamp("2023-06-30")

CURRENT_ABBREVIATIONS = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
]

HISTORICAL_TO_CURRENT = {
    "TRI": "ATL", "MLH": "ATL", "STL": "ATL",
    "NYN": "BKN", "NJN": "BKN",
    "CHH": "CHA",
    "NOH": "NOP", "NOK": "NOP", "NOL": "NOP",
    "NOJ": "UTA",
    "FTW": "DET",
    "PHW": "GSW", "SFW": "GSW",
    "BUF": "LAC", "SDC": "LAC", "SDP": "LAC",
    "MNL": "LAL",
    "VAN": "MEM",
    "SEA": "OKC",
    "SYR": "PHI",
    "ROC": "SAC", "CIN": "SAC", "KCO": "SAC", "KCK": "SAC", "KAN": "SAC",
    "CHP": "WAS", "BAL": "WAS", "CAP": "WAS", "WSB": "WAS",
}

for _abbr in CURRENT_ABBREVIATIONS:
    HISTORICAL_TO_CURRENT.setdefault(_abbr, _abbr)


@dataclass
class ColumnMap:
    date: str
    team_home: str
    team_away: str
    points_home: str
    points_away: str
    fg_home: str
    fg_away: str
    fg3a_home: str | None
    fg3a_away: str | None
    fg3m_home: str | None
    fg3m_away: str | None
    fg3_pct_home: str | None
    fg3_pct_away: str | None
    fga_home: str | None
    fga_away: str | None
    season_type: str | None
    game_id: str | None


def find_first_existing(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    colset = set(df.columns)
    for col in candidates:
        if col in colset:
            return col
    return None


def detect_columns(df: pd.DataFrame) -> ColumnMap:
    date_col = find_first_existing(df, ["game_date", "date", "game_date_est"])
    if not date_col:
        raise KeyError("Missing date column.")

    team_home = find_first_existing(df, ["team_abbreviation_home", "home_team", "team_home"])
    team_away = find_first_existing(df, ["team_abbreviation_away", "away_team", "team_away"])
    points_home = find_first_existing(df, ["pts_home", "home_points", "points_home"])
    points_away = find_first_existing(df, ["pts_away", "away_points", "points_away"])
    fg_home = find_first_existing(df, ["fg_pct_home", "home_fg_pct", "fg_home"])
    fg_away = find_first_existing(df, ["fg_pct_away", "away_fg_pct", "fg_away"])
    fg3a_home = find_first_existing(df, ["fg3a_home", "fg3aHome", "home_fg3a", "fg3a"])
    fg3a_away = find_first_existing(df, ["fg3a_away", "fg3aAway", "away_fg3a", "fg3a"])
    fg3m_home = find_first_existing(df, ["fg3m_home", "fg3mHome", "home_fg3m", "fg3m"])
    fg3m_away = find_first_existing(df, ["fg3m_away", "fg3mAway", "away_fg3m", "fg3m"])
    fg3_pct_home = find_first_existing(
        df, ["fg3_pct_home", "fg3PctHome", "home_fg3_pct", "fg3_pct"]
    )
    fg3_pct_away = find_first_existing(
        df, ["fg3_pct_away", "fg3PctAway", "away_fg3_pct", "fg3_pct"]
    )
    fga_home = find_first_existing(df, ["fga_home", "fgaHome", "home_fga", "fga"])
    fga_away = find_first_existing(df, ["fga_away", "fgaAway", "away_fga", "fga"])

    required = {
        "team_home": team_home,
        "team_away": team_away,
        "points_home": points_home,
        "points_away": points_away,
        "fg_home": fg_home,
        "fg_away": fg_away,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    return ColumnMap(
        date=date_col,
        team_home=team_home,
        team_away=team_away,
        points_home=points_home,
        points_away=points_away,
        fg_home=fg_home,
        fg_away=fg_away,
        fg3a_home=fg3a_home,
        fg3a_away=fg3a_away,
        fg3m_home=fg3m_home,
        fg3m_away=fg3m_away,
        fg3_pct_home=fg3_pct_home,
        fg3_pct_away=fg3_pct_away,
        fga_home=fga_home,
        fga_away=fga_away,
        season_type=find_first_existing(df, ["season_type", "game_type", "type"]),
        game_id=find_first_existing(df, ["game_id", "id", "gameid"]),
    )


def normalize_teams(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.upper()
        .str.strip()
        .map(HISTORICAL_TO_CURRENT)
        .fillna(series.astype(str).str.upper().str.strip())
    )


def derive_season_year(dates: pd.Series) -> pd.Series:
    return dates.dt.year.where(dates.dt.month >= 10, dates.dt.year - 1).astype(int)


def derive_season_label(season_year: pd.Series) -> pd.Series:
    return season_year.astype(str) + "-" + ((season_year + 1) % 100).astype(str).str.zfill(2)


def transform_to_team_game(
    df: pd.DataFrame, cols: ColumnMap
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    warnings: list[str] = []
    included_3pt_cols: list[str] = []
    missing_3pt_cols: list[str] = []

    work = df.copy()
    work[cols.date] = pd.to_datetime(work[cols.date], errors="coerce")
    work = work[work[cols.date].notna()].copy()

    # Date filter required by project spec.
    work = work[work[cols.date].between(DATE_START, DATE_END, inclusive="both")].copy()

    work[cols.team_home] = normalize_teams(work[cols.team_home])
    work[cols.team_away] = normalize_teams(work[cols.team_away])

    modern_set = set(CURRENT_ABBREVIATIONS)
    valid_mask = work[cols.team_home].isin(modern_set) & work[cols.team_away].isin(modern_set)
    dropped_non_modern = int((~valid_mask).sum())
    work = work[valid_mask].copy()
    if dropped_non_modern:
        warnings.append(
            f"Dropped {dropped_non_modern} games with non-modern team abbreviations after normalization."
        )

    season_type_values = work[cols.season_type].copy() if cols.season_type else pd.Series("Regular", index=work.index)
    if cols.season_type:
        null_season_type = int(season_type_values.isna().sum())
        if null_season_type:
            season_type_values = season_type_values.fillna("Regular")
            warnings.append(f"Filled {null_season_type} missing season_type values with 'Regular'.")

    game_id_values = work[cols.game_id].astype(str) if cols.game_id else (
        work[cols.date].dt.strftime("%Y%m%d") + "_" + work.index.astype(str)
    )

    home_dict = {
        "date": work[cols.date],
        "team": work[cols.team_home],
        "opponent": work[cols.team_away],
        "home_away": "Home",
        "points": pd.to_numeric(work[cols.points_home], errors="coerce"),
        "fg_pct": pd.to_numeric(work[cols.fg_home], errors="coerce"),
        "opponent_points": pd.to_numeric(work[cols.points_away], errors="coerce"),
        "season_type": season_type_values.values,
        "game_id": game_id_values.values,
    }
    away_dict = {
        "date": work[cols.date],
        "team": work[cols.team_away],
        "opponent": work[cols.team_home],
        "home_away": "Away",
        "points": pd.to_numeric(work[cols.points_away], errors="coerce"),
        "fg_pct": pd.to_numeric(work[cols.fg_away], errors="coerce"),
        "opponent_points": pd.to_numeric(work[cols.points_home], errors="coerce"),
        "season_type": season_type_values.values,
        "game_id": game_id_values.values,
    }

    metric_pairs = [
        ("fg3a", cols.fg3a_home, cols.fg3a_away),
        ("fg3m", cols.fg3m_home, cols.fg3m_away),
        ("fg3_pct", cols.fg3_pct_home, cols.fg3_pct_away),
        ("fga", cols.fga_home, cols.fga_away),
    ]
    for metric_name, home_col, away_col in metric_pairs:
        if home_col and away_col:
            home_dict[metric_name] = pd.to_numeric(work[home_col], errors="coerce")
            away_dict[metric_name] = pd.to_numeric(work[away_col], errors="coerce")
            included_3pt_cols.append(metric_name)
        else:
            missing_3pt_cols.append(metric_name)
            if home_col or away_col:
                missing_side = "away" if home_col else "home"
                warnings.append(
                    f"Could not include `{metric_name}` because {missing_side} column is missing."
                )
            else:
                warnings.append(
                    f"Could not include `{metric_name}` because both home/away columns are missing."
                )

    home = pd.DataFrame(home_dict)
    away = pd.DataFrame(away_dict)

    out = pd.concat([home, away], ignore_index=True)
    if "fg3a" in out.columns and "fga" in out.columns:
        out["three_pa_rate"] = np.where(out["fga"] > 0, out["fg3a"] / out["fga"], np.nan)
    out["season_year"] = derive_season_year(out["date"])
    out["season_label"] = derive_season_label(out["season_year"])
    out["win"] = np.where(out["points"] > out["opponent_points"], "Win", "Loss")

    # Remove rows with missing critical fields to keep dataset dashboard-ready.
    critical = ["team", "date", "points", "fg_pct"]
    missing_critical = int(out[critical].isna().any(axis=1).sum())
    if missing_critical:
        out = out.dropna(subset=critical).copy()
        warnings.append(f"Dropped {missing_critical} rows due to NaN in critical fields: {critical}.")

    # Enforce only modern team abbreviations after full transformation.
    out = out[out["team"].isin(modern_set) & out["opponent"].isin(modern_set)].copy()

    before_dedup = len(out)
    out = out.drop_duplicates().copy()
    dedup_removed = before_dedup - len(out)
    if dedup_removed:
        warnings.append(f"Removed {dedup_removed} duplicate rows.")

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")

    final_cols = [
        "date",
        "team",
        "opponent",
        "home_away",
        "points",
        "fg_pct",
        "win",
        "season_type",
        "game_id",
        "season_year",
        "season_label",
    ]
    optional_col_order = ["fg3a", "fg3m", "fg3_pct", "fga", "three_pa_rate"]
    final_cols.extend([col for col in optional_col_order if col in out.columns])

    return (
        out[final_cols].sort_values(["date", "game_id", "home_away"]).reset_index(drop=True),
        warnings,
        included_3pt_cols,
        missing_3pt_cols,
    )


def write_report(
    df: pd.DataFrame, warnings: list[str], included_3pt_cols: list[str], missing_3pt_cols: list[str]
) -> None:
    season_years = sorted(df["season_year"].dropna().astype(int).unique().tolist())
    date_min = df["date"].min() if not df.empty else "N/A"
    date_max = df["date"].max() if not df.empty else "N/A"
    warning_lines = "\n".join(f"- {w}" for w in warnings) if warnings else "- None"
    included_lines = ", ".join(included_3pt_cols) if included_3pt_cols else "None"
    missing_lines = ", ".join(sorted(set(missing_3pt_cols))) if missing_3pt_cols else "None"

    report = f"""# Data Preparation Report

## Post-filter Date Range
- min(date): {date_min}
- max(date): {date_max}

## Dataset Size
- Total row count: {len(df)}
- Unique teams: {df['team'].nunique()}

## Seasons
- Unique season_year values: {season_years}

## Assumptions
- Historical team abbreviations were normalized to modern 30-team abbreviations.
- Any game still containing non-modern abbreviations after normalization was dropped.
- If `season_type` was missing, values were set to `Regular`.
- `win` is computed from `points > opponent_points`.

## Data Quality Actions
{warning_lines}

## Three-Point Metrics
- Included columns: {included_lines}
- Missing/unavailable columns: {missing_lines}
"""

    REPORT_PATH.write_text(report)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)
    cols = detect_columns(df)

    processed, warnings, included_3pt_cols, missing_3pt_cols = transform_to_team_game(df, cols)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(OUTPUT_PATH, index=False)
    write_report(processed, warnings, included_3pt_cols, missing_3pt_cols)

    # Sanity check prints requested by user.
    print(f"min(date): {processed['date'].min()}")
    print(f"max(date): {processed['date'].max()}")
    print(f"number of rows: {len(processed)}")
    print(
        "unique season_year values:",
        sorted(processed["season_year"].dropna().astype(int).unique().tolist()),
    )
    print("included 3pt columns:", included_3pt_cols if included_3pt_cols else "None")
    if "three_pa_rate" in processed.columns:
        print("three_pa_rate describe:")
        print(processed["three_pa_rate"].describe().to_string())
    print("first 5 rows:")
    print(processed.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
