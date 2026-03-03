# Data Preparation Report

## Input Columns Detected
- Date: `game_date`
- Game ID: `game_id`
- Points (home/away): `pts_home` / `pts_away`
- FG% (home/away): `fg_pct_home` / `fg_pct_away`
- Season type source: `season_type`

## Assumptions And Inference Rules
- Team abbreviations are normalized from `game.csv` using `normalize_team_abbreviations` in `normalize_teams.py`.
- `season_year` is derived as: month >= 10 -> year, else year - 1.
- `season_label` is derived from `season_year` as `{season_year}-{(season_year+1)%100:02d}` for readable chart labels.
- Only NBA seasons with `season_year` in 1999..2022 are kept.
- Team-game table duplicates each game into one Home row and one Away row.
- `win` is derived from team points vs opponent points.
- `season_type` is normalized to `Regular`/`Playoffs`; unknown or missing values default to `Regular`.

## Row Counts
- Rows before filtering: 55698
- Rows after valid-date parsing: 55698
- Rows after season filter (1999-2022): 30709
- Final team-game rows (x2 per game where available): 61418

## Missing-Value Handling
- Missing `points`: 0
- Missing `fg_pct`: 0
- Missing `season_type`: 0

## Warnings
- Dropped games with abbreviations outside modern 30-team set after normalization (10000 rows). Invalid home=['ALB', 'AND', 'BAR', 'BLT', 'BOM', 'CHN', 'CHS', 'CHZ', 'CLR', 'DEF', 'DN', 'DRT', 'EAM', 'EPT', 'EST', 'FBU', 'FCB', 'FLA', 'GNS', 'GOS', 'HUS', 'INO', 'JET', 'KHI', 'LBN', 'LRO', 'LYV', 'MAL', 'MIH', 'MLN', 'MMT', 'MTA', 'PHL', 'PIT', 'PRO', 'RMA', 'RMD', 'ROM', 'SAN', 'SDR', 'SHE', 'STP', 'TCB', 'UBB', 'UTH', 'WAT', 'WST'], invalid away=['ADL', 'AND', 'BAR', 'BAU', 'BLT', 'BNE', 'BOM', 'CHS', 'CHZ', 'CLR', 'DEF', 'DN', 'DRT', 'EPT', 'EST', 'FEN', 'FLA', 'GNS', 'GOS', 'GUA', 'HUS', 'INO', 'JET', 'LAB', 'LBN', 'LRY', 'MAC', 'MEL', 'MIH', 'MOS', 'MPS', 'MRA', 'MTA', 'OLP', 'PAN', 'PAR', 'PHL', 'PIT', 'PRO', 'RMD', 'SAN', 'SDR', 'SDS', 'SHE', 'SLA', 'SYD', 'TCB', 'UTH', 'WAT', 'WST', 'ZAK']

## Final Dataset Head (first 5 rows)
| date | year | season_year | season_label | team | opponent | home_away | points | fg_pct | win | season_type | game_id | point_diff |
|---|---:|---:|---|---|---|---|---:|---:|---|---|---|---:|
| 1999-11-02 | 1999 | 1999 | 1999-00 | CLE | NYK | Away | 84.0 | 0.39 | Loss | Regular | 29900001 | -8.0 |
| 1999-11-02 | 1999 | 1999 | 1999-00 | NYK | CLE | Home | 92.0 | 0.432 | Win | Regular | 29900001 | 8.0 |
| 1999-11-02 | 1999 | 1999 | 1999-00 | IND | BKN | Away | 119.0 | 0.474 | Win | Regular | 29900002 | 7.0 |
| 1999-11-02 | 1999 | 1999 | 1999-00 | BKN | IND | Home | 112.0 | 0.444 | Loss | Regular | 29900002 | -7.0 |
| 1999-11-02 | 1999 | 1999 | 1999-00 | ATL | WAS | Away | 87.0 | 0.397 | Loss | Regular | 29900003 | -7.0 |
