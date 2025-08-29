
import io, math, requests, pytz
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from typing import Optional
ASSET_ROCKET = "assets/rocket_hd.png"
ASSET_MOON   = "assets/moon_hd.png"

st.set_page_config(page_title="IGNITE Rocket Progress", page_icon="🚀", layout="wide")

TZ = pytz.timezone("America/Chicago")

DEFAULT_WEIGHTS = {"call": 1, "demo": 3, "pilot": 6, "deal": 12}

def load_data(csv_url: Optional[str], uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif csv_url:
        try:
            df = pd.read_csv(csv_url)
        except Exception:
            st.warning("Couldn't load the provided CSV URL. Falling back to sample data.")
            df = pd.read_csv("sample_data.csv")
    else:
        df = pd.read_csv("sample_data.csv")
    df.columns = [c.strip().lower() for c in df.columns]
    if "timestamp" not in df.columns:
        raise ValueError("CSV must include a 'timestamp' column")
    if "rep" not in df.columns:
        df["rep"] = "Unknown"
    if "action" not in df.columns:
        raise ValueError("CSV must include an 'action' column")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.tz_localize("UTC").dt.tz_convert(TZ)
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["week"] = df["timestamp"].dt.isocalendar().week
    df["year"] = df["timestamp"].dt.year
    df["weekday"] = df["timestamp"].dt.day_name()
    return df

def period_bounds(mode: str):
    now = datetime.now(TZ)
    if mode == "Weekly":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year+1, month=1)
        else:
            end = start.replace(month=start.month+1)
    return start, end

def score_df(df, weights, start, end):
    dfp = df[(df["timestamp"] >= start) & (df["timestamp"] < end)].copy()
    dfp["weight"] = dfp["action"].map(lambda a: weights.get(str(a).strip().lower(), 0))
    dfp["points"] = dfp["weight"]
    return dfp

def compute_progress(dfp, goal_points: int):
    total_points = int(dfp["points"].sum()) if not dfp.empty else 0
    progress = min(total_points / goal_points, 1.0) if goal_points > 0 else 0.0
    return total_points, progress

