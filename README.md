# Triple Double Receipt

A triple double is a headline. This app shows the invoice underneath it.

For every NBA player who recorded a triple double in the 2024–25 regular season,
**Triple Double Receipt** reconstructs the game from play-by-play data — tracing
each assist to the exact shot type it produced and calculating a **Total Points
Touched** number: the player's own points plus every point their passing directly
created that game.

---

## Pages

| Page | What it does |
|------|--------------|
| **Player Log** | Select any player with a triple double; see all their triple-double games with Total Points Touched |
| **The Receipt** | Hero view — receipt-style breakdown of a single game: every assist line-item, subtotals, stacked bar chart |
| **Leaderboard** | Full season rankings by Total Points Touched; filterable by assists, rebounds, and date range |

---

## Data Architecture

This app uses a **two-layer architecture** to stay fast and stable on Streamlit Community Cloud:

1. **`data_pull.py`** — a standalone script you run **locally** to fetch all data from the NBA APIs and write clean CSVs to `/data`.
2. **`app.py` + pages** — the Streamlit app reads **exclusively from those CSVs**. No live API calls happen at runtime.

The `/data` CSVs are committed to the repo so the app works on Streamlit Cloud immediately after deploy, without needing a separate data pipeline.

---

## Refresh Data

Run from the project root:

```bash
# Full pull (all triple-double games for 2024-25)
python data_pull.py

# Targeted single-game refresh (re-fetches play-by-play only)
python data_pull.py --game-id 0022401234
```

Progress is printed to the console at each step. Errors are logged to `data/pull_errors.log`.

On completion, a summary prints:
- How many games were fetched
- How many CSVs were written
- Which games (if any) failed play-by-play parsing

---

## Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Populate data (required before first run)
python data_pull.py

# 3. Start the app
streamlit run app.py
```

---

## Deploy to Streamlit Community Cloud

1. Push this entire repo to GitHub (including the `/data` CSVs).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, set **Main file path** to `app.py`.
4. Click **Deploy**.

> **Note:** The `/data` CSVs must be committed to the repo for the app to work
> on Streamlit Cloud without a separate data pipeline. The app shows a warning
> banner if the data is older than 24 hours, but continues to serve whatever
> CSV data exists.

To refresh data on a schedule, run `python data_pull.py` locally and push the
updated CSVs, or set up a GitHub Actions workflow to run the script on a cron.

---

## Total Points Touched — Methodology

For each triple-double game, we pull the full play-by-play and find every
possession where the focal player recorded an assist. For each assist we capture:

- **Shot type**: 2-point field goal, 3-point field goal, or free throw sequence
- **And-1 plays**: count the field goal points + the made free throw
- **Points credited**: `points_scored + free_throw_points` per assist event

**Total Points Touched = player's own PTS + sum of all points generated via assists**

Technical free throws are excluded. If play-by-play is unavailable for a game,
the Receipt page shows a clear message rather than crashing.
