# NBA Dashboard (GitHub Pages Deployment)

This repository is organized for frontend deployment of an interactive NBA dashboard.

## Folder structure

- `index.html` - dashboard entry page (should load data from `data/dashboard_ready_season_filtered.csv`)
- `script.js` - visualization and interaction logic
- `style.css` - dashboard styling
- `data/dashboard_ready_season_filtered.csv` - cleaned dataset used by the dashboard

## Data preparation summary

The deployed dataset was prepared from raw NBA game-level data by:
- normalizing historical team abbreviations to modern 30-team abbreviations,
- reshaping each game into two team-game rows (home and away),
- deriving analysis fields such as `win`, `point_diff`, `season_year`, and `season_label`,
- filtering by NBA season windows to keep seasons 1999-2000 through 2022-2023.

## Deployment note

Raw data files and preprocessing scripts are intentionally excluded from this deployment-focused repository so GitHub Pages serves only frontend assets and final dashboard data.

## Required data path in frontend

`index.html`/`script.js` should load:

`data/dashboard_ready_season_filtered.csv`

## Data source

This dataset is sourced from Kaggle:  
https://www.kaggle.com/datasets/wyattowalsh/basketball
