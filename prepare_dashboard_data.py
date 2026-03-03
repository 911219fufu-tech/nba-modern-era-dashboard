"""Prepare a dashboard-ready NBA team-game dataset.

Running this script will:
1. Normalize team abbreviations in home/away columns using normalize_teams.py
2. Filter games to NBA seasons 1999-2000 through 2022-2023 using season_year
3. Expand each game to two team-game rows (home and away)
4. Compute win/loss and point differential
5. Write dashboard_ready_season_filtered.csv and data_prep_report.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from normalize_teams import CURRENT_ABBREVIATIONS, normalize_team_abbreviations

RAW_PATH = Path("game.csv")
NORMALIZED_PATH = Path("game_normalized.csv")
SEASON_FILTERED_OUTPUT_PATH = Path("dashboard_ready_season_filtered.csv")
REPORT_PATH = Path("data_prep_report.md")

SEASON_YEAR_START = 1999
SEASON_YEAR_END = 2022


@dataclass
class SelectedColumns:
    date_col: str
    game_id_col: str | None
    pts_home_col: str
    pts_away_col: str
    fg_home_col: str
    fg_away_col: str
    season_type_col: str | None


def _find_first_existing(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    columns = set(df.columns)
    for col in candidates:
        if col in columns:
            return col
    return None


def detect_columns(df: pd.DataFrame) -> SelectedColumns:
    """Best-effort mapping for required fields across common naming variants."""
    date_col = _find_first_existing(
        df,
        ["game_date", "date", "gameDate", "game_datetime", "game_date_est"],
    )
    if not date_col:
        raise KeyError("Could not detect a game date column.")

    game_id_col = _find_first_existing(df, ["game_id", "id", "gameid"]) 

    pts_home_col = _find_first_existing(
        df,
        ["pts_home", "home_points", "points_home", "score_home", "home_pts"],
    )
    pts_away_col = _find_first_existing(
        df,
        ["pts_away", "away_points", "points_away", "score_away", "away_pts"],
    )
    if not pts_home_col or not pts_away_col:
        raise KeyError("Could not detect both home and away points columns.")

    fg_home_col = _find_first_existing(
        df,
        [
            "fg_pct_home",
            "home_fg_pct",
            "fgp_home",
            "fg_percent_home",
            "field_goal_pct_home",
        ],
    )
    fg_away_col = _find_first_existing(
        df,
        [
            "fg_pct_away",
            "away_fg_pct",
            "fgp_away",
            "fg_percent_away",
            "field_goal_pct_away",
        ],
    )
    if not fg_home_col or not fg_away_col:
        raise KeyError("Could not detect both home and away FG% columns.")

    season_type_col = _find_first_existing(
        df,
        [
            "season_type",
            "season_type_home",
            "game_type",
            "type",
            "playoffs",
            "is_playoffs",
            "postseason",
        ],
    )

    return SelectedColumns(
        date_col=date_col,
        game_id_col=game_id_col,
        pts_home_col=pts_home_col,
        pts_away_col=pts_away_col,
        fg_home_col=fg_home_col,
        fg_away_col=fg_away_col,
        season_type_col=season_type_col,
    )


def normalize_source_data() -> tuple[pd.DataFrame, list[str]]:
    """Load raw data and normalize team abbreviations to modern teams."""
    warnings: list[str] = []
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing required input file: {RAW_PATH}")

    raw_df = pd.read_csv(RAW_PATH)
    print("Detected columns in raw input:")
    print(list(raw_df.columns))

    normalized_df = normalize_team_abbreviations(raw_df)
    normalized_df.to_csv(NORMALIZED_PATH, index=False)

    normalized_df["team_abbreviation_home"] = (
        normalized_df["team_abbreviation_home"].astype(str).str.upper()
    )
    normalized_df["team_abbreviation_away"] = (
        normalized_df["team_abbreviation_away"].astype(str).str.upper()
    )

    home_values = set(normalized_df["team_abbreviation_home"].dropna())
    away_values = set(normalized_df["team_abbreviation_away"].dropna())
    modern_set = set(CURRENT_ABBREVIATIONS)
    invalid_home = sorted(home_values - modern_set)
    invalid_away = sorted(away_values - modern_set)

    if invalid_home or invalid_away:
        before = len(normalized_df)
        keep_mask = normalized_df["team_abbreviation_home"].isin(modern_set) & normalized_df[
            "team_abbreviation_away"
        ].isin(modern_set)
        normalized_df = normalized_df[keep_mask].copy()
        dropped = before - len(normalized_df)
        warnings.append(
            "Dropped games with abbreviations outside modern 30-team set after normalization "
            f"({dropped} rows). Invalid home={invalid_home}, invalid away={invalid_away}"
        )

    normalized_df.to_csv(NORMALIZED_PATH, index=False)

    return normalized_df, warnings


def infer_season_type(series: pd.Series) -> pd.Series:
    """Normalize season type labels to {Regular, Playoffs} when possible."""
    s = series.astype(str).str.strip().str.lower()
    inferred = pd.Series("Regular", index=series.index)

    playoff_tokens = ["playoff", "postseason", "post season", "po"]
    regular_tokens = ["regular", "reg", "rs"]

    is_playoff = s.apply(lambda x: any(token in x for token in playoff_tokens))
    is_regular = s.apply(lambda x: any(token in x for token in regular_tokens))

    inferred.loc[is_playoff] = "Playoffs"
    inferred.loc[is_regular] = "Regular"

    # If values are numeric flags (e.g., 1/0), treat 1 as playoffs.
    numeric = pd.to_numeric(series, errors="coerce")
    inferred.loc[numeric == 1] = "Playoffs"
    inferred.loc[numeric == 0] = "Regular"

    return inferred


def derive_season_year(date_series: pd.Series) -> pd.Series:
    """Map dates to NBA season start year.

    NBA seasons cross calendar years, starting in Oct/Nov and ending the next year.
    This label is more accurate than calendar year for season-level analysis.
    """
    years = date_series.dt.year
    months = date_series.dt.month
    return years.where(months >= 10, years - 1).astype("int64")


def derive_season_label(season_year_series: pd.Series) -> pd.Series:
    """Create readable season labels like 1999-00, 2009-10, 2022-23."""
    next_two_digit = ((season_year_series + 1) % 100).astype("int64")
    return season_year_series.astype(str) + "-" + next_two_digit.astype(str).str.zfill(2)


def build_team_game_table(df: pd.DataFrame, cols: SelectedColumns) -> tuple[pd.DataFrame, list[str], dict[str, int]]:
    """Create one row per team per game from game-level home/away records."""
    warnings: list[str] = []
    counts: dict[str, int] = {}

    working = df.copy()
    working[cols.date_col] = pd.to_datetime(working[cols.date_col], errors="coerce")

    before_date_filter = len(working)
    working = working[working[cols.date_col].notna()].copy()
    dropped_bad_dates = before_date_filter - len(working)
    if dropped_bad_dates:
        warnings.append(f"Dropped {dropped_bad_dates} rows with invalid or missing game dates.")

    working["year"] = working[cols.date_col].dt.year
    working["season_year"] = derive_season_year(working[cols.date_col])
    working["season_label"] = derive_season_label(working["season_year"])
    before_season_filter = len(working)
    working = working[
        working["season_year"].between(SEASON_YEAR_START, SEASON_YEAR_END, inclusive="both")
    ].copy()

    counts["rows_before_filtering"] = before_date_filter
    counts["rows_after_date_parse"] = before_season_filter
    counts["rows_after_season_filter"] = len(working)

    if cols.season_type_col:
        season_type = infer_season_type(working[cols.season_type_col])
        unknown_mask = season_type.isna() | (season_type == "")
        if unknown_mask.any():
            season_type.loc[unknown_mask] = "Regular"
            warnings.append("Some season_type values were empty after inference; defaulted to 'Regular'.")
    else:
        season_type = pd.Series("Regular", index=working.index)
        warnings.append("No season type column detected; defaulted all rows to 'Regular'.")

    game_id_series = (
        working[cols.game_id_col]
        if cols.game_id_col
        else (working[cols.date_col].dt.strftime("%Y%m%d") + "_" + working.index.astype(str))
    )

    home = pd.DataFrame(
        {
            "date": working[cols.date_col],
            "year": working["year"].astype("int64"),
            "season_year": working["season_year"].astype("int64"),
            "season_label": working["season_label"].astype(str),
            "game_id": game_id_series.astype(str),
            "team": working["team_abbreviation_home"],
            "opponent": working["team_abbreviation_away"],
            "home_away": "Home",
            "points": pd.to_numeric(working[cols.pts_home_col], errors="coerce"),
            "opponent_points": pd.to_numeric(working[cols.pts_away_col], errors="coerce"),
            "fg_pct": pd.to_numeric(working[cols.fg_home_col], errors="coerce"),
            "season_type": season_type.values,
        }
    )

    away = pd.DataFrame(
        {
            "date": working[cols.date_col],
            "year": working["year"].astype("int64"),
            "season_year": working["season_year"].astype("int64"),
            "season_label": working["season_label"].astype(str),
            "game_id": game_id_series.astype(str),
            "team": working["team_abbreviation_away"],
            "opponent": working["team_abbreviation_home"],
            "home_away": "Away",
            "points": pd.to_numeric(working[cols.pts_away_col], errors="coerce"),
            "opponent_points": pd.to_numeric(working[cols.pts_home_col], errors="coerce"),
            "fg_pct": pd.to_numeric(working[cols.fg_away_col], errors="coerce"),
            "season_type": season_type.values,
        }
    )

    team_game = pd.concat([home, away], ignore_index=True)
    team_game["point_diff"] = team_game["points"] - team_game["opponent_points"]
    team_game["win"] = team_game["point_diff"].apply(
        lambda x: "Win" if pd.notna(x) and x > 0 else "Loss"
    )

    missing_points = int(team_game["points"].isna().sum())
    missing_fg = int(team_game["fg_pct"].isna().sum())
    if missing_points:
        warnings.append(f"{missing_points} team-game rows have missing points.")
    if missing_fg:
        warnings.append(f"{missing_fg} team-game rows have missing fg_pct.")

    # Keep the minimum required columns first.
    team_game = team_game[
        [
            "date",
            "year",
            "season_year",
            "season_label",
            "team",
            "opponent",
            "home_away",
            "points",
            "fg_pct",
            "win",
            "season_type",
            "game_id",
            "point_diff",
            "opponent_points",
        ]
    ].sort_values(["date", "game_id", "home_away"]).reset_index(drop=True)

    return team_game, warnings, counts


def write_report(
    cols: SelectedColumns,
    counts: dict[str, int],
    warnings: list[str],
    final_df: pd.DataFrame,
) -> None:
    """Write markdown report for dataset preparation decisions and outputs."""
    missing_summary = final_df[["points", "fg_pct", "season_type"]].isna().sum()
    header = "| date | year | season_year | season_label | team | opponent | home_away | points | fg_pct | win | season_type | game_id | point_diff |\n"
    divider = "|---|---:|---:|---|---|---|---|---:|---:|---|---|---|---:|\n"

    sample = final_df.head(5).copy()
    sample["date"] = sample["date"].dt.strftime("%Y-%m-%d")
    rows = "\n".join(
        "| "
        + " | ".join(str(v) for v in row)
        + " |"
        for row in sample[
            [
                "date",
                "year",
                "season_year",
                "season_label",
                "team",
                "opponent",
                "home_away",
                "points",
                "fg_pct",
                "win",
                "season_type",
                "game_id",
                "point_diff",
            ]
        ].to_numpy()
    )

    warning_lines = "\n".join(f"- {w}" for w in warnings) if warnings else "- None"

    report = f"""# Data Preparation Report

