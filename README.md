# IGNITE Rocket Progress (Streamlit)

A simple, shareable dashboard that shows your weekly/monthly progress to goal — with a **rocket flying toward the moon** as you log calls, demos, pilots, and deals.

## One-minute deploy (Streamlit Community Cloud)
1. Put these files in a public GitHub repo (e.g., `ignite-rocket-progress`).
2. Go to https://share.streamlit.io → **Deploy an app** → point to `app.py`.
3. On first run, it uses `sample_data.csv`. Paste your **Google Sheets CSV** URL in the sidebar to go live.

### Get a Google Sheets CSV URL
- In Google Sheets: **File → Share → Publish to web → Link → CSV** (choose the tab with your log), then copy that link.
- **Schema expected**: 
  ```
  timestamp,rep,action,notes
  2025-08-29 10:05,Alex,call,Recap + next step
  ```
  Supported actions (weights editable in the app): `call, demo, pilot, deal`.

## Goal & Weights
- Set a **Goal (points)** in the sidebar (e.g., 60).
- Default weights: `call=1`, `demo=3`, `pilot=6`, `deal=12`. Edit as needed to match your SPIFF.

## Periods
- Toggle **Weekly** or **Monthly** (weeks start Monday; timezone America/Chicago).

## Files
- `app.py` – Streamlit app
- `requirements.txt` – dependencies
- `sample_data.csv` – example data

## Tips
- Create a **Google Form** for reps to log activity → responses feed your Google Sheet.
- Use the app’s **Refresh** button after new entries arrive, or install a browser auto‑refresh extension on your wallboard.
