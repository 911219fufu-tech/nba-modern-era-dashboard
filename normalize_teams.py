"""Utilities to normalize historical NBA team abbreviations to the 30 modern franchises."""
from __future__ import annotations

from typing import Iterable

import pandas as pd

# The 30 official team abbreviations used by NBA.com for the 2023 season.
CURRENT_ABBREVIATIONS = [
    "ATL",
    "BOS",
    "BKN",
    "CHA",
    "CHI",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GSW",
    "HOU",
    "IND",
    "LAC",
    "LAL",
    "MEM",
    "MIA",
    "MIL",
    "MIN",
    "NOP",
    "NYK",
    "OKC",
    "ORL",
    "PHI",
    "PHX",
    "POR",
    "SAC",
    "SAS",
    "TOR",
    "UTA",
    "WAS",
]

# Historical abbreviations mapped to the current franchise identifier. This list
# consolidates name changes and relocations from 1946-2023, ensuring that any
# pre-merger records collapse into the modern 30-team set.
HISTORICAL_TO_CURRENT = {
    # Hawks lineage
    "TRI": "ATL",  # Tri-Cities Blackhawks
    "MLH": "ATL",  # Milwaukee Hawks
    "STL": "ATL",  # St. Louis Hawks
    # Celtics lineage has been BOS for entirety
    # Nets lineage
    "NYN": "BKN",
    "NJN": "BKN",
    # Hornets / Pelicans lineage
    "CHH": "CHA",
    "CHA": "CHA",  # Bobcats / Hornets modern
    "NOH": "NOP",
    "NOK": "NOP",
    "NOL": "NOP",
    "NOJ": "UTA",  # New Orleans Jazz
    # Bulls unchanged
    # Cavaliers unchanged
    # Mavericks unchanged
    # Nuggets unchanged
    # Pistons lineage
    "FTW": "DET",  # Fort Wayne Pistons
    # Warriors lineage
    "PHW": "GSW",
    "SFW": "GSW",
    # Rockets unchanged
    # Pacers unchanged
    # Clippers lineage
    "BUF": "LAC",  # Buffalo Braves
    "SDC": "LAC",  # San Diego Clippers
    "SDP": "LAC",  # San Diego Padres placeholder (historic stat quirk)
    # Lakers lineage
    "MNL": "LAL",  # Minneapolis Lakers
    # Grizzlies lineage
    "VAN": "MEM",
    # Heat unchanged
    # Bucks unchanged
    # Timberwolves unchanged
    # Knicks unchanged
    # Thunder lineage
    "SEA": "OKC",
    # Magic unchanged
    # 76ers lineage
    "SYR": "PHI",  # Syracuse Nationals
    # Suns unchanged
    # Trail Blazers unchanged
    # Kings lineage
    "ROC": "SAC",  # Rochester Royals
    "CIN": "SAC",  # Cincinnati Royals
    "KCO": "SAC",  # Kansas City-Omaha Kings
    "KCK": "SAC",  # Kansas City Kings
    "KAN": "SAC",
    # Spurs unchanged
    # Raptors unchanged (expansion 1995)
    # Jazz lineage handled above
    # Wizards / Bullets lineage
    "CHP": "WAS",  # Chicago Packers/Zephyrs
    "BAL": "WAS",  # Baltimore Bullets
    "CAP": "WAS",  # Capital Bullets
    "WSB": "WAS",  # Washington Bullets
    "WAS": "WAS",
}

# Ensure every modern abbreviation maps to itself for convenience.
for _abbr in CURRENT_ABBREVIATIONS:
    HISTORICAL_TO_CURRENT.setdefault(_abbr, _abbr)

def normalize_team_abbreviations(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with home/away team abbreviations normalized.

    Parameters
    ----------
    df:
        A DataFrame that contains ``team_abbreviation_home`` and
        ``team_abbreviation_away`` columns.

    Returns
    -------
    pandas.DataFrame
        Copy of the input with both columns upper-cased and remapped so only the
        30 current abbreviations remain.
    """

    required_cols: Iterable[str] = ["team_abbreviation_home", "team_abbreviation_away"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Missing columns required for normalization: {missing}")

    normalized = df.copy()
    for col in required_cols:
        normalized[col] = (
            normalized[col]
            .astype(str)
            .str.upper()
            .map(HISTORICAL_TO_CURRENT)
            .fillna(normalized[col].str.upper())
        )

    return normalized


def main() -> None:
    """Example CLI usage for quick manual verification."""
    csv_path = "game.csv"
    df = pd.read_csv(csv_path)
    normalized = normalize_team_abbreviations(df)
    normalized.to_csv("game_normalized.csv", index=False)
    unique_home = sorted(normalized["team_abbreviation_home"].unique())
    unique_away = sorted(normalized["team_abbreviation_away"].unique())
    print(f"Unique home abbreviations: {len(unique_home)} -> {unique_home}")
    print(f"Unique away abbreviations: {len(unique_away)} -> {unique_away}")


if __name__ == "__main__":
    main()