## Input Columns Detected
- Date: `{cols.date_col}`
- Game ID: `{cols.game_id_col if cols.game_id_col else 'generated'}`
- Points (home/away): `{cols.pts_home_col}` / `{cols.pts_away_col}`
- FG% (home/away): `{cols.fg_home_col}` / `{cols.fg_away_col}`
- Season type source: `{cols.season_type_col if cols.season_type_col else 'not found (defaulted)'}`

## Assumptions And Inference Rules
- Team abbreviations are normalized from `game.csv` using `normalize_team_abbreviations` in `normalize_teams.py`.
- `season_year` is derived as: month >= 10 -> year, else year - 1.
- `season_label` is derived from `season_year` as `{{season_year}}-{{(season_year+1)%100:02d}}` for readable chart labels.
- Only NBA seasons with `season_year` in {SEASON_YEAR_START}..{SEASON_YEAR_END} are kept.
- Team-game table duplicates each game into one Home row and one Away row.
- `win` is derived from team points vs opponent points.
- `season_type` is normalized to `Regular`/`Playoffs`; unknown or missing values default to `Regular`.

## Row Counts
- Rows before filtering: {counts.get('rows_before_filtering', 0)}
- Rows after valid-date parsing: {counts.get('rows_after_date_parse', 0)}
- Rows after season filter ({SEASON_YEAR_START}-{SEASON_YEAR_END}): {counts.get('rows_after_season_filter', 0)}
- Final team-game rows (x2 per game where available): {len(final_df)}

