# Data Preparation Report

## Post-filter Date Range
- min(date): 1999-11-02
- max(date): 2023-06-12

## Dataset Size
- Total row count: 61418
- Unique teams: 30

## Seasons
- Unique season_year values: [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]

## Assumptions
- Historical team abbreviations were normalized to modern 30-team abbreviations.
- Any game still containing non-modern abbreviations after normalization was dropped.
- If `season_type` was missing, values were set to `Regular`.
- `win` is computed from `points > opponent_points`.

## Data Quality Actions
- Dropped 139 games with non-modern team abbreviations after normalization.

## Three-Point Metrics
- Included columns: fg3a, fg3m, fg3_pct, fga
- Missing/unavailable columns: None
