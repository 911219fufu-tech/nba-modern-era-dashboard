# NBA Dashboard (GitHub Pages Deployment)

This repository contains a static interactive dashboard for **NBA Modern Era Performance Analysis (1999-2023)**.

## Folder structure

- `index.html` - main dashboard page
- `style.css` - dashboard styling
- `script.js` - data loading, filtering, and chart rendering logic
- `data/nba_team_game_1999_2023.csv` - dashboard dataset

## Data preparation summary

The dashboard dataset is team-game level (one row per team per game). It includes:

- `date`, `team`, `opponent`, `home_away`
- `points`, `fg_pct`, `win`, `season_type`
- `game_id`, `season_year`, `season_label`

Preparation highlights:

- historical team abbreviations normalized to modern teams,
- date filtering for the modern era window,
- season fields added for cross-season analysis,
- metrics structured for interactive filtering and linked charts.

## Deployment note

Raw preprocessing scripts and intermediate data are excluded from the deployment-focused dashboard build. The GitHub Pages version uses static assets only.

## Data source

This dataset is sourced from Kaggle:  
https://www.kaggle.com/datasets/wyattowalsh/basketball

## How to Run Locally

1. From the project root, start a local server:
   `python -m http.server 8000`
2. Open in browser:
   `http://localhost:8000`

## Deploy to GitHub Pages

1. Push this repository to GitHub.
2. In the repository, open `Settings` -> `Pages`.
3. Under **Build and deployment**, choose:
   - Source: `Deploy from a branch`
   - Branch: `main` (or your default branch), folder `/ (root)`
4. Save settings and wait for deployment.
5. Open the generated GitHub Pages URL.