def make_rocket_image(progress: float, width=700, height=900):
    img = Image.new("RGB", (width, height), (6, 9, 26))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = 10 + int(10 * (y/height))
        g = 15 + int(10 * (y/height))
        b = 46 + int(10 * (y/height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    rng = np.random.default_rng(42)
    n_stars = 200
    xs = rng.integers(0, width, n_stars)
    ys = rng.integers(0, height, n_stars)
    for x, y in zip(xs, ys):
        draw.point((int(x), int(y)), fill=(220, 220, 255))

    moon_r = 70
    moon_center = (width//2, 100)
    draw.ellipse([moon_center[0]-moon_r,  moon_center[1]-moon_r,
                  moon_center[0]+moon_r,  moon_center[1]+moon_r],
                 fill=(235, 236, 240), outline=(200, 200, 210), width=2)

    ground_h = 80
    draw.rectangle([0, height-ground_h, width, height], fill=(20, 20, 24))

    y_bottom = height - ground_h - 120
    y_top = moon_center[1] + moon_r + 20
    y_pos = int(y_bottom - (y_bottom - y_top) * progress)

    cx = width//2
    body_h = 140
    body_w = 48
    body_top = y_pos - body_h//2
    body_left = cx - body_w//2
    draw.rounded_rectangle([body_left, body_top, body_left+body_w, body_top+body_h], radius=16, fill=(230, 230, 235))

    nose_h = 28
    draw.polygon([(cx, body_top - nose_h),
                  (body_left, body_top+8),
                  (body_left+body_w, body_top+8)], fill=(240, 50, 60))

    fin_h = 28
    fin_w = 22
    draw.polygon([(body_left, body_top+70),
                  (body_left - fin_w, body_top+70 + fin_h),
                  (body_left, body_top+90)], fill=(240, 50, 60))
    draw.polygon([(body_left+body_w, body_top+70),
                  (body_left+body_w + fin_w, body_top+70 + fin_h),
                  (body_left+body_w, body_top+90)], fill=(240, 50, 60))

    win_r = 10
    draw.ellipse([cx-win_r, body_top+40-win_r, cx+win_r, body_top+40+win_r], fill=(90, 140, 255))

    flame_h = 40 + int(10 * abs(math.sin(progress*math.pi*4)))
    flame_w = 24
    draw.polygon([(cx, body_top+body_h+10),
                  (cx - flame_w//2, body_top+body_h+10+flame_h),
                  (cx + flame_w//2, body_top+body_h+10+flame_h)], fill=(255, 170, 0))

    pct = int(progress * 100)
    txt = f"{pct}% to goal"
    draw.text((20, 20), txt, fill=(255,255,255))
    return img

st.sidebar.header("Configure")
mode = st.sidebar.radio("Period", ["Weekly", "Monthly"])
goal_points = st.sidebar.number_input("Goal (points)", min_value=1, value=60, step=1)
st.sidebar.caption("Default weights: call=1, demo=3, pilot=6, deal=12 (edit below)")

w_call  = st.sidebar.number_input("Weight: call",  min_value=0, value=DEFAULT_WEIGHTS["call"],  step=1)
w_demo  = st.sidebar.number_input("Weight: demo",  min_value=0, value=DEFAULT_WEIGHTS["demo"],  step=1)
w_pilot = st.sidebar.number_input("Weight: pilot", min_value=0, value=DEFAULT_WEIGHTS["pilot"], step=1)
w_deal  = st.sidebar.number_input("Weight: deal",  min_value=0, value=DEFAULT_WEIGHTS["deal"],  step=1)
weights = {"call": w_call, "demo": w_demo, "pilot": w_pilot, "deal": w_deal}

st.sidebar.markdown("---")
csv_url = st.sidebar.text_input("Google Sheet CSV URL (optional)", help="Sheets → File → Share → Publish to web → CSV link")
uploaded = st.sidebar.file_uploader("...or upload a CSV (columns: timestamp, rep, action, notes)")
st.sidebar.button("🔄 Refresh data")

df = load_data(csv_url, uploaded)
start, end = period_bounds(mode)
dfp = score_df(df, weights, start, end)
total_points, progress = compute_progress(dfp, goal_points)

st.title("🚀 IGNITE Rocket Progress")
colA, colB = st.columns([1.2, 1])

with colA:
    st.subheader(f"{mode} Progress")
    st.caption(f"{start.strftime('%b %d, %Y')} → {(end - timedelta(seconds=1)).strftime('%b %d, %Y')} (America/Chicago)")
    img = make_rocket_image(progress)
    st.image(img, use_container_width=True)
    st.progress(progress, text=f"{int(progress*100)}%")
    st.metric("Total points", f"{total_points:,}")

with colB:
    st.subheader("Activity breakdown")
    act = dfp.groupby("action")["points"].sum().reset_index().sort_values("points", ascending=False)
    st.dataframe(act, use_container_width=True)
    st.subheader("Leaderboard")
    board = dfp.groupby("rep")["points"].sum().reset_index().sort_values("points", ascending=False)
    st.dataframe(board, use_container_width=True)

st.markdown("---")
st.subheader("Timeline (this period)")
if dfp.empty:
    st.info("No activity in this period yet. Add rows to your Google Sheet / CSV and click Refresh.")
else:
    daily = dfp.copy()
    daily["day"] = daily["timestamp"].dt.strftime("%Y-%m-%d")
    daily = daily.groupby(["day"])["points"].sum().reset_index()
    import altair as alt
    chart = alt.Chart(daily).mark_bar().encode(
        x=alt.X("day:N", sort=None, title="Day"),
        y=alt.Y("points:Q", title="Points")
    ).properties(height=260)
    st.altair_chart(chart, use_container_width=True)

st.markdown("---")
with st.expander("How to connect Google Sheets", expanded=False):
    st.markdown("1) Create a Google Form with fields: rep, action (call/demo/pilot/deal), notes.")
    st.markdown("2) Link it to a Google Sheet (Form → Responses → green Sheets icon).")
    st.markdown("3) In the Sheet, create a 'log' tab with columns: timestamp, rep, action, notes.")
    st.markdown("4) In Google Sheets: File → Share → Publish to web → CSV, then copy the link.")
    st.markdown("5) Paste that CSV link in the sidebar field 'Google Sheet CSV URL'.")
    st.caption("Updates appear on refresh. For near‑real‑time, use a browser auto-refresh on your wallboard.")
st.caption("Built for Jeff • MANTIS • Streamlit Community Cloud ready")