## Missing-Value Handling
- Missing `points`: {int(missing_summary['points'])}
- Missing `fg_pct`: {int(missing_summary['fg_pct'])}
- Missing `season_type`: {int(missing_summary['season_type'])}

## Warnings
{warning_lines}

## Final Dataset Head (first 5 rows)
{header}{divider}{rows}
"""

    REPORT_PATH.write_text(report)


def main() -> None:
    normalized_df, norm_warnings = normalize_source_data()
    cols = detect_columns(normalized_df)
    final_df, prep_warnings, counts = build_team_game_table(normalized_df, cols)

    final_df.to_csv(SEASON_FILTERED_OUTPUT_PATH, index=False)
    write_report(cols, counts, norm_warnings + prep_warnings, final_df)

    print("\nDetected columns:")
    print(list(normalized_df.columns))

    print("\nColumn mapping used:")
    print(
        {
            "date": cols.date_col,
            "game_id": cols.game_id_col,
            "pts_home": cols.pts_home_col,
            "pts_away": cols.pts_away_col,
            "fg_pct_home": cols.fg_home_col,
            "fg_pct_away": cols.fg_away_col,
            "season_type": cols.season_type_col,
        }
    )

    warnings = norm_warnings + prep_warnings
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")
    else:
        print("\nWarnings:\n- None")

    print(f"\nWrote: {NORMALIZED_PATH}")
    print(f"Wrote: {SEASON_FILTERED_OUTPUT_PATH}")
    print(f"Wrote: {REPORT_PATH}")

    print("\nSummary stats for dashboard_ready_season_filtered.csv:")
    print(f"min(date): {final_df['date'].min().date()}")
    print(f"max(date): {final_df['date'].max().date()}")
    unique_season_years = sorted(final_df['season_year'].dropna().astype(int).unique().tolist())
    print(f"unique season_year values: {unique_season_years}")
    season_pairs = (
        final_df[["season_year", "season_label"]]
        .drop_duplicates()
        .sort_values("season_year")
        .head(5)
    )
    print("sample season_year/season_label pairs (first 5 unique seasons):")
    print(season_pairs.to_string(index=False))
    print(f"total row count: {len(final_df)}")

    print("\nFirst 5 rows of dashboard_ready_season_filtered.csv:")
    preview = final_df.head(5).copy()
    preview["date"] = preview["date"].dt.strftime("%Y-%m-%d")
    print(preview.to_string(index=False))


# Why `season_year` is better than calendar year for NBA analysis:
# season-year alignment keeps Oct-Jun games in one coherent competitive season,
# preventing split-season bias in charts, filters, and aggregations.
if __name__ == "__main__":
    main()
