
from __future__ import annotations

import os
import math
import html
import textwrap
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="MLB Betting Dashboard", layout="wide")

BASE_URL = "https://statsapi.mlb.com/api/v1"
SPORTSGAMEODDS_BASE_URL = "https://api.sportsgameodds.com/v2"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
BASEBALL_SAVANT_PITCH_ARSENALS_URL = "https://baseballsavant.mlb.com/leaderboard/pitch-arsenals"
BASEBALL_SAVANT_PITCH_ARSENAL_STATS_URL = "https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats"
APP_DIR = Path(__file__).parent
REAL_DATA_PATH = APP_DIR / "data" / "team_game_logs_real.csv"
DEMO_DATA_PATH = APP_DIR / "data" / "demo_team_game_logs.csv"
ODDS_SNAPSHOT_PATH = APP_DIR / "data" / "odds_snapshots.csv"
PITCHER_PROP_TRACKER_PATH = APP_DIR / "data" / "pitcher_prop_tracker.csv"
PITCHER_ER_PROP_SNAPSHOT_PATH = APP_DIR / "data" / "pitcher_er_prop_snapshots.csv"
BEST_BET_TRACKER_PATH = APP_DIR / "data" / "best_bet_suggestions.csv"

BEST_BET_TRACKER_COLUMNS = [
    "created_at",
    "game_date",
    "game_id",
    "matchup",
    "side",
    "opponent",
    "side_label",
    "signal",
    "score",
    "max_score",
    "edge_score",
    "passed_rules",
    "failed_rules",
    "failed_details",
    "metrics",
    "why",
    "result",
    "away_score",
    "home_score",
    "winning_team",
    "grade_reason",
    "graded_at",
]

PITCHER_PROP_COLUMNS = [
    "created_at",
    "game_date",
    "game_id",
    "matchup",
    "team",
    "opponent",
    "pitcher_id",
    "pitcher_name",
    "market",
    "side",
    "line",
    "price",
    "book",
    "source",
    "odd_id",
    "stat_entity_id",
    "signal",
    "signal_score",
    "signal_reasons",
    "movement",
    "start_required",
    "note",
    "actual_er",
    "actual_ip",
    "actual_hits",
    "actual_walks",
    "actual_started",
    "result",
    "grade_reason",
    "graded_at",
]

PITCHER_ER_PROP_SNAPSHOT_COLUMNS = [
    "fetched_at",
    "game_date",
    "event_id",
    "start_time",
    "matchup",
    "team",
    "opponent",
    "pitcher_id",
    "pitcher_name",
    "stat_entity_id",
    "odd_id",
    "side",
    "book",
    "price",
    "line",
    "open_price",
    "open_line",
    "implied_prob",
    "movement",
    "movement_dir",
    "signal",
    "signal_score",
    "signal_reasons",
]

BALLPARK_PROFILES = {
    "Angel Stadium": {"lat": 33.8003, "lon": -117.8827, "cf_bearing": 40, "run": 0, "hr": 0, "roof": "open"},
    "Busch Stadium": {"lat": 38.6226, "lon": -90.1928, "cf_bearing": 70, "run": 0, "hr": 0, "roof": "open"},
    "Chase Field": {"lat": 33.4455, "lon": -112.0667, "cf_bearing": 20, "run": 1, "hr": 0, "roof": "retractable"},
    "Citi Field": {"lat": 40.7571, "lon": -73.8458, "cf_bearing": 45, "run": 0, "hr": 0, "roof": "open"},
    "Citizens Bank Park": {"lat": 39.9058, "lon": -75.1665, "cf_bearing": 10, "run": 1, "hr": 1, "roof": "open"},
    "Comerica Park": {"lat": 42.3390, "lon": -83.0485, "cf_bearing": 150, "run": 0, "hr": -1, "roof": "open"},
    "Coors Field": {"lat": 39.7561, "lon": -104.9942, "cf_bearing": 10, "run": 2, "hr": 1, "roof": "open"},
    "Daikin Park": {"lat": 29.7573, "lon": -95.3555, "cf_bearing": 345, "run": 0, "hr": 0, "roof": "retractable"},
    "Dodger Stadium": {"lat": 34.0739, "lon": -118.2400, "cf_bearing": 35, "run": 0, "hr": 0, "roof": "open"},
    "Fenway Park": {"lat": 42.3467, "lon": -71.0972, "cf_bearing": 35, "run": 1, "hr": 0, "roof": "open"},
    "George M. Steinbrenner Field": {"lat": 27.9798, "lon": -82.5069, "cf_bearing": 70, "run": 0, "hr": 0, "roof": "open"},
    "Globe Life Field": {"lat": 32.7473, "lon": -97.0842, "cf_bearing": 35, "run": 0, "hr": 0, "roof": "retractable"},
    "Great American Ball Park": {"lat": 39.0979, "lon": -84.5082, "cf_bearing": 45, "run": 1, "hr": 2, "roof": "open"},
    "Guaranteed Rate Field": {"lat": 41.8300, "lon": -87.6338, "cf_bearing": 135, "run": 0, "hr": 1, "roof": "open"},
    "Kauffman Stadium": {"lat": 39.0517, "lon": -94.4803, "cf_bearing": 45, "run": 0, "hr": -1, "roof": "open"},
    "loanDepot park": {"lat": 25.7781, "lon": -80.2197, "cf_bearing": 95, "run": 0, "hr": 0, "roof": "retractable"},
    "Minute Maid Park": {"lat": 29.7573, "lon": -95.3555, "cf_bearing": 345, "run": 0, "hr": 0, "roof": "retractable"},
    "Nationals Park": {"lat": 38.8730, "lon": -77.0074, "cf_bearing": 65, "run": 0, "hr": 0, "roof": "open"},
    "Oracle Park": {"lat": 37.7786, "lon": -122.3893, "cf_bearing": 90, "run": -1, "hr": -1, "roof": "open"},
    "Oriole Park at Camden Yards": {"lat": 39.2839, "lon": -76.6217, "cf_bearing": 30, "run": 0, "hr": 0, "roof": "open"},
    "PNC Park": {"lat": 40.4469, "lon": -80.0057, "cf_bearing": 25, "run": 0, "hr": -1, "roof": "open"},
    "Petco Park": {"lat": 32.7073, "lon": -117.1566, "cf_bearing": 0, "run": -1, "hr": -1, "roof": "open"},
    "Progressive Field": {"lat": 41.4962, "lon": -81.6852, "cf_bearing": 15, "run": 0, "hr": 0, "roof": "open"},
    "Rate Field": {"lat": 41.8300, "lon": -87.6338, "cf_bearing": 135, "run": 0, "hr": 1, "roof": "open"},
    "Rogers Centre": {"lat": 43.6414, "lon": -79.3894, "cf_bearing": 115, "run": 0, "hr": 0, "roof": "retractable"},
    "Sutter Health Park": {"lat": 38.5804, "lon": -121.5139, "cf_bearing": 70, "run": 0, "hr": 0, "roof": "open"},
    "T-Mobile Park": {"lat": 47.5914, "lon": -122.3325, "cf_bearing": 35, "run": -1, "hr": -1, "roof": "retractable"},
    "Target Field": {"lat": 44.9817, "lon": -93.2776, "cf_bearing": 95, "run": 0, "hr": 0, "roof": "open"},
    "Truist Park": {"lat": 33.8908, "lon": -84.4678, "cf_bearing": 45, "run": 0, "hr": 1, "roof": "open"},
    "Wrigley Field": {"lat": 41.9484, "lon": -87.6553, "cf_bearing": 55, "run": 0, "hr": 0, "roof": "open"},
    "Yankee Stadium": {"lat": 40.8296, "lon": -73.9262, "cf_bearing": 75, "run": 0, "hr": 1, "roof": "open"},
}

TEAM_COLORS = {
    "Arizona Diamondbacks": "#A71930",
    "Atlanta Braves": "#CE1141",
    "Baltimore Orioles": "#DF4601",
    "Boston Red Sox": "#BD3039",
    "Chicago Cubs": "#0E3386",
    "Chicago White Sox": "#27251F",
    "Cincinnati Reds": "#C6011F",
    "Cleveland Guardians": "#E31937",
    "Colorado Rockies": "#333366",
    "Detroit Tigers": "#0C2340",
    "Houston Astros": "#EB6E1F",
    "Kansas City Royals": "#004687",
    "Los Angeles Angels": "#BA0021",
    "Los Angeles Dodgers": "#005A9C",
    "Miami Marlins": "#00A3E0",
    "Milwaukee Brewers": "#12284B",
    "Minnesota Twins": "#002B5C",
    "New York Mets": "#002D72",
    "New York Yankees": "#132448",
    "Athletics": "#003831",
    "Philadelphia Phillies": "#E81828",
    "Pittsburgh Pirates": "#FDB827",
    "San Diego Padres": "#2F241D",
    "San Francisco Giants": "#FD5A1E",
    "Seattle Mariners": "#0C2C56",
    "St. Louis Cardinals": "#C41E3A",
    "Tampa Bay Rays": "#092C5C",
    "Texas Rangers": "#003278",
    "Toronto Blue Jays": "#134A8E",
    "Washington Nationals": "#AB0003",
}

TEAM_ABBREVIATIONS = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Athletics": "ATH",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}

GRAPH_AWAY_COLOR = "#c084fc"
GRAPH_HOME_COLOR = "#38bdf8"

PITCH_TYPE_LABELS = {
    "FF": "4-seam",
    "SI": "Sinker",
    "FC": "Cutter",
    "SL": "Slider",
    "ST": "Sweeper",
    "SV": "Slurve",
    "CU": "Curve",
    "KC": "Knuckle curve",
    "CH": "Change",
    "FS": "Splitter",
    "KN": "Knuckleball",
}

DASHBOARD_CSS = """
<style>
    :root {
        --dash-bg: #070d18;
        --dash-bg-soft: #0b1220;
        --dash-panel: #111827;
        --dash-panel-soft: #172033;
        --dash-tile: #1d2939;
        --dash-ink: #f8fafc;
        --dash-muted: #cbd5e1;
        --dash-subtle: #94a3b8;
        --dash-border: #26364a;
        --dash-accent: #2dd4bf;
        --dash-accent-soft: #123c3a;
        --dash-shadow: 0 14px 34px rgba(0, 0, 0, 0.32);
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        background: var(--dash-bg);
        color: var(--dash-ink);
    }

    [data-testid="stHeader"] {
        background: rgba(7, 13, 24, 0.92);
    }

	    .block-container {
	        padding-top: 1.35rem;
	        padding-bottom: 2.4rem;
	        max-width: 1540px;
	        overflow-x: hidden;
	    }

	    html,
	    body,
	    .stApp {
	        max-width: 100%;
	        overflow-x: hidden;
	    }

	    * {
	        box-sizing: border-box;
	    }

    .stApp,
    .stMarkdown,
    p,
    label,
    span,
    div {
        color: var(--dash-ink);
    }

    [data-testid="stSidebar"] {
        background: #050a13;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: #eef4ff !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: var(--dash-panel-soft) !important;
        border-color: var(--dash-border) !important;
        color: var(--dash-ink) !important;
    }

    [data-testid="stSidebar"] .stButton button {
        background: var(--dash-accent);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #ffffff !important;
        font-weight: 700;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: #0b625c;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.28);
    }

    h2, h3 {
        color: var(--dash-ink);
        letter-spacing: 0;
    }

    h2 {
        border-top: 1px solid var(--dash-border);
        padding-top: 1rem;
        margin-top: 1.5rem;
        font-size: 1.25rem;
    }

    div[data-testid="stMetric"] {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.95rem 1rem;
        box-shadow: var(--dash-shadow);
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--dash-muted) !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--dash-ink) !important;
        font-size: 2.15rem !important;
        line-height: 1.08 !important;
    }

	    .stButton button,
	    [data-testid="baseButton-secondary"],
	    [data-testid="baseButton-primary"] {
	        background: var(--dash-panel-soft) !important;
	        border: 1px solid var(--dash-border) !important;
	        color: var(--dash-ink) !important;
	        font-size: 1rem !important;
	        font-weight: 800 !important;
	        min-height: 44px;
	        white-space: normal;
	    }

    .stButton button:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        border-color: var(--dash-accent) !important;
        color: #ffffff !important;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stDateInput"] label {
        font-weight: 700;
        color: var(--dash-ink) !important;
        font-size: 1.08rem !important;
    }

    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        min-height: 50px;
    }

    div[data-testid="stSelectbox"] [data-baseweb="select"] * {
        font-size: 1.08rem !important;
        font-weight: 800 !important;
    }

    div[data-testid="stRadio"] [role="radiogroup"] {
        gap: 0.48rem;
        flex-wrap: wrap;
    }

    div[data-testid="stRadio"] [role="radiogroup"] label {
        background: rgba(15, 23, 42, 0.74);
        border: 1px solid var(--dash-border);
        border-radius: 999px;
        padding: 0.24rem 0.58rem;
        min-height: 40px;
    }

	    [data-baseweb="select"] > div,
	    [data-baseweb="input"] > div,
	    input,
	    textarea {
	        background: var(--dash-panel-soft) !important;
	        border-color: var(--dash-border) !important;
	        color: var(--dash-ink) !important;
	        min-height: 44px;
	    }

    .dashboard-hero {
        background: linear-gradient(135deg, #08111f 0%, #10243a 56%, #0f766e 100%);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px;
        color: #ffffff;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--dash-shadow);
    }

    .dashboard-hero__eyebrow {
        font-size: 0.86rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #a7f3d0;
        margin-bottom: 0.25rem;
    }

    .dashboard-hero__title {
        font-size: 2.2rem;
        line-height: 1.08;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    .dashboard-hero__subtitle {
        color: #d7e4f2;
        font-size: 1.05rem;
        max-width: 860px;
    }

    .dashboard-card {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        box-shadow: var(--dash-shadow);
    }

    .game-card {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        min-height: 104px;
        box-shadow: var(--dash-shadow);
    }

    .game-card__label {
        font-size: 0.86rem;
        color: var(--dash-muted);
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.3rem;
    }

    .game-card__team {
        font-size: 1.46rem;
        color: var(--dash-ink);
        font-weight: 800;
        line-height: 1.15;
    }

    .game-card__meta {
        color: var(--dash-muted);
        font-size: 0.98rem;
        margin-top: 0.35rem;
    }

	    .best-bet-grid {
	        display: grid;
	        grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
	        gap: 0.75rem;
	        margin-bottom: 0.85rem;
	        min-width: 0;
	    }

	    .best-bet-card,
	    .best-bet-empty {
	        background: var(--dash-panel);
	        border: 1px solid var(--dash-border);
	        border-radius: 8px;
	        padding: 0.9rem 1rem;
	        box-shadow: var(--dash-shadow);
	        min-width: 0;
	    }

    .best-bet-card--suggested {
        border-color: rgba(45, 212, 191, 0.66);
        box-shadow: 0 14px 34px rgba(45, 212, 191, 0.12);
    }

    .best-bet-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .best-bet-kicker {
        color: #99f6e4;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .best-bet-team {
        color: var(--dash-ink);
        font-size: 1.28rem;
        line-height: 1.14;
        font-weight: 900;
        margin-top: 0.16rem;
    }

    .best-bet-game,
    .best-bet-why,
    .best-bet-empty {
        color: var(--dash-muted);
        font-size: 0.94rem;
        line-height: 1.35;
    }

    .best-bet-score {
        border: 1px solid rgba(45, 212, 191, 0.45);
        background: rgba(45, 212, 191, 0.12);
        color: #ccfbf1;
        border-radius: 999px;
        padding: 0.2rem 0.56rem;
        font-size: 0.84rem;
        font-weight: 900;
        white-space: nowrap;
    }

    .best-bet-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.5rem;
        margin-bottom: 0.7rem;
    }

    .best-bet-metric {
        background: var(--dash-panel-soft);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.52rem 0.6rem;
        min-width: 0;
    }

    .best-bet-metric__label {
        color: var(--dash-subtle);
        font-size: 0.78rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.12rem;
    }

    .best-bet-metric__value {
        color: var(--dash-ink);
        font-size: 0.96rem;
        font-weight: 850;
        line-height: 1.24;
        overflow-wrap: anywhere;
    }

    .best-bet-checks {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin: 0.1rem 0 0.7rem;
    }

    .best-bet-chip {
        border: 1px solid var(--dash-border);
        border-radius: 999px;
        padding: 0.18rem 0.48rem;
        font-size: 0.76rem;
        font-weight: 850;
        white-space: nowrap;
    }

    .best-bet-chip--on {
        background: rgba(45, 212, 191, 0.14);
        border-color: rgba(45, 212, 191, 0.38);
        color: #99f6e4;
    }

    .best-bet-chip--off {
        background: rgba(148, 163, 184, 0.1);
        color: var(--dash-subtle);
    }

	    .best-bet-near {
	        background: var(--dash-panel);
	        border: 1px solid var(--dash-border);
	        border-radius: 8px;
	        padding: 0.9rem 1rem;
	        margin-bottom: 0.9rem;
	        box-shadow: var(--dash-shadow);
	        overflow-x: auto;
	    }

    .best-bet-near__title {
        color: var(--dash-ink);
        font-size: 1.05rem;
        font-weight: 900;
        margin-bottom: 0.18rem;
    }

    .best-bet-near__sub {
        color: var(--dash-muted);
        font-size: 0.92rem;
        margin-bottom: 0.65rem;
    }

    .best-bet-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }

    .best-bet-table th,
    .best-bet-table td {
        border-bottom: 1px solid var(--dash-border);
        padding: 0.48rem 0.5rem;
        text-align: left;
        vertical-align: top;
    }

    .best-bet-table th {
        color: var(--dash-muted) !important;
        font-size: 0.78rem !important;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .best-bet-table td {
        color: var(--dash-ink) !important;
        font-size: 0.88rem !important;
        line-height: 1.35;
    }

    .best-bet-table__muted {
        color: var(--dash-muted);
        font-size: 0.82rem;
    }

    .quick-read {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.95rem 1rem;
        margin: 0.65rem 0 0.9rem;
        box-shadow: var(--dash-shadow);
    }

    .quick-read__top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .quick-read__title {
        font-size: 1.18rem;
        font-weight: 800;
        color: var(--dash-ink);
    }

    .quick-read__meta {
        font-size: 0.94rem;
        color: var(--dash-muted);
    }

    .quick-read__grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
    }

    .quick-tile {
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.7rem 0.75rem;
        background: var(--dash-panel-soft);
    }

    .quick-tile__label {
        font-size: 0.84rem;
        color: var(--dash-muted);
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }

    .quick-tile__value {
        font-size: 1.18rem;
        color: var(--dash-ink);
        font-weight: 800;
        line-height: 1.2;
    }

    .h2h-sheet {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at 12% 10%, rgba(45, 212, 191, 0.15), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(245, 158, 11, 0.12), transparent 26%),
            linear-gradient(180deg, #07101d 0%, #0a1220 100%);
        border: 1px solid rgba(45, 212, 191, 0.24);
        border-radius: 8px;
        box-shadow: 0 18px 46px rgba(0, 0, 0, 0.38);
        padding: 1rem 1.08rem 1.12rem;
        margin-bottom: 0.88rem;
    }

    .h2h-sheet:before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background-image:
            linear-gradient(rgba(148, 163, 184, 0.045) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px);
        background-size: 42px 42px;
        opacity: 0.35;
    }

    .h2h-sheet > * {
        position: relative;
        z-index: 1;
    }

    .h2h-sheet__top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        margin-bottom: 0.9rem;
        color: var(--dash-muted);
        font-size: 0.76rem;
        font-weight: 950;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .h2h-sheet__title,
    .h2h-sheet__period {
        display: flex;
        align-items: center;
        gap: 0.42rem;
        min-width: 0;
    }

    .h2h-sheet__period {
        justify-content: flex-end;
        color: #e2e8f0;
        text-align: right;
    }

    .h2h-sheet__dot {
        width: 0.55rem;
        height: 0.55rem;
        border-radius: 999px;
        background: #22c55e;
        box-shadow: 0 0 18px rgba(34, 197, 94, 0.7);
        flex: 0 0 auto;
    }

    .h2h-sheet__teams {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 3.4rem minmax(0, 1fr);
        gap: 0.72rem;
        align-items: center;
        margin-bottom: 1.05rem;
    }

    .h2h-team {
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 0.72rem;
        border: 1px solid var(--team-color);
        border: 1px solid color-mix(in srgb, var(--team-color) 45%, var(--dash-border));
        background:
            linear-gradient(90deg, var(--team-glow), rgba(17, 24, 39, 0.5)),
            rgba(15, 23, 42, 0.84);
        border-radius: 8px;
        padding: 0.82rem 0.9rem;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .h2h-team--home {
        flex-direction: row-reverse;
        text-align: right;
        background:
            linear-gradient(270deg, var(--team-glow), rgba(17, 24, 39, 0.5)),
            rgba(15, 23, 42, 0.84);
    }

    .h2h-team__logo {
        width: 3rem;
        height: 3rem;
        border-radius: 8px;
        display: grid;
        place-items: center;
        color: #ffffff;
        background: var(--team-color);
        font-size: 1.08rem;
        font-weight: 950;
        letter-spacing: 0.02em;
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.28);
        flex: 0 0 auto;
    }

    .h2h-team__body {
        min-width: 0;
    }

    .h2h-team__name {
        color: var(--dash-ink);
        font-size: 1.42rem;
        font-weight: 950;
        line-height: 1.08;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .h2h-team__meta {
        color: var(--dash-muted);
        font-size: 0.82rem;
        font-weight: 800;
        line-height: 1.25;
        margin-top: 0.18rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .h2h-sheet__vs {
        width: 2.3rem;
        height: 2.3rem;
        margin: 0 auto;
        border-radius: 999px;
        display: grid;
        place-items: center;
        color: #f8fafc;
        background: #111827;
        border: 1px solid var(--dash-border);
        font-size: 0.82rem;
        font-weight: 950;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.32);
    }

    .h2h-sheet__section {
        color: #dbeafe;
        font-size: 0.78rem;
        font-weight: 950;
        letter-spacing: 0.16em;
        text-align: center;
        text-transform: uppercase;
        margin-bottom: 0.62rem;
    }

    .h2h-sheet__section--pitching {
        margin-top: 1.05rem;
    }

    .h2h-stat-rows {
        display: grid;
        gap: 0.48rem;
    }

    .h2h-stat-row {
        display: grid;
        grid-template-columns: 6.1rem minmax(0, 1fr) 8.2rem minmax(0, 1fr) 6.1rem;
        gap: 0.62rem;
        align-items: center;
    }

    .h2h-stat-row--spaced {
        margin-top: 0.52rem;
    }

    .h2h-stat__value {
        color: var(--dash-ink);
        display: flex;
        align-items: baseline;
        gap: 0.28rem;
        font-size: 1.18rem;
        font-weight: 950;
        line-height: 1;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }

    .h2h-stat__value--away {
        justify-content: flex-start;
    }

    .h2h-stat__value--home {
        justify-content: flex-end;
    }

    .h2h-stat__trend {
        font-size: 0.75rem;
        font-weight: 950;
        line-height: 1;
    }

    .h2h-stat__trend--good {
        color: #22c55e;
    }

    .h2h-stat__trend--bad {
        color: #fb5168;
    }

    .h2h-stat__trend--neutral {
        color: rgba(148, 163, 184, 0.28);
    }

    .h2h-stat__track {
        position: relative;
        height: 0.48rem;
        overflow: hidden;
        background: rgba(15, 23, 42, 0.84);
        border-radius: 999px;
        box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.08);
    }

    .h2h-stat__fill {
        position: absolute;
        top: 0;
        bottom: 0;
        border-radius: 999px;
        min-width: 3px;
    }

    .h2h-stat__fill--away {
        right: 0;
        background: linear-gradient(90deg, #16a34a, #2dd4bf);
        box-shadow: 0 0 14px rgba(45, 212, 191, 0.42);
    }

    .h2h-stat__fill--home {
        left: 0;
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        box-shadow: 0 0 14px rgba(245, 158, 11, 0.34);
    }

    .h2h-stat__fill--strong {
        background: linear-gradient(90deg, #16a34a, #22c55e) !important;
        box-shadow: 0 0 14px rgba(34, 197, 94, 0.42) !important;
    }

    .h2h-stat__fill--average {
        background: linear-gradient(90deg, #d97706, #fbbf24) !important;
        box-shadow: 0 0 14px rgba(251, 191, 36, 0.34) !important;
    }

    .h2h-stat__fill--weak {
        background: linear-gradient(90deg, #dc2626, #fb7185) !important;
        box-shadow: 0 0 14px rgba(251, 113, 133, 0.34) !important;
    }

    .h2h-stat__fill--neutral {
        background: linear-gradient(90deg, #0284c7, #38bdf8) !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.3) !important;
    }

    .h2h-stat__center {
        min-width: 0;
        text-align: center;
    }

    .h2h-stat__label {
        color: var(--dash-ink);
        font-size: 0.88rem;
        font-weight: 950;
        letter-spacing: 0.04em;
        line-height: 1.04;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .h2h-stat__sub {
        color: var(--dash-subtle);
        font-size: 0.68rem;
        font-weight: 800;
        line-height: 1.12;
        margin-top: 0.08rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .h2h-sheet__footer {
        color: var(--dash-subtle);
        font-size: 0.78rem;
        font-weight: 750;
        margin-top: 0.82rem;
        text-align: center;
    }

    .team-comparison-stack {
        display: grid;
        gap: 0.82rem;
    }

    .compare-chart {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        box-shadow: var(--dash-shadow);
        padding: 0.92rem 1rem 1rem;
        overflow: hidden;
    }

    .compare-chart__title {
        color: var(--dash-ink);
        font-size: 1.24rem;
        font-weight: 900;
        line-height: 1.12;
        text-align: center;
        margin-bottom: 0.42rem;
    }

    .compare-chart__legend,
    .compare-chart__row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 4.7rem minmax(0, 1fr);
        gap: 0.62rem;
        align-items: center;
    }

    .compare-chart__legend {
        margin-bottom: 0.62rem;
    }

    .compare-chart__side {
        min-width: 0;
    }

    .compare-chart__side--away {
        text-align: right;
    }

    .compare-chart__side--home {
        text-align: left;
    }

    .compare-chart__class {
        display: block;
        font-size: 0.82rem;
        font-weight: 950;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        line-height: 1.1;
    }

    .compare-chart__class--away {
        color: #38bdf8;
    }

    .compare-chart__class--home {
        color: #fb923c;
    }

    .compare-chart__team {
        display: block;
        color: var(--dash-ink);
        font-size: 1.08rem;
        font-weight: 950;
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .compare-chart__side--away .compare-chart__team {
        color: #38bdf8;
    }

    .compare-chart__side--home .compare-chart__team {
        color: #fb923c;
    }

    .compare-chart__middle {
        color: var(--dash-subtle);
        font-size: 0.74rem;
        font-weight: 900;
        letter-spacing: 0.05em;
        text-align: center;
        text-transform: uppercase;
    }

    .compare-chart__rows {
        display: grid;
        gap: 0.5rem;
    }

    .compare-chart__label {
        color: var(--dash-muted);
        font-size: 0.84rem;
        font-weight: 950;
        text-align: center;
        white-space: nowrap;
    }

    .compare-chart__track {
        position: relative;
        height: 2.15rem;
        overflow: hidden;
        border: 1px solid var(--dash-border);
        background: #07101d;
    }

    .compare-chart__track--away {
        border-radius: 8px 0 0 8px;
    }

    .compare-chart__track--home {
        border-radius: 0 8px 8px 0;
    }

    .compare-chart__fill {
        position: absolute;
        top: 0;
        bottom: 0;
        min-width: 3px;
    }

    .compare-chart__fill--away {
        right: 0;
        border-radius: 8px 0 0 8px;
    }

    .compare-chart__fill--home {
        left: 0;
        border-radius: 0 8px 8px 0;
    }

    .compare-chart__fill--strong {
        background: linear-gradient(90deg, #16a34a, #5ee331);
    }

    .compare-chart__fill--average {
        background: linear-gradient(90deg, #d97706, #fde047);
    }

    .compare-chart__fill--weak {
        background: linear-gradient(90deg, #dc2626, #fb7185);
    }

    .compare-chart__fill--neutral {
        background: linear-gradient(90deg, #0284c7, #38bdf8);
    }

    .compare-chart__value {
        position: absolute;
        top: 50%;
        z-index: 2;
        color: #ffffff;
        font-size: 0.92rem;
        font-weight: 950;
        line-height: 1;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);
        transform: translateY(-50%);
        font-variant-numeric: tabular-nums;
    }

    .compare-chart__value--away {
        right: 0.5rem;
    }

    .compare-chart__value--home {
        left: 0.5rem;
    }

    .compare-chart__value--empty {
        color: var(--dash-subtle);
        text-shadow: none;
    }

    .team-profile-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 0.82rem;
    }

    .team-profile-card {
        background: var(--dash-panel);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        box-shadow: var(--dash-shadow);
        padding: 0.86rem 0.9rem;
        min-width: 0;
    }

    .team-profile-card--away {
        border-left: 5px solid #38bdf8;
    }

    .team-profile-card--home {
        border-left: 5px solid #fb923c;
    }

    .team-profile-card__head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.65rem;
        margin-bottom: 0.55rem;
    }

    .team-profile-card__kicker {
        color: var(--dash-subtle);
        font-size: 0.75rem;
        font-weight: 950;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 0.12rem;
    }

    .team-profile-card__team {
        color: var(--dash-ink);
        font-size: 1.12rem;
        font-weight: 950;
        line-height: 1.12;
        overflow-wrap: anywhere;
    }

    .team-profile-card__badge {
        border-radius: 999px;
        padding: 0.16rem 0.5rem;
        font-size: 0.74rem;
        font-weight: 950;
        line-height: 1.2;
        white-space: nowrap;
    }

    .team-profile-card__badges {
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        gap: 0.35rem;
        flex-wrap: wrap;
    }

    .team-profile-card__context {
        border-radius: 999px;
        padding: 0.16rem 0.5rem;
        font-size: 0.74rem;
        font-weight: 950;
        line-height: 1.2;
        white-space: nowrap;
        background: rgba(34, 197, 94, 0.18);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.32);
    }

    .team-profile-card__context--unknown {
        background: rgba(148, 163, 184, 0.14);
        color: var(--dash-muted);
        border-color: rgba(148, 163, 184, 0.24);
    }

    .team-profile-card__badge--balanced,
    .team-profile-card__badge--contact {
        background: rgba(34, 197, 94, 0.16);
        color: #86efac;
    }

    .team-profile-card__badge--power {
        background: rgba(56, 189, 248, 0.16);
        color: #7dd3fc;
    }

    .team-profile-card__badge--volatile {
        background: rgba(245, 158, 11, 0.16);
        color: #fcd34d;
    }

    .team-profile-card__badge--cold {
        background: rgba(248, 113, 113, 0.16);
        color: #fca5a5;
    }

    .team-profile-card__badge--neutral {
        background: rgba(148, 163, 184, 0.16);
        color: var(--dash-muted);
    }

    .team-profile-card__note {
        color: var(--dash-muted);
        font-size: 0.94rem;
        font-weight: 650;
        line-height: 1.35;
        margin-bottom: 0.72rem;
    }

    .team-profile-metrics {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.48rem;
    }

    .team-profile-metric {
        background: var(--dash-panel-soft);
        border: 1px solid var(--dash-border);
        border-radius: 8px;
        padding: 0.48rem 0.54rem;
        min-width: 0;
    }

    .team-profile-metric__label {
        color: var(--dash-subtle);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.12rem;
    }

    .team-profile-metric__value {
        color: var(--dash-ink);
        font-size: 1.02rem;
        font-weight: 950;
        line-height: 1.12;
        font-variant-numeric: tabular-nums;
    }

    .section-note {
        color: var(--dash-muted);
        margin-top: -0.65rem;
        margin-bottom: 0.65rem;
        font-size: 1rem;
    }

    /* Force the custom HTML cards into the same dark system. Many cards are
       rendered with inline styles, so the important overrides are deliberate. */
    [style*="background:#ffffff"],
    [style*="background: #ffffff"],
    [style*="background: rgb(255, 255, 255)"],
    [style*="background:#fbfcfd"],
    [style*="background: #fbfcfd"],
    [style*="background: rgb(251, 252, 253)"],
    [style*="background: rgb(249, 249, 251)"],
    [style*="background: rgb(240, 242, 246)"] {
        background: var(--dash-panel) !important;
        color: var(--dash-ink) !important;
        border-color: var(--dash-border) !important;
        box-shadow: var(--dash-shadow) !important;
    }

    [style*="background:#f1f5f9"],
    [style*="background: #f1f5f9"],
    [style*="background: rgb(241, 245, 249)"],
    [style*="background: rgb(241, 241, 241)"],
    [style*="background:#eef2f7"],
    [style*="background: #eef2f7"],
    [style*="background: rgb(238, 242, 247)"] {
        background: var(--dash-panel-soft) !important;
        color: var(--dash-ink) !important;
    }

    [style*="color:#172033"],
    [style*="color: #172033"],
    [style*="color:#111827"],
    [style*="color: #111827"],
    [style*="color:#334155"],
    [style*="color: #334155"],
    [style*="color: rgb(23, 32, 51)"],
    [style*="color: rgb(17, 24, 39)"],
    [style*="color: rgb(51, 65, 85)"] {
        color: var(--dash-ink) !important;
    }

    [style*="color:#666"],
    [style*="color: #666"],
    [style*="color:#777"],
    [style*="color: #777"],
    [style*="color:#667085"],
    [style*="color: #667085"],
    [style*="color:#475467"],
    [style*="color: #475467"],
    [style*="color:#98a2b3"],
    [style*="color: #98a2b3"],
    [style*="color: rgb(102, 102, 102)"],
    [style*="color: rgb(119, 119, 119)"],
    [style*="color: rgb(102, 112, 133)"],
    [style*="color: rgb(71, 84, 103)"],
    [style*="color: rgb(152, 162, 179)"] {
        color: var(--dash-muted) !important;
    }

    [style*="border:1px solid #d9e0e8"],
    [style*="border: 1px solid #d9e0e8"],
    [style*="border:1px solid #e5ebf2"],
    [style*="border: 1px solid #e5ebf2"],
    [style*="border-bottom:1px solid #e5e5e5"],
    [style*="border-bottom: 1px solid #e5e5e5"],
    [style*="border-bottom:1px solid #f0f0f0"],
    [style*="border-bottom: 1px solid #f0f0f0"],
    [style*="border: 1px solid rgb(217, 224, 232)"],
    [style*="border: 1px solid rgb(229, 235, 242)"],
    [style*="border-bottom: 1px solid rgb(229, 229, 229)"],
    [style*="border-bottom: 1px solid rgb(240, 240, 240)"] {
        border-color: var(--dash-border) !important;
    }

	    table {
	        color: var(--dash-ink) !important;
	    }

	    .element-container:has(table),
	    div:has(> table) {
	        max-width: 100%;
	        overflow-x: auto;
	    }

    th {
        color: var(--dash-muted) !important;
        font-size: 0.8rem !important;
    }

    td {
        color: var(--dash-ink) !important;
        font-size: 0.82rem !important;
    }

    [style*="font-size:0.6rem"],
    [style*="font-size:0.61rem"],
    [style*="font-size:0.62rem"],
    [style*="font-size:0.63rem"],
    [style*="font-size:0.64rem"],
    [style*="font-size:0.66rem"],
    [style*="font-size:0.68rem"],
    [style*="font-size: 0.6rem"],
    [style*="font-size: 0.61rem"],
    [style*="font-size: 0.62rem"],
    [style*="font-size: 0.63rem"],
    [style*="font-size: 0.64rem"],
    [style*="font-size: 0.66rem"],
    [style*="font-size: 0.68rem"] {
        font-size: 0.78rem !important;
    }

    [style*="font-size:0.72rem"],
    [style*="font-size:0.74rem"],
    [style*="font-size:0.75rem"],
    [style*="font-size:0.76rem"],
    [style*="font-size:0.78rem"],
    [style*="font-size:0.8rem"],
    [style*="font-size:0.80rem"],
    [style*="font-size:0.82rem"],
    [style*="font-size: 0.72rem"],
    [style*="font-size: 0.74rem"],
    [style*="font-size: 0.75rem"],
    [style*="font-size: 0.76rem"],
    [style*="font-size: 0.78rem"],
    [style*="font-size: 0.8rem"],
    [style*="font-size: 0.80rem"],
    [style*="font-size: 0.82rem"] {
        font-size: 0.94rem !important;
    }

    [style*="font-size:0.85rem"],
    [style*="font-size:0.9rem"],
    [style*="font-size:0.95rem"],
    [style*="font-size:0.98rem"],
    [style*="font-size: 0.85rem"],
    [style*="font-size: 0.9rem"],
    [style*="font-size: 0.95rem"],
    [style*="font-size: 0.98rem"] {
        font-size: 1.05rem !important;
    }

    [style*="font-size:1rem"],
    [style*="font-size:1.02rem"],
    [style*="font-size:1.05rem"],
    [style*="font-size:1.12rem"],
    [style*="font-size:1.15rem"],
    [style*="font-size: 1rem"],
    [style*="font-size: 1.02rem"],
    [style*="font-size: 1.05rem"],
    [style*="font-size: 1.12rem"],
    [style*="font-size: 1.15rem"] {
        font-size: 1.32rem !important;
    }

    [style*="font-size:1.28rem"],
    [style*="font-size:1.35rem"],
    [style*="font-size: 1.28rem"],
    [style*="font-size: 1.35rem"] {
        font-size: 1.58rem !important;
    }

    [style*="font-size:1.8rem"],
    [style*="font-size: 1.8rem"] {
        font-size: 2.08rem !important;
    }

	    .stDataFrame,
	    [data-testid="stDataFrame"] {
	        background: var(--dash-panel) !important;
	        color: var(--dash-ink) !important;
	        max-width: 100%;
	        overflow-x: auto;
	    }

	    [data-testid="stHorizontalBlock"] {
	        gap: 0.75rem;
	    }

	    [data-testid="column"] {
	        min-width: 0;
	    }

	    [data-testid="stPlotlyChart"],
	    .js-plotly-plot,
	    .plot-container,
	    .svg-container {
	        max-width: 100% !important;
	    }

	    hr {
	        border-color: var(--dash-border) !important;
	    }

	    @media (max-width: 900px) {
	        .block-container {
	            padding-left: 0.75rem;
	            padding-right: 0.75rem;
	        }

	        [data-testid="stHorizontalBlock"] {
	            flex-wrap: wrap;
	        }

	        [data-testid="column"] {
	            flex: 1 1 100% !important;
	            width: 100% !important;
	            min-width: 100% !important;
	        }

	        .game-card {
	            min-height: auto;
	        }

	        .quick-read__top,
	        .best-bet-top {
	            align-items: flex-start;
	            flex-direction: column;
	        }

	        .best-bet-grid {
	            grid-template-columns: minmax(0, 1fr);
	        }

	        .best-bet-table {
	            min-width: 720px;
	        }

	        .h2h-stat-row {
	            grid-template-columns: 5.2rem minmax(0, 1fr) 6.6rem minmax(0, 1fr) 5.2rem;
	            gap: 0.48rem;
	        }

	        .h2h-stat__label {
	            font-size: 0.78rem;
	        }

	        .h2h-stat__sub {
	            font-size: 0.64rem;
	        }
	    }

	    @media (max-width: 760px) {
	        .block-container {
	            padding-top: 0.65rem;
	            padding-bottom: 1.6rem;
	        }

	        h1 {
	            font-size: 1.55rem !important;
	            line-height: 1.15 !important;
	        }

	        h2 {
	            font-size: 1.12rem;
	            margin-top: 1rem;
	            padding-top: 0.8rem;
	        }

	        h3 {
	            font-size: 1.02rem !important;
	        }

	        .dashboard-hero {
	            padding: 0.9rem 0.85rem;
	            margin-bottom: 0.75rem;
	        }

	        .dashboard-hero__title {
	            font-size: 1.55rem;
	        }

	        .dashboard-hero__subtitle {
	            font-size: 0.96rem;
	            line-height: 1.35;
	        }

	        .game-card {
	            padding: 0.78rem 0.85rem;
	        }

	        .game-card__team {
	            font-size: 1.22rem;
	            overflow-wrap: anywhere;
	        }

	        .game-card__meta {
	            font-size: 0.92rem;
	        }

	        .quick-read__grid {
	            grid-template-columns: repeat(2, minmax(0, 1fr));
	        }

	        .h2h-sheet {
	            padding: 0.82rem 0.72rem 0.9rem;
	        }

	        .h2h-sheet__top {
	            align-items: flex-start;
	            flex-direction: column;
	            gap: 0.35rem;
	            font-size: 0.68rem;
	            margin-bottom: 0.72rem;
	        }

	        .h2h-sheet__teams {
	            grid-template-columns: minmax(0, 1fr) 2.1rem minmax(0, 1fr);
	            gap: 0.36rem;
	            margin-bottom: 0.82rem;
	        }

	        .h2h-team,
	        .h2h-team--home {
	            align-items: flex-start;
	            flex-direction: column;
	            gap: 0.42rem;
	            padding: 0.62rem;
	            text-align: left;
	        }

	        .h2h-team__logo {
	            width: 2.25rem;
	            height: 2.25rem;
	            font-size: 0.84rem;
	        }

	        .h2h-team__name {
	            font-size: 0.94rem;
	            white-space: normal;
	        }

	        .h2h-team__meta {
	            font-size: 0.7rem;
	            white-space: normal;
	        }

	        .h2h-sheet__vs {
	            width: 1.92rem;
	            height: 1.92rem;
	            font-size: 0.68rem;
	        }

	        .h2h-sheet__section {
	            font-size: 0.68rem;
	            margin-bottom: 0.54rem;
	        }

	        .h2h-stat-rows {
	            gap: 0.44rem;
	        }

	        .h2h-stat-row {
	            grid-template-columns: 4.3rem minmax(0, 1fr) 5.6rem minmax(0, 1fr) 4.3rem;
	            gap: 0.3rem;
	        }

	        .h2h-stat__value {
	            font-size: 0.86rem;
	            gap: 0.18rem;
	        }

	        .h2h-stat__trend {
	            font-size: 0.62rem;
	        }

	        .h2h-stat__track {
	            height: 0.42rem;
	        }

	        .h2h-stat__label {
	            font-size: 0.66rem;
	            letter-spacing: 0.02em;
	        }

	        .h2h-stat__sub {
	            display: none;
	        }

	        .h2h-sheet__footer {
	            font-size: 0.68rem;
	        }

	        .compare-chart {
	            padding: 0.78rem 0.72rem 0.86rem;
	        }

	        .compare-chart__legend,
	        .compare-chart__row {
	            grid-template-columns: minmax(0, 1fr) 3.75rem minmax(0, 1fr);
	            gap: 0.42rem;
	        }

	        .compare-chart__title {
	            font-size: 1.05rem;
	        }

	        .compare-chart__track {
	            height: 1.92rem;
	        }

	        .team-profile-grid {
	            grid-template-columns: minmax(0, 1fr);
	        }

	        .team-profile-metrics {
	            grid-template-columns: repeat(2, minmax(0, 1fr));
	        }

	        .quick-read,
	        .best-bet-card,
	        .best-bet-empty,
	        .best-bet-near {
	            padding: 0.78rem 0.82rem;
	        }

	        .quick-tile {
	            padding: 0.62rem 0.65rem;
	        }

	        .quick-tile__value {
	            font-size: 1.02rem;
	            overflow-wrap: anywhere;
	        }

	        .best-bet-team {
	            font-size: 1.08rem;
	        }

	        .best-bet-score {
	            border-radius: 8px;
	            width: 100%;
	            text-align: center;
	        }

	        .best-bet-metrics {
	            grid-template-columns: repeat(2, minmax(0, 1fr));
	        }

	        .best-bet-chip {
	            white-space: normal;
	        }

	        div[data-testid="stMetric"] {
	            padding: 0.75rem 0.8rem;
	        }

	        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
	            font-size: 1.72rem !important;
	        }

	        [data-testid="stSelectbox"],
	        [data-testid="stMultiSelect"],
	        [data-testid="stTextInput"],
	        [data-testid="stDateInput"],
	        [data-testid="stRadio"],
	        [data-testid="stCheckbox"],
	        [data-testid="stSlider"],
	        [data-testid="stButton"] {
	            margin-bottom: 0.55rem;
	        }

	        .stButton button,
	        [data-testid="baseButton-secondary"],
	        [data-testid="baseButton-primary"] {
	            width: 100%;
	            min-height: 48px;
	        }
	    }

	    @media (max-width: 430px) {
	        .block-container {
	            padding-left: 0.55rem;
	            padding-right: 0.55rem;
	        }

	        .dashboard-hero__eyebrow {
	            font-size: 0.72rem;
	        }

	        .dashboard-hero__title {
	            font-size: 1.34rem;
	        }

	        .quick-read__grid,
	        .best-bet-metrics {
	            grid-template-columns: minmax(0, 1fr);
	        }

	        .h2h-stat-row {
	            grid-template-columns: 3.75rem minmax(0, 1fr) 4.6rem minmax(0, 1fr) 3.75rem;
	            gap: 0.22rem;
	        }

	        .h2h-stat__value {
	            font-size: 0.76rem;
	        }

	        .h2h-stat__label {
	            font-size: 0.6rem;
	        }

	        .quick-tile__label,
	        .best-bet-kicker,
	        .best-bet-metric__label {
	            font-size: 0.72rem;
	        }

	        .section-note {
	            font-size: 0.9rem;
	        }

	        .compare-chart__legend,
	        .compare-chart__row {
	            grid-template-columns: minmax(0, 1fr) 3.15rem minmax(0, 1fr);
	            gap: 0.28rem;
	        }

	        .compare-chart__title {
	            font-size: 0.98rem;
	        }

	        .compare-chart__class,
	        .compare-chart__middle,
	        .compare-chart__label {
	            font-size: 0.68rem;
	        }

	        .compare-chart__team {
	            font-size: 0.84rem;
	        }

	        .compare-chart__value {
	            font-size: 0.78rem;
	        }

	        .team-profile-card {
	            padding: 0.72rem 0.72rem;
	        }

	        .team-profile-card__head {
	            flex-direction: column;
	            gap: 0.38rem;
	        }

        .team-profile-card__team {
            font-size: 0.98rem;
        }

        .team-profile-card__badges {
            justify-content: flex-start;
        }

        table {
            min-width: 560px;
        }

	        [style*="grid-template-columns:repeat(6,1fr)"],
	        [style*="grid-template-columns: repeat(6,1fr)"],
	        [style*="grid-template-columns:repeat(6, 1fr)"],
	        [style*="grid-template-columns: repeat(6, 1fr)"] {
	            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
	        }

	        [style*="grid-template-columns:repeat(3,1fr)"],
	        [style*="grid-template-columns: repeat(3,1fr)"],
	        [style*="grid-template-columns:repeat(3, 1fr)"],
	        [style*="grid-template-columns: repeat(3, 1fr)"] {
	            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
	            gap: 0.45rem !important;
	        }

	        [style*="font-size:1.8rem"],
	        [style*="font-size: 1.8rem"] {
	            font-size: 1.55rem !important;
	        }
	    }
	</style>
	"""

st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="dashboard-hero">
      <div class="dashboard-hero__eyebrow">MLB analytics workspace</div>
      <div class="dashboard-hero__title">MLB Betting Dashboard</div>
      <div class="dashboard-hero__subtitle">Game context, team momentum, pitcher form, bullpen pressure, lineup splits and trend charts in one view.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def mlb_get(path: str, params: dict | None = None, timeout: int = 30) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def mlb_get_safe(path: str, params: dict | None = None) -> dict:
    try:
        return mlb_get(path, params)
    except Exception:
        return {}

def angle_distance(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)

def park_profile_for_venue(venue: str | None) -> dict:
    venue_name = str(venue or "")
    if venue_name in BALLPARK_PROFILES:
        return {"venue": venue_name, **BALLPARK_PROFILES[venue_name]}
    normalized = normalize_name(venue_name)
    for name, profile in BALLPARK_PROFILES.items():
        if normalize_name(name) == normalized:
            return {"venue": name, **profile}
    return {"venue": venue_name, "lat": None, "lon": None, "cf_bearing": None, "run": 0, "hr": 0, "roof": "unknown"}

def nearest_hour_weather(hourly: dict, game_time: Any) -> dict:
    times = pd.to_datetime(hourly.get("time", []), errors="coerce")
    if len(times) == 0:
        return {}
    game_ts = pd.to_datetime(game_time, errors="coerce", utc=True)
    if pd.isna(game_ts):
        target = times[0]
    else:
        target = game_ts.tz_convert(None)
    deltas = [abs((t - target).total_seconds()) if pd.notna(t) else float("inf") for t in times]
    idx = int(min(range(len(deltas)), key=lambda i: deltas[i]))
    return {key: (values[idx] if isinstance(values, list) and idx < len(values) else None) for key, values in hourly.items() if key != "time"} | {"time": str(times[idx])}

@st.cache_data(ttl=900)
def fetch_weather_context(venue: str | None, game_time: Any) -> dict:
    profile = park_profile_for_venue(venue)
    if not profile.get("lat") or not profile.get("lon"):
        return {
            "label": "weather unavailable",
            "score": 0,
            "park_score": 0,
            "weather_score": 0,
            "summary": "Weather unavailable for this venue.",
            "reasons": ["venue coordinates unavailable"],
            "profile": profile,
        }

    params = {
        "latitude": profile["lat"],
        "longitude": profile["lon"],
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "GMT",
        "forecast_days": 3,
    }
    try:
        resp = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return {
            "label": "weather unavailable",
            "score": 0,
            "park_score": int(profile.get("run", 0)),
            "weather_score": 0,
            "summary": f"Weather fetch failed: {exc}",
            "reasons": ["weather fetch failed"],
            "profile": profile,
        }

    hour = nearest_hour_weather(data.get("hourly", {}) or {}, game_time)
    temp = safe_float(hour.get("temperature_2m"))
    humidity = safe_float(hour.get("relative_humidity_2m"))
    precip = safe_float(hour.get("precipitation_probability"))
    wind_speed = safe_float(hour.get("wind_speed_10m"))
    wind_dir_from = safe_float(hour.get("wind_direction_10m"))
    gust = safe_float(hour.get("wind_gusts_10m"))
    cf_bearing = safe_float(profile.get("cf_bearing"))

    weather_score = 0
    reasons = []
    wind_label = "wind n/a"
    if pd.notna(wind_speed) and pd.notna(wind_dir_from) and pd.notna(cf_bearing):
        wind_to = (wind_dir_from + 180) % 360
        out_dist = angle_distance(wind_to, cf_bearing)
        in_dist = angle_distance(wind_to, (cf_bearing + 180) % 360)
        if out_dist <= 45:
            wind_label = "out to center"
            if wind_speed >= 15:
                weather_score += 2
                reasons.append("strong wind out")
            elif wind_speed >= 10:
                weather_score += 1
                reasons.append("wind out")
        elif in_dist <= 45:
            wind_label = "in from center"
            if wind_speed >= 15:
                weather_score -= 2
                reasons.append("strong wind in")
            elif wind_speed >= 10:
                weather_score -= 1
                reasons.append("wind in")
        else:
            wind_label = "crosswind"
            if wind_speed >= 15:
                reasons.append("strong crosswind")

    if pd.notna(temp):
        if temp >= 85:
            weather_score += 1
            reasons.append("hot air")
        elif temp <= 55:
            weather_score -= 1
            reasons.append("cold air")

    if pd.notna(precip) and precip >= 35:
        reasons.append("precip risk")

    park_score = int(profile.get("run", 0)) + int(profile.get("hr", 0))
    raw_score = weather_score + park_score
    roof = str(profile.get("roof", "open"))
    if roof == "retractable":
        raw_score = int(math.copysign(min(abs(raw_score), 1), raw_score)) if raw_score else 0
        reasons.append("retractable roof check")

    if raw_score >= 3:
        label = "over boost"
    elif raw_score >= 1:
        label = "slight over"
    elif raw_score <= -3:
        label = "under boost"
    elif raw_score <= -1:
        label = "slight under"
    else:
        label = "neutral"

    parts = []
    if pd.notna(temp):
        parts.append(f"{temp:.0f}F")
    if pd.notna(wind_speed):
        parts.append(f"{wind_speed:.0f} mph {wind_label}")
    if pd.notna(gust) and gust >= 15:
        parts.append(f"gust {gust:.0f}")
    if pd.notna(humidity):
        parts.append(f"{humidity:.0f}% humidity")
    summary = " | ".join(parts) if parts else "Weather data loaded."

    return {
        "label": label,
        "score": raw_score,
        "park_score": park_score,
        "weather_score": weather_score,
        "summary": summary,
        "reasons": reasons[:5],
        "time": hour.get("time"),
        "temp": temp,
        "humidity": humidity,
        "precip": precip,
        "wind_speed": wind_speed,
        "wind_dir_from": wind_dir_from,
        "wind_label": wind_label,
        "gust": gust,
        "profile": profile,
    }

def get_sportsgameodds_api_key() -> str:
    try:
        key = st.secrets.get("SPORTSGAMEODDS_API_KEY", "")
        if key:
            return str(key)
    except Exception:
        pass
    return os.getenv("SPORTSGAMEODDS_API_KEY", "")

def sportsgameodds_get(path: str, api_key: str, params: dict | None = None) -> dict:
    url = f"{SPORTSGAMEODDS_BASE_URL}{path}"
    resp = requests.get(url, headers={"x-api-key": api_key}, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def american_implied_probability(odds: Any) -> float:
    try:
        value = int(float(str(odds).replace("+", "")))
    except (TypeError, ValueError):
        return float("nan")
    if value > 0:
        return 100 / (value + 100)
    return abs(value) / (abs(value) + 100)

def normalize_name(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())

TEAM_NAME_ALIASES = {
    "arizonadiamondbacks": {"arizonadiamondbacks", "diamondbacks", "dbacks", "ari"},
    "athletics": {"athletics", "oaklandathletics", "as", "athleticsmlb", "oak"},
    "atlantabraves": {"atlantabraves", "braves", "atl"},
    "baltimoreorioles": {"baltimoreorioles", "orioles", "bal"},
    "bostonredsox": {"bostonredsox", "redsox", "bos"},
    "chicagocubs": {"chicagocubs", "cubs", "chc"},
    "chicagowhitesox": {"chicagowhitesox", "whitesox", "chw", "cws"},
    "cincinnatireds": {"cincinnatireds", "reds", "cin"},
    "clevelandguardians": {"clevelandguardians", "guardians", "cle"},
    "coloradorockies": {"coloradorockies", "rockies", "col"},
    "detroittigers": {"detroittigers", "tigers", "det"},
    "houstonastros": {"houstonastros", "astros", "hou"},
    "kansascityroyals": {"kansascityroyals", "royals", "kc", "kcr"},
    "losangelesangels": {"losangelesangels", "laangels", "angels", "anaheimangels", "laa"},
    "losangelesdodgers": {"losangelesdodgers", "ladodgers", "dodgers", "lad"},
    "miamimarlins": {"miamimarlins", "marlins", "mia"},
    "milwaukeebrewers": {"milwaukeebrewers", "brewers", "mil"},
    "minnesotatwins": {"minnesotatwins", "twins", "min"},
    "newyorkmets": {"newyorkmets", "nymets", "mets", "nym"},
    "newyorkyankees": {"newyorkyankees", "nyyankees", "yankees", "nyy"},
    "philadelphiaphillies": {"philadelphiaphillies", "phillies", "phi"},
    "pittsburghpirates": {"pittsburghpirates", "pirates", "pit"},
    "sandiegopadres": {"sandiegopadres", "padres", "sd", "sdp"},
    "sanfranciscogiants": {"sanfranciscogiants", "sfgiants", "giants", "sf", "sfg"},
    "seattlemariners": {"seattlemariners", "mariners", "sea"},
    "stlouiscardinals": {"stlouiscardinals", "cardinals", "stl"},
    "tampabayrays": {"tampabayrays", "rays", "tb", "tbr"},
    "texasrangers": {"texasrangers", "rangers", "tex"},
    "torontobluejays": {"torontobluejays", "bluejays", "tor"},
    "washingtonnationals": {"washingtonnationals", "nationals", "was", "wsh"},
}

def team_name_keys(value: Any) -> set[str]:
    normalized = normalize_name(value)
    keys = {normalized}
    for canonical, aliases in TEAM_NAME_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            keys.update(aliases)
            keys.add(canonical)
            break
    return {k for k in keys if k}

def team_names_match(expected: str, candidates: list[str]) -> bool:
    expected_keys = team_name_keys(expected)
    for candidate in candidates:
        candidate_keys = team_name_keys(candidate)
        if expected_keys & candidate_keys:
            return True
        for expected_key in expected_keys:
            for candidate_key in candidate_keys:
                if len(expected_key) >= 5 and len(candidate_key) >= 5 and (expected_key in candidate_key or candidate_key in expected_key):
                    return True
    return False

def parse_timestamp_utc(value: Any) -> pd.Timestamp | None:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            unit = "ms" if abs(value) > 10_000_000_000 else "s"
            ts = pd.to_datetime(value, unit=unit, utc=True, errors="coerce")
        else:
            ts = pd.to_datetime(value, utc=True, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).tz_convert("UTC")

def format_timestamp_et(value: Any) -> str:
    ts = parse_timestamp_utc(value)
    if ts is None:
        return ""
    try:
        et = ts.tz_convert("America/New_York")
    except (TypeError, ValueError):
        et = ts
    return et.strftime("%I:%M %p ET").lstrip("0")

def game_base_label(game: dict) -> str:
    return game.get("label") or f"{game.get('away_team_name', 'Away')} @ {game.get('home_team_name', 'Home')}"

def game_state_key(game: dict) -> str:
    game_id = game.get("game_id")
    if game_id not in {None, ""}:
        return str(game_id)
    return "|".join(str(part or "") for part in [game_base_label(game), game.get("game_time"), game.get("venue")])

def game_option_label(game: dict, duplicate_matchup: bool = False) -> str:
    base = game_base_label(game)
    double_header = str(game.get("double_header") or "").upper() not in {"", "N"}
    game_number = safe_int(game.get("game_number"))
    should_disambiguate = duplicate_matchup or double_header
    if not should_disambiguate:
        return base

    parts = []
    if game_number:
        parts.append(f"G{game_number}")
    time_label = format_timestamp_et(game.get("game_time"))
    if time_label:
        parts.append(time_label)
    if not parts and game.get("game_id"):
        parts.append(f"MLB game {game.get('game_id')}")
    return f"{base} - {' | '.join(parts)}" if parts else base

def add_game_display_labels(games: list[dict]) -> list[dict]:
    matchup_counts = Counter(game_base_label(game) for game in games)
    for game in games:
        game["game_key"] = game_state_key(game)
        game["display_label"] = game_option_label(game, matchup_counts[game_base_label(game)] > 1)
    return games

def game_display_label(game: dict) -> str:
    return game.get("display_label") or game_base_label(game)

def nested_get(data: dict, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default

def sgo_team_names(event: dict, side: str) -> list[str]:
    team = nested_get(event, ["teams", side], {}) or {}
    names = team.get("names", {}) if isinstance(team, dict) else {}
    values = []
    if isinstance(team, dict):
        values.extend([team.get("teamID"), team.get("name"), team.get("displayName")])
    if isinstance(names, dict):
        values.extend(names.values())
    return [str(v) for v in values if v]

def sgo_event_start_timestamp(event: dict) -> pd.Timestamp | None:
    for key in ["startTime", "startsAt", "statusTime", "gameTime", "scheduled", "commenceTime", "date"]:
        ts = parse_timestamp_utc(event.get(key))
        if ts is not None:
            return ts
    for path in [["status", "startTime"], ["status", "startsAt"], ["schedule", "startTime"]]:
        ts = parse_timestamp_utc(nested_get(event, path))
        if ts is not None:
            return ts
    return None

def find_sgo_event(events: list[dict], away_team: str, home_team: str, game: dict | None = None) -> dict:
    matches = []
    for event in events:
        away_names = sgo_team_names(event, "away")
        home_names = sgo_team_names(event, "home")
        if team_names_match(away_team, away_names) and team_names_match(home_team, home_names):
            matches.append(event)
    if not matches:
        return {}
    if len(matches) == 1:
        return matches[0]

    target_start = parse_timestamp_utc((game or {}).get("game_time"))
    if target_start is not None:
        timed_matches = []
        for event in matches:
            event_start = sgo_event_start_timestamp(event)
            if event_start is None:
                continue
            delta_seconds = abs((event_start - target_start).total_seconds())
            timed_matches.append((delta_seconds, event))
        if timed_matches:
            return sorted(timed_matches, key=lambda item: item[0])[0][1]
    return matches[0]

def describe_sgo_events(events: list[dict], limit: int = 8) -> str:
    labels = []
    for event in events[:limit]:
        away = sgo_team_names(event, "away")
        home = sgo_team_names(event, "home")
        away_label = away[0] if away else "Away n/a"
        home_label = home[0] if home else "Home n/a"
        time_label = format_timestamp_et(sgo_event_start_timestamp(event))
        labels.append(f"{away_label} @ {home_label}" + (f" - {time_label}" if time_label else ""))
    return "\n".join(labels)

def sgo_selected_odd_ids(markets: list[str]) -> list[str]:
    odd_ids = []
    if "Moneyline" in markets:
        odd_ids.extend(["points-away-game-ml-away", "points-home-game-ml-home"])
    if "Run line" in markets:
        odd_ids.extend(["points-away-game-sp-away", "points-home-game-sp-home"])
    if "Game total" in markets:
        odd_ids.extend(["points-all-game-ou-over", "points-all-game-ou-under"])
    return odd_ids

@st.cache_data(ttl=60)
def fetch_sgo_events_for_date(api_key: str, game_date: str, odd_ids: tuple[str, ...]) -> tuple[list[dict], str]:
    if not api_key:
        return [], "Missing SportsGameOdds API key."
    start = f"{game_date}T00:00:00Z"
    end = (pd.Timestamp(game_date) + pd.Timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
    params = {
        "leagueID": "MLB",
        "oddsAvailable": "true",
        "startsAfter": start,
        "startsBefore": end,
        "oddID": "points-away-game-ml-away,points-home-game-ml-home",
        "includeOpposingOdds": "true",
        "includeOpenCloseOdds": "true",
        "limit": 100,
    }
    if odd_ids:
        params["oddID"] = ",".join(odd_ids)
        params["includeOpposingOdds"] = "true"
    try:
        data = sportsgameodds_get("/events", api_key, params)
    except Exception as exc:
        return [], str(exc)
    if not data.get("success", True):
        return [], str(data.get("error", "SportsGameOdds request failed."))
    return data.get("data", []) or [], ""

@st.cache_data(ttl=60)
def fetch_sgo_events_for_pitcher_props(api_key: str, game_date: str, bookmakers: tuple[str, ...]) -> tuple[list[dict], str]:
    if not api_key:
        return [], "Missing SportsGameOdds API key."
    start = f"{game_date}T00:00:00Z"
    end = (pd.Timestamp(game_date) + pd.Timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
    params = {
        "leagueID": "MLB",
        "oddsAvailable": "true",
        "startsAfter": start,
        "startsBefore": end,
        "includeOpenCloseOdds": "true",
        "limit": 100,
    }
    try:
        data = sportsgameodds_get("/events", api_key, params)
    except Exception as exc:
        return [], str(exc)
    if not data.get("success", True):
        return [], str(data.get("error", "SportsGameOdds request failed."))
    return data.get("data", []) or [], ""

@st.cache_data(ttl=60)
def fetch_sgo_event_full_odds(api_key: str, event_id: str) -> tuple[dict, str]:
    if not api_key:
        return {}, "Missing SportsGameOdds API key."
    if not event_id:
        return {}, "Missing SportsGameOdds event id."

    request_variants = [
        {"eventID": event_id, "includeOpenCloseOdds": "true"},
        {"eventID": event_id},
    ]
    last_error = ""
    for params in request_variants:
        try:
            data = sportsgameodds_get("/events", api_key, params)
        except Exception as exc:
            last_error = str(exc)
            continue
        if not data.get("success", True):
            last_error = str(data.get("error", "SportsGameOdds request failed."))
            continue
        events = data.get("data", []) or []
        return (events[0] if events else {}), ""
    return {}, last_error or "SportsGameOdds event request failed."

def sgo_entity_to_player_name(stat_entity_id: Any) -> str:
    parts = [part for part in str(stat_entity_id or "").replace("-", "_").split("_") if part]
    while parts and parts[-1].upper() in {"MLB", "NBA", "NFL", "NHL"}:
        parts.pop()
    while parts and parts[-1].isdigit():
        parts.pop()
    return " ".join(part.capitalize() for part in parts)

def sgo_market_player_name(market_name: Any) -> str:
    text = str(market_name or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    markers = [" earned runs", " pitching earned runs", " to record", " over/under", " yes/no"]
    cut_positions = [lowered.find(marker) for marker in markers if lowered.find(marker) > 0]
    if cut_positions:
        return text[: min(cut_positions)].strip()
    return ""

def _name_words(value: Any) -> list[str]:
    return [word for word in str(value or "").replace(".", "").replace("-", " ").split() if word]

def player_names_match(expected: str, candidates: list[str]) -> bool:
    expected_norm = normalize_name(expected)
    if not expected_norm:
        return False
    expected_words = _name_words(expected)
    expected_last = normalize_name(expected_words[-1]) if expected_words else ""
    expected_first_initial = normalize_name(expected_words[0])[:1] if expected_words else ""
    for candidate in candidates:
        candidate_norm = normalize_name(candidate)
        if not candidate_norm:
            continue
        if expected_norm == candidate_norm:
            return True
        if len(expected_norm) >= 6 and len(candidate_norm) >= 6 and (expected_norm in candidate_norm or candidate_norm in expected_norm):
            return True
        candidate_words = _name_words(candidate)
        candidate_last = normalize_name(candidate_words[-1]) if candidate_words else ""
        candidate_first_initial = normalize_name(candidate_words[0])[:1] if candidate_words else ""
        if expected_last and candidate_last == expected_last and expected_first_initial == candidate_first_initial:
            return True
    return False

def pitcher_er_odd_candidates(odd: dict) -> list[str]:
    candidates = [
        sgo_entity_to_player_name(odd.get("statEntityID")),
        sgo_market_player_name(odd.get("marketName")),
        odd.get("playerName", ""),
        nested_get(odd, ["player", "name"], ""),
        nested_get(odd, ["player", "fullName"], ""),
    ]
    return [str(c) for c in candidates if c]

def is_pitcher_er_odd(odd: dict) -> bool:
    odd_id = str(odd.get("oddID", ""))
    stat_id = str(odd.get("statID", ""))
    return (
        (stat_id == "pitching_earnedRuns" or odd_id.startswith("pitching_earnedRuns-"))
        and str(odd.get("betTypeID", "")) == "ou"
        and str(odd.get("periodID", "")) == "game"
    )

def match_pitcher_er_odd_to_starter(odd: dict, pitchers: list[dict]) -> dict:
    candidates = pitcher_er_odd_candidates(odd)
    for pitcher in pitchers:
        if player_names_match(str(pitcher.get("pitcher_name", "")), candidates):
            return pitcher
    return {}

def flatten_sgo_pitcher_er_props(event: dict, game: dict, pitchers: list[dict], bookmakers: list[str] | None = None) -> list[dict]:
    rows = []
    odds = event.get("odds", {}) if isinstance(event, dict) else {}
    wanted_books = {b.lower() for b in bookmakers or [] if b}
    for odd in odds.values():
        if not isinstance(odd, dict) or not is_pitcher_er_odd(odd):
            continue
        pitcher = match_pitcher_er_odd_to_starter(odd, pitchers)
        if not pitcher:
            continue
        side = str(odd.get("sideID", "")).lower()
        if side not in {"over", "under"}:
            continue
        by_book = odd.get("byBookmaker", {}) if isinstance(odd, dict) else {}
        for bookmaker_id, book_odds in by_book.items():
            if wanted_books and bookmaker_id.lower() not in wanted_books:
                continue
            if book_odds and book_odds.get("available") is False:
                continue
            price = book_odds.get("odds")
            line = book_odds.get("overUnder", odd.get("overUnder"))
            if price in {None, ""} or line in {None, ""}:
                continue
            rows.append(
                {
                    "game_id": game.get("game_id"),
                    "event_id": event.get("eventID"),
                    "start_time": event.get("startTime") or event.get("startsAt") or event.get("statusTime"),
                    "game_date": pd.Timestamp(game.get("game_time") or pd.Timestamp.today()).strftime("%Y-%m-%d"),
                    "matchup": game_display_label(game),
                    "team": pitcher.get("team"),
                    "opponent": pitcher.get("opponent"),
                    "pitcher_id": pitcher.get("pitcher_id"),
                    "pitcher_name": pitcher.get("pitcher_name"),
                    "stat_entity_id": odd.get("statEntityID"),
                    "odd_id": odd.get("oddID"),
                    "market": "Pitcher ER",
                    "side": side,
                    "book": bookmaker_id,
                    "price": price,
                    "line": line,
                    "open_price": book_odds.get("openOdds"),
                    "open_line": book_odds.get("openOverUnder"),
                    "implied_prob": american_implied_probability(price),
                }
            )
    return rows

def odds_market_label(odd: dict) -> str:
    odd_id = odd.get("oddID", "")
    if odd.get("betTypeID") == "ml":
        return "Moneyline"
    if odd.get("betTypeID") == "sp":
        return "Run line"
    if odd.get("betTypeID") == "ou":
        return "Game total" if "points-all-" in odd_id else "Total"
    return str(odd.get("betTypeID") or odd_id)

def odds_line_value(book_odds: dict, odd: dict) -> Any:
    if odd.get("betTypeID") == "sp":
        return book_odds.get("spread", odd.get("spread"))
    if odd.get("betTypeID") == "ou":
        return book_odds.get("overUnder", odd.get("overUnder"))
    return ""

def odds_open_line_value(book_odds: dict, odd: dict) -> Any:
    if odd.get("betTypeID") == "sp":
        return book_odds.get("openSpread")
    if odd.get("betTypeID") == "ou":
        return book_odds.get("openOverUnder")
    return ""

def flatten_sgo_odds(event: dict, bookmakers: list[str] | None = None) -> list[dict]:
    rows = []
    odds = event.get("odds", {}) if isinstance(event, dict) else {}
    wanted_books = {b.lower() for b in bookmakers or [] if b}
    for odd in odds.values():
        by_book = odd.get("byBookmaker", {}) if isinstance(odd, dict) else {}
        for bookmaker_id, book_odds in by_book.items():
            if wanted_books and bookmaker_id.lower() not in wanted_books:
                continue
            if book_odds and book_odds.get("available") is False:
                continue
            price = book_odds.get("odds")
            line = odds_line_value(book_odds, odd)
            open_price = book_odds.get("openOdds")
            open_line = odds_open_line_value(book_odds, odd)
            rows.append(
                {
                    "event_id": event.get("eventID"),
                    "start_time": event.get("startTime") or event.get("startsAt") or event.get("statusTime"),
                    "market": odds_market_label(odd),
                    "odd_id": odd.get("oddID"),
                    "side": odd.get("sideID"),
                    "book": bookmaker_id,
                    "price": price,
                    "line": line,
                    "open_price": open_price,
                    "open_line": open_line,
                    "implied_prob": american_implied_probability(price),
                }
            )
    return rows

def read_odds_snapshots() -> pd.DataFrame:
    if not ODDS_SNAPSHOT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(ODDS_SNAPSHOT_PATH)

def append_odds_snapshots(rows: list[dict], matchup_label: str) -> int:
    if not rows:
        return 0
    fetched_at = pd.Timestamp.now(tz="UTC").isoformat()
    out_rows = [{**row, "matchup": matchup_label, "fetched_at": fetched_at} for row in rows]
    df = pd.DataFrame(out_rows)
    ODDS_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = read_odds_snapshots()
    combined = pd.concat([existing, df], ignore_index=True) if not existing.empty else df
    combined.to_csv(ODDS_SNAPSHOT_PATH, index=False)
    return len(df)

def add_odds_movement(rows: list[dict], snapshots: pd.DataFrame) -> list[dict]:
    if not rows or snapshots.empty:
        return rows
    required_cols = {"event_id", "odd_id", "book", "price", "fetched_at"}
    if not required_cols.issubset(set(snapshots.columns)):
        return rows
    snapshots = snapshots.copy()
    snapshots["fetched_at"] = pd.to_datetime(snapshots["fetched_at"], errors="coerce")
    output = []
    for row in rows:
        mask = (
            (snapshots.get("event_id").astype(str) == str(row.get("event_id")))
            & (snapshots.get("odd_id").astype(str) == str(row.get("odd_id")))
            & (snapshots.get("book").astype(str) == str(row.get("book")))
        )
        prior = snapshots[mask].sort_values("fetched_at").tail(1)
        movement = ""
        movement_dir = "neutral"
        if not prior.empty:
            prev = prior.iloc[0]
            try:
                price_delta = int(float(str(row.get("price")).replace("+", ""))) - int(float(str(prev.get("price")).replace("+", "")))
                if price_delta > 0:
                    movement = f"price better by {price_delta}"
                    movement_dir = "up"
                elif price_delta < 0:
                    movement = f"price worse by {abs(price_delta)}"
                    movement_dir = "down"
                else:
                    movement = "price unchanged"
                    movement_dir = "neutral"
            except (TypeError, ValueError):
                movement = ""
                movement_dir = "neutral"
        output.append({**row, "movement": movement, "movement_dir": movement_dir})
    return output

def american_odds_int(odds: Any) -> int | None:
    try:
        return int(float(str(odds).replace("+", "")))
    except (TypeError, ValueError):
        return None

def odds_side_context(row: dict, away_team: str, home_team: str) -> str:
    odd_id = str(row.get("odd_id", "")).lower()
    side = str(row.get("side", "")).lower()
    if "over" in odd_id or side == "over":
        return "over"
    if "under" in odd_id or side == "under":
        return "under"
    if "-away" in odd_id or side == "away":
        return "away"
    if "-home" in odd_id or side == "home":
        return "home"
    return side

def odds_price_warning(price: Any) -> str:
    value = american_odds_int(price)
    if value is None:
        return "missing price"
    if value <= -170:
        return "expensive"
    if value <= -140:
        return "pricey"
    return ""

def score_side_signal(team_snap: dict, opp_pitcher: dict, own_pitcher: dict, opp_bullpen: dict, context: dict, run_line: bool = False) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    if team_snap.get("offense_signal") == "strong":
        score += 2
        reasons.append("strong offense")
    elif team_snap.get("offense_signal") == "good":
        score += 1
        reasons.append("good offense")
    elif team_snap.get("offense_signal") in {"weak", "cooling"}:
        score -= 1
        reasons.append("offense risk")

    opp_truth = (opp_pitcher or {}).get("era_truth", {})
    if opp_truth.get("label") in {"danger spot", "lucky ERA", "regression risk"}:
        score += 2
        reasons.append(f"opp starter {opp_truth.get('label')}")
    elif opp_truth.get("label") == "watch traffic":
        score += 1
        reasons.append("opp starter traffic")
    elif opp_truth.get("label") == "true strong":
        score -= 2
        reasons.append("opp starter true strong")

    own_truth = (own_pitcher or {}).get("era_truth", {})
    if own_truth.get("label") in {"true strong", "unlucky ERA"}:
        score += 1
        reasons.append(f"own starter {own_truth.get('label')}")
    elif own_truth.get("label") in {"danger spot", "lucky ERA", "regression risk"}:
        score -= 1
        reasons.append(f"own starter {own_truth.get('label')}")

    if (opp_bullpen or {}).get("label") in {"high traffic", "run risk"}:
        score += 1
        reasons.append("opp bullpen risk")
    if (context or {}).get("label") == "context boost":
        score += 1
        reasons.append("venue context boost")
    elif (context or {}).get("label") == "context drag":
        score -= 1
        reasons.append("venue context drag")

    if run_line and score < 4:
        reasons.append("run line needs stronger edge")
    return score, reasons[:4]

def score_total_signal(
    away_snap: dict,
    home_snap: dict,
    away_pitcher: dict,
    home_pitcher: dict,
    away_bullpen: dict,
    home_bullpen: dict,
    side: str,
    weather_context: dict | None = None,
    total_line: Any = None,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    strong_offenses = sum(1 for snap in [away_snap, home_snap] if snap.get("offense_signal") in {"strong", "good"})
    weak_offenses = sum(1 for snap in [away_snap, home_snap] if snap.get("offense_signal") in {"weak", "cooling"})
    risky_starters = sum(1 for p in [away_pitcher, home_pitcher] if (p.get("era_truth", {}) or {}).get("label") in {"danger spot", "lucky ERA", "regression risk", "watch traffic"})
    strong_starters = sum(1 for p in [away_pitcher, home_pitcher] if (p.get("era_truth", {}) or {}).get("label") == "true strong")
    risky_bullpens = sum(1 for b in [away_bullpen, home_bullpen] if b.get("label") in {"high traffic", "run risk"})
    weather_score = int((weather_context or {}).get("score", 0))
    line_value = safe_float(total_line)

    score += strong_offenses
    score += risky_starters
    score += risky_bullpens
    score -= weak_offenses
    score -= strong_starters
    score += weather_score

    if strong_offenses:
        reasons.append(f"{strong_offenses} offense signal(s)")
    if risky_starters:
        reasons.append(f"{risky_starters} starter risk(s)")
    if risky_bullpens:
        reasons.append(f"{risky_bullpens} bullpen risk(s)")
    if strong_starters:
        reasons.append(f"{strong_starters} true-strong starter(s)")
    if weak_offenses:
        reasons.append(f"{weak_offenses} offense drag(s)")
    if weather_score > 0:
        reasons.append(f"park/weather {weather_context.get('label')}")
    elif weather_score < 0:
        reasons.append(f"park/weather {weather_context.get('label')}")

    if side == "under":
        score = -score
        if pd.notna(line_value) and line_value <= 7.5:
            score -= 1
            reasons.append("low under line")
        reasons = ["inverse total read"] + reasons[:3]
    elif side == "over":
        if pd.notna(line_value) and line_value >= 9.5:
            score -= 1
            reasons.append("high over line")
        if pd.notna(line_value) and line_value < 8:
            score -= 1
            reasons.append("low total variance")
    return score, reasons[:4]

def classify_odds_signal(score: int, market: str) -> str:
    playable_threshold = 5 if market in {"Run line", "Game total"} else 4
    if score >= playable_threshold:
        return "Playable"
    if score >= 2:
        return "Lean"
    if score >= 1:
        return "Watch"
    return "No bet"

def pitcher_truth_label(pitcher: dict) -> str:
    return str(((pitcher or {}).get("era_truth", {}) or {}).get("label", ""))

def pitcher_has_bad_truth(pitcher: dict) -> bool:
    return pitcher_truth_label(pitcher) in {"danger spot", "lucky ERA", "regression risk"}

def pitcher_has_targetable_truth(pitcher: dict) -> bool:
    return pitcher_truth_label(pitcher) in {"danger spot", "lucky ERA", "regression risk", "watch traffic"}

def bullpen_is_targetable(bullpen: dict) -> bool:
    return (bullpen or {}).get("label") in {"high traffic", "run risk"}

def context_is_drag(context: dict) -> bool:
    return (context or {}).get("label") == "context drag"

def offense_is_positive(snapshot: dict) -> bool:
    return (snapshot or {}).get("offense_signal") in {"strong", "good"}

def offense_is_strong(snapshot: dict) -> bool:
    return (snapshot or {}).get("offense_signal") == "strong"

def offense_is_weak(snapshot: dict) -> bool:
    return (snapshot or {}).get("offense_signal") in {"weak", "cooling"}

def side_has_run_edge(team_snap: dict, opp_snap: dict) -> bool:
    team_l7 = safe_float((team_snap or {}).get("last7_runs"))
    opp_l7 = safe_float((opp_snap or {}).get("last7_runs"))
    team_season = safe_float((team_snap or {}).get("season_runs"))
    opp_season = safe_float((opp_snap or {}).get("season_runs"))
    recent_edge = pd.notna(team_l7) and pd.notna(opp_l7) and team_l7 >= opp_l7
    season_edge = pd.notna(team_season) and pd.notna(opp_season) and team_season >= opp_season
    return recent_edge or season_edge

def side_playable_check(
    market: str,
    team_snap: dict,
    opp_snap: dict,
    opp_pitcher: dict,
    own_pitcher: dict,
    opp_bullpen: dict,
    context: dict,
) -> tuple[bool, str]:
    failures = []
    opp_weakness = pitcher_has_targetable_truth(opp_pitcher) or bullpen_is_targetable(opp_bullpen)

    if market == "Moneyline":
        if not offense_is_positive(team_snap):
            failures.append("needs positive offense")
        if pitcher_has_bad_truth(own_pitcher):
            failures.append("own starter risk")
        if not opp_weakness:
            failures.append("needs opp pitcher/bullpen weakness")
        if context_is_drag(context):
            failures.append("context drag")

    elif market == "Run line":
        if not offense_is_strong(team_snap):
            failures.append("run line needs strong offense")
        if pitcher_has_bad_truth(own_pitcher):
            failures.append("own starter risk")
        if not opp_weakness:
            failures.append("needs opp pitcher/bullpen weakness")
        if context_is_drag(context):
            failures.append("context drag")
        if not side_has_run_edge(team_snap, opp_snap):
            failures.append("needs run edge")
        if offense_is_strong(opp_snap) and not pitcher_has_targetable_truth(opp_pitcher):
            failures.append("opponent offense threat")

    if failures:
        return False, "playable checklist failed: " + ", ".join(failures[:3])
    return True, ""

def total_component_counts(
    away_snap: dict,
    home_snap: dict,
    away_pitcher: dict,
    home_pitcher: dict,
    away_bullpen: dict,
    home_bullpen: dict,
    weather_context: dict | None = None,
) -> dict:
    return {
        "strong_offenses": sum(1 for snap in [away_snap, home_snap] if offense_is_positive(snap)),
        "weak_offenses": sum(1 for snap in [away_snap, home_snap] if offense_is_weak(snap)),
        "risky_starters": sum(1 for p in [away_pitcher, home_pitcher] if pitcher_has_targetable_truth(p)),
        "strong_starters": sum(1 for p in [away_pitcher, home_pitcher] if pitcher_truth_label(p) == "true strong"),
        "risky_bullpens": sum(1 for b in [away_bullpen, home_bullpen] if bullpen_is_targetable(b)),
        "weather_score": safe_int((weather_context or {}).get("score")),
    }

def total_playable_check(side: str, components: dict) -> tuple[bool, str]:
    failures = []
    weather_score = components.get("weather_score", 0)

    if side == "over":
        independent = sum(
            [
                components.get("strong_offenses", 0) >= 2,
                components.get("risky_starters", 0) >= 1,
                components.get("risky_bullpens", 0) >= 1,
                weather_score > 0,
            ]
        )
        if independent < 3:
            failures.append("needs 3 over factors")
        if components.get("weak_offenses", 0) >= 2:
            failures.append("two offense drags")
        if components.get("strong_starters", 0) >= 2:
            failures.append("two true-strong starters")

    elif side == "under":
        independent = sum(
            [
                components.get("weak_offenses", 0) >= 1,
                components.get("strong_starters", 0) >= 1,
                components.get("risky_starters", 0) == 0,
                components.get("risky_bullpens", 0) == 0,
                weather_score < 0,
            ]
        )
        if independent < 3:
            failures.append("needs 3 under factors")
        if components.get("strong_offenses", 0) >= 2:
            failures.append("two offense boosts")
        if components.get("risky_starters", 0) >= 1:
            failures.append("starter risk blocks under")

    else:
        failures.append("unknown total side")

    if failures:
        return False, "playable checklist failed: " + ", ".join(failures[:3])
    return True, ""

def action_signal_rank(label: str) -> int:
    return {"Playable": 2, "Lean": 1}.get(str(label), 0)

def conflict_line_key(row: dict) -> str:
    market = row.get("market", "")
    if market == "Moneyline":
        return "ml"
    line = safe_float(row.get("line"))
    if pd.isna(line):
        return "no-line"
    if market == "Run line":
        return f"{abs(line):.1f}"
    if market == "Game total":
        return f"{line:.1f}"
    return str(row.get("line", ""))

def apply_conflict_filter(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple, list[int]] = {}
    for idx, row in enumerate(rows):
        if row.get("market") not in {"Moneyline", "Run line", "Game total"}:
            continue
        if action_signal_rank(row.get("signal", "")) == 0:
            continue
        key = (
            str(row.get("event_id", "")),
            str(row.get("book", "")),
            str(row.get("market", "")),
            conflict_line_key(row),
        )
        grouped.setdefault(key, []).append(idx)

    output = [dict(row) for row in rows]
    for indexes in grouped.values():
        sides = {str(output[i].get("side", "")).lower() for i in indexes}
        if not ({"away", "home"}.issubset(sides) or {"over", "under"}.issubset(sides)):
            continue
        max_score = max(safe_float(output[i].get("signal_score")) for i in indexes)
        best_indexes = [i for i in indexes if safe_float(output[i].get("signal_score")) == max_score]
        if len(best_indexes) != 1:
            for i in indexes:
                output[i]["signal"] = "No clear edge"
                existing = str(output[i].get("signal_reasons", ""))
                output[i]["signal_reasons"] = "; ".join([part for part in [existing, "conflicting signals tied"] if part])[:240]
            continue
        best_idx = best_indexes[0]
        best_side = output[best_idx].get("side", "")
        for i in indexes:
            if i == best_idx:
                continue
            output[i]["signal"] = "No bet"
            existing = str(output[i].get("signal_reasons", ""))
            output[i]["signal_reasons"] = "; ".join([part for part in [existing, f"weaker than {best_side} side"] if part])[:240]
    return output

def add_betting_signals_to_odds(
    rows: list[dict],
    game: dict,
    away_snapshot: dict,
    home_snapshot: dict,
    away_pitcher: dict,
    home_pitcher: dict,
    away_bullpen: dict,
    home_bullpen: dict,
    away_context: dict,
    home_context: dict,
    weather_context: dict | None = None,
) -> list[dict]:
    output = []
    for row in rows:
        market = row.get("market", "")
        side_context = odds_side_context(row, game.get("away_team_name", ""), game.get("home_team_name", ""))
        playable_note = ""
        if market in {"Moneyline", "Run line"}:
            if side_context == "away":
                score, reasons = score_side_signal(away_snapshot, home_pitcher, away_pitcher, home_bullpen, away_context, run_line=market == "Run line")
                playable_ok, playable_note = side_playable_check(market, away_snapshot, home_snapshot, home_pitcher, away_pitcher, home_bullpen, away_context)
            elif side_context == "home":
                score, reasons = score_side_signal(home_snapshot, away_pitcher, home_pitcher, away_bullpen, home_context, run_line=market == "Run line")
                playable_ok, playable_note = side_playable_check(market, home_snapshot, away_snapshot, away_pitcher, home_pitcher, away_bullpen, home_context)
            else:
                score, reasons = 0, ["unknown side"]
                playable_ok = False
        elif market == "Game total":
            score, reasons = score_total_signal(
                away_snapshot,
                home_snapshot,
                away_pitcher,
                home_pitcher,
                away_bullpen,
                home_bullpen,
                side_context,
                weather_context,
                row.get("line"),
            )
            total_components = total_component_counts(away_snapshot, home_snapshot, away_pitcher, home_pitcher, away_bullpen, home_bullpen, weather_context)
            playable_ok, playable_note = total_playable_check(side_context, total_components)
        else:
            score, reasons = 0, ["unsupported market"]
            playable_ok = False
        label = classify_odds_signal(score, market)
        if label == "Playable" and not playable_ok:
            label = "Lean"
            if playable_note:
                reasons.append(playable_note)
        output.append({**row, "signal": label, "signal_score": score, "signal_reasons": "; ".join(reasons[:4])})
    return apply_conflict_filter(output)

def best_bet_recent_ops_strong(snapshot: dict) -> bool:
    last7 = safe_float((snapshot or {}).get("last7_ops"))
    last3 = safe_float((snapshot or {}).get("last3_ops"))
    return pd.notna(last7) and pd.notna(last3) and last7 >= 0.760 and last3 >= 0.740

def best_bet_recent_obp_strong(snapshot: dict) -> bool:
    last7 = safe_float((snapshot or {}).get("last7_obp"))
    last3 = safe_float((snapshot or {}).get("last3_obp"))
    return pd.notna(last7) and pd.notna(last3) and last7 >= 0.330 and last3 >= 0.320

def best_bet_opponent_offense_weak(snapshot: dict) -> bool:
    last7_ops = safe_float((snapshot or {}).get("last7_ops"))
    last7_obp = safe_float((snapshot or {}).get("last7_obp"))
    last3_ops = safe_float((snapshot or {}).get("last3_ops"))
    last3_obp = safe_float((snapshot or {}).get("last3_obp"))
    return (
        offense_is_weak(snapshot)
        or (pd.notna(last7_ops) and pd.notna(last7_obp) and last7_ops <= 0.700 and last7_obp <= 0.310)
        or (pd.notna(last3_ops) and pd.notna(last3_obp) and last3_ops <= 0.680 and last3_obp <= 0.300)
    )

def best_bet_bullpen_great(bullpen: dict) -> bool:
    games = safe_int((bullpen or {}).get("games"))
    era = safe_float((bullpen or {}).get("era"))
    whip = safe_float((bullpen or {}).get("whip"))
    if games < 3 or bullpen_is_targetable(bullpen):
        return False
    if (bullpen or {}).get("label") == "steady":
        return True
    return pd.notna(era) and pd.notna(whip) and era <= 3.25 and whip <= 1.25

def best_bet_starter_at_or_better(pitcher: dict) -> bool:
    if not (pitcher or {}).get("id"):
        return False
    recent = pitcher_recent_label(pitcher)
    return recent in {"better than season", "near season"} and not pitcher_has_bad_truth(pitcher)

def best_bet_opponent_starter_shaky(pitcher: dict) -> bool:
    if not (pitcher or {}).get("id"):
        return False
    era = safe_float((pitcher or {}).get("era"))
    whip = safe_float((pitcher or {}).get("whip"))
    recent = pitcher_recent_label(pitcher)
    return (
        pitcher_has_targetable_truth(pitcher)
        or recent == "worse than season"
        or (pd.notna(era) and pd.notna(whip) and era >= 4.75 and whip >= 1.35)
    )

def best_bet_rule_components(
    team_snap: dict,
    opp_snap: dict,
    own_pitcher: dict,
    opp_pitcher: dict,
    own_bullpen: dict,
    opp_bullpen: dict,
) -> dict[str, bool]:
    return {
        "OPS": best_bet_recent_ops_strong(team_snap),
        "OBP": best_bet_recent_obp_strong(team_snap),
        "Own bullpen": best_bet_bullpen_great(own_bullpen),
        "Own starter": best_bet_starter_at_or_better(own_pitcher),
        "Opp offense": best_bet_opponent_offense_weak(opp_snap),
        "Opp starter": best_bet_opponent_starter_shaky(opp_pitcher),
        "Opp bullpen": bullpen_is_targetable(opp_bullpen),
    }

def best_bet_failure_details(
    components: dict[str, bool],
    team_snap: dict,
    opp_snap: dict,
    own_pitcher: dict,
    opp_pitcher: dict,
    own_bullpen: dict,
    opp_bullpen: dict,
) -> list[str]:
    failures = []
    if not components.get("OPS"):
        failures.append(
            f"OPS: needs L7 >= .760 and L3 >= .740; has L7 {format_stat(team_snap.get('last7_ops'), 3)}, L3 {format_stat(team_snap.get('last3_ops'), 3)}"
        )
    if not components.get("OBP"):
        failures.append(
            f"OBP: needs L7 >= .330 and L3 >= .320; has L7 {format_stat(team_snap.get('last7_obp'), 3)}, L3 {format_stat(team_snap.get('last3_obp'), 3)}"
        )
    if not components.get("Own bullpen"):
        failures.append(
            f"Own bullpen: needs steady or <= 3.25 ERA / <= 1.25 WHIP; has {_friendly_signal_label(own_bullpen.get('label', 'n/a'))}, {format_stat(own_bullpen.get('era'), 2)} ERA, {format_stat(own_bullpen.get('whip'), 3)} WHIP"
        )
    if not components.get("Own starter"):
        failures.append(
            f"Own starter: needs near/better recent form and no ERA-truth risk; has {pitcher_recent_label(own_pitcher)}, {pitcher_truth_label(own_pitcher) or 'no truth flag'}"
        )
    if not components.get("Opp offense"):
        failures.append(
            f"Opp offense: needs weak/cooling or low recent OPS/OBP; has {_friendly_signal_label(opp_snap.get('offense_signal', 'n/a'))}, L7 OPS {format_stat(opp_snap.get('last7_ops'), 3)}, L7 OBP {format_stat(opp_snap.get('last7_obp'), 3)}"
        )
    if not components.get("Opp starter"):
        failures.append(
            f"Opp starter: needs targetable or worse than season; has {pitcher_recent_label(opp_pitcher)}, {pitcher_truth_label(opp_pitcher) or 'no truth flag'}, {format_stat(opp_pitcher.get('era'), 2)} ERA / {format_stat(opp_pitcher.get('whip'), 3)} WHIP"
        )
    if not components.get("Opp bullpen"):
        failures.append(
            f"Opp bullpen: needs high traffic/run risk; has {_friendly_signal_label(opp_bullpen.get('label', 'n/a'))}, {format_stat(opp_bullpen.get('era'), 2)} ERA, {format_stat(opp_bullpen.get('whip'), 3)} WHIP"
        )
    return failures

def best_bet_metric_summary(label: str, value: str) -> str:
    return f"""
    <div class="best-bet-metric">
      <div class="best-bet-metric__label">{html.escape(label)}</div>
      <div class="best-bet-metric__value">{html.escape(value)}</div>
    </div>
    """

def best_bet_side_candidate(
    game: dict,
    side_team: str,
    opponent_team: str,
    side_label: str,
    team_snap: dict,
    opp_snap: dict,
    own_pitcher: dict,
    opp_pitcher: dict,
    own_bullpen: dict,
    opp_bullpen: dict,
    lefty_leverage: dict | None = None,
    min_score: int = 6,
) -> dict | None:
    components = best_bet_rule_components(team_snap, opp_snap, own_pitcher, opp_pitcher, own_bullpen, opp_bullpen)
    score = sum(1 for passed in components.values() if passed)
    if score < min_score:
        return None

    team_l7_ops = safe_float(team_snap.get("last7_ops"))
    team_l7_obp = safe_float(team_snap.get("last7_obp"))
    opp_l7_ops = safe_float(opp_snap.get("last7_ops"))
    own_bp_era = safe_float(own_bullpen.get("era"))
    opp_bp_era = safe_float(opp_bullpen.get("era"))
    lefty_score = safe_float((lefty_leverage or {}).get("score"))
    lefty_boost = min(lefty_score, 10) * 0.65 if (lefty_leverage or {}).get("active") and pd.notna(lefty_score) else 0.0
    edge_score = (
        score * 10
        + (team_l7_ops if pd.notna(team_l7_ops) else 0) * 8
        + (team_l7_obp if pd.notna(team_l7_obp) else 0) * 5
        - (opp_l7_ops if pd.notna(opp_l7_ops) else 0) * 4
        - (own_bp_era if pd.notna(own_bp_era) else 4.50) * 0.20
        + (opp_bp_era if pd.notna(opp_bp_era) else 4.50) * 0.18
        + lefty_boost
    )
    signal = "Suggested" if score == len(components) else "Watch"

    why_parts = []
    if components["OPS"] and components["OBP"]:
        why_parts.append("recent OPS and OBP both clear the strong line")
    if components["Own bullpen"]:
        why_parts.append("own bullpen is clean over the last 5")
    if components["Own starter"]:
        why_parts.append(f"{own_pitcher.get('name', 'starter')} is {pitcher_recent_label(own_pitcher)}")
    if components["Opp offense"]:
        why_parts.append(f"{opponent_team} offense is weak/cooling")
    if components["Opp starter"]:
        opp_truth = pitcher_truth_label(opp_pitcher) or pitcher_recent_label(opp_pitcher)
        why_parts.append(f"opposing starter is targetable ({opp_truth})")
    if components["Opp bullpen"]:
        why_parts.append(f"{opponent_team} bullpen is {_friendly_signal_label(opp_bullpen.get('label', 'risk')).lower()}")
    if (lefty_leverage or {}).get("active"):
        why_parts.append(f"lefty leverage: {(lefty_leverage or {}).get('label', 'active')}")
    why = "; ".join(why_parts[:5]) + "." if why_parts else "Only a few required edges matched."
    failed_details = best_bet_failure_details(components, team_snap, opp_snap, own_pitcher, opp_pitcher, own_bullpen, opp_bullpen)

    return {
        "game_id": game.get("game_id"),
        "game": game_display_label(game),
        "side": side_team,
        "opponent": opponent_team,
        "side_label": side_label,
        "signal": signal,
        "score": score,
        "max_score": len(components),
        "edge_score": edge_score,
        "components": components,
        "failed": [label for label, passed in components.items() if not passed],
        "failed_details": failed_details,
        "metrics": [
            ("Recent OPS", f"L7 {format_stat(team_snap.get('last7_ops'), 3)} | L3 {format_stat(team_snap.get('last3_ops'), 3)}"),
            ("Recent OBP", f"L7 {format_stat(team_snap.get('last7_obp'), 3)} | L3 {format_stat(team_snap.get('last3_obp'), 3)}"),
            ("Own SP", f"{own_pitcher.get('name', 'TBD')} | {pitcher_recent_label(own_pitcher)}"),
            ("Own BP", f"{_friendly_signal_label(own_bullpen.get('label', 'n/a'))} | {format_stat(own_bullpen.get('era'), 2)} ERA"),
            ("Opp offense", f"{_friendly_signal_label(opp_snap.get('offense_signal', 'n/a'))} | L7 OPS {format_stat(opp_snap.get('last7_ops'), 3)}"),
            ("Opp SP", f"{opp_pitcher.get('name', 'TBD')} | {pitcher_truth_label(opp_pitcher) or pitcher_recent_label(opp_pitcher)}"),
            ("Opp BP", f"{_friendly_signal_label(opp_bullpen.get('label', 'n/a'))} | {format_stat(opp_bullpen.get('era'), 2)} ERA"),
            ("Lefty leverage", f"{(lefty_leverage or {}).get('label', 'n/a')} | score {safe_int((lefty_leverage or {}).get('score'))}"),
        ],
        "lefty_leverage": lefty_leverage or {},
        "why": why,
    }

def build_best_bet_shortlist(games: list[dict], team_logs: pd.DataFrame, selected_date: Any, season: int) -> dict[str, list[dict]]:
    rows = []
    for game in games:
        status = str(game.get("status", "")).lower()
        if "final" in status or "completed" in status:
            continue

        away_team = game.get("away_team_name", "")
        home_team = game.get("home_team_name", "")
        away_snapshot = team_snapshot(team_logs, away_team)
        home_snapshot = team_snapshot(team_logs, home_team)

        away_pitcher = build_pitcher_card(game.get("away_pitcher_id"), game.get("away_pitcher_name"), season)
        home_pitcher = build_pitcher_card(game.get("home_pitcher_id"), game.get("home_pitcher_name"), season)
        away_pitcher["era_truth"] = pitcher_era_truth_signal(away_pitcher)
        home_pitcher["era_truth"] = pitcher_era_truth_signal(home_pitcher)

        away_bullpen = build_bullpen_card(team_logs, away_team, selected_date, 5)
        home_bullpen = build_bullpen_card(team_logs, home_team, selected_date, 5)
        away_lefty_leverage = build_lefty_leverage_profile(away_snapshot, game.get("away_team_id"), home_pitcher, season)
        home_lefty_leverage = build_lefty_leverage_profile(home_snapshot, game.get("home_team_id"), away_pitcher, season)

        away_candidate = best_bet_side_candidate(
            game,
            away_team,
            home_team,
            "Away",
            away_snapshot,
            home_snapshot,
            away_pitcher,
            home_pitcher,
            away_bullpen,
            home_bullpen,
            away_lefty_leverage,
            min_score=0,
        )
        home_candidate = best_bet_side_candidate(
            game,
            home_team,
            away_team,
            "Home",
            home_snapshot,
            away_snapshot,
            home_pitcher,
            away_pitcher,
            home_bullpen,
            away_bullpen,
            home_lefty_leverage,
            min_score=0,
        )
        rows.extend([row for row in [away_candidate, home_candidate] if row])

    sorted_rows = sorted(rows, key=lambda row: (row.get("score", 0), row.get("edge_score", 0)), reverse=True)
    shortlist = [
        {**row, "signal": "Suggested" if row.get("score") == row.get("max_score") else "Watch"}
        for row in sorted_rows
        if row.get("score", 0) >= 6
    ][:10]
    near_misses = [row for row in sorted_rows if row.get("score", 0) < 6][:6]
    return {"shortlist": shortlist, "near_misses": near_misses}

def render_best_bet_near_misses(rows: list[dict]) -> str:
    if not rows:
        return ""
    table_rows = []
    for row in rows:
        failed = ", ".join(row.get("failed", [])) or "n/a"
        details = "<br>".join(html.escape(detail) for detail in row.get("failed_details", [])) or "No failed-rule details."
        table_rows.append(
            textwrap.dedent(
                f"""
                <tr>
                  <td><strong>{html.escape(str(row.get("side", "")))}</strong><br><span class="best-bet-table__muted">{html.escape(str(row.get("game", "")))}</span></td>
                  <td>{safe_int(row.get("score"))}/{safe_int(row.get("max_score"))}</td>
                  <td>{html.escape(failed)}</td>
                  <td>{details}</td>
                </tr>
                """
            ).strip()
        )
    return textwrap.dedent(
        f"""
        <div class="best-bet-near">
          <div class="best-bet-near__title">Near misses</div>
          <div class="best-bet-near__sub">Closest sides below the system line. Use this to see if the rules are too strict or correctly filtering weak reads.</div>
          <table class="best-bet-table">
            <thead>
              <tr>
                <th style="width:22%;">Side</th>
                <th style="width:9%;">Score</th>
                <th style="width:20%;">Failed</th>
                <th>Why it failed</th>
              </tr>
            </thead>
            <tbody>{"".join(table_rows)}</tbody>
          </table>
        </div>
        """
    ).strip()

def render_best_bet_shortlist(scan: dict[str, list[dict]] | list[dict]) -> str:
    if isinstance(scan, list):
        rows = scan
        near_misses = []
    else:
        rows = scan.get("shortlist", [])
        near_misses = scan.get("near_misses", [])

    if not rows:
        near_html = render_best_bet_near_misses(near_misses)
        return textwrap.dedent(
            f"""
            <div class="best-bet-empty">
              No full-rule matches right now. That is useful too: the app is waiting for offense, starter form, and bullpen edges to line up instead of forcing a play.
            </div>
            {near_html}
            """
        ).strip()

    cards = []
    for row in rows:
        card_class = "best-bet-card best-bet-card--suggested" if row.get("signal") == "Suggested" else "best-bet-card"
        chips = "".join(
            f'<span class="best-bet-chip {"best-bet-chip--on" if passed else "best-bet-chip--off"}">{html.escape(label)}</span>'
            for label, passed in (row.get("components") or {}).items()
        )
        metrics = "".join(best_bet_metric_summary(label, value) for label, value in row.get("metrics", []))
        signal_text = "Suggested side" if row.get("signal") == "Suggested" else "Watchlist"
        cards.append(
            textwrap.dedent(
                f"""
                <div class="{card_class}">
                  <div class="best-bet-top">
                    <div>
                      <div class="best-bet-kicker">{html.escape(signal_text)}</div>
                      <div class="best-bet-team">{html.escape(str(row.get("side", "")))}</div>
                      <div class="best-bet-game">{html.escape(str(row.get("game", "")))}</div>
                    </div>
                    <div class="best-bet-score">{safe_int(row.get("score"))}/{safe_int(row.get("max_score"))}</div>
                  </div>
                  <div class="best-bet-metrics">{metrics}</div>
                  <div class="best-bet-checks">{chips}</div>
                  <div class="best-bet-why">{html.escape(str(row.get("why", "")))}</div>
                </div>
                """
            ).strip()
        )
    return f'<div class="best-bet-grid">{"".join(cards)}</div>{render_best_bet_near_misses(near_misses)}'

def pitcher_quality_start_rate(pitcher: dict) -> float:
    starts = safe_int((pitcher or {}).get("starts"))
    if not starts:
        return float("nan")
    return safe_int((pitcher or {}).get("quality_starts")) / starts

def pitcher_ranking_score(pitcher: dict) -> tuple[float, list[str]]:
    if not pitcher or not pitcher.get("id"):
        return float("-inf"), ["No probable starter data."]

    era = safe_float(pitcher.get("era"))
    whip = safe_float(pitcher.get("whip"))
    h9 = safe_float(pitcher.get("h9"))
    bb9 = safe_float(pitcher.get("bb9"))
    k9 = safe_float(pitcher.get("k9"))
    hr9 = safe_float(pitcher.get("hr9"))
    last3_era = safe_float(pitcher.get("last3_era"))
    last3_whip = safe_float(pitcher.get("last3_whip"))
    qs_rate = pitcher_quality_start_rate(pitcher)
    leash = (pitcher.get("pitch_leash") or {})
    six_ip_rate = safe_float(leash.get("season_6ip_rate"))
    truth_label = pitcher_truth_label(pitcher)
    recent_label = pitcher_recent_label(pitcher)
    leash_label = str(leash.get("label") or "")

    score = 0.0
    reasons = []

    if pd.notna(era):
        if era <= 3.25:
            score += 2
            reasons.append("strong season ERA")
        elif era <= 4.00:
            score += 1
            reasons.append("solid season ERA")
        elif era >= 5.00:
            score -= 2
            reasons.append("high season ERA")
        elif era >= 4.50:
            score -= 1
            reasons.append("below-average season ERA")

    if pd.notna(whip):
        if whip <= 1.15:
            score += 2
            reasons.append("clean WHIP")
        elif whip <= 1.25:
            score += 1
            reasons.append("solid WHIP")
        elif whip >= 1.45:
            score -= 2
            reasons.append("heavy traffic WHIP")
        elif whip >= 1.35:
            score -= 1
            reasons.append("traffic WHIP")

    if pd.notna(h9):
        if h9 <= 7.5:
            score += 1
            reasons.append("limits hits")
        elif h9 >= 10.0:
            score -= 2
            reasons.append("heavy contact")
        elif h9 >= 9.0:
            score -= 1
            reasons.append("contact risk")

    if pd.notna(bb9):
        if bb9 <= 2.25:
            score += 1
            reasons.append("good control")
        elif bb9 >= 4.25:
            score -= 2
            reasons.append("serious walk risk")
        elif bb9 >= 3.35:
            score -= 1
            reasons.append("walk risk")

    if pd.notna(k9):
        if k9 >= 9.5:
            score += 1
            reasons.append("strikeout buffer")
        elif k9 < 6.5:
            score -= 1
            reasons.append("low K buffer")

    if pd.notna(hr9):
        if hr9 <= 0.85:
            score += 1
            reasons.append("keeps ball in park")
        elif hr9 >= 1.45:
            score -= 2
            reasons.append("HR damage")
        elif hr9 >= 1.20:
            score -= 1
            reasons.append("HR risk")

    if recent_label == "better than season":
        score += 2
        reasons.append("recent form better than season")
    elif recent_label == "near season":
        score += 0.5
        reasons.append("recent form near season")
    elif recent_label == "worse than season":
        score -= 2
        reasons.append("recent form worse than season")

    if pd.notna(last3_era):
        if last3_era <= 3.25:
            score += 1
            reasons.append("clean L3 ERA")
        elif last3_era >= 5.50:
            score -= 1
            reasons.append("rough L3 ERA")
    if pd.notna(last3_whip):
        if last3_whip <= 1.15:
            score += 1
            reasons.append("clean L3 WHIP")
        elif last3_whip >= 1.45:
            score -= 2
            reasons.append("L3 traffic")

    if pd.notna(qs_rate):
        if qs_rate >= 0.65:
            score += 2
            reasons.append("strong QS rate")
        elif qs_rate >= 0.50:
            score += 1
            reasons.append("average QS rate")
        elif qs_rate < 0.35:
            score -= 1
            reasons.append("low QS rate")

    if pd.notna(six_ip_rate):
        if six_ip_rate >= 0.65:
            score += 1
            reasons.append("works deep")
        elif six_ip_rate < 0.35:
            score -= 1
            reasons.append("rarely reaches 6 IP")

    if truth_label in {"true strong", "unlucky ERA"}:
        score += 2
        reasons.append(truth_label)
    elif truth_label == "stable":
        score += 0.5
        reasons.append("ERA indicators stable")
    elif truth_label == "watch traffic":
        score -= 1
        reasons.append("ERA truth traffic watch")
    elif truth_label in {"danger spot", "lucky ERA", "regression risk"}:
        score -= 3
        reasons.append(f"ERA truth {truth_label}")

    if leash_label == "deep leash":
        score += 1
        reasons.append("deep leash")
    elif leash_label == "short leash":
        score -= 2
        reasons.append("short leash")
    elif leash_label in {"traffic hook risk", "watch leash"}:
        score -= 1
        reasons.append(leash_label)

    return score, reasons[:5]

def pitcher_ranking_grade(score: float) -> str:
    if score == float("-inf") or pd.isna(score):
        return "TBD"
    if score >= 10:
        return "Elite"
    if score >= 7:
        return "Strong"
    if score >= 4:
        return "Stable"
    if score >= 1:
        return "Average"
    if score >= -2:
        return "Targetable"
    return "High risk"

def pitcher_ranking_rows(games: list[dict], season: int) -> list[dict]:
    rows = []
    for game in games:
        matchup = game_display_label(game)
        game_status = str(game.get("status") or "")
        for side_key, side_label, opp_key in [("away", "Away", "home"), ("home", "Home", "away")]:
            team = game.get(f"{side_key}_team_name", "")
            opponent = game.get(f"{opp_key}_team_name", "")
            pitcher = build_pitcher_card(game.get(f"{side_key}_pitcher_id"), game.get(f"{side_key}_pitcher_name"), season)
            pitcher["era_truth"] = pitcher_era_truth_signal(pitcher)
            score, reasons = pitcher_ranking_score(pitcher)
            leash = pitcher.get("pitch_leash", {}) or {}
            rows.append(
                {
                    "Game ID": game.get("game_id"),
                    "Game": matchup,
                    "Status": game_status,
                    "Team": team,
                    "Opponent": opponent,
                    "Side": side_label,
                    "Pitcher": pitcher.get("name", "TBD"),
                    "Hand": pitcher.get("pitch_hand") or "",
                    "Grade": pitcher_ranking_grade(score),
                    "Score": score if score != float("-inf") else float("nan"),
                    "ERA": safe_float(pitcher.get("era")),
                    "WHIP": safe_float(pitcher.get("whip")),
                    "L3 ERA": safe_float(pitcher.get("last3_era")),
                    "L3 WHIP": safe_float(pitcher.get("last3_whip")),
                    "K/9": safe_float(pitcher.get("k9")),
                    "BB/9": safe_float(pitcher.get("bb9")),
                    "HR/9": safe_float(pitcher.get("hr9")),
                    "QS": pitcher.get("quality_start_label", "n/a"),
                    "QS%": pitcher_quality_start_rate(pitcher),
                    "6IP%": safe_float(leash.get("season_6ip_rate")),
                    "Leash": leash.get("label", "n/a"),
                    "Recent": pitcher_recent_label(pitcher),
                    "ERA Truth": pitcher_truth_label(pitcher) or "n/a",
                    "Why": "; ".join(reasons) if reasons else "No ranking details available.",
                    "_pitcher": pitcher,
                }
            )
    return rows

def pitchers_ranking_df(games: list[dict], season: int) -> pd.DataFrame:
    rows = pitcher_ranking_rows(games, season)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def sort_pitchers_ranking(df: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    if df.empty:
        return df
    if sort_mode == "Most Targetable":
        return df.sort_values(["Score", "WHIP", "ERA"], ascending=[True, False, False], na_position="last")
    if sort_mode == "Best Recent":
        return df.sort_values(["L3 ERA", "L3 WHIP", "Score"], ascending=[True, True, False], na_position="last")
    if sort_mode == "Deepest Leash":
        return df.sort_values(["6IP%", "Score"], ascending=[False, False], na_position="last")
    if sort_mode == "Worst Traffic":
        return df.sort_values(["WHIP", "BB/9", "L3 WHIP"], ascending=[False, False, False], na_position="last")
    return df.sort_values(["Score", "ERA", "WHIP"], ascending=[False, True, True], na_position="last")

def pitcher_ranking_display_df(df: pd.DataFrame) -> pd.DataFrame:
    display = df.drop(columns=[col for col in ["_pitcher"] if col in df.columns]).copy()
    for pct_col in ["QS%", "6IP%"]:
        if pct_col in display.columns:
            display[pct_col] = pd.to_numeric(display[pct_col], errors="coerce") * 100
    cols = [
        "Grade",
        "Score",
        "Pitcher",
        "Hand",
        "Team",
        "Opponent",
        "ERA",
        "WHIP",
        "L3 ERA",
        "L3 WHIP",
        "K/9",
        "BB/9",
        "HR/9",
        "QS",
        "QS%",
        "6IP%",
        "Leash",
        "Recent",
        "ERA Truth",
        "Why",
    ]
    return display[[col for col in cols if col in display.columns]]

def render_pitchers_page(games: list[dict], season: int, show_detail_cards: bool) -> None:
    render_section_intro(
        "Starting pitcher rankings",
        "Probable starters for the selected date, ranked by season quality, recent form, traffic, ERA truth, quality starts, and leash.",
    )

    if not games:
        st.warning("No MLB games found for that date.")
        return

    with st.spinner("Ranking probable starters..."):
        ranking = pitchers_ranking_df(games, season)

    if ranking.empty:
        st.warning("No probable starters found for this date.")
        return

    c1, c2, c3 = st.columns([1.1, 1.1, 1.6])
    with c1:
        sort_mode = st.selectbox("Sort", ["Best First", "Most Targetable", "Best Recent", "Deepest Leash", "Worst Traffic"], index=0)
    with c2:
        grade_options = ["Elite", "Strong", "Stable", "Average", "Targetable", "High risk", "TBD"]
        present_grades = [grade for grade in grade_options if grade in set(ranking["Grade"].dropna())]
        grade_filter = st.multiselect("Grade", present_grades, default=present_grades)
    with c3:
        team_filter = st.multiselect("Teams", sorted(ranking["Team"].dropna().unique()), default=[])

    display = sort_pitchers_ranking(ranking, sort_mode)
    if grade_filter:
        display = display[display["Grade"].isin(grade_filter)]
    if team_filter:
        display = display[display["Team"].isin(team_filter)]

    strong_count = int(ranking["Grade"].isin(["Elite", "Strong"]).sum())
    targetable_count = int(ranking["Grade"].isin(["Targetable", "High risk"]).sum())
    best_row = ranking.sort_values("Score", ascending=False, na_position="last").head(1)
    risk_row = ranking.sort_values("Score", ascending=True, na_position="last").head(1)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Elite / strong", strong_count)
    k2.metric("Targetable / risk", targetable_count)
    k3.metric("Top starter", best_row.iloc[0]["Pitcher"] if not best_row.empty else "n/a")
    k4.metric("Biggest risk", risk_row.iloc[0]["Pitcher"] if not risk_row.empty else "n/a")

    st.dataframe(
        pitcher_ranking_display_df(display),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "ERA": st.column_config.NumberColumn("ERA", format="%.2f"),
            "WHIP": st.column_config.NumberColumn("WHIP", format="%.3f"),
            "L3 ERA": st.column_config.NumberColumn("L3 ERA", format="%.2f"),
            "L3 WHIP": st.column_config.NumberColumn("L3 WHIP", format="%.3f"),
            "K/9": st.column_config.NumberColumn("K/9", format="%.2f"),
            "BB/9": st.column_config.NumberColumn("BB/9", format="%.2f"),
            "HR/9": st.column_config.NumberColumn("HR/9", format="%.2f"),
            "QS%": st.column_config.NumberColumn("QS%", format="%.0f%%"),
            "6IP%": st.column_config.NumberColumn("6IP%", format="%.0f%%"),
        },
    )

    if not show_detail_cards:
        return

    default_pitchers = display["Pitcher"].head(2).tolist()
    selected_pitchers = st.multiselect(
        "Pitcher detail cards",
        display["Pitcher"].tolist(),
        default=default_pitchers,
    )
    if not selected_pitchers:
        return

    detail_rows = display[display["Pitcher"].isin(selected_pitchers)].to_dict("records")
    detail_cols = st.columns(2)
    for idx, row in enumerate(detail_rows):
        pitcher = row.get("_pitcher", {}) or {}
        with detail_cols[idx % 2]:
            st.markdown(render_pitcher_html_card(pitcher), unsafe_allow_html=True)

def hitter_window_stat(row: dict, window: str, stat: str) -> float:
    profile = row.get("Hit Consistency", {}) or {}
    windows = profile.get("windows", {}) or {}
    return safe_float((windows.get(window, {}) or {}).get(stat))

def hitter_recent_ops(row: dict) -> float:
    window_ops = hitter_window_stat(row, "last7", "ops")
    if pd.notna(window_ops):
        return window_ops
    return safe_float(row.get("Last7 OPS"))

def hitter_hot_score(row: dict) -> tuple[float, list[str]]:
    season_ops = safe_float(row.get("OPS"))
    last7_ops = hitter_recent_ops(row)
    obp = safe_float(row.get("OBP"))
    avg = safe_float(row.get("AVG"))
    last7_avg = hitter_window_stat(row, "last7", "avg")
    profile = row.get("Hit Consistency", {}) or {}
    consistency = str(profile.get("label") or "n/a")
    season_tier = str(row.get("Season Tier") or "")

    score = 0.0
    reasons = []

    if pd.notna(last7_ops):
        if last7_ops >= 1.000:
            score += 4
            reasons.append("elite L7 OPS")
        elif last7_ops >= 0.900:
            score += 3
            reasons.append("great L7 OPS")
        elif last7_ops >= 0.800:
            score += 2
            reasons.append("L7 OPS over .800")
        elif last7_ops >= 0.740:
            score += 1
            reasons.append("solid L7 OPS")
        elif last7_ops < 0.650:
            score -= 2
            reasons.append("weak L7 OPS")

    if pd.notna(season_ops):
        if season_ops >= 0.800:
            score += 1.25
            reasons.append("great season OPS")
        elif season_ops >= 0.700:
            score += 0.25
            reasons.append("average season OPS")
        else:
            score -= 0.75
            reasons.append("weak season OPS")

    if pd.notna(season_ops) and pd.notna(last7_ops):
        delta = last7_ops - season_ops
        if last7_ops >= 0.800 and delta >= 0.100:
            score += 2
            reasons.append("L7 OPS well above season")
        elif last7_ops >= 0.800 and delta >= 0.040:
            score += 1
            reasons.append("L7 OPS above season")
        elif delta <= -0.100:
            score -= 2
            reasons.append("L7 OPS well below baseline")
        elif delta <= -0.050:
            score -= 1
            reasons.append("L7 OPS below baseline")
        if season_ops < 0.700 and last7_ops < 0.800:
            score -= 1.5
            reasons.append("weak season bat needs .800+ L7")

    if pd.notna(obp):
        if obp >= 0.390:
            score += 2
            reasons.append("elite OBP")
        elif obp >= 0.350:
            score += 1
            reasons.append("strong OBP")
        elif obp >= 0.330:
            score += 0.5
            reasons.append("useful OBP")
        elif obp < 0.300:
            score -= 1
            reasons.append("low OBP")

    if pd.notna(avg):
        if avg >= 0.310:
            score += 1.5
            reasons.append("high season AVG")
        elif avg >= 0.280:
            score += 0.75
            reasons.append("solid season AVG")
        elif avg < 0.230:
            score -= 1
            reasons.append("low season AVG")

    if pd.notna(last7_avg):
        if last7_avg >= 0.320:
            score += 1
            reasons.append("L7 hit rate hot")
        elif last7_avg >= 0.280:
            score += 0.5
            reasons.append("L7 hit rate solid")
        elif last7_avg <= 0.200:
            score -= 1
            reasons.append("L7 hit rate cold")

    consistency_weights = {
        "Stable high": 2.5,
        "Heating": 2.0,
        "Stable": 1.0,
        "Neutral": 0.0,
        "Small sample": -0.5,
        "Volatile": -1.0,
        "Cooling from heater": -1.5,
        "Cooling": -2.0,
        "Cold": -2.5,
    }
    consistency_weight = consistency_weights.get(consistency, 0.0)
    score += consistency_weight
    if consistency_weight > 0:
        reasons.append(consistency.lower())
    elif consistency_weight < 0:
        reasons.append(consistency.lower())

    if season_tier == "hot":
        score += 0.5

    return score, reasons[:6]

def hitter_hot_grade(score: float) -> str:
    if pd.isna(score):
        return "TBD"
    if score >= 10:
        return "Blazing"
    if score >= 7:
        return "Hot"
    if score >= 4:
        return "Warm"
    if score >= 1:
        return "Average"
    if score >= -1:
        return "Watch"
    return "Cold"

def hitter_hot_grade_tone(grade: str) -> tuple[str, str, str]:
    tones = {
        "Blazing": ("#064e3b", "#a7f3d0", "rgba(16, 185, 129, 0.45)"),
        "Hot": ("#123c3a", "#99f6e4", "rgba(45, 212, 191, 0.42)"),
        "Warm": ("#3b2f0b", "#fde68a", "rgba(245, 158, 11, 0.40)"),
        "Average": ("#172033", "#cbd5e1", "rgba(148, 163, 184, 0.32)"),
        "Watch": ("#3b2414", "#fed7aa", "rgba(251, 146, 60, 0.38)"),
        "Cold": ("#3f1418", "#fecaca", "rgba(248, 113, 113, 0.40)"),
        "TBD": ("#172033", "#cbd5e1", "rgba(148, 163, 184, 0.32)"),
    }
    return tones.get(grade, tones["TBD"])

def hitter_risk_rank(label: str) -> int:
    return {
        "Cold": 4,
        "Cooling": 3,
        "Cooling from heater": 3,
        "Volatile": 2,
        "Small sample": 1,
    }.get(str(label), 0)

def hitter_consistency_rank(label: str) -> int:
    return {
        "Stable high": 5,
        "Heating": 4,
        "Stable": 3,
        "Neutral": 2,
        "Small sample": 1,
        "Volatile": 0,
        "Cooling from heater": -1,
        "Cooling": -2,
        "Cold": -3,
    }.get(str(label), 0)

def hitter_ranking_rows(games: list[dict], season: int, as_of_date: Any | None, teams: list[str] | None = None) -> list[dict]:
    rows = []
    selected_teams = set(teams or [])
    for game in games:
        matchup = game_display_label(game)
        game_status = str(game.get("status") or "")
        for side_key, side_label, opp_key in [("away", "Away", "home"), ("home", "Home", "away")]:
            team = game.get(f"{side_key}_team_name", "")
            opponent = game.get(f"{opp_key}_team_name", "")
            if selected_teams and team not in selected_teams:
                continue
            lineup, is_posted = fetch_lineup_rows(safe_int(game.get("game_id")), side_key, season, as_of_date)
            source = "Posted lineup" if is_posted else "Fallback bats"
            for hitter in lineup:
                player = hitter.get("Player")
                if not player:
                    continue
                profile = hitter.get("Hit Consistency", {}) or {}
                windows = profile.get("windows", {}) or {}
                season_window = windows.get("season", {}) or {}
                last30_window = windows.get("last30", {}) or {}
                last15_window = windows.get("last15", {}) or {}
                last7_window = windows.get("last7", {}) or {}
                score, reasons = hitter_hot_score(hitter)
                consistency = str(profile.get("label") or "n/a")
                rows.append(
                    {
                        "Game ID": game.get("game_id"),
                        "Game": matchup,
                        "Status": game_status,
                        "Team": team,
                        "Opponent": opponent,
                        "Side": side_label,
                        "Source": source,
                        "Player": player,
                        "Spot": hitter.get("Spot"),
                        "Pos": hitter.get("Pos"),
                        "Bats": hitter.get("Bats"),
                        "Grade": hitter_hot_grade(score),
                        "Score": score,
                        "AVG": safe_float(hitter.get("AVG")),
                        "OBP": safe_float(hitter.get("OBP")),
                        "OPS": safe_float(hitter.get("OPS")),
                        "L7 OPS": hitter_recent_ops(hitter),
                        "L7 AVG": safe_float(last7_window.get("avg")),
                        "15D AVG": safe_float(last15_window.get("avg")),
                        "30D AVG": safe_float(last30_window.get("avg")),
                        "Season AVG": safe_float(season_window.get("avg")),
                        "L7 G": safe_int(last7_window.get("games")),
                        "L7 AB": safe_int(last7_window.get("ab")),
                        "Consistency": consistency,
                        "Consistency Note": str(profile.get("note") or ""),
                        "Why": "; ".join(reasons) if reasons else "No hitter hotness signal available.",
                        "_risk_rank": hitter_risk_rank(consistency),
                        "_consistency_rank": hitter_consistency_rank(consistency),
                    }
                )
    return rows

def hitters_ranking_df(games: list[dict], season: int, as_of_date: Any | None, teams: list[str] | None = None) -> pd.DataFrame:
    rows = hitter_ranking_rows(games, season, as_of_date, teams)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def sort_hitters_ranking(df: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    if df.empty:
        return df
    if sort_mode == "Best L7 OPS":
        return df.sort_values(["L7 OPS", "Score", "OBP"], ascending=[False, False, False], na_position="last")
    if sort_mode == "Best OBP":
        return df.sort_values(["OBP", "Score", "L7 OPS"], ascending=[False, False, False], na_position="last")
    if sort_mode == "Stable Hit Profile":
        return df.sort_values(["_consistency_rank", "Score", "L7 OPS"], ascending=[False, False, False], na_position="last")
    if sort_mode == "Cooling Risks":
        return df.sort_values(["_risk_rank", "Score"], ascending=[False, True], na_position="last")
    return df.sort_values(["Score", "L7 OPS", "OBP"], ascending=[False, False, False], na_position="last")

def hitter_ranking_display_df(df: pd.DataFrame) -> pd.DataFrame:
    display = df.drop(columns=[col for col in ["_risk_rank", "_consistency_rank"] if col in df.columns]).copy()
    cols = [
        "Grade",
        "Score",
        "Player",
        "Team",
        "Opponent",
        "Side",
        "Source",
        "Spot",
        "Pos",
        "Bats",
        "AVG",
        "OBP",
        "OPS",
        "L7 OPS",
        "L7 AVG",
        "15D AVG",
        "30D AVG",
        "Consistency",
        "L7 G",
        "L7 AB",
        "Why",
    ]
    return display[[col for col in cols if col in display.columns]]

def render_hot_hitter_card(row: dict) -> str:
    grade = str(row.get("Grade") or "TBD")
    badge_bg, badge_color, border_color = hitter_hot_grade_tone(grade)
    team = str(row.get("Team") or "Team")
    team_color = TEAM_COLORS.get(team, "#2dd4bf")
    score = safe_float(row.get("Score"))
    score_width = 0 if pd.isna(score) else max(4, min(100, (score + 3) / 15 * 100))
    metrics = [
        ("Season OPS", format_lineup_cell(row.get("OPS"), 3)),
        ("L7 OPS", format_lineup_cell(row.get("L7 OPS"), 3)),
        ("OBP", format_lineup_cell(row.get("OBP"), 3)),
        ("L7 AVG", format_lineup_cell(row.get("L7 AVG"), 3)),
    ]
    metric_html = "".join(
        f'<div style="background:#172033; border:1px solid #26364a; border-radius:8px; padding:0.45rem 0.5rem;">'
        f'<div style="color:#94a3b8; font-size:0.68rem; font-weight:850; text-transform:uppercase; letter-spacing:0.06em;">{html.escape(label)}</div>'
        f'<div style="color:#f8fafc; font-size:1.02rem; font-weight:900; font-variant-numeric:tabular-nums;">{html.escape(value)}</div>'
        f'</div>'
        for label, value in metrics
    )
    return compact_html(f"""
    <div class="best-bet-card" style="border-color:{border_color};">
      <div class="best-bet-top">
        <div>
          <div class="best-bet-kicker">{html.escape(team)} vs {html.escape(str(row.get("Opponent") or ""))}</div>
          <div class="best-bet-team" style="display:flex; align-items:center; gap:0.48rem;">
            <span style="display:inline-flex; align-items:center; justify-content:center; width:2.15rem; height:2.15rem; border-radius:8px; background:{html.escape(team_color)}; color:#ffffff; font-size:0.78rem; font-weight:950;">{html.escape(team_abbreviation(team))}</span>
            <span>{html.escape(str(row.get("Player") or ""))}</span>
          </div>
          <div class="best-bet-game">{html.escape(str(row.get("Game") or ""))} | {html.escape(str(row.get("Source") or ""))}</div>
        </div>
        <div class="best-bet-score" style="background:{badge_bg}; color:{badge_color}; border-color:{border_color};">{html.escape(grade)} {format_lineup_cell(score, 1)}</div>
      </div>
      <div style="height:0.45rem; border-radius:999px; background:#0b1220; border:1px solid #26364a; overflow:hidden; margin-bottom:0.72rem;">
        <div style="width:{score_width:.1f}%; height:100%; background:linear-gradient(90deg, #38bdf8, #2dd4bf);"></div>
      </div>
      <div class="best-bet-metrics">{metric_html}</div>
      <div class="best-bet-why"><strong>{html.escape(str(row.get("Consistency") or "n/a"))}</strong> | {html.escape(str(row.get("Why") or ""))}</div>
      <div class="best-bet-game" style="margin-top:0.35rem;">{html.escape(str(row.get("Consistency Note") or ""))}</div>
    </div>
    """)

def render_hot_hitter_cards(rows: list[dict]) -> str:
    if not rows:
        return ""
    return f'<div class="best-bet-grid">{"".join(render_hot_hitter_card(row) for row in rows)}</div>'

def render_hitters_page(games: list[dict], season: int, selected_date: Any, show_detail_cards: bool) -> None:
    render_section_intro(
        "Hottest hitters",
        "Hitters from the selected slate ranked by last 7 OPS, season baseline, on-base pressure, and batting-average consistency.",
    )

    if not games:
        st.warning("No MLB games found for that date.")
        return

    game_labels = [game_display_label(game) for game in games]
    games_by_label = {game_display_label(game): game for game in games}
    selected_game_labels = st.multiselect("Games to scan", game_labels, default=game_labels[:1])
    games_to_scan = [games_by_label[label] for label in selected_game_labels if label in games_by_label]
    if not games_to_scan:
        st.info("Choose at least one game to scan.")
        return

    slate_teams = sorted(
        {
            team
            for game in games_to_scan
            for team in [game.get("away_team_name"), game.get("home_team_name")]
            if team
        }
    )
    team_scan_filter = st.multiselect("Teams to scan", slate_teams, default=[])

    with st.spinner("Ranking hitters..."):
        ranking = hitters_ranking_df(games_to_scan, season, selected_date, team_scan_filter)

    if ranking.empty:
        st.warning("No hitter rows found for this date yet. Lineups may not be posted, and fallback batter data was unavailable.")
        return

    c1, c2, c3, c4 = st.columns([1.05, 1.1, 1.0, 1.0])
    with c1:
        sort_mode = st.selectbox("Sort", ["Hottest First", "Best L7 OPS", "Best OBP", "Stable Hit Profile", "Cooling Risks"], index=0)
    with c2:
        grade_options = ["Blazing", "Hot", "Warm", "Average", "Watch", "Cold", "TBD"]
        present_grades = [grade for grade in grade_options if grade in set(ranking["Grade"].dropna())]
        grade_filter = st.multiselect("Grade", present_grades, default=present_grades)
    with c3:
        min_l7_ops = st.slider("Min L7 OPS", min_value=0.500, max_value=1.250, value=0.650, step=0.010)
    with c4:
        source_options = sorted(ranking["Source"].dropna().unique())
        source_filter = st.multiselect("Source", source_options, default=source_options)

    display = sort_hitters_ranking(ranking, sort_mode)
    if grade_filter:
        display = display[display["Grade"].isin(grade_filter)]
    if source_filter:
        display = display[display["Source"].isin(source_filter)]
    display = display[pd.to_numeric(display["L7 OPS"], errors="coerce").fillna(0) >= min_l7_ops]

    hot_count = int(ranking["Grade"].isin(["Blazing", "Hot"]).sum())
    warm_count = int(ranking["Grade"].isin(["Blazing", "Hot", "Warm"]).sum())
    cooling_count = int(ranking["Consistency"].isin(["Cooling", "Cooling from heater", "Cold", "Volatile"]).sum())
    top_row = ranking.sort_values("Score", ascending=False, na_position="last").head(1)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Blazing / hot", hot_count)
    k2.metric("Warm or better", warm_count)
    k3.metric("Cooling risks", cooling_count)
    k4.metric("Top hitter", top_row.iloc[0]["Player"] if not top_row.empty else "n/a")

    st.dataframe(
        hitter_ranking_display_df(display),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "AVG": st.column_config.NumberColumn("AVG", format="%.3f"),
            "OBP": st.column_config.NumberColumn("OBP", format="%.3f"),
            "OPS": st.column_config.NumberColumn("OPS", format="%.3f"),
            "L7 OPS": st.column_config.NumberColumn("L7 OPS", format="%.3f"),
            "L7 AVG": st.column_config.NumberColumn("L7 AVG", format="%.3f"),
            "15D AVG": st.column_config.NumberColumn("15D AVG", format="%.3f"),
            "30D AVG": st.column_config.NumberColumn("30D AVG", format="%.3f"),
        },
    )

    if show_detail_cards and not display.empty:
        st.markdown(render_hot_hitter_cards(display.head(6).to_dict("records")), unsafe_allow_html=True)

def read_best_bet_tracker() -> pd.DataFrame:
    if not BEST_BET_TRACKER_PATH.exists():
        return pd.DataFrame(columns=BEST_BET_TRACKER_COLUMNS)
    df = pd.read_csv(BEST_BET_TRACKER_PATH)
    for col in BEST_BET_TRACKER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[BEST_BET_TRACKER_COLUMNS].copy()

def save_best_bet_tracker(df: pd.DataFrame) -> None:
    BEST_BET_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for col in BEST_BET_TRACKER_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out[BEST_BET_TRACKER_COLUMNS].to_csv(BEST_BET_TRACKER_PATH, index=False)

def _best_bet_tracker_key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("game_date") or ""),
        str(row.get("game_id") or ""),
        str(row.get("side") or ""),
    )

def serialize_best_bet_tracker_row(row: dict, selected_date: Any) -> dict:
    components = row.get("components") or {}
    passed_rules = [label for label, passed in components.items() if passed]
    failed_rules = row.get("failed") or [label for label, passed in components.items() if not passed]
    metrics = [f"{label}: {value}" for label, value in (row.get("metrics") or [])]
    return {
        "created_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "game_date": str(selected_date),
        "game_id": row.get("game_id"),
        "matchup": row.get("game"),
        "side": row.get("side"),
        "opponent": row.get("opponent"),
        "side_label": row.get("side_label"),
        "signal": row.get("signal"),
        "score": row.get("score"),
        "max_score": row.get("max_score"),
        "edge_score": row.get("edge_score"),
        "passed_rules": ", ".join(passed_rules),
        "failed_rules": ", ".join(failed_rules),
        "failed_details": " | ".join(str(item) for item in (row.get("failed_details") or [])),
        "metrics": " | ".join(metrics),
        "why": row.get("why"),
        "result": "pending",
        "away_score": "",
        "home_score": "",
        "winning_team": "",
        "grade_reason": "",
        "graded_at": "",
    }

def append_best_bet_suggestions(scan: dict[str, list[dict]] | list[dict], selected_date: Any) -> int:
    rows = scan if isinstance(scan, list) else (scan.get("shortlist", []) if isinstance(scan, dict) else [])
    if not rows:
        return 0
    existing = read_best_bet_tracker()
    existing_rows = existing.to_dict("records") if not existing.empty else []
    existing_by_key = {_best_bet_tracker_key(row): idx for idx, row in enumerate(existing_rows)}
    saved = 0

    for row in rows:
        tracker_row = serialize_best_bet_tracker_row(row, selected_date)
        key = _best_bet_tracker_key(tracker_row)
        if key in existing_by_key:
            idx = existing_by_key[key]
            created_at = existing_rows[idx].get("created_at") or tracker_row["created_at"]
            result = existing_rows[idx].get("result") or "pending"
            grade_fields = {
                "result": result,
                "away_score": existing_rows[idx].get("away_score", ""),
                "home_score": existing_rows[idx].get("home_score", ""),
                "winning_team": existing_rows[idx].get("winning_team", ""),
                "grade_reason": existing_rows[idx].get("grade_reason", ""),
                "graded_at": existing_rows[idx].get("graded_at", ""),
            }
            existing_rows[idx].update({**tracker_row, "created_at": created_at, **grade_fields})
        else:
            existing_by_key[key] = len(existing_rows)
            existing_rows.append(tracker_row)
            saved += 1

    save_best_bet_tracker(pd.DataFrame(existing_rows))
    return saved

def grade_best_bet_row(row: dict) -> dict:
    updated = dict(row)
    game_id = safe_int(row.get("game_id"))
    if not game_id:
        updated["result"] = "pending"
        updated["grade_reason"] = "Missing MLB game id."
        return updated

    live = fetch_game_live_feed(game_id)
    status = str(nested_get(live, ["gameData", "status", "detailedState"], ""))
    if not _is_final_status(status):
        updated["result"] = "pending"
        updated["grade_reason"] = f"Game status: {status or 'not final yet'}."
        return updated

    away_team = str(nested_get(live, ["gameData", "teams", "away", "name"], ""))
    home_team = str(nested_get(live, ["gameData", "teams", "home", "name"], ""))
    away_score = safe_int(nested_get(live, ["liveData", "linescore", "teams", "away", "runs"], 0))
    home_score = safe_int(nested_get(live, ["liveData", "linescore", "teams", "home", "runs"], 0))
    side = str(row.get("side") or "")
    opponent = str(row.get("opponent") or "")

    if not side or side not in {away_team, home_team}:
        updated.update(
            {
                "result": "pending",
                "away_score": away_score,
                "home_score": home_score,
                "grade_reason": f"Final score found, but side '{side or 'n/a'}' did not match MLB team names.",
            }
        )
        return updated

    side_score = away_score if side == away_team else home_score
    opponent_score = home_score if side == away_team else away_score
    winning_team = away_team if away_score > home_score else home_team if home_score > away_score else ""
    if side_score == opponent_score:
        result = "push"
    else:
        result = "win" if side_score > opponent_score else "loss"
    updated.update(
        {
            "result": result,
            "away_score": away_score,
            "home_score": home_score,
            "winning_team": winning_team,
            "grade_reason": f"{side} {side_score}, {opponent or 'opponent'} {opponent_score}.",
            "graded_at": pd.Timestamp.now(tz="UTC").isoformat(),
        }
    )
    return updated

def grade_best_bet_tracker(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if df.empty:
        return df, 0
    rows = []
    changed = 0
    for row in df.to_dict("records"):
        previous_result = str(row.get("result") or "").lower()
        if previous_result in {"win", "loss", "push", "void"}:
            rows.append(row)
            continue
        updated = grade_best_bet_row(row)
        rows.append(updated)
        if str(updated.get("result") or "").lower() != previous_result:
            changed += 1
    return pd.DataFrame(rows), changed

def best_bet_tracker_summary(df: pd.DataFrame, signal: str | None = None) -> dict:
    if df.empty:
        return {"wins": 0, "losses": 0, "pushes": 0, "pending": 0, "win_rate": float("nan")}
    out = df.copy()
    if signal:
        out = out[out["signal"].fillna("").astype(str).str.lower() == signal.lower()]
    result = out["result"].fillna("").astype(str).str.lower() if "result" in out.columns else pd.Series(dtype=str)
    wins = int((result == "win").sum())
    losses = int((result == "loss").sum())
    pushes = int((result == "push").sum())
    pending = int((result == "pending").sum() + (result == "").sum())
    graded = wins + losses
    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "pending": pending,
        "win_rate": (wins / graded) if graded else float("nan"),
    }

def best_bet_tracker_display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "created_at" in out.columns:
        out["_created_sort"] = pd.to_datetime(out["created_at"], errors="coerce")
        out = out.sort_values("_created_sort", ascending=False).drop(columns=["_created_sort"])
    cols = [
        "game_date",
        "matchup",
        "side",
        "signal",
        "score",
        "passed_rules",
        "failed_rules",
        "result",
        "grade_reason",
        "why",
    ]
    out = out[[col for col in cols if col in out.columns]].head(40)
    return out.rename(
        columns={
            "game_date": "Date",
            "matchup": "Game",
            "side": "Side",
            "signal": "Signal",
            "score": "Score",
            "passed_rules": "Passed rules",
            "failed_rules": "Failed rules",
            "result": "Result",
            "grade_reason": "Result note",
            "why": "Why",
        }
    )

def read_pitcher_er_prop_snapshots() -> pd.DataFrame:
    if not PITCHER_ER_PROP_SNAPSHOT_PATH.exists():
        return pd.DataFrame(columns=PITCHER_ER_PROP_SNAPSHOT_COLUMNS)
    df = pd.read_csv(PITCHER_ER_PROP_SNAPSHOT_PATH)
    for col in PITCHER_ER_PROP_SNAPSHOT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    ordered_cols = PITCHER_ER_PROP_SNAPSHOT_COLUMNS + [col for col in df.columns if col not in PITCHER_ER_PROP_SNAPSHOT_COLUMNS]
    return df[ordered_cols]

def append_pitcher_er_prop_snapshots(rows: list[dict]) -> int:
    if not rows:
        return 0
    fetched_at = pd.Timestamp.now(tz="UTC").isoformat()
    out_rows = []
    for row in rows:
        out_rows.append({col: row.get(col, "") for col in PITCHER_ER_PROP_SNAPSHOT_COLUMNS} | {"fetched_at": fetched_at})
    df = pd.DataFrame(out_rows)
    PITCHER_ER_PROP_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = read_pitcher_er_prop_snapshots()
    combined = pd.concat([existing, df], ignore_index=True) if not existing.empty else df
    combined.to_csv(PITCHER_ER_PROP_SNAPSHOT_PATH, index=False)
    return len(df)

def add_pitcher_er_prop_movement(rows: list[dict], snapshots: pd.DataFrame) -> list[dict]:
    if not rows or snapshots.empty:
        return rows
    required_cols = {"event_id", "stat_entity_id", "side", "book", "line", "price", "fetched_at"}
    if not required_cols.issubset(set(snapshots.columns)):
        return rows
    snapshots = snapshots.copy()
    snapshots["fetched_at"] = pd.to_datetime(snapshots["fetched_at"], errors="coerce")
    output = []
    for row in rows:
        mask = (
            (snapshots.get("event_id").astype(str) == str(row.get("event_id")))
            & (snapshots.get("stat_entity_id").astype(str) == str(row.get("stat_entity_id")))
            & (snapshots.get("side").astype(str) == str(row.get("side")))
            & (snapshots.get("book").astype(str) == str(row.get("book")))
        )
        prior = snapshots[mask].sort_values("fetched_at").tail(1)
        movement = ""
        movement_dir = "neutral"
        if not prior.empty:
            prev = prior.iloc[0]
            current_line = safe_float(row.get("line"))
            prev_line = safe_float(prev.get("line"))
            if pd.notna(current_line) and pd.notna(prev_line) and current_line != prev_line:
                line_delta = current_line - prev_line
                movement = f"line {'up' if line_delta > 0 else 'down'} {abs(line_delta):.1f}"
                movement_dir = "up" if line_delta > 0 else "down"
            else:
                try:
                    price_delta = int(float(str(row.get("price")).replace("+", ""))) - int(float(str(prev.get("price")).replace("+", "")))
                    if price_delta > 0:
                        movement = f"price up {price_delta}"
                        movement_dir = "up"
                    elif price_delta < 0:
                        movement = f"price down {abs(price_delta)}"
                        movement_dir = "down"
                    else:
                        movement = "unchanged"
                        movement_dir = "neutral"
                except (TypeError, ValueError):
                    movement = ""
                    movement_dir = "neutral"
        output.append({**row, "movement": movement, "movement_dir": movement_dir})
    return output

def pitcher_context_split(pitcher: dict, context: str) -> dict:
    splits = (pitcher or {}).get("home_away", {}) or {}
    return splits.get(context, {}) or {}

def pitcher_er_context_score(pitcher: dict, side: str, context: str) -> tuple[int, list[str]]:
    split = pitcher_context_split(pitcher, context)
    era = safe_float(split.get("era"))
    whip = safe_float(split.get("whip"))
    if safe_int(split.get("games")) < 3:
        return 0, []
    if side == "over":
        if (pd.notna(era) and era >= 4.50) or (pd.notna(whip) and whip >= 1.35):
            return 1, [f"rough {context} split"]
        if pd.notna(era) and era <= 3.25 and pd.notna(whip) and whip <= 1.20:
            return -1, [f"strong {context} split"]
    elif side == "under":
        if pd.notna(era) and era <= 3.25 and pd.notna(whip) and whip <= 1.20:
            return 1, [f"strong {context} split"]
        if (pd.notna(era) and era >= 4.50) or (pd.notna(whip) and whip >= 1.35):
            return -1, [f"rough {context} split"]
    return 0, []

def score_pitcher_er_prop(
    row: dict,
    pitcher: dict,
    opponent_snapshot: dict,
    opponent_lineup: list[dict],
    weather_context: dict | None,
    pitcher_context: str,
) -> tuple[int, list[str]]:
    side = str(row.get("side", "")).lower()
    line = safe_float(row.get("line"))
    truth_label = pitcher_truth_label(pitcher)
    lineup_summary = summarize_lineup_strength(opponent_lineup)
    weather_score = safe_int((weather_context or {}).get("score"))
    score = 0
    reasons = []

    if side == "over":
        if truth_label in {"danger spot", "lucky ERA", "regression risk"}:
            score += 2
            reasons.append(f"starter {truth_label}")
        elif truth_label == "watch traffic":
            score += 1
            reasons.append("starter traffic")
        elif truth_label in {"true strong", "unlucky ERA"}:
            score -= 2
            reasons.append(f"starter {truth_label}")

        whip = safe_float(pitcher.get("whip"))
        if pd.notna(whip) and whip >= 1.45:
            score += 2
            reasons.append("season WHIP 1.45+")
        elif pd.notna(whip) and whip >= 1.30:
            score += 1
            reasons.append("season WHIP 1.30+")
        if pd.notna(safe_float(pitcher.get("h9"))) and safe_float(pitcher.get("h9")) >= 9.0:
            score += 1
            reasons.append("contact risk")
        if pd.notna(safe_float(pitcher.get("bb9"))) and safe_float(pitcher.get("bb9")) >= 3.5:
            score += 1
            reasons.append("walk risk")

        last3_era = safe_float(pitcher.get("last3_era"))
        last3_whip = safe_float(pitcher.get("last3_whip"))
        if pd.notna(last3_era) and last3_era >= 5.00:
            score += 2
            reasons.append("last 3 ERA trouble")
        elif pd.notna(last3_era) and last3_era >= 4.50:
            score += 1
            reasons.append("recent ERA leak")
        if pd.notna(last3_whip) and last3_whip >= 1.45:
            score += 2
            reasons.append("last 3 WHIP traffic")
        elif pd.notna(last3_whip) and last3_whip >= 1.35:
            score += 1
            reasons.append("recent WHIP traffic")

        ip_per_start = safe_float(pitcher.get("last3_ip_per_start"))
        if pd.notna(ip_per_start) and ip_per_start < 4.75 and pd.notna(line) and line >= 2.5:
            score -= 1
            reasons.append("short leash")

        offense_signal = (opponent_snapshot or {}).get("offense_signal")
        if offense_signal == "strong":
            score += 2
            reasons.append("opponent bats strong")
        elif offense_signal == "good":
            score += 1
            reasons.append("opponent bats good")
        elif offense_signal in {"weak", "cooling"}:
            score -= 1
            reasons.append("opponent offense drag")

        if lineup_summary["hot_count"] >= 3:
            score += 2
            reasons.append("3+ hot bats")
        elif lineup_summary["hot_count"] >= 2:
            score += 1
            reasons.append("2+ hot bats")
        if lineup_summary["l7_great_count"] >= 5:
            score += 1
            reasons.append("deep L7 OPS")
        if lineup_summary["weak_count"] >= 5:
            score -= 1
            reasons.append("thin lineup")
        if ((pitcher or {}).get("vs_roster", {}) or {}).get("alerts"):
            score += 1
            reasons.append("BvP alert")

        if weather_score >= 2:
            score += 2
            reasons.append("park/weather over")
        elif weather_score > 0:
            score += 1
            reasons.append("park/weather lift")
        elif weather_score < 0:
            score -= 1
            reasons.append("park/weather drag")

        split_score, split_reasons = pitcher_er_context_score(pitcher, side, pitcher_context)
        score += split_score
        reasons.extend(split_reasons)
        if pd.notna(line) and line <= 1.5:
            score += 1
            reasons.append("low ER line")
        elif pd.notna(line) and line >= 3.5:
            score -= 1
            reasons.append("high ER line")

    elif side == "under":
        if truth_label in {"true strong", "unlucky ERA"}:
            score += 2
            reasons.append(f"starter {truth_label}")
        elif truth_label == "stable":
            score += 1
            reasons.append("starter stable")
        elif truth_label in {"danger spot", "lucky ERA", "regression risk"}:
            score -= 2
            reasons.append(f"starter {truth_label}")
        elif truth_label == "watch traffic":
            score -= 1
            reasons.append("starter traffic")

        whip = safe_float(pitcher.get("whip"))
        if pd.notna(whip) and whip <= 1.10:
            score += 2
            reasons.append("elite WHIP")
        elif pd.notna(whip) and whip <= 1.20:
            score += 1
            reasons.append("low WHIP")
        if pd.notna(safe_float(pitcher.get("h9"))) and safe_float(pitcher.get("h9")) <= 7.5:
            score += 1
            reasons.append("limits hits")
        if pd.notna(safe_float(pitcher.get("bb9"))) and safe_float(pitcher.get("bb9")) <= 2.4:
            score += 1
            reasons.append("limits walks")

        last3_era = safe_float(pitcher.get("last3_era"))
        last3_whip = safe_float(pitcher.get("last3_whip"))
        if pd.notna(last3_era) and last3_era <= 2.50:
            score += 2
            reasons.append("last 3 run control")
        elif pd.notna(last3_era) and last3_era <= 3.25:
            score += 1
            reasons.append("recent ERA stable")
        if pd.notna(last3_whip) and last3_whip <= 1.05:
            score += 2
            reasons.append("last 3 low traffic")
        elif pd.notna(last3_whip) and last3_whip <= 1.20:
            score += 1
            reasons.append("recent WHIP stable")

        ip_per_start = safe_float(pitcher.get("last3_ip_per_start"))
        if pd.notna(ip_per_start) and ip_per_start >= 5.50:
            score += 1
            reasons.append("works deep")

        offense_signal = (opponent_snapshot or {}).get("offense_signal")
        if offense_signal in {"weak", "cooling"}:
            score += 1
            reasons.append("opponent offense drag")
        elif offense_signal == "strong":
            score -= 2
            reasons.append("opponent bats strong")
        elif offense_signal == "good":
            score -= 1
            reasons.append("opponent bats good")

        if lineup_summary["hot_count"] == 0:
            score += 1
            reasons.append("no hot bats")
        elif lineup_summary["hot_count"] >= 2:
            score -= 1
            reasons.append("hot bats threat")
        if ((pitcher or {}).get("vs_roster", {}) or {}).get("alerts"):
            score -= 1
            reasons.append("BvP alert")

        if weather_score <= -2:
            score += 2
            reasons.append("park/weather under")
        elif weather_score < 0:
            score += 1
            reasons.append("park/weather help")
        elif weather_score > 1:
            score -= 1
            reasons.append("park/weather lift")

        split_score, split_reasons = pitcher_er_context_score(pitcher, side, pitcher_context)
        score += split_score
        reasons.extend(split_reasons)
        if pd.notna(line) and line <= 1.5:
            score -= 1
            reasons.append("low ER line")
        elif pd.notna(line) and line >= 3.5:
            score += 1
            reasons.append("high ER line")
    else:
        reasons.append("unknown side")

    return score, reasons[:6]

def classify_pitcher_er_signal(score: int) -> str:
    if score >= 6:
        return "Playable"
    if score >= 3:
        return "Lean"
    if score >= 2:
        return "Watch"
    return "No bet"

def pitcher_er_playable_check(side: str, pitcher: dict, opponent_snapshot: dict, opponent_lineup: list[dict]) -> tuple[bool, str]:
    truth_label = pitcher_truth_label(pitcher)
    lineup_summary = summarize_lineup_strength(opponent_lineup)
    offense_signal = (opponent_snapshot or {}).get("offense_signal")
    alerts = bool(((pitcher or {}).get("vs_roster", {}) or {}).get("alerts"))
    if side == "over":
        if truth_label in {"true strong", "unlucky ERA"}:
            return False, "playable blocked: starter profile is too strong"
        if offense_signal in {"weak", "cooling"} and lineup_summary["hot_count"] < 2 and not alerts:
            return False, "playable blocked: opponent bats do not support over"
    elif side == "under":
        if truth_label in {"danger spot", "lucky ERA", "regression risk"}:
            return False, "playable blocked: starter traffic risk"
        if alerts:
            return False, "playable blocked: BvP/hot-bat alert"
        if offense_signal == "strong" and lineup_summary["hot_count"] >= 2:
            return False, "playable blocked: strong opponent bats"
    return True, ""

def apply_pitcher_er_conflict_filter(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple, list[int]] = {}
    for idx, row in enumerate(rows):
        if action_signal_rank(row.get("signal", "")) == 0:
            continue
        key = (
            str(row.get("event_id", "")),
            str(row.get("stat_entity_id") or row.get("pitcher_name", "")),
            str(row.get("book", "")),
            str(row.get("line", "")),
        )
        grouped.setdefault(key, []).append(idx)

    output = [dict(row) for row in rows]
    for indexes in grouped.values():
        sides = {str(output[i].get("side", "")).lower() for i in indexes}
        if not {"over", "under"}.issubset(sides):
            continue
        max_score = max(safe_float(output[i].get("signal_score")) for i in indexes)
        best_indexes = [i for i in indexes if safe_float(output[i].get("signal_score")) == max_score]
        if len(best_indexes) != 1:
            for i in indexes:
                output[i]["signal"] = "No clear edge"
                existing = str(output[i].get("signal_reasons", ""))
                output[i]["signal_reasons"] = "; ".join([part for part in [existing, "conflicting ER signals tied"] if part])[:240]
            continue
        best_idx = best_indexes[0]
        best_side = output[best_idx].get("side", "")
        for i in indexes:
            if i == best_idx:
                continue
            output[i]["signal"] = "No bet"
            existing = str(output[i].get("signal_reasons", ""))
            output[i]["signal_reasons"] = "; ".join([part for part in [existing, f"weaker than {best_side} side"] if part])[:240]
    return output

def add_pitcher_er_signals_to_props(
    rows: list[dict],
    game: dict,
    away_pitcher: dict,
    home_pitcher: dict,
    away_snapshot: dict,
    home_snapshot: dict,
    away_lineup: list[dict],
    home_lineup: list[dict],
    weather_context: dict | None,
) -> list[dict]:
    output = []
    for row in rows:
        team = str(row.get("team", ""))
        if team == game.get("away_team_name"):
            pitcher = away_pitcher
            opponent_snapshot = home_snapshot
            opponent_lineup = home_lineup
            pitcher_context = "away"
        elif team == game.get("home_team_name"):
            pitcher = home_pitcher
            opponent_snapshot = away_snapshot
            opponent_lineup = away_lineup
            pitcher_context = "home"
        else:
            pitcher = {}
            opponent_snapshot = {}
            opponent_lineup = []
            pitcher_context = ""
        score, reasons = score_pitcher_er_prop(row, pitcher, opponent_snapshot, opponent_lineup, weather_context, pitcher_context)
        label = classify_pitcher_er_signal(score)
        if label == "Playable":
            playable_ok, playable_note = pitcher_er_playable_check(str(row.get("side", "")).lower(), pitcher, opponent_snapshot, opponent_lineup)
            if not playable_ok:
                label = "Lean"
                reasons.append(playable_note)
        output.append({**row, "signal": label, "signal_score": score, "signal_reasons": "; ".join(reasons[:6])})
    return apply_pitcher_er_conflict_filter(output)

def pitcher_er_props_display_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    cols = [
        "pitcher_name",
        "team",
        "side",
        "line",
        "price",
        "book",
        "open_line",
        "open_price",
        "movement",
        "implied_prob",
    ]
    df = df[[col for col in cols if col in df.columns]].copy()
    sort_cols = [col for col in ["pitcher_name", "book", "line", "side"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=True)
    if "implied_prob" in df.columns:
        df["implied_prob"] = df["implied_prob"].apply(lambda value: "" if pd.isna(value) else f"{value:.1%}")
    return df.rename(
        columns={
            "pitcher_name": "Pitcher",
            "team": "Team",
            "side": "Side",
            "line": "Line",
            "price": "Price",
            "book": "Book",
            "open_line": "Open line",
            "open_price": "Open price",
            "movement": "Move",
            "implied_prob": "Implied",
        }
    )

def save_pitcher_er_props_to_tracker(rows: list[dict], allowed_signals: set[str] | None = None) -> int:
    allowed = allowed_signals or {"Playable"}
    candidates = [row for row in rows if row.get("signal") in allowed]
    if not candidates:
        return 0
    existing = read_pitcher_prop_tracker()
    existing_keys = set()
    if not existing.empty:
        for item in existing.to_dict("records"):
            existing_keys.add(
                (
                    str(item.get("game_id", "")),
                    str(item.get("pitcher_id") or item.get("stat_entity_id") or item.get("pitcher_name", "")),
                    str(item.get("side", "")),
                    str(item.get("line", "")),
                    str(item.get("book", "")),
                    str(item.get("market", "")),
                )
            )
    new_rows = []
    for row in candidates:
        key = (
            str(row.get("game_id", "")),
            str(row.get("pitcher_id") or row.get("stat_entity_id") or row.get("pitcher_name", "")),
            str(row.get("side", "")),
            str(row.get("line", "")),
            str(row.get("book", "")),
            "Earned Runs",
        )
        if key in existing_keys:
            continue
        existing_keys.add(key)
        new_rows.append(
            {
                "created_at": pd.Timestamp.now(tz="UTC").isoformat(),
                "game_date": row.get("game_date"),
                "game_id": row.get("game_id"),
                "matchup": row.get("matchup"),
                "team": row.get("team"),
                "opponent": row.get("opponent"),
                "pitcher_id": row.get("pitcher_id"),
                "pitcher_name": row.get("pitcher_name"),
                "market": "Earned Runs",
                "side": row.get("side"),
                "line": row.get("line"),
                "price": row.get("price"),
                "book": row.get("book"),
                "source": "SportsGameOdds",
                "odd_id": row.get("odd_id"),
                "stat_entity_id": row.get("stat_entity_id"),
                "signal": row.get("signal"),
                "signal_score": row.get("signal_score"),
                "signal_reasons": row.get("signal_reasons"),
                "movement": row.get("movement"),
                "start_required": "true",
                "note": row.get("signal_reasons"),
                "result": "pending",
            }
        )
    if not new_rows:
        return 0
    combined = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True) if not existing.empty else pd.DataFrame(new_rows)
    save_pitcher_prop_tracker(combined)
    return len(new_rows)

def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

def innings_to_float(ip: Any) -> float:
    if ip is None:
        return float("nan")
    s = str(ip)
    if "." not in s:
        return safe_float(s)
    whole, frac = s.split(".", 1)
    whole_i = safe_int(whole)
    frac_i = safe_int(frac)
    if frac_i == 0:
        return float(whole_i)
    if frac_i == 1:
        return whole_i + 1 / 3
    if frac_i == 2:
        return whole_i + 2 / 3
    return safe_float(s)

def format_stat(value: Any, digits: int = 3) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"

def format_percent(value: Any, digits: int = 0) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric):
        return "n/a"
    return f"{numeric * 100:.{digits}f}%"

def innings_to_outs(ip: Any) -> int:
    innings = innings_to_float(ip)
    if pd.isna(innings):
        return 0
    return int(round(innings * 3))

def format_outs_as_ip(outs: int) -> str:
    return f"{outs // 3}.{outs % 3}"

def trend_arrow(delta: float) -> str:
    if pd.isna(delta):
        return "→"
    if delta > 0.003:
        return "↑"
    if delta < -0.003:
        return "↓"
    return "→"

def build_team_row(game_id: int, game_date: str, team_name: str, opponent_name: str, home_away: str, batting: dict) -> dict:
    ab = safe_int(batting.get("atBats"))
    h = safe_int(batting.get("hits"))
    bb = safe_int(batting.get("baseOnBalls"))
    hbp = safe_int(batting.get("hitByPitch"))
    sf = safe_int(batting.get("sacFlies"))
    pa = safe_int(batting.get("plateAppearances"))
    doubles = safe_int(batting.get("doubles"))
    triples = safe_int(batting.get("triples"))
    hr = safe_int(batting.get("homeRuns"))
    runs = safe_int(batting.get("runs"))
    so = safe_int(batting.get("strikeOuts"))
    if not pa:
        pa = ab + bb + hbp + sf
    singles = max(h - doubles - triples - hr, 0)
    tb = singles + 2 * doubles + 3 * triples + 4 * hr
    denom = ab + bb + hbp + sf
    obp = round((h + bb + hbp) / denom, 3) if denom else None
    slg = round(tb / ab, 3) if ab else None
    ops = round(obp + slg, 3) if obp is not None and slg is not None else None
    return {
        "game_id": game_id,
        "date": game_date,
        "team": team_name,
        "opponent": opponent_name,
        "home_away": home_away,
        "runs": runs,
        "ab": ab,
        "h": h,
        "bb": bb,
        "pa": pa,
        "so": so,
        "singles": singles,
        "doubles": doubles,
        "triples": triples,
        "hr": hr,
        "hbp": hbp,
        "sf": sf,
        "tb": tb,
        "obp": obp,
        "slg": slg,
        "ops": ops,
    }

def update_team_game_logs(season: int) -> tuple[bool, str]:
    try:
        today = pd.Timestamp.today().normalize()
        season_start = pd.Timestamp(f"{season}-01-01")
        season_end = pd.Timestamp(f"{season}-12-31")
        target_end = min(today - pd.Timedelta(days=1), season_end)
        existing = pd.DataFrame()
        if REAL_DATA_PATH.exists():
            try:
                existing = pd.read_csv(REAL_DATA_PATH)
                if "date" in existing.columns:
                    existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
            except Exception:
                existing = pd.DataFrame()

        if not existing.empty and "date" in existing.columns and existing["date"].notna().any():
            latest_existing = existing["date"].max().normalize()
            if latest_existing >= target_end:
                return True, f"Team logs already up to date through {latest_existing.strftime('%Y-%m-%d')}."
            start_ts = max(season_start, latest_existing - pd.Timedelta(days=5))
        else:
            start_ts = season_start

        if target_end < start_ts:
            return True, f"Team logs already fresh through {target_end.strftime('%Y-%m-%d')}."

        schedule = mlb_get(
            "/schedule",
            {
                "sportId": 1,
                "startDate": start_ts.strftime("%Y-%m-%d"),
                "endDate": target_end.strftime("%Y-%m-%d"),
            },
            timeout=20,
        )
        rows = []
        seen = set()
        failed_games = []
        for date_block in schedule.get("dates", []):
            for game in date_block.get("games", []):
                game_id = safe_int(game.get("gamePk"))
                if not game_id or game_id in seen:
                    continue
                if game.get("gameType") != "R":
                    continue
                if str(game.get("status", {}).get("detailedState", "")).lower() != "final":
                    continue
                seen.add(game_id)
                try:
                    box = mlb_get(f"/game/{game_id}/boxscore", timeout=12)
                except Exception as exc:
                    failed_games.append(f"{game_id}: {exc}")
                    continue
                away = box.get("teams", {}).get("away", {})
                home = box.get("teams", {}).get("home", {})
                away_name = away.get("team", {}).get("name", "Away")
                home_name = home.get("team", {}).get("name", "Home")
                game_date = str(game.get("officialDate") or date_block.get("date"))
                away_batting = away.get("teamStats", {}).get("batting", {}) or {}
                home_batting = home.get("teamStats", {}).get("batting", {}) or {}
                rows.append(build_team_row(game_id, game_date, away_name, home_name, "away", away_batting))
                rows.append(build_team_row(game_id, game_date, home_name, away_name, "home", home_batting))
        fresh = pd.DataFrame(rows)
        if fresh.empty and existing.empty:
            return False, "No finished regular-season games were returned."
        if not fresh.empty:
            refreshed_ids = set(pd.to_numeric(fresh["game_id"], errors="coerce").dropna().astype(int))
            if not existing.empty and "game_id" in existing.columns:
                existing = existing[~pd.to_numeric(existing["game_id"], errors="coerce").isin(refreshed_ids)]
            df = pd.concat([existing, fresh], ignore_index=True) if not existing.empty else fresh
        else:
            df = existing.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.sort_values(["team", "date", "game_id"]).reset_index(drop=True)
        REAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(REAL_DATA_PATH, index=False)
        message = (
            f"Updated {len(rows)} team-game rows from {start_ts.strftime('%Y-%m-%d')} through {target_end.strftime('%Y-%m-%d')}. "
            f"Saved {len(df)} total rows to {REAL_DATA_PATH}."
        )
        if failed_games:
            message += "\nSkipped boxscores:\n" + "\n".join(failed_games[:10])
        return True, message
    except Exception as e:
        return False, str(e)

def get_data_signature() -> float:
    if REAL_DATA_PATH.exists():
        return REAL_DATA_PATH.stat().st_mtime
    if DEMO_DATA_PATH.exists():
        return DEMO_DATA_PATH.stat().st_mtime
    return 0.0

def expected_latest_result_date(selected_date: pd.Timestamp) -> pd.Timestamp:
    today = pd.Timestamp.today().normalize()
    selected = pd.Timestamp(selected_date).normalize()
    return min(selected, today - pd.Timedelta(days=1))

def latest_team_log_date() -> pd.Timestamp | None:
    if not REAL_DATA_PATH.exists():
        return None
    try:
        dates = pd.read_csv(REAL_DATA_PATH, usecols=["date"])["date"]
    except Exception:
        return None
    parsed = pd.to_datetime(dates, errors="coerce").dropna()
    if parsed.empty:
        return None
    return parsed.max().normalize()

def team_logs_are_stale(selected_date: pd.Timestamp) -> tuple[bool, pd.Timestamp | None, pd.Timestamp]:
    latest = latest_team_log_date()
    expected = expected_latest_result_date(selected_date)
    if latest is None:
        return True, latest, expected
    return latest < expected, latest, expected

@st.cache_data
def load_team_logs(data_signature: float) -> pd.DataFrame:
    if REAL_DATA_PATH.exists():
        return pd.read_csv(REAL_DATA_PATH)
    return pd.read_csv(DEMO_DATA_PATH)

def prepare_team_logs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df["team"] = df["team"].astype(str).str.strip()
    if "game_id" not in df.columns:
        df["game_id"] = pd.NA
    if "home_away" not in df.columns:
        df["home_away"] = pd.NA
    else:
        df["home_away"] = df["home_away"].astype(str).str.strip().str.lower()
    if "runs" not in df.columns:
        df["runs"] = pd.NA
    for col in ["pa", "so", "singles", "doubles", "triples", "hr"]:
        if col not in df.columns:
            df[col] = pd.NA
    numeric_cols = [c for c in ["game_id", "runs", "ab", "h", "bb", "pa", "so", "singles", "doubles", "triples", "hr", "hbp", "sf", "tb", "obp", "slg", "ops"] if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "game_id" in df.columns and "runs" in df.columns:
        opp_runs = df[["game_id", "team", "runs"]].rename(columns={"team": "opponent", "runs": "opponent_runs"})
        df = df.merge(opp_runs, on=["game_id", "opponent"], how="left")
    return df.sort_values(["team", "date"]).reset_index(drop=True)

def trailing_average(series: pd.Series, n: int) -> float:
    s = series.dropna()
    if s.empty:
        return float("nan")
    return float(s.tail(n).mean())

def previous_window_average(series: pd.Series, n: int) -> float:
    s = series.dropna()
    if len(s) <= n:
        return float("nan")
    prev = s.iloc[max(0, len(s) - 2 * n): len(s) - n]
    if prev.empty:
        return float("nan")
    return float(prev.mean())

def season_metric(team_df: pd.DataFrame, metric: str) -> float:
    return aggregate_team_metric(team_df, metric)

def aggregate_team_metric(team_df: pd.DataFrame, metric: str) -> float:
    if team_df.empty:
        return float("nan")
    ab = team_df["ab"].fillna(0).sum()
    h = team_df["h"].fillna(0).sum()
    bb = team_df["bb"].fillna(0).sum()
    hbp = team_df["hbp"].fillna(0).sum()
    sf = team_df["sf"].fillna(0).sum()
    tb = team_df["tb"].fillna(0).sum()
    denom = ab + bb + hbp + sf
    obp = ((h + bb + hbp) / denom) if denom else float("nan")
    slg = (tb / ab) if ab else float("nan")
    ops = obp + slg if pd.notna(obp) and pd.notna(slg) else float("nan")
    return float(obp if metric == "obp" else ops)

def aggregate_batting_profile(team_df: pd.DataFrame) -> dict:
    if team_df.empty:
        return {
            "games": 0,
            "runs": 0,
            "hits": 0,
            "walks": 0,
            "strikeouts": 0,
            "home_runs": 0,
            "pa": 0,
            "ab": 0,
            "avg": float("nan"),
            "obp": float("nan"),
            "slg": float("nan"),
            "ops": float("nan"),
            "iso": float("nan"),
            "k_pct": float("nan"),
            "bb_pct": float("nan"),
            "xbh_pct": float("nan"),
            "hr_per_game": float("nan"),
        }

    ab = team_df["ab"].fillna(0).sum()
    h = team_df["h"].fillna(0).sum()
    bb = team_df["bb"].fillna(0).sum()
    hbp = team_df["hbp"].fillna(0).sum()
    sf = team_df["sf"].fillna(0).sum()
    tb = team_df["tb"].fillna(0).sum()
    so = team_df["so"].sum(skipna=True) if "so" in team_df.columns and team_df["so"].notna().any() else float("nan")
    doubles = team_df["doubles"].fillna(0).sum() if "doubles" in team_df.columns else 0
    triples = team_df["triples"].fillna(0).sum() if "triples" in team_df.columns else 0
    hr = team_df["hr"].fillna(0).sum() if "hr" in team_df.columns else 0
    runs = team_df["runs"].fillna(0).sum() if "runs" in team_df.columns else 0
    obp_denom = ab + bb + hbp + sf
    pa = team_df["pa"].fillna(0).sum() if "pa" in team_df.columns and team_df["pa"].notna().any() else obp_denom
    avg = (h / ab) if ab else float("nan")
    obp = ((h + bb + hbp) / obp_denom) if obp_denom else float("nan")
    slg = (tb / ab) if ab else float("nan")
    ops = obp + slg if pd.notna(obp) and pd.notna(slg) else float("nan")
    iso = slg - avg if pd.notna(slg) and pd.notna(avg) else float("nan")
    k_pct = (so / pa) if pa and pd.notna(so) else float("nan")
    bb_pct = (bb / pa) if pa else float("nan")
    xbh_pct = ((doubles + triples + hr) / h) if h else float("nan")
    return {
        "games": int(len(team_df)),
        "runs": int(runs),
        "hits": int(h),
        "walks": int(bb),
        "strikeouts": int(so) if pd.notna(so) else 0,
        "home_runs": int(hr),
        "pa": int(pa),
        "ab": int(ab),
        "avg": avg,
        "obp": obp,
        "slg": slg,
        "ops": ops,
        "iso": iso,
        "k_pct": k_pct,
        "bb_pct": bb_pct,
        "xbh_pct": xbh_pct,
        "hr_per_game": (hr / len(team_df)) if len(team_df) else float("nan"),
    }

def batting_profile_label(profile: dict) -> tuple[str, str, str]:
    avg = safe_float(profile.get("avg"))
    obp = safe_float(profile.get("obp"))
    slg = safe_float(profile.get("slg"))
    ops = safe_float(profile.get("ops"))
    iso = safe_float(profile.get("iso"))
    k_pct = safe_float(profile.get("k_pct"))
    bb_pct = safe_float(profile.get("bb_pct"))
    xbh_pct = safe_float(profile.get("xbh_pct"))

    if pd.notna(k_pct) and k_pct >= 0.265 and pd.notna(iso) and iso >= 0.180:
        return "Swing-and-miss damage", "volatile", "High strikeout profile with enough power to flip innings quickly."
    if pd.notna(avg) and avg < 0.225 and pd.notna(ops) and ops < 0.680:
        return "Low-threat offense", "cold", "Low average and low overall production."
    if pd.notna(avg) and avg < 0.245 and pd.notna(iso) and iso >= 0.175:
        return "Power, low average", "power", "More extra-base damage than singles pressure."
    if pd.notna(avg) and avg >= 0.260 and pd.notna(k_pct) and k_pct <= 0.205 and pd.notna(iso) and iso < 0.150:
        return "Contact pressure", "contact", "Puts the ball in play often, but with limited thump."
    if pd.notna(avg) and avg >= 0.255 and pd.notna(slg) and slg >= 0.430 and (pd.isna(k_pct) or k_pct <= 0.240):
        return "Balanced attack", "balanced", "Contact and extra-base quality are both present."
    if pd.notna(avg) and avg >= 0.255 and pd.notna(xbh_pct) and xbh_pct < 0.300:
        return "Singles-heavy", "contact", "Hit volume is present, but extra-base share is light."
    if pd.notna(k_pct) and k_pct >= 0.255:
        return "Strikeout-heavy", "volatile", "Whiffs create K-prop upside and more empty innings."
    if pd.notna(bb_pct) and bb_pct >= 0.095 and pd.notna(obp) and obp >= 0.330:
        return "Patient traffic", "balanced", "Walks and on-base pressure can extend innings."
    if pd.notna(slg) and slg >= 0.430:
        return "Extra-base threat", "power", "Slugging profile carries damage risk."
    return "Neutral profile", "neutral", "No extreme batting shape in the recent sample."

def build_batting_profile(team_df: pd.DataFrame, n: int = 7) -> dict:
    recent_df = team_df.sort_values("date").tail(n)
    recent = aggregate_batting_profile(recent_df)
    season = aggregate_batting_profile(team_df)
    label, tone, note = batting_profile_label(recent)
    return {"label": label, "tone": tone, "note": note, "recent": recent, "season": season}

def trailing_team_metric(team_df: pd.DataFrame, metric: str, n: int) -> float:
    return aggregate_team_metric(team_df.sort_values("date").tail(n), metric)

def add_rolling_team_metric(df: pd.DataFrame, metric: str, window: int) -> pd.DataFrame:
    df = df.sort_values(["team", "date"]).copy()
    grouped = df.groupby("team", group_keys=False)
    rolling_ab = grouped["ab"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())
    rolling_h = grouped["h"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())
    rolling_bb = grouped["bb"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())
    rolling_hbp = grouped["hbp"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())
    rolling_sf = grouped["sf"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())
    rolling_tb = grouped["tb"].transform(lambda s: s.rolling(window=window, min_periods=1).sum())

    rolling_denom = rolling_ab + rolling_bb + rolling_hbp + rolling_sf
    rolling_obp = (rolling_h + rolling_bb + rolling_hbp) / rolling_denom.where(rolling_denom != 0)
    rolling_slg = rolling_tb / rolling_ab.where(rolling_ab != 0)
    df["rolling_value"] = rolling_obp if metric == "obp" else rolling_obp + rolling_slg
    return df

def calculate_recent_hitting(logs: list[dict], n: int = 7) -> dict:
    recent = sorted([g for g in logs if g], key=lambda x: x.get("date", ""))[-n:]
    if not recent:
        return {"avg": float("nan"), "obp": float("nan"), "ops": float("nan")}
    ab = sum(safe_int(g.get("atBats")) for g in recent)
    h = sum(safe_int(g.get("hits")) for g in recent)
    bb = sum(safe_int(g.get("baseOnBalls")) for g in recent)
    hbp = sum(safe_int(g.get("hitByPitch")) for g in recent)
    sf = sum(safe_int(g.get("sacFlies")) for g in recent)
    tb = sum(safe_int(g.get("totalBases")) for g in recent)
    avg = (h / ab) if ab else float("nan")
    obp = ((h + bb + hbp) / (ab + bb + hbp + sf)) if (ab + bb + hbp + sf) else float("nan")
    slg = (tb / ab) if ab else float("nan")
    ops = (obp + slg) if pd.notna(obp) and pd.notna(slg) else float("nan")
    return {"avg": avg, "obp": obp, "ops": ops}

def hitting_split_from_logs(logs: list[dict]) -> dict:
    if not logs:
        return {
            "games": 0,
            "ab": 0,
            "h": 0,
            "avg": float("nan"),
            "obp": float("nan"),
            "slg": float("nan"),
            "ops": float("nan"),
            "hpg": float("nan"),
        }
    ab = sum(safe_int(g.get("atBats")) for g in logs)
    h = sum(safe_int(g.get("hits")) for g in logs)
    bb = sum(safe_int(g.get("baseOnBalls")) for g in logs)
    hbp = sum(safe_int(g.get("hitByPitch")) for g in logs)
    sf = sum(safe_int(g.get("sacFlies")) for g in logs)
    tb = sum(safe_int(g.get("totalBases")) for g in logs)
    games = len(logs)
    denom = ab + bb + hbp + sf
    avg = (h / ab) if ab else float("nan")
    obp = ((h + bb + hbp) / denom) if denom else float("nan")
    slg = (tb / ab) if ab else float("nan")
    ops = (obp + slg) if pd.notna(obp) and pd.notna(slg) else float("nan")
    return {
        "games": games,
        "ab": ab,
        "h": h,
        "avg": avg,
        "obp": obp,
        "slg": slg,
        "ops": ops,
        "hpg": (h / games) if games else float("nan"),
    }

def hitting_logs_through_date(logs: list[dict], end_date: Any | None) -> list[dict]:
    dated = []
    end_ts = pd.Timestamp(end_date).normalize() if end_date is not None else None
    for log in logs:
        game_ts = pd.to_datetime(log.get("date"), errors="coerce")
        if pd.isna(game_ts):
            continue
        game_ts = game_ts.normalize()
        if end_ts is not None and game_ts > end_ts:
            continue
        dated.append({**log, "_date_ts": game_ts})
    return sorted(dated, key=lambda x: x["_date_ts"])

def hitting_logs_since(logs: list[dict], start_ts: pd.Timestamp) -> list[dict]:
    return [g for g in logs if g.get("_date_ts") is not None and g["_date_ts"] >= start_ts]

def hitter_consistency_label(windows: dict) -> tuple[str, str, str, float]:
    season = windows.get("season", {})
    last30 = windows.get("last30", {})
    last15 = windows.get("last15", {})
    last7 = windows.get("last7", {})
    season_avg = safe_float(season.get("avg"))
    avg30 = safe_float(last30.get("avg"))
    avg15 = safe_float(last15.get("avg"))
    avg7 = safe_float(last7.get("avg"))
    avgs = [v for v in [season_avg, avg30, avg15, avg7] if pd.notna(v)]
    if len(avgs) < 4:
        return "Small sample", "neutral", "Not enough completed game data across all windows.", 0.0

    if safe_int(season.get("ab")) < 60 or safe_int(last30.get("ab")) < 25 or safe_int(last15.get("ab")) < 12 or safe_int(last7.get("ab")) < 6:
        return "Small sample", "neutral", "Useful note, but the recent at-bat sample is light.", 1.0

    avg_floor = min(avgs)
    avg_range = max(avgs) - avg_floor
    recent_peak = max(avg30, avg15)
    hpg_floor = min(safe_float(w.get("hpg")) for w in windows.values() if pd.notna(safe_float(w.get("hpg"))))
    score = (avg_floor * 1000) + (safe_float(avg7) * 140) + (hpg_floor * 35) - (avg_range * 220)

    if recent_peak >= 0.380 and avg7 <= recent_peak - 0.080:
        return "Cooling from heater", "cooling", "Recent average was very hot, but the 7-day window has pulled back.", score - 30
    if season_avg >= 0.280 and avg30 <= season_avg - 0.035 and avg15 <= season_avg - 0.045 and avg7 <= season_avg - 0.055:
        return "Cooling", "cooling", "Season average is strong, but each recent window is below that baseline.", score - 25
    if avg7 >= season_avg + 0.060 and avg15 >= season_avg + 0.025:
        return "Heating", "heating", "Recent hit rate is clearly above the season baseline.", score + 25
    if avg7 >= avg15 + 0.050 and avg7 >= 0.300:
        return "Heating", "heating", "The 7-day window is jumping above the 15-day trend.", score + 15
    if avg_floor >= 0.285 and avg_range <= 0.055:
        return "Stable high", "stable", "High average with very little movement across the windows.", score + 35
    if avg_floor >= 0.260 and avg_range <= 0.050:
        return "Stable", "stable", "The hit profile is holding steady across all windows.", score + 20
    if avg_range >= 0.130:
        return "Volatile", "volatile", "Large swings between windows make the batting average less trustworthy.", score - 20
    if avg7 < 0.220 and avg15 < 0.240:
        return "Cold", "cold", "Both short windows are below a playable hit profile.", score - 35
    return "Neutral", "neutral", "No extreme heating or cooling pattern in the hit profile.", score

def build_hitter_consistency_profile(logs: list[dict], as_of_date: Any | None = None) -> dict:
    dated_logs = hitting_logs_through_date(logs, as_of_date)
    if not dated_logs:
        empty = hitting_split_from_logs([])
        windows = {"season": empty, "last30": empty, "last15": empty, "last7": empty}
        return {"windows": windows, "label": "Small sample", "tone": "neutral", "note": "No completed game log data yet.", "score": 0.0}
    end_ts = pd.Timestamp(as_of_date).normalize() if as_of_date is not None else max(g["_date_ts"] for g in dated_logs)
    windows = {
        "season": hitting_split_from_logs(dated_logs),
        "last30": hitting_split_from_logs(hitting_logs_since(dated_logs, end_ts - pd.Timedelta(days=29))),
        "last15": hitting_split_from_logs(hitting_logs_since(dated_logs, end_ts - pd.Timedelta(days=14))),
        "last7": hitting_split_from_logs(hitting_logs_since(dated_logs, end_ts - pd.Timedelta(days=6))),
    }
    label, tone, note, score = hitter_consistency_label(windows)
    avgs = [safe_float(w.get("avg")) for w in windows.values()]
    valid_avgs = [v for v in avgs if pd.notna(v)]
    return {
        "windows": windows,
        "label": label,
        "tone": tone,
        "note": note,
        "score": score,
        "avg_floor": min(valid_avgs) if valid_avgs else float("nan"),
        "avg_range": (max(valid_avgs) - min(valid_avgs)) if valid_avgs else float("nan"),
    }

def pitching_split_from_logs(logs: list[dict]) -> dict:
    if not logs:
        return {
            "games": 0,
            "outs": 0,
            "ip": float("nan"),
            "era": float("nan"),
            "whip": float("nan"),
            "h9": float("nan"),
            "bb9": float("nan"),
            "k9": float("nan"),
            "hr9": float("nan"),
            "home_runs": 0,
        }

    outs = sum(innings_to_outs(g.get("inningsPitched")) for g in logs)
    hits = sum(safe_int(g.get("hits")) for g in logs)
    walks = sum(safe_int(g.get("baseOnBalls")) for g in logs)
    earned_runs = sum(safe_int(g.get("earnedRuns")) for g in logs)
    strikeouts = sum(safe_int(g.get("strikeOuts")) for g in logs)
    home_runs = sum(safe_int(g.get("homeRuns")) for g in logs)
    innings = outs / 3
    return {
        "games": len(logs),
        "outs": outs,
        "ip": innings,
        "era": (earned_runs * 9 / innings) if innings else float("nan"),
        "whip": ((hits + walks) / innings) if innings else float("nan"),
        "h9": (hits * 9 / innings) if innings else float("nan"),
        "bb9": (walks * 9 / innings) if innings else float("nan"),
        "k9": (strikeouts * 9 / innings) if innings else float("nan"),
        "hr9": (home_runs * 9 / innings) if innings else float("nan"),
        "home_runs": home_runs,
    }

def pitching_home_away_splits(logs: list[dict]) -> dict:
    def is_home_game(log: dict) -> bool | None:
        value = log.get("is_home")
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
        return None

    home_logs = [g for g in logs if is_home_game(g) is True]
    away_logs = [g for g in logs if is_home_game(g) is False]
    has_data = bool(home_logs or away_logs)
    return {
        "has_data": has_data,
        "home": pitching_split_from_logs(home_logs),
        "away": pitching_split_from_logs(away_logs),
    }

def is_context_game(log: dict, context: str) -> bool:
    value = log.get("is_home")
    if isinstance(value, bool):
        is_home = value
    elif isinstance(value, str):
        if value.lower() == "true":
            is_home = True
        elif value.lower() == "false":
            is_home = False
        else:
            return False
    else:
        return False
    return is_home if context == "home" else not is_home

def build_context_production_rows(lineup_rows: list[dict], season: int, context: str, n: int = 5, limit: int = 5) -> list[dict]:
    rows = []
    for hitter in lineup_rows:
        pid = safe_int(hitter.get("Player ID"))
        if not pid:
            continue
        pdata = fetch_player_bundle(pid, season, "hitting")
        logs = sorted([g for g in pdata.get("game_log", []) if is_context_game(g, context)], key=lambda x: x.get("date", ""))[-n:]
        if not logs:
            continue
        runs = sum(safe_int(g.get("runs")) for g in logs)
        rbi = sum(safe_int(g.get("rbi", g.get("runsBattedIn"))) for g in logs)
        hits = sum(safe_int(g.get("hits")) for g in logs)
        total_bases = sum(safe_int(g.get("totalBases")) for g in logs)
        rows.append(
            {
                "Player": hitter.get("Player") or pdata.get("name"),
                "Spot": hitter.get("Spot", ""),
                "Pos": hitter.get("Pos", ""),
                "games": len(logs),
                "runs": runs,
                "rbi": rbi,
                "production": runs + rbi,
                "hits": hits,
                "tb": total_bases,
                "context": context,
            }
        )
    return sorted(rows, key=lambda x: (x["production"], x["rbi"], x["runs"], x["tb"]), reverse=True)[:limit]

@st.cache_data(ttl=1800)
def fetch_schedule_for_date(game_date: str) -> list[dict]:
    data = mlb_get_safe("/schedule", {"sportId": 1, "date": game_date, "hydrate": "probablePitcher,team"})
    games_out = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            away = game.get("teams", {}).get("away", {})
            home = game.get("teams", {}).get("home", {})
            games_out.append(
                {
                    "game_id": game.get("gamePk"),
                    "label": f"{away.get('team', {}).get('name', 'Away')} @ {home.get('team', {}).get('name', 'Home')}",
                    "away_team_id": away.get("team", {}).get("id"),
                    "away_team_name": away.get("team", {}).get("name"),
                    "home_team_id": home.get("team", {}).get("id"),
                    "home_team_name": home.get("team", {}).get("name"),
                    "away_pitcher_id": away.get("probablePitcher", {}).get("id"),
                    "away_pitcher_name": away.get("probablePitcher", {}).get("fullName"),
                    "home_pitcher_id": home.get("probablePitcher", {}).get("id"),
                    "home_pitcher_name": home.get("probablePitcher", {}).get("fullName"),
                    "status": game.get("status", {}).get("detailedState"),
                    "venue": game.get("venue", {}).get("name"),
                    "game_time": game.get("gameDate"),
                    "game_number": game.get("gameNumber"),
                    "double_header": game.get("doubleHeader"),
                    "series_game_number": game.get("seriesGameNumber"),
                }
            )
    fallback_time = pd.Timestamp("2100-01-01", tz="UTC")
    games_out = sorted(games_out, key=lambda game: (parse_timestamp_utc(game.get("game_time")) or fallback_time, str(game.get("game_id") or "")))
    return add_game_display_labels(games_out)

@st.cache_data(ttl=1800)
def fetch_player_bundle(player_id: int, season: int, group: str) -> dict:
    if not player_id:
        return {"id": player_id, "name": None, "stats": {}, "game_log": [], "bat_side": None, "pitch_hand": None}

    person = mlb_get_safe(f"/people/{player_id}")
    person_info = {}
    people = person.get("people", []) if isinstance(person, dict) else []
    if people:
        person_info = people[0]

    season_data = mlb_get_safe(
        f"/people/{player_id}/stats",
        {"stats": "season", "group": group, "season": season, "sportIds": 1},
    )
    game_log_data = mlb_get_safe(
        f"/people/{player_id}/stats",
        {"stats": "gameLog", "group": group, "season": season, "sportIds": 1},
    )

    stats = {}
    season_blocks = season_data.get("stats", []) if isinstance(season_data, dict) else []
    if season_blocks and season_blocks[0].get("splits"):
        stats = season_blocks[0]["splits"][0].get("stat", {}) or {}

    game_log = []
    log_blocks = game_log_data.get("stats", []) if isinstance(game_log_data, dict) else []
    if log_blocks and log_blocks[0].get("splits"):
        for split in log_blocks[0]["splits"]:
            row = split.get("stat", {}) or {}
            row["date"] = split.get("date")
            row["game_id"] = split.get("game", {}).get("gamePk")
            row["opponent"] = split.get("opponent", {}).get("name")
            row["is_home"] = split.get("isHome")
            game_log.append(row)

    return {
        "id": player_id,
        "name": person_info.get("fullName"),
        "stats": stats,
        "game_log": game_log,
        "bat_side": person_info.get("batSide", {}).get("code"),
        "pitch_hand": person_info.get("pitchHand", {}).get("code"),
    }

@st.cache_data(ttl=1800)
def fetch_pitcher_stat_split(player_id: int, season: int, split_code: str) -> dict:
    if not player_id:
        return {}
    data = mlb_get_safe(
        f"/people/{player_id}/stats",
        {"stats": "statSplits", "group": "pitching", "season": season, "sportIds": 1, "sitCodes": split_code},
    )
    stat_blocks = data.get("stats", []) if isinstance(data, dict) else []
    if stat_blocks and stat_blocks[0].get("splits"):
        return stat_blocks[0]["splits"][0].get("stat", {}) or {}
    return {}

@st.cache_data(ttl=1800)
def fetch_team_hitting_stat_split(team_id: int, season: int, split_code: str) -> dict:
    if not team_id:
        return {}
    data = mlb_get_safe(
        f"/teams/{team_id}/stats",
        {"stats": "statSplits", "group": "hitting", "season": season, "sportIds": 1, "sitCodes": split_code},
    )
    stat_blocks = data.get("stats", []) if isinstance(data, dict) else []
    if stat_blocks and stat_blocks[0].get("splits"):
        return stat_blocks[0]["splits"][0].get("stat", {}) or {}
    return {}

@st.cache_data(ttl=21600)
def fetch_savant_pitch_arsenals(season: int) -> pd.DataFrame:
    try:
        response = requests.get(
            BASEBALL_SAVANT_PITCH_ARSENALS_URL,
            params={"year": season, "min": 0, "type": "n_", "hand": "", "csv": "true"},
            timeout=30,
        )
        response.raise_for_status()
        from io import StringIO

        return pd.read_csv(StringIO(response.text))
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=21600)
def fetch_savant_pitch_arsenal_stats(season: int) -> pd.DataFrame:
    try:
        response = requests.get(
            BASEBALL_SAVANT_PITCH_ARSENAL_STATS_URL,
            params={"type": "pitcher", "pitchType": "", "year": season, "team": "", "min": 1, "csv": "true"},
            timeout=30,
        )
        response.raise_for_status()
        from io import StringIO

        return pd.read_csv(StringIO(response.text))
    except Exception:
        return pd.DataFrame()

def pitcher_arsenal_profile(player_id: int | None, season: int) -> dict:
    if not player_id:
        return {"available": False, "top_mix": [], "slider_group": float("nan"), "breaking": float("nan"), "damage": []}

    arsenals = fetch_savant_pitch_arsenals(season)
    if arsenals.empty or "pitcher" not in arsenals.columns:
        return {"available": False, "top_mix": [], "slider_group": float("nan"), "breaking": float("nan"), "damage": []}

    pitcher_ids = pd.to_numeric(arsenals["pitcher"], errors="coerce")
    rows = arsenals[pitcher_ids == safe_int(player_id)]
    if rows.empty:
        return {"available": False, "top_mix": [], "slider_group": float("nan"), "breaking": float("nan"), "damage": []}

    row = rows.iloc[0].to_dict()
    mix_columns = {
        "FF": "n_ff",
        "SI": "n_si",
        "FC": "n_fc",
        "SL": "n_sl",
        "ST": "n_st",
        "SV": "n_sv",
        "CU": "n_cu",
        "CH": "n_ch",
        "FS": "n_fs",
        "KN": "n_kn",
    }
    pitch_mix = []
    for code, column in mix_columns.items():
        value = safe_float(row.get(column))
        if pd.notna(value) and value > 0:
            pitch_mix.append({"code": code, "name": PITCH_TYPE_LABELS.get(code, code), "usage": value})
    pitch_mix = sorted(pitch_mix, key=lambda item: item["usage"], reverse=True)

    slider_group = sum(
        safe_float(row.get(column)) if pd.notna(safe_float(row.get(column))) else 0.0
        for column in ["n_sl", "n_st", "n_sv"]
    )
    breaking = slider_group + (safe_float(row.get("n_cu")) if pd.notna(safe_float(row.get("n_cu"))) else 0.0)

    damage = []
    arsenal_stats = fetch_savant_pitch_arsenal_stats(season)
    if not arsenal_stats.empty and {"player_id", "pitch_type"}.issubset(set(arsenal_stats.columns)):
        stat_ids = pd.to_numeric(arsenal_stats["player_id"], errors="coerce")
        stat_rows = arsenal_stats[(stat_ids == safe_int(player_id)) & (arsenal_stats["pitch_type"].isin(["SL", "ST", "SV", "CU", "KC"]))]
        for stat_row in stat_rows.to_dict("records"):
            usage = safe_float(stat_row.get("pitch_usage"))
            woba = safe_float(stat_row.get("woba"))
            slg = safe_float(stat_row.get("slg"))
            hard_hit = safe_float(stat_row.get("hard_hit_percent"))
            if pd.notna(usage) and usage >= 8 and (
                (pd.notna(woba) and woba >= 0.340)
                or (pd.notna(slg) and slg >= 0.450)
                or (pd.notna(hard_hit) and hard_hit >= 45)
            ):
                code = str(stat_row.get("pitch_type") or "")
                damage.append(
                    {
                        "code": code,
                        "name": PITCH_TYPE_LABELS.get(code, str(stat_row.get("pitch_name") or code)),
                        "usage": usage,
                        "woba": woba,
                        "slg": slg,
                        "hard_hit": hard_hit,
                    }
                )
    damage = sorted(damage, key=lambda item: safe_float(item.get("woba")), reverse=True)

    return {
        "available": True,
        "top_mix": pitch_mix[:4],
        "slider_group": slider_group,
        "breaking": breaking,
        "damage": damage[:3],
    }

def handedness_lineup_summary(lineup_rows: list[dict] | None) -> dict:
    rows = lineup_rows or []
    actual_rows = [row for row in rows if 1 <= safe_int(row.get("Spot")) <= 9]
    counted_rows = actual_rows or rows[:9]
    left_switch = [
        row for row in counted_rows
        if str(row.get("Bats") or "").upper() in {"L", "S"}
    ]
    top5 = [
        row for row in counted_rows
        if 1 <= safe_int(row.get("Spot")) <= 5 and str(row.get("Bats") or "").upper() in {"L", "S"}
    ]
    return {
        "available": bool(counted_rows),
        "posted": bool(actual_rows),
        "count": len(left_switch),
        "top5": len(top5),
        "total": len(counted_rows),
    }

def build_lefty_leverage_profile(
    team_snap: dict,
    team_id: int | None,
    opposing_pitcher: dict,
    season: int,
    lineup_rows: list[dict] | None = None,
) -> dict:
    pitcher_hand = str((opposing_pitcher or {}).get("pitch_hand") or "").upper()
    pitcher_id = safe_int((opposing_pitcher or {}).get("id"))
    team_name = str((team_snap or {}).get("team") or "Team")
    pitcher_name = str((opposing_pitcher or {}).get("name") or "opposing starter")

    if pitcher_hand != "R":
        return {
            "active": False,
            "label": "Not active",
            "tone": "neutral",
            "score": 0,
            "note": "Lefty leverage is only checked against right-handed starters.",
            "reasons": [],
            "pitcher_split": {},
            "team_split": {},
            "arsenal": {"available": False, "top_mix": [], "slider_group": float("nan"), "breaking": float("nan"), "damage": []},
            "lineup": handedness_lineup_summary(lineup_rows),
        }

    pitcher_split = fetch_pitcher_stat_split(pitcher_id, season, "vl")
    team_split = fetch_team_hitting_stat_split(safe_int(team_id), season, "vr")
    arsenal = pitcher_arsenal_profile(pitcher_id, season)
    lineup = handedness_lineup_summary(lineup_rows)

    score = 0
    reasons = []
    pitcher_ops = safe_float(pitcher_split.get("ops"))
    pitcher_obp = safe_float(pitcher_split.get("obp"))
    pitcher_slg = safe_float(pitcher_split.get("slg"))
    pitcher_whip = safe_float(pitcher_split.get("whip"))
    pitcher_hr9 = safe_float(pitcher_split.get("homeRunsPer9"))
    team_ops = safe_float(team_split.get("ops"))
    team_obp = safe_float(team_split.get("obp"))
    last7_ops = safe_float((team_snap or {}).get("last7_ops"))
    last7_obp = safe_float((team_snap or {}).get("last7_obp"))
    last3_ops = safe_float((team_snap or {}).get("last3_ops"))
    slider_group = safe_float(arsenal.get("slider_group"))
    breaking = safe_float(arsenal.get("breaking"))

    if pd.notna(pitcher_ops):
        if pitcher_ops >= 0.800:
            score += 2
            reasons.append(f"{pitcher_name} allows {format_stat(pitcher_ops, 3)} OPS vs LHB")
        elif pitcher_ops >= 0.760:
            score += 1
            reasons.append(f"{pitcher_name} allows {format_stat(pitcher_ops, 3)} OPS vs LHB")
    if pd.notna(pitcher_obp) and pitcher_obp >= 0.340:
        score += 1
        reasons.append(f"{format_stat(pitcher_obp, 3)} OBP allowed vs LHB")
    if pd.notna(pitcher_slg) and pitcher_slg >= 0.450:
        score += 1
        reasons.append(f"{format_stat(pitcher_slg, 3)} SLG allowed vs LHB")
    if pd.notna(pitcher_whip) and pitcher_whip >= 1.40:
        score += 1
        reasons.append(f"{format_stat(pitcher_whip, 2)} WHIP vs LHB")
    if pd.notna(pitcher_hr9) and pitcher_hr9 >= 1.30:
        score += 1
        reasons.append(f"{format_stat(pitcher_hr9, 2)} HR/9 vs LHB")
    if pd.notna(slider_group) and slider_group >= 25:
        score += 1
        reasons.append(f"{format_stat(slider_group, 0)}% slider/sweeper/slurve")
    if pd.notna(breaking) and breaking >= 35:
        score += 1
        reasons.append(f"{format_stat(breaking, 0)}% breaking-ball mix")
    if arsenal.get("damage"):
        score += 1
        damage = arsenal["damage"][0]
        reasons.append(f"{damage.get('name')} has damage risk")
    if pd.notna(team_ops):
        if team_ops >= 0.760:
            score += 2
            reasons.append(f"{team_name} owns {format_stat(team_ops, 3)} OPS vs RHP")
        elif team_ops >= 0.730:
            score += 1
            reasons.append(f"{team_name} owns {format_stat(team_ops, 3)} OPS vs RHP")
    if pd.notna(team_obp) and team_obp >= 0.330:
        score += 1
        reasons.append(f"{team_name} owns {format_stat(team_obp, 3)} OBP vs RHP")
    if pd.notna(last7_ops):
        if last7_ops >= 0.780:
            score += 2
            reasons.append(f"L7 team OPS {format_stat(last7_ops, 3)}")
        elif last7_ops >= 0.740:
            score += 1
            reasons.append(f"L7 team OPS {format_stat(last7_ops, 3)}")
    if pd.notna(last7_obp) and last7_obp >= 0.335:
        score += 1
        reasons.append(f"L7 OBP {format_stat(last7_obp, 3)}")
    if pd.notna(last3_ops) and last3_ops >= 0.760:
        score += 1
        reasons.append(f"L3 OPS {format_stat(last3_ops, 3)}")
    if lineup.get("posted"):
        if lineup.get("count", 0) >= 4:
            score += 1
            reasons.append(f"{lineup.get('count')} L/S bats posted")
        if lineup.get("top5", 0) >= 2:
            score += 1
            reasons.append(f"{lineup.get('top5')} L/S bats in top five")

    if not pitcher_split:
        label, tone, note = "No split data", "neutral", "Pitcher vs-left split was not available from MLB."
    elif score >= 9:
        label, tone, note = "Strong lefty leverage", "good", "Pitcher vs-left weakness, arsenal context, and team support line up."
    elif score >= 6:
        label, tone, note = "Lefty leverage", "good", "Enough lefty-side indicators line up to treat this as a scoring/context boost."
    elif score >= 4:
        label, tone, note = "Watch lefty leverage", "warning", "There is some lefty-side signal, but it needs lineup or recent-form confirmation."
    else:
        label, tone, note = "No clear lefty edge", "neutral", "The right-handed starter does not show enough lefty-side weakness here."

    return {
        "active": score >= 6,
        "label": label,
        "tone": tone,
        "score": score,
        "note": note,
        "reasons": reasons[:8],
        "pitcher_split": pitcher_split,
        "team_split": team_split,
        "arsenal": arsenal,
        "lineup": lineup,
    }

@st.cache_data(ttl=1800)
def fetch_game_boxscore(game_id: int) -> dict:
    return mlb_get_safe(f"/game/{game_id}/boxscore")

@st.cache_data(ttl=900)
def fetch_game_live_feed(game_id: int) -> dict:
    return mlb_get_safe(f"/game/{game_id}/feed/live")

def _extract_player_from_team_box(team_box: dict, pid: int) -> dict | None:
    players = team_box.get("players", {}) or {}
    return players.get(f"ID{pid}") or players.get(str(pid))

def read_pitcher_prop_tracker() -> pd.DataFrame:
    if not PITCHER_PROP_TRACKER_PATH.exists():
        return pd.DataFrame(columns=PITCHER_PROP_COLUMNS)
    df = pd.read_csv(PITCHER_PROP_TRACKER_PATH)
    for col in PITCHER_PROP_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    ordered_cols = PITCHER_PROP_COLUMNS + [col for col in df.columns if col not in PITCHER_PROP_COLUMNS]
    return df[ordered_cols]

def save_pitcher_prop_tracker(df: pd.DataFrame) -> None:
    PITCHER_PROP_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for col in PITCHER_PROP_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out.to_csv(PITCHER_PROP_TRACKER_PATH, index=False)

def append_pitcher_prop_tracker(row: dict) -> None:
    existing = read_pitcher_prop_tracker()
    new_row = {col: row.get(col, "") for col in PITCHER_PROP_COLUMNS}
    combined = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
    save_pitcher_prop_tracker(combined)

def _pitcher_boxscore_line(box: dict, pitcher_id: int, pitcher_name: str) -> tuple[dict, str]:
    wanted_name = normalize_name(pitcher_name)
    teams = box.get("teams", {}) if isinstance(box, dict) else {}
    for side in ["away", "home"]:
        team_box = teams.get(side, {}) or {}
        team_name = team_box.get("team", {}).get("name", "")
        pitcher_ids = [safe_int(pid) for pid in team_box.get("pitchers", []) if safe_int(pid)]
        players = team_box.get("players", {}) or {}
        player_boxes = []
        for pid in pitcher_ids:
            player_box = _extract_player_from_team_box(team_box, pid)
            if player_box:
                player_boxes.append(player_box)
        player_boxes.extend([p for p in players.values() if p not in player_boxes])

        for player_box in player_boxes:
            person = player_box.get("person", {}) or {}
            person_id = safe_int(person.get("id"))
            person_name = person.get("fullName", "")
            is_match = (pitcher_id and person_id == pitcher_id) or (wanted_name and normalize_name(person_name) == wanted_name)
            if not is_match:
                continue
            pitching = player_box.get("stats", {}).get("pitching", {}) or {}
            if pitching:
                return pitching, team_name
    return {}, ""

def _game_status_label(game_id: int) -> str:
    live = fetch_game_live_feed(game_id)
    return str(nested_get(live, ["gameData", "status", "detailedState"], ""))

def _is_final_status(status: str) -> bool:
    lowered = str(status or "").lower()
    return any(token in lowered for token in ["final", "completed", "game over"])

def _grade_over_under(side: str, actual: float, line: float) -> str:
    side = str(side or "").lower()
    if pd.isna(actual) or pd.isna(line):
        return "pending"
    if actual == line:
        return "push"
    if side == "over":
        return "win" if actual > line else "loss"
    if side == "under":
        return "win" if actual < line else "loss"
    return "pending"

def grade_pitcher_prop_row(row: dict) -> dict:
    game_id = safe_int(row.get("game_id"))
    pitcher_id = safe_int(row.get("pitcher_id"))
    pitcher_name = str(row.get("pitcher_name") or "")
    line = safe_float(row.get("line"))
    side = str(row.get("side") or "").lower()
    start_required = str(row.get("start_required", "true")).lower() not in {"false", "0", "no"}
    updated = dict(row)

    if not game_id:
        updated["result"] = "pending"
        updated["grade_reason"] = "Missing game id."
        return updated

    box = fetch_game_boxscore(game_id)
    pitching, team_name = _pitcher_boxscore_line(box, pitcher_id, pitcher_name)
    if pitching:
        actual_er = safe_int(pitching.get("earnedRuns"))
        actual_ip = pitching.get("inningsPitched", "")
        actual_hits = safe_int(pitching.get("hits"))
        actual_walks = safe_int(pitching.get("baseOnBalls"))
        actual_started = safe_int(pitching.get("gamesStarted")) > 0 if "gamesStarted" in pitching else None
        if start_required and actual_started is False:
            updated.update(
                {
                    "team": row.get("team") or team_name,
                    "actual_er": actual_er,
                    "actual_ip": actual_ip,
                    "actual_hits": actual_hits,
                    "actual_walks": actual_walks,
                    "actual_started": "no",
                    "result": "void",
                    "grade_reason": f"{pitcher_name}: pitching line found, but he did not start.",
                    "graded_at": pd.Timestamp.now(tz="UTC").isoformat(),
                }
            )
            return updated
        result = _grade_over_under(side, float(actual_er), line)
        updated.update(
            {
                "team": row.get("team") or team_name,
                "actual_er": actual_er,
                "actual_ip": actual_ip,
                "actual_hits": actual_hits,
                "actual_walks": actual_walks,
                "actual_started": "" if actual_started is None else ("yes" if actual_started else "no"),
                "result": result,
                "grade_reason": f"{pitcher_name}: {actual_er} ER, {actual_ip} IP, {actual_hits} H, {actual_walks} BB vs line {row.get('line')}.",
                "graded_at": pd.Timestamp.now(tz="UTC").isoformat(),
            }
        )
        return updated

    status = _game_status_label(game_id)
    if _is_final_status(status):
        updated.update(
            {
                "actual_er": "",
                "actual_ip": "",
                "actual_hits": "",
                "actual_walks": "",
                "actual_started": "",
                "result": "void",
                "grade_reason": f"{pitcher_name or 'Pitcher'} did not appear in the final boxscore.",
                "graded_at": pd.Timestamp.now(tz="UTC").isoformat(),
            }
        )
    else:
        updated.update(
            {
                "result": "pending",
                "grade_reason": f"Game status: {status or 'not final yet'}.",
            }
        )
    return updated

def grade_pitcher_prop_tracker(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if df.empty:
        return df, 0
    rows = []
    changed = 0
    for row in df.to_dict("records"):
        previous_result = str(row.get("result") or "").lower()
        if previous_result in {"win", "loss", "push", "void"}:
            rows.append(row)
            continue
        updated = grade_pitcher_prop_row(row)
        rows.append(updated)
        if str(updated.get("result") or "").lower() != previous_result:
            changed += 1
    return pd.DataFrame(rows), changed

def pitcher_prop_summary(df: pd.DataFrame) -> dict:
    if df.empty or "result" not in df.columns:
        return {"wins": 0, "losses": 0, "pushes": 0, "voids": 0, "pending": 0, "win_rate": float("nan")}
    result = df["result"].fillna("").astype(str).str.lower()
    wins = int((result == "win").sum())
    losses = int((result == "loss").sum())
    pushes = int((result == "push").sum())
    voids = int((result == "void").sum())
    pending = int((result == "pending").sum() + (result == "").sum())
    graded = wins + losses
    return {
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "voids": voids,
        "pending": pending,
        "win_rate": (wins / graded) if graded else float("nan"),
    }

def pitcher_prop_display_df(df: pd.DataFrame, current_game_id: int | None = None, current_only: bool = False) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if current_only and current_game_id:
        out = out[out["game_id"].astype(str) == str(current_game_id)]
    if "created_at" in out.columns:
        out["_created_sort"] = pd.to_datetime(out["created_at"], errors="coerce")
        out = out.sort_values("_created_sort", ascending=False).drop(columns=["_created_sort"])
    cols = [
        "game_date",
        "matchup",
        "pitcher_name",
        "side",
        "line",
        "price",
        "book",
        "source",
        "signal",
        "signal_score",
        "signal_reasons",
        "movement",
        "actual_er",
        "actual_ip",
        "actual_started",
        "result",
        "grade_reason",
        "note",
    ]
    out = out[[col for col in cols if col in out.columns]].head(50)
    return out.rename(
        columns={
            "game_date": "Date",
            "matchup": "Game",
            "pitcher_name": "Pitcher",
            "side": "Side",
            "line": "Line",
            "price": "Price",
            "book": "Book",
            "source": "Source",
            "signal": "Signal",
            "signal_score": "Score",
            "signal_reasons": "Why",
            "movement": "Move",
            "actual_er": "ER",
            "actual_ip": "IP",
            "actual_started": "Started",
            "result": "Result",
            "grade_reason": "Result note",
            "note": "Pregame note",
        }
    )

def ops_tier(ops_value: float) -> str:
    if pd.isna(ops_value):
        return "n/a"
    if ops_value < 0.700:
        return "weak"
    if ops_value < 0.800:
        return "average"
    return "great"

def last7_form_label(season_ops: float, recent_ops: float) -> str:
    if pd.isna(recent_ops):
        return "n/a"
    if recent_ops >= 0.800 and (pd.isna(season_ops) or recent_ops > season_ops):
        return "hot"
    return ops_tier(recent_ops)

def fetch_lineup_rows(game_id: int, side: str, season: int, as_of_date: Any | None = None) -> tuple[list[dict], bool]:
    box = fetch_game_boxscore(game_id)
    team_box = box.get("teams", {}).get(side, {}) if box else {}
    if not team_box:
        return [], False

    batter_ids = team_box.get("batters", []) or []
    rows = []
    seen = set()

    for idx, pid in enumerate(batter_ids, start=1):
        pid = safe_int(pid)
        if not pid or pid in seen:
            continue
        seen.add(pid)
        player_box = _extract_player_from_team_box(team_box, pid)
        if not player_box:
            continue

        pdata = fetch_player_bundle(pid, season, "hitting")
        stat = pdata.get("stats", {}) or {}
        recent = calculate_recent_hitting(pdata.get("game_log", []), 7)
        consistency = build_hitter_consistency_profile(pdata.get("game_log", []), as_of_date)
        batting_order = str(player_box.get("battingOrder") or "")
        lineup_spot = safe_int(batting_order[:-2]) if batting_order and len(batting_order) >= 3 else idx

        season_ops = safe_float(stat.get("ops"))
        recent_ops = recent.get("ops", float("nan"))
        season_label = ops_tier(season_ops)
        recent_label = last7_form_label(season_ops, recent_ops)

        rows.append(
            {
                "Player ID": pid,
                "Spot": lineup_spot,
                "Player": pdata.get("name") or player_box.get("person", {}).get("fullName"),
                "Pos": player_box.get("position", {}).get("abbreviation", ""),
                "Bats": pdata.get("bat_side") or "",
                "AVG": safe_float(stat.get("avg")),
                "OBP": safe_float(stat.get("obp")),
                "OPS": season_ops,
                "Last7 OPS": recent_ops,
                "Season Tier": season_label,
                "HR": safe_int(stat.get("homeRuns")),
                "BB": safe_int(stat.get("baseOnBalls")),
                "SO": safe_int(stat.get("strikeOuts")),
                "L7 Form": recent_label,
                "Hit Consistency": consistency,
            }
        )

    if rows:
        return sorted(rows, key=lambda x: x["Spot"]), True

    fallback = []
    players = team_box.get("players", {}) or {}
    for player_box in players.values():
        pos = player_box.get("position", {}).get("abbreviation", "")
        if pos == "P":
            continue
        pid = safe_int(player_box.get("person", {}).get("id"))
        if not pid:
            continue
        pdata = fetch_player_bundle(pid, season, "hitting")
        stat = pdata.get("stats", {}) or {}
        season_ops = safe_float(stat.get("ops"))
        if pd.isna(season_ops):
            continue
        recent = calculate_recent_hitting(pdata.get("game_log", []), 7)
        consistency = build_hitter_consistency_profile(pdata.get("game_log", []), as_of_date)
        recent_ops = recent.get("ops", float("nan"))
        season_label = ops_tier(season_ops)
        recent_label = last7_form_label(season_ops, recent_ops)
        fallback.append(
            {
                "Player ID": pid,
                "Spot": 99,
                "Player": pdata.get("name") or player_box.get("person", {}).get("fullName"),
                "Pos": pos,
                "Bats": pdata.get("bat_side") or "",
                "AVG": safe_float(stat.get("avg")),
                "OBP": safe_float(stat.get("obp")),
                "OPS": season_ops,
                "Last7 OPS": recent_ops,
                "Season Tier": season_label,
                "HR": safe_int(stat.get("homeRuns")),
                "BB": safe_int(stat.get("baseOnBalls")),
                "SO": safe_int(stat.get("strikeOuts")),
                "L7 Form": recent_label,
                "Hit Consistency": consistency,
            }
        )
    fallback = sorted(fallback, key=lambda x: (x["OPS"] if pd.notna(x["OPS"]) else -1), reverse=True)[:9]
    return fallback, False

def build_pitcher_era_trend(starter_logs: list[dict], rolling_window: int = 3) -> list[dict]:
    rows = []
    running_outs = 0
    running_er = 0
    for idx, game in enumerate(starter_logs):
        outs = innings_to_outs(game.get("inningsPitched"))
        er = safe_int(game.get("earnedRuns"))
        if outs <= 0:
            continue

        running_outs += outs
        running_er += er
        rolling_logs = starter_logs[max(0, idx - rolling_window + 1): idx + 1]
        rolling_outs = sum(innings_to_outs(g.get("inningsPitched")) for g in rolling_logs)
        rolling_er = sum(safe_int(g.get("earnedRuns")) for g in rolling_logs)
        rows.append(
            {
                "date": game.get("date"),
                "opponent": game.get("opponent") or "",
                "outs": outs,
                "er": er,
                "runs": safe_int(game.get("runs")),
                "game_era": (er * 27 / outs) if outs else float("nan"),
                "rolling_era": (rolling_er * 27 / rolling_outs) if rolling_outs else float("nan"),
                "season_era": (running_er * 27 / running_outs) if running_outs else float("nan"),
            }
        )
    return rows

def pitch_count_from_log(log: dict) -> int:
    for key in ["numberOfPitches", "pitchesThrown", "pitchCount"]:
        if log.get(key) not in [None, ""]:
            return safe_int(log.get(key))
    return 0

def average_values(values: list[Any]) -> float:
    clean = [safe_float(v) for v in values]
    clean = [v for v in clean if pd.notna(v)]
    return (sum(clean) / len(clean)) if clean else float("nan")

def rate_from_bools(values: list[bool]) -> float:
    return (sum(1 for value in values if value) / len(values)) if values else float("nan")

def pitcher_pitch_leash_profile(starter_logs: list[dict]) -> dict:
    logs = [g for g in starter_logs if g]
    if not logs:
        return {
            "label": "n/a",
            "tone": "neutral",
            "note": "No starter pitch-count data available.",
            "season_pitches_per_start": float("nan"),
            "last5_pitches_per_start": float("nan"),
            "last3_pitches_per_start": float("nan"),
            "season_pitches_per_out": float("nan"),
            "last5_pitches_per_out": float("nan"),
            "last3_pitches_per_out": float("nan"),
            "season_6ip_rate": float("nan"),
            "last5_6ip_rate": float("nan"),
        }

    def avg_pitches(source_logs: list[dict]) -> float:
        return average_values([pitch_count_from_log(g) for g in source_logs if pitch_count_from_log(g) > 0])

    def pitches_per_out(source_logs: list[dict]) -> float:
        paired = [(pitch_count_from_log(g), innings_to_outs(g.get("inningsPitched"))) for g in source_logs]
        paired = [(pitches, outs) for pitches, outs in paired if pitches > 0 and outs > 0]
        total_outs = sum(outs for _, outs in paired)
        return (sum(pitches for pitches, _ in paired) / total_outs) if total_outs else float("nan")

    def six_ip_rate(source_logs: list[dict]) -> float:
        outs = [innings_to_outs(g.get("inningsPitched")) for g in source_logs]
        outs = [value for value in outs if value > 0]
        return rate_from_bools([value >= 18 for value in outs])

    last5 = logs[-5:]
    last3 = logs[-3:]
    season_pitches = avg_pitches(logs)
    last5_pitches = avg_pitches(last5)
    last3_pitches = avg_pitches(last3)
    season_p_out = pitches_per_out(logs)
    last5_p_out = pitches_per_out(last5)
    last3_p_out = pitches_per_out(last3)
    season_6ip = six_ip_rate(logs)
    last5_6ip = six_ip_rate(last5)

    if pd.isna(last5_pitches):
        label = "n/a"
        tone = "neutral"
    elif last5_pitches >= 92 and pd.notna(last5_6ip) and last5_6ip >= 0.60 and (pd.isna(last5_p_out) or last5_p_out <= 5.4):
        label = "deep leash"
        tone = "good"
    elif last5_pitches <= 76 or (pd.notna(last5_6ip) and last5_6ip <= 0.20 and last5_pitches < 84):
        label = "short leash"
        tone = "bad"
    elif pd.notna(last5_p_out) and last5_p_out >= 5.8:
        label = "traffic hook risk"
        tone = "warning"
    elif last5_pitches >= 86:
        label = "normal leash"
        tone = "neutral"
    else:
        label = "watch leash"
        tone = "warning"

    note_parts = []
    if pd.notna(last5_pitches):
        note_parts.append(f"L5 {format_stat(last5_pitches, digits=0)} pitches/start")
    if pd.notna(last5_6ip):
        note_parts.append(f"6 IP rate {format_percent(last5_6ip)}")
    if pd.notna(last5_p_out):
        note_parts.append(f"{format_stat(last5_p_out, digits=1)} pitches/out")
    note = "; ".join(note_parts) if note_parts else "No starter pitch-count data available."

    return {
        "label": label,
        "tone": tone,
        "note": note,
        "season_pitches_per_start": season_pitches,
        "last5_pitches_per_start": last5_pitches,
        "last3_pitches_per_start": last3_pitches,
        "season_pitches_per_out": season_p_out,
        "last5_pitches_per_out": last5_p_out,
        "last3_pitches_per_out": last3_p_out,
        "season_6ip_rate": season_6ip,
        "last5_6ip_rate": last5_6ip,
    }

def build_pitcher_card(player_id: int | None, player_name: str | None, season: int) -> dict:
    if not player_id:
        return {
            "id": player_id,
            "name": player_name or "TBD",
            "pitch_hand": None,
            "last3_games": [],
            "era_trend": [],
            "pitch_leash": pitcher_pitch_leash_profile([]),
        }
    pdata = fetch_player_bundle(player_id, season, "pitching")
    stat = pdata.get("stats", {}) or {}
    name = pdata.get("name") or player_name or "TBD"

    if not stat:
        return {
            "id": player_id,
            "name": name,
            "pitch_hand": pdata.get("pitch_hand"),
            "era": float("nan"),
            "whip": float("nan"),
            "h9": float("nan"),
            "bb9": float("nan"),
            "k9": float("nan"),
            "hr9": float("nan"),
            "home_runs": 0,
            "starts": 0,
            "quality_starts": 0,
            "quality_start_label": "n/a",
            "last3_era": float("nan"),
            "last3_whip": float("nan"),
            "last3_hits": 0,
            "last3_walks": 0,
            "last3_home_runs": 0,
            "last3_hr9": float("nan"),
            "last3_ip_per_start": float("nan"),
            "last3_games": [],
            "era_trend": [],
            "home_away": pitching_home_away_splits([]),
            "pitch_leash": pitcher_pitch_leash_profile([]),
        }

    ip = innings_to_float(stat.get("inningsPitched"))
    hits = safe_int(stat.get("hits"))
    walks = safe_int(stat.get("baseOnBalls"))
    ks = safe_int(stat.get("strikeOuts"))
    home_runs = safe_int(stat.get("homeRuns"))

    h9 = (hits * 9 / ip) if pd.notna(ip) and ip else float("nan")
    bb9 = (walks * 9 / ip) if pd.notna(ip) and ip else float("nan")
    k9 = (ks * 9 / ip) if pd.notna(ip) and ip else float("nan")
    hr9 = (home_runs * 9 / ip) if pd.notna(ip) and ip else float("nan")

    all_logs = sorted([g for g in pdata.get("game_log", []) if g], key=lambda x: x.get("date", ""))
    starter_logs = [g for g in all_logs if safe_int(g.get("gamesStarted")) > 0]
    split_source_logs = starter_logs or all_logs
    pitch_leash = pitcher_pitch_leash_profile(split_source_logs)
    starts = len(starter_logs)
    quality_starts = sum(1 for g in starter_logs if safe_int(g.get("runs")) <= 3)
    quality_start_label = f"{quality_starts}/{starts}" if starts else "n/a"
    logs = (starter_logs or all_logs)[-3:]
    ip3 = sum(innings_to_float(g.get("inningsPitched")) for g in logs)
    h3 = sum(safe_int(g.get("hits")) for g in logs)
    bb3 = sum(safe_int(g.get("baseOnBalls")) for g in logs)
    er3 = sum(safe_int(g.get("earnedRuns")) for g in logs)
    hr3 = sum(safe_int(g.get("homeRuns")) for g in logs)
    last3_era = (er3 * 9 / ip3) if ip3 else float("nan")
    last3_whip = ((h3 + bb3) / ip3) if ip3 else float("nan")
    last3_hr9 = (hr3 * 9 / ip3) if ip3 else float("nan")
    starts_count = len(logs)
    last3_ip_per_start = (ip3 / starts_count) if starts_count else float("nan")
    last3_games = []
    for g in logs:
        g_ip = innings_to_float(g.get("inningsPitched"))
        g_hits = safe_int(g.get("hits"))
        g_walks = safe_int(g.get("baseOnBalls"))
        g_er = safe_int(g.get("earnedRuns"))
        g_outs = innings_to_outs(g.get("inningsPitched"))
        g_pitches = pitch_count_from_log(g)
        last3_games.append(
            {
                "date": g.get("date"),
                "opponent": g.get("opponent") or "",
                "is_home": g.get("is_home"),
                "ip": g_ip,
                "outs": g_outs,
                "pitches": g_pitches,
                "pitches_per_out": (g_pitches / g_outs) if g_pitches and g_outs else float("nan"),
                "er": g_er,
                "hits": g_hits,
                "walks": g_walks,
                "strikeouts": safe_int(g.get("strikeOuts")),
                "home_runs": safe_int(g.get("homeRuns")),
                "era": (g_er * 9 / g_ip) if g_ip else float("nan"),
                "whip": ((g_hits + g_walks) / g_ip) if g_ip else float("nan"),
            }
        )

    return {
        "id": player_id,
        "name": name,
        "pitch_hand": pdata.get("pitch_hand"),
        "era": safe_float(stat.get("era")),
        "whip": safe_float(stat.get("whip")),
        "h9": h9,
        "bb9": bb9,
        "k9": k9,
        "hr9": hr9,
        "home_runs": home_runs,
        "starts": starts,
        "quality_starts": quality_starts,
        "quality_start_label": quality_start_label,
        "last3_era": last3_era,
        "last3_whip": last3_whip,
        "last3_hits": h3,
        "last3_walks": bb3,
        "last3_home_runs": hr3,
        "last3_hr9": last3_hr9,
        "last3_ip_per_start": last3_ip_per_start,
        "last3_games": last3_games,
        "era_trend": build_pitcher_era_trend(starter_logs or all_logs),
        "home_away": pitching_home_away_splits(split_source_logs),
        "pitch_leash": pitch_leash,
    }

@st.cache_data(ttl=1800)
def fetch_batter_vs_pitcher_stat(batter_id: int, pitcher_id: int, season: int) -> dict:
    if not batter_id or not pitcher_id:
        return {}
    data = mlb_get_safe(
        f"/people/{batter_id}/stats",
        {"stats": "vsPlayer", "group": "hitting", "season": season, "sportIds": 1, "opposingPlayerId": pitcher_id},
    )
    stat_blocks = data.get("stats", []) if isinstance(data, dict) else []
    if stat_blocks and stat_blocks[0].get("splits"):
        return stat_blocks[0]["splits"][0].get("stat", {}) or {}
    return {}

def aggregate_bvp_rows(rows: list[dict]) -> dict:
    totals = {"ab": 0, "h": 0, "bb": 0, "hbp": 0, "sf": 0, "tb": 0, "so": 0, "hr": 0}
    for row in rows:
        totals["ab"] += safe_int(row.get("ab"))
        totals["h"] += safe_int(row.get("h"))
        totals["bb"] += safe_int(row.get("bb"))
        totals["hbp"] += safe_int(row.get("hbp"))
        totals["sf"] += safe_int(row.get("sf"))
        totals["tb"] += safe_int(row.get("tb"))
        totals["so"] += safe_int(row.get("so"))
        totals["hr"] += safe_int(row.get("hr"))
    denom = totals["ab"] + totals["bb"] + totals["hbp"] + totals["sf"]
    obp = (totals["h"] + totals["bb"] + totals["hbp"]) / denom if denom else float("nan")
    slg = totals["tb"] / totals["ab"] if totals["ab"] else float("nan")
    ops = obp + slg if pd.notna(obp) and pd.notna(slg) else float("nan")
    return {**totals, "obp": obp, "slg": slg, "ops": ops}

def bvp_avg(row: dict) -> float:
    ab = safe_int(row.get("ab"))
    return safe_int(row.get("h")) / ab if ab else float("nan")

def build_pitcher_vs_roster(player_id: int | None, lineup_rows: list[dict], season: int) -> dict:
    if not player_id or not lineup_rows:
        return {"rows": [], "summary": aggregate_bvp_rows([])}
    rows = []
    for hitter in lineup_rows:
        batter_id = safe_int(hitter.get("Player ID"))
        stat = fetch_batter_vs_pitcher_stat(batter_id, player_id, season)
        ab = safe_int(stat.get("atBats"))
        bb = safe_int(stat.get("baseOnBalls"))
        hbp = safe_int(stat.get("hitByPitch"))
        sf = safe_int(stat.get("sacFlies"))
        if ab + bb + hbp + sf == 0:
            continue
        rows.append(
            {
                "player": hitter.get("Player", ""),
                "ab": ab,
                "h": safe_int(stat.get("hits")),
                "bb": bb,
                "hbp": hbp,
                "sf": sf,
                "tb": safe_int(stat.get("totalBases")),
                "so": safe_int(stat.get("strikeOuts")),
                "hr": safe_int(stat.get("homeRuns")),
                "last7_ops": safe_float(hitter.get("Last7 OPS")),
                "l7_form": hitter.get("L7 Form", ""),
                "season_ops": safe_float(hitter.get("OPS")),
            }
        )
    return {"rows": rows, "summary": aggregate_bvp_rows(rows)}

def pitcher_recent_struggle(pitcher: dict) -> tuple[bool, str]:
    last3_era = safe_float((pitcher or {}).get("last3_era"))
    last3_whip = safe_float((pitcher or {}).get("last3_whip"))
    truth_label = pitcher_truth_label(pitcher)
    reasons = []
    if pd.notna(last3_era) and last3_era >= 4.50:
        reasons.append(f"L3 ERA {last3_era:.2f}")
    if pd.notna(last3_whip) and last3_whip >= 1.35:
        reasons.append(f"L3 WHIP {last3_whip:.3f}")
    if truth_label in {"danger spot", "lucky ERA", "regression risk", "watch traffic"}:
        reasons.append(f"ERA truth {truth_label}")
    return bool(reasons), ", ".join(reasons[:3])

def add_pitcher_vs_roster_alerts(pitcher: dict) -> dict:
    vs_roster = dict((pitcher or {}).get("vs_roster", {}) or {})
    rows = list(vs_roster.get("rows", []) or [])
    struggling, struggle_reason = pitcher_recent_struggle(pitcher)
    alerts = []
    if struggling:
        for row in rows:
            avg = bvp_avg(row)
            if (
                safe_int(row.get("ab")) >= 10
                and pd.notna(avg)
                and avg >= 0.300
                and row.get("l7_form") == "hot"
            ):
                alerts.append(
                    {
                        **row,
                        "avg": avg,
                        "reason": f"hot L7 form + {safe_int(row.get('ab'))} BvP AB at {avg:.3f} AVG + {struggle_reason}",
                    }
                )
    vs_roster["alerts"] = sorted(alerts, key=lambda r: (safe_float(r.get("avg")), safe_float(r.get("last7_ops"))), reverse=True)
    return vs_roster

def pitcher_era_truth_signal(pitcher: dict) -> dict:
    era = pitcher.get("era", float("nan"))
    whip = pitcher.get("whip", float("nan"))
    h9 = pitcher.get("h9", float("nan"))
    bb9 = pitcher.get("bb9", float("nan"))
    k9 = pitcher.get("k9", float("nan"))
    hr9 = pitcher.get("hr9", float("nan"))
    last3_era = pitcher.get("last3_era", float("nan"))
    last3_whip = pitcher.get("last3_whip", float("nan"))

    reasons = []
    red_flags = 0
    support_flags = 0

    if pd.notna(whip):
        if whip >= 1.50:
            red_flags += 2
            reasons.append(f"very high WHIP ({format_stat(whip, digits=3)})")
        elif whip >= 1.35:
            red_flags += 1
            reasons.append(f"traffic WHIP ({format_stat(whip, digits=3)})")
        elif whip <= 1.15:
            support_flags += 1
            reasons.append(f"strong WHIP ({format_stat(whip, digits=3)})")

    if pd.notna(bb9):
        if bb9 >= 4.25:
            red_flags += 1
            reasons.append(f"serious walk risk ({format_stat(bb9, digits=2)} BB/9)")
        elif bb9 >= 3.25:
            red_flags += 1
            reasons.append(f"walk risk ({format_stat(bb9, digits=2)} BB/9)")
        elif bb9 <= 2.25:
            support_flags += 1
            reasons.append(f"good control ({format_stat(bb9, digits=2)} BB/9)")

    if pd.notna(h9):
        if h9 >= 10.0:
            red_flags += 1
            reasons.append(f"heavy contact ({format_stat(h9, digits=2)} H/9)")
        elif h9 >= 8.8:
            red_flags += 1
            reasons.append(f"contact risk ({format_stat(h9, digits=2)} H/9)")
        elif h9 <= 7.5:
            support_flags += 1
            reasons.append(f"limits hits ({format_stat(h9, digits=2)} H/9)")

    if pd.notna(k9) and k9 < 6.5:
        red_flags += 1
        reasons.append(f"low strikeout buffer ({format_stat(k9, digits=2)} K/9)")
    elif pd.notna(k9) and k9 >= 9.5:
        support_flags += 1
        reasons.append(f"strong strikeout buffer ({format_stat(k9, digits=2)} K/9)")

    if pd.notna(hr9):
        if hr9 >= 1.45:
            red_flags += 1
            reasons.append(f"power damage ({format_stat(hr9, digits=2)} HR/9)")
        elif hr9 >= 1.20:
            red_flags += 1
            reasons.append(f"HR risk ({format_stat(hr9, digits=2)} HR/9)")
        elif hr9 <= 0.85:
            support_flags += 1
            reasons.append(f"suppresses HR ({format_stat(hr9, digits=2)} HR/9)")

    if pd.notna(last3_whip) and last3_whip >= 1.45:
        red_flags += 1
        reasons.append(f"recent traffic ({format_stat(last3_whip, digits=3)} L3 WHIP)")

    if pd.notna(era) and pd.notna(last3_era) and last3_era >= era + 1.00:
        red_flags += 1
        reasons.append(f"recent ERA worse than season ({format_stat(last3_era, digits=2)} L3)")

    if pd.isna(era):
        return {"label": "n/a", "tone": "neutral", "note": "No season ERA available.", "reasons": []}

    if era <= 3.25 and pd.notna(whip) and whip >= 1.50:
        label = "danger spot"
        tone = "bad"
    elif era <= 3.25 and red_flags >= 2:
        label = "lucky ERA"
        tone = "bad"
    elif era <= 3.50 and red_flags >= 2:
        label = "regression risk"
        tone = "bad"
    elif era >= 4.75 and support_flags >= 2 and red_flags == 0:
        label = "unlucky ERA"
        tone = "good"
    elif era <= 3.25 and support_flags >= 2 and red_flags == 0:
        label = "true strong"
        tone = "good"
    elif red_flags >= 3:
        label = "danger spot"
        tone = "bad"
    elif red_flags >= 1:
        label = "watch traffic"
        tone = "warning"
    else:
        label = "stable"
        tone = "neutral"

    reason_text = "; ".join(reasons[:3]) if reasons else "ERA and traffic indicators are aligned."
    return {"label": label, "tone": tone, "note": reason_text, "reasons": reasons}

def _team_box_for_name(box: dict, team_name: str) -> dict:
    teams = box.get("teams", {}) if box else {}
    for side in ["away", "home"]:
        team_box = teams.get(side, {}) or {}
        if team_box.get("team", {}).get("name") == team_name:
            return team_box
    return {}

def _pitching_stat(player_box: dict, stat_name: str) -> int:
    stat = player_box.get("stats", {}).get("pitching", {}) or {}
    return safe_int(stat.get(stat_name))

def _bullpen_game_from_box(team_box: dict) -> dict:
    pitcher_ids = [safe_int(pid) for pid in team_box.get("pitchers", []) if safe_int(pid)]
    totals = {
        "outs": 0,
        "hits": 0,
        "runs": 0,
        "earned_runs": 0,
        "walks": 0,
        "strikeouts": 0,
        "home_runs": 0,
        "pitchers": 0,
    }

    for idx, pid in enumerate(pitcher_ids):
        player_box = _extract_player_from_team_box(team_box, pid)
        if not player_box:
            continue
        pitching = player_box.get("stats", {}).get("pitching", {}) or {}
        has_started_flag = "gamesStarted" in pitching
        is_starter = safe_int(pitching.get("gamesStarted")) > 0 if has_started_flag else idx == 0
        if is_starter:
            continue

        totals["outs"] += innings_to_outs(pitching.get("inningsPitched"))
        totals["hits"] += _pitching_stat(player_box, "hits")
        totals["runs"] += _pitching_stat(player_box, "runs")
        totals["earned_runs"] += _pitching_stat(player_box, "earnedRuns")
        totals["walks"] += _pitching_stat(player_box, "baseOnBalls")
        totals["strikeouts"] += _pitching_stat(player_box, "strikeOuts")
        totals["home_runs"] += _pitching_stat(player_box, "homeRuns")
        totals["pitchers"] += 1

    return totals

def _team_pitching_game_from_box(team_box: dict) -> dict:
    pitcher_ids = [safe_int(pid) for pid in team_box.get("pitchers", []) if safe_int(pid)]
    totals = {
        "outs": 0,
        "hits": 0,
        "runs": 0,
        "earned_runs": 0,
        "walks": 0,
        "strikeouts": 0,
        "home_runs": 0,
        "pitchers": 0,
    }

    for pid in pitcher_ids:
        player_box = _extract_player_from_team_box(team_box, pid)
        if not player_box:
            continue
        pitching = player_box.get("stats", {}).get("pitching", {}) or {}
        if not pitching:
            continue

        totals["outs"] += innings_to_outs(pitching.get("inningsPitched"))
        totals["hits"] += _pitching_stat(player_box, "hits")
        totals["runs"] += _pitching_stat(player_box, "runs")
        totals["earned_runs"] += _pitching_stat(player_box, "earnedRuns")
        totals["walks"] += _pitching_stat(player_box, "baseOnBalls")
        totals["strikeouts"] += _pitching_stat(player_box, "strikeOuts")
        totals["home_runs"] += _pitching_stat(player_box, "homeRuns")
        totals["pitchers"] += 1

    return totals

def _rate_per_nine(value: int, outs: int) -> float:
    innings = outs / 3
    return (value * 9 / innings) if innings else float("nan")

def _whip(hits: int, walks: int, outs: int) -> float:
    innings = outs / 3
    return ((hits + walks) / innings) if innings else float("nan")

def bullpen_risk_label(bullpen: dict) -> str:
    era = bullpen.get("era", float("nan"))
    whip = bullpen.get("whip", float("nan"))
    bb9 = bullpen.get("bb9", float("nan"))
    runs_per_game = bullpen.get("runs_per_game", float("nan"))
    if bullpen.get("games", 0) == 0:
        return "n/a"
    if pd.notna(era) and pd.notna(whip) and era <= 3.20 and whip <= 1.20:
        return "steady"
    if (pd.notna(era) and era >= 5.00) or (pd.notna(whip) and whip >= 1.55) or (pd.notna(bb9) and bb9 >= 4.50):
        return "high traffic"
    if pd.notna(runs_per_game) and runs_per_game >= 3.00:
        return "run risk"
    return "neutral"

@st.cache_data(ttl=1800)
def build_bullpen_card(team_logs: pd.DataFrame, team_name: str, selected_date: Any, n: int = 5) -> dict:
    selected_ts = pd.Timestamp(selected_date)
    team_games = (
        team_logs[(team_logs["team"] == team_name) & (team_logs["date"] < selected_ts)]
        .sort_values(["date", "game_id"])
        .tail(n)
    )
    rows = []
    totals = {
        "outs": 0,
        "hits": 0,
        "runs": 0,
        "earned_runs": 0,
        "walks": 0,
        "strikeouts": 0,
        "home_runs": 0,
        "pitchers": 0,
    }

    for game_row in team_games.to_dict("records"):
        game_id = safe_int(game_row.get("game_id"))
        if not game_id:
            continue
        box = fetch_game_boxscore(game_id)
        team_box = _team_box_for_name(box, team_name)
        if not team_box:
            continue
        game_totals = _bullpen_game_from_box(team_box)
        for key in totals:
            totals[key] += game_totals[key]
        rows.append(
            {
                "date": pd.Timestamp(game_row.get("date")).strftime("%Y-%m-%d"),
                "opponent": game_row.get("opponent", ""),
                **game_totals,
            }
        )

    games = len(rows)
    outs = totals["outs"]
    innings = outs / 3
    era = _rate_per_nine(totals["earned_runs"], outs)
    whip = _whip(totals["hits"], totals["walks"], outs)
    bb9 = _rate_per_nine(totals["walks"], outs)
    k9 = _rate_per_nine(totals["strikeouts"], outs)
    hr9 = _rate_per_nine(totals["home_runs"], outs)
    runs_per_game = (totals["runs"] / games) if games else float("nan")

    bullpen = {
        "team": team_name,
        "games": games,
        "ip": innings,
        "outs": outs,
        "era": era,
        "whip": whip,
        "bb9": bb9,
        "k9": k9,
        "hr9": hr9,
        "runs": totals["runs"],
        "earned_runs": totals["earned_runs"],
        "hits": totals["hits"],
        "walks": totals["walks"],
        "strikeouts": totals["strikeouts"],
        "home_runs": totals["home_runs"],
        "runs_per_game": runs_per_game,
        "pitchers_used": totals["pitchers"],
        "rows": rows,
    }
    bullpen["label"] = bullpen_risk_label(bullpen)
    return bullpen

def team_pitching_staff_label(staff: dict) -> str:
    era = safe_float((staff or {}).get("era"))
    whip = safe_float((staff or {}).get("whip"))
    bb9 = safe_float((staff or {}).get("bb9"))
    if safe_int((staff or {}).get("games")) == 0:
        return "n/a"
    if pd.notna(era) and pd.notna(whip) and era <= 3.60 and whip <= 1.24:
        return "steady"
    if (pd.notna(era) and era >= 5.00) or (pd.notna(whip) and whip >= 1.45) or (pd.notna(bb9) and bb9 >= 4.25):
        return "high traffic"
    return "neutral"

@st.cache_data(ttl=1800)
def build_team_pitching_card(team_logs: pd.DataFrame, team_name: str, selected_date: Any, n: int = 7) -> dict:
    selected_ts = pd.Timestamp(selected_date)
    team_games = (
        team_logs[(team_logs["team"] == team_name) & (team_logs["date"] < selected_ts)]
        .sort_values(["date", "game_id"])
        .tail(n)
    )
    totals = {
        "outs": 0,
        "hits": 0,
        "runs": 0,
        "earned_runs": 0,
        "walks": 0,
        "strikeouts": 0,
        "home_runs": 0,
        "pitchers": 0,
    }
    rows = []

    for game_row in team_games.to_dict("records"):
        game_id = safe_int(game_row.get("game_id"))
        if not game_id:
            continue
        box = fetch_game_boxscore(game_id)
        team_box = _team_box_for_name(box, team_name)
        if not team_box:
            continue
        game_totals = _team_pitching_game_from_box(team_box)
        for key in totals:
            totals[key] += game_totals[key]
        rows.append(
            {
                "date": pd.Timestamp(game_row.get("date")).strftime("%Y-%m-%d"),
                "opponent": game_row.get("opponent", ""),
                **game_totals,
            }
        )

    games = len(rows)
    outs = totals["outs"]
    innings = outs / 3
    staff = {
        "team": team_name,
        "games": games,
        "ip": innings,
        "outs": outs,
        "era": _rate_per_nine(totals["earned_runs"], outs),
        "whip": _whip(totals["hits"], totals["walks"], outs),
        "h9": _rate_per_nine(totals["hits"], outs),
        "bb9": _rate_per_nine(totals["walks"], outs),
        "k9": _rate_per_nine(totals["strikeouts"], outs),
        "hr9": _rate_per_nine(totals["home_runs"], outs),
        "runs": totals["runs"],
        "earned_runs": totals["earned_runs"],
        "hits": totals["hits"],
        "walks": totals["walks"],
        "strikeouts": totals["strikeouts"],
        "home_runs": totals["home_runs"],
        "pitchers_used": totals["pitchers"],
        "runs_per_game": (totals["runs"] / games) if games else float("nan"),
        "rows": rows,
    }
    staff["label"] = team_pitching_staff_label(staff)
    return staff

def _bullpen_reliever_appearances_from_box(team_box: dict, game_date: str) -> list[dict]:
    pitcher_ids = [safe_int(pid) for pid in team_box.get("pitchers", []) if safe_int(pid)]
    rows = []
    for idx, pid in enumerate(pitcher_ids):
        player_box = _extract_player_from_team_box(team_box, pid)
        if not player_box:
            continue
        pitching = player_box.get("stats", {}).get("pitching", {}) or {}
        if not pitching:
            continue
        has_started_flag = "gamesStarted" in pitching
        is_starter = safe_int(pitching.get("gamesStarted")) > 0 if has_started_flag else idx == 0
        if is_starter:
            continue

        outs = innings_to_outs(pitching.get("inningsPitched"))
        hits = _pitching_stat(player_box, "hits")
        runs = _pitching_stat(player_box, "runs")
        earned_runs = _pitching_stat(player_box, "earnedRuns")
        walks = _pitching_stat(player_box, "baseOnBalls")
        strikeouts = _pitching_stat(player_box, "strikeOuts")
        home_runs = _pitching_stat(player_box, "homeRuns")
        pitches = safe_int(pitching.get("numberOfPitches") or pitching.get("pitchesThrown"))
        if not any([outs, hits, runs, earned_runs, walks, strikeouts, home_runs, pitches]):
            continue

        rows.append(
            {
                "date": game_date,
                "player_id": pid,
                "name": player_box.get("person", {}).get("fullName", ""),
                "outs": outs,
                "hits": hits,
                "runs": runs,
                "earned_runs": earned_runs,
                "walks": walks,
                "strikeouts": strikeouts,
                "home_runs": home_runs,
                "pitches": pitches,
            }
        )
    return rows

def bullpen_arm_availability_label(days_rest: int | None, last_pitches: int, apps_last_two_days: int) -> str:
    if days_rest is None:
        return "unknown"
    if days_rest >= 2:
        return "available"
    if days_rest == 1 and last_pitches <= 20 and apps_last_two_days <= 1:
        return "likely available"
    if days_rest == 1 and last_pitches <= 30 and apps_last_two_days <= 1:
        return "watch"
    return "taxed"

def bullpen_arm_form_label(outs: int, earned_runs: int, hits: int, walks: int) -> str:
    if outs == 0:
        return "traffic"
    era = _rate_per_nine(earned_runs, outs)
    whip = _whip(hits, walks, outs)
    bb9 = _rate_per_nine(walks, outs)
    if pd.notna(era) and pd.notna(whip) and era <= 2.75 and whip <= 1.10:
        return "sharp"
    if (pd.notna(era) and era >= 5.00) or (pd.notna(whip) and whip >= 1.50) or (pd.notna(bb9) and bb9 >= 4.50):
        return "struggling"
    return "stable"

@st.cache_data(ttl=1800)
def build_bullpen_arms(team_logs: pd.DataFrame, team_name: str, selected_date: Any, n: int = 5) -> list[dict]:
    selected_ts = pd.Timestamp(selected_date).normalize()
    team_games = (
        team_logs[(team_logs["team"] == team_name) & (team_logs["date"] < selected_ts)]
        .sort_values(["date", "game_id"])
        .tail(n)
    )
    appearances = []
    for game_row in team_games.to_dict("records"):
        game_id = safe_int(game_row.get("game_id"))
        if not game_id:
            continue
        game_date = pd.Timestamp(game_row.get("date")).strftime("%Y-%m-%d")
        box = fetch_game_boxscore(game_id)
        team_box = _team_box_for_name(box, team_name)
        if not team_box:
            continue
        appearances.extend(_bullpen_reliever_appearances_from_box(team_box, game_date))

    grouped: dict[str, dict] = {}
    for app in appearances:
        key = str(app.get("player_id") or normalize_name(app.get("name")))
        if key not in grouped:
            grouped[key] = {
                "team": team_name,
                "player_id": app.get("player_id"),
                "name": app.get("name"),
                "appearances": 0,
                "outs": 0,
                "hits": 0,
                "runs": 0,
                "earned_runs": 0,
                "walks": 0,
                "strikeouts": 0,
                "home_runs": 0,
                "total_pitches": 0,
                "dates": [],
                "last_pitches": 0,
            }
        item = grouped[key]
        item["appearances"] += 1
        item["outs"] += safe_int(app.get("outs"))
        item["hits"] += safe_int(app.get("hits"))
        item["runs"] += safe_int(app.get("runs"))
        item["earned_runs"] += safe_int(app.get("earned_runs"))
        item["walks"] += safe_int(app.get("walks"))
        item["strikeouts"] += safe_int(app.get("strikeouts"))
        item["home_runs"] += safe_int(app.get("home_runs"))
        item["total_pitches"] += safe_int(app.get("pitches"))
        item["dates"].append(str(app.get("date")))

    arms = []
    for item in grouped.values():
        dates = sorted(pd.to_datetime(item.pop("dates"), errors="coerce").dropna())
        last_date = dates[-1] if dates else None
        days_rest = int((selected_ts - last_date.normalize()).days) if last_date is not None else None
        apps_last_two_days = sum(1 for date in dates if (selected_ts - date.normalize()).days <= 2)
        last_date_label = last_date.strftime("%Y-%m-%d") if last_date is not None else "n/a"
        last_pitches = 0
        if last_date is not None:
            last_date_text = last_date.strftime("%Y-%m-%d")
            last_pitches = sum(safe_int(app.get("pitches")) for app in appearances if app.get("name") == item.get("name") and app.get("date") == last_date_text)
        outs = safe_int(item.get("outs"))
        hits = safe_int(item.get("hits"))
        walks = safe_int(item.get("walks"))
        earned_runs = safe_int(item.get("earned_runs"))
        item.update(
            {
                "last_used": last_date_label,
                "days_rest": days_rest,
                "apps_last_two_days": apps_last_two_days,
                "last_pitches": last_pitches,
                "era": _rate_per_nine(earned_runs, outs),
                "whip": _whip(hits, walks, outs),
                "bb9": _rate_per_nine(walks, outs),
                "k9": _rate_per_nine(safe_int(item.get("strikeouts")), outs),
                "availability": bullpen_arm_availability_label(days_rest, last_pitches, apps_last_two_days),
                "form": bullpen_arm_form_label(outs, earned_runs, hits, walks),
            }
        )
        arms.append(item)

    availability_order = {"available": 0, "likely available": 1, "watch": 2, "taxed": 3, "unknown": 4}
    form_order = {"sharp": 0, "stable": 1, "struggling": 2, "traffic": 3}
    return sorted(
        arms,
        key=lambda row: (
            availability_order.get(row.get("availability"), 9),
            form_order.get(row.get("form"), 9),
            -(row.get("outs") or 0),
        ),
    )

def bullpen_comparison_df(team_logs: pd.DataFrame, selected_date: Any, n: int = 5) -> pd.DataFrame:
    rows = []
    for team_name in sorted(team_logs["team"].dropna().unique()):
        bullpen = build_bullpen_card(team_logs, team_name, selected_date, n)
        arms = build_bullpen_arms(team_logs, team_name, selected_date, n)
        available_count = sum(1 for arm in arms if arm.get("availability") in {"available", "likely available"})
        watch_count = sum(1 for arm in arms if arm.get("availability") in {"watch", "taxed"})
        rows.append(
            {
                "Team": team_name,
                "Status": _friendly_signal_label(str(bullpen.get("label", "n/a"))),
                "Games": safe_int(bullpen.get("games")),
                "IP": format_outs_as_ip(safe_int(bullpen.get("outs"))),
                "ERA": safe_float(bullpen.get("era")),
                "WHIP": safe_float(bullpen.get("whip")),
                "R/G": safe_float(bullpen.get("runs_per_game")),
                "BB/9": safe_float(bullpen.get("bb9")),
                "K/9": safe_float(bullpen.get("k9")),
                "HR/9": safe_float(bullpen.get("hr9")),
                "Pitchers Used": safe_int(bullpen.get("pitchers_used")),
                "Recent Arms": len(arms),
                "Likely Available": available_count,
                "Watch/Taxed": watch_count,
            }
        )
    return pd.DataFrame(rows)

def sort_bullpen_comparison(df: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    if df.empty:
        return df
    label_order = {"High traffic": 0, "Run risk": 1, "Neutral": 2, "Steady": 3, "No data": 4}
    sort_df = df.copy()
    if sort_mode == "Best ERA":
        return sort_df.sort_values(["ERA", "WHIP"], ascending=[True, True], na_position="last")
    if sort_mode == "Worst ERA":
        return sort_df.sort_values(["ERA", "WHIP"], ascending=[False, False], na_position="last")
    if sort_mode == "Most Available":
        return sort_df.sort_values(["Likely Available", "Watch/Taxed", "ERA"], ascending=[False, True, True], na_position="last")
    sort_df["_risk_order"] = sort_df["Status"].map(label_order).fillna(9)
    return sort_df.sort_values(["_risk_order", "ERA", "WHIP"], ascending=[True, False, False], na_position="last").drop(columns=["_risk_order"])

def bullpen_arms_display_df(arms: list[dict]) -> pd.DataFrame:
    rows = []
    for arm in arms:
        rows.append(
            {
                "Pitcher": arm.get("name", ""),
                "Status": str(arm.get("availability", "")).title(),
                "Form": str(arm.get("form", "")).title(),
                "Last Used": arm.get("last_used", "n/a"),
                "Rest": "n/a" if arm.get("days_rest") is None else f'{safe_int(arm.get("days_rest"))}d',
                "Last Pitches": safe_int(arm.get("last_pitches")),
                "App": safe_int(arm.get("appearances")),
                "IP": format_outs_as_ip(safe_int(arm.get("outs"))),
                "ERA": safe_float(arm.get("era")),
                "WHIP": safe_float(arm.get("whip")),
                "BB/9": safe_float(arm.get("bb9")),
                "K/9": safe_float(arm.get("k9")),
            }
        )
    return pd.DataFrame(rows)

def ladder_label(last3: float, last7: float, season: float) -> str:
    if pd.isna(last3) or pd.isna(last7) or pd.isna(season):
        return "n/a"
    if last3 > last7 > season:
        return "building"
    if last7 > season and last3 >= last7:
        return "uptrend"
    if last7 > season and last3 < last7:
        return "cooling"
    if last3 < last7 < season:
        return "downtrend"
    if last3 > season or last7 > season:
        return "mixed positive"
    return "below baseline"

def combine_offense_signal(ops_label: str, runs_label: str) -> str:
    if ops_label == "building" and runs_label == "building":
        return "strong"
    if ops_label in {"building", "uptrend"} and runs_label in {"building", "uptrend"}:
        return "good"
    if "cooling" in {ops_label, runs_label}:
        return "cooling"
    if ops_label in {"below baseline", "downtrend"} and runs_label in {"below baseline", "downtrend"}:
        return "weak"
    return "mixed"

def pitcher_recent_label(pitcher: dict) -> str:
    era = pitcher.get("era")
    whip = pitcher.get("whip")
    last3_era = pitcher.get("last3_era")
    last3_whip = pitcher.get("last3_whip")
    if pd.isna(era) or pd.isna(whip) or pd.isna(last3_era) or pd.isna(last3_whip):
        return "n/a"
    worse = 0
    better = 0
    if last3_era >= era + 0.50:
        worse += 1
    elif last3_era <= era - 0.50:
        better += 1
    if last3_whip >= whip + 0.10:
        worse += 1
    elif last3_whip <= whip - 0.10:
        better += 1
    if worse >= 1:
        return "worse than season"
    if better >= 1:
        return "better than season"
    return "near season"

def metric_band(value: Any, bands: list[tuple[float, str, str]]) -> dict:
    value_f = safe_float(value)
    if pd.isna(value_f):
        return {"label": "n/a", "tone": "neutral"}
    for threshold, label, tone in bands:
        if value_f <= threshold:
            return {"label": label, "tone": tone}
    return {"label": bands[-1][1], "tone": bands[-1][2]}

def pitcher_profile_signal(pitcher: dict) -> dict:
    h9 = safe_float((pitcher or {}).get("h9"))
    bb9 = safe_float((pitcher or {}).get("bb9"))
    k9 = safe_float((pitcher or {}).get("k9"))
    hr9 = safe_float((pitcher or {}).get("hr9"))
    whip = safe_float((pitcher or {}).get("whip"))

    contact = metric_band(
        h9,
        [
            (7.50, "limits hits", "good"),
            (8.80, "average contact", "neutral"),
            (10.00, "contact risk", "warning"),
            (float("inf"), "heavy contact", "bad"),
        ],
    )
    command = metric_band(
        bb9,
        [
            (2.25, "strong command", "good"),
            (3.25, "average command", "neutral"),
            (4.25, "walk risk", "warning"),
            (float("inf"), "wild profile", "bad"),
        ],
    )
    strikeouts = metric_band(
        -k9 if pd.notna(k9) else float("nan"),
        [
            (-9.50, "plus K buffer", "good"),
            (-8.00, "average K buffer", "neutral"),
            (-6.50, "low K buffer", "warning"),
            (float("inf"), "pitch-to-contact", "bad"),
        ],
    )
    power = metric_band(
        hr9,
        [
            (0.85, "HR suppressor", "good"),
            (1.15, "average power", "neutral"),
            (1.45, "HR risk", "warning"),
            (float("inf"), "power damage", "bad"),
        ],
    )
    traffic = metric_band(
        whip,
        [
            (1.15, "clean traffic", "good"),
            (1.30, "stable traffic", "neutral"),
            (1.50, "traffic watch", "warning"),
            (float("inf"), "heavy traffic", "bad"),
        ],
    )

    components = {
        "Contact": {**contact, "value": h9, "stat": "H/9"},
        "Command": {**command, "value": bb9, "stat": "BB/9"},
        "K buffer": {**strikeouts, "value": k9, "stat": "K/9"},
        "Power": {**power, "value": hr9, "stat": "HR/9"},
        "Traffic": {**traffic, "value": whip, "stat": "WHIP"},
    }

    bad_count = sum(1 for item in components.values() if item.get("tone") == "bad")
    warning_count = sum(1 for item in components.values() if item.get("tone") == "warning")
    good_count = sum(1 for item in components.values() if item.get("tone") == "good")

    if power["tone"] in {"bad", "warning"} and traffic["tone"] in {"bad", "warning"}:
        label = "power and traffic risk"
        tone = "bad" if bad_count else "warning"
    elif command["tone"] in {"bad", "warning"}:
        label = "command risk"
        tone = "bad" if command["tone"] == "bad" else "warning"
    elif contact["tone"] in {"bad", "warning"}:
        label = "contact risk"
        tone = "bad" if contact["tone"] == "bad" else "warning"
    elif good_count >= 3 and warning_count == 0 and bad_count == 0:
        label = "run prevention profile"
        tone = "good"
    elif power["tone"] == "good" and contact["tone"] == "good":
        label = "contact suppressor"
        tone = "good"
    else:
        label = "balanced profile"
        tone = "neutral"

    return {"label": label, "tone": tone, "components": components}

def team_last5_record(team_logs: pd.DataFrame, team_name: str) -> dict:
    team_df = team_logs[team_logs["team"] == team_name].sort_values(["date", "game_id"]).tail(5)
    wins = 0
    losses = 0
    ties = 0
    form = []
    for row in team_df.to_dict("records"):
        runs = row.get("runs")
        opponent_runs = row.get("opponent_runs")
        if pd.isna(runs) or pd.isna(opponent_runs):
            continue
        if runs > opponent_runs:
            wins += 1
            form.append("W")
        elif runs < opponent_runs:
            losses += 1
            form.append("L")
        else:
            ties += 1
            form.append("T")
    label = f"{wins}-{losses}" if ties == 0 else f"{wins}-{losses}-{ties}"
    return {"wins": wins, "losses": losses, "ties": ties, "label": label, "form": "".join(form), "games": len(form)}

def team_snapshot(team_logs: pd.DataFrame, team_name: str) -> dict:
    team_df = team_logs[team_logs["team"] == team_name].sort_values("date")
    if team_df.empty:
        return {"team": team_name, "last5_record": {"label": "0-0", "form": "", "games": 0}}

    runs_series = team_df["runs"] if "runs" in team_df.columns else pd.Series(dtype=float)

    season_ops = season_metric(team_df, "ops")
    last15_ops = trailing_team_metric(team_df, "ops", 15)
    last7_ops = trailing_team_metric(team_df, "ops", 7)
    last3_ops = trailing_team_metric(team_df, "ops", 3)
    season_obp = season_metric(team_df, "obp")
    last15_obp = trailing_team_metric(team_df, "obp", 15)
    last7_obp = trailing_team_metric(team_df, "obp", 7)
    last3_obp = trailing_team_metric(team_df, "obp", 3)

    season_runs = float(runs_series.dropna().mean()) if not runs_series.dropna().empty else float("nan")
    last15_runs = trailing_average(runs_series, 15)
    last7_runs = trailing_average(runs_series, 7)
    last3_runs = trailing_average(runs_series, 3)

    ops_label = ladder_label(last3_ops, last7_ops, season_ops)
    obp_label = ladder_label(last3_obp, last7_obp, season_obp)
    runs_label = ladder_label(last3_runs, last7_runs, season_runs)
    offense_signal = combine_offense_signal(ops_label, runs_label)
    batting_profile = build_batting_profile(team_df, 7)
    batting_profiles = {
        "last3": build_batting_profile(team_df, 3),
        "last7": batting_profile,
        "last15": build_batting_profile(team_df, 15),
    }

    return {
        "team": team_name,
        "season_ops": season_ops,
        "last15_ops": last15_ops,
        "last7_ops": last7_ops,
        "last3_ops": last3_ops,
        "season_obp": season_obp,
        "last15_obp": last15_obp,
        "last7_obp": last7_obp,
        "last3_obp": last3_obp,
        "season_runs": season_runs,
        "last15_runs": last15_runs,
        "last7_runs": last7_runs,
        "last3_runs": last3_runs,
        "ops_label": ops_label,
        "obp_label": obp_label,
        "runs_label": runs_label,
        "offense_signal": offense_signal,
        "batting_profile": batting_profile,
        "batting_profiles": batting_profiles,
        "last5_record": team_last5_record(team_logs, team_name),
    }

def _split_context_metric(team_df: pd.DataFrame) -> dict:
    if team_df.empty:
        return {"games": 0, "ops": float("nan"), "obp": float("nan"), "runs": float("nan")}
    runs_series = team_df["runs"] if "runs" in team_df.columns else pd.Series(dtype=float)
    return {
        "games": int(len(team_df)),
        "ops": season_metric(team_df, "ops"),
        "obp": season_metric(team_df, "obp"),
        "runs": float(runs_series.dropna().mean()) if not runs_series.dropna().empty else float("nan"),
    }

def home_away_snapshot(team_logs: pd.DataFrame, team_name: str, context: str) -> dict:
    team_df = team_logs[team_logs["team"] == team_name].sort_values("date")
    has_split_data = "home_away" in team_df.columns and team_df["home_away"].isin(["home", "away"]).any()
    if team_df.empty or not has_split_data:
        return {
            "team": team_name,
            "context": context,
            "has_data": False,
            "overall": _split_context_metric(team_df),
            "home": {"games": 0, "ops": float("nan"), "obp": float("nan"), "runs": float("nan")},
            "away": {"games": 0, "ops": float("nan"), "obp": float("nan"), "runs": float("nan")},
            "context_split": {"games": 0, "ops": float("nan"), "obp": float("nan"), "runs": float("nan")},
            "ops_edge": float("nan"),
            "obp_edge": float("nan"),
            "runs_edge": float("nan"),
            "label": "update needed",
        }

    overall = _split_context_metric(team_df)
    home = _split_context_metric(team_df[team_df["home_away"] == "home"])
    away = _split_context_metric(team_df[team_df["home_away"] == "away"])
    context_split = home if context == "home" else away
    ops_edge = context_split["ops"] - overall["ops"] if pd.notna(context_split["ops"]) and pd.notna(overall["ops"]) else float("nan")
    obp_edge = context_split["obp"] - overall["obp"] if pd.notna(context_split["obp"]) and pd.notna(overall["obp"]) else float("nan")
    runs_edge = context_split["runs"] - overall["runs"] if pd.notna(context_split["runs"]) and pd.notna(overall["runs"]) else float("nan")
    if pd.isna(ops_edge) and pd.isna(runs_edge):
        label = "n/a"
    elif (pd.notna(ops_edge) and ops_edge >= 0.035) or (pd.notna(runs_edge) and runs_edge >= 0.35):
        label = "context boost"
    elif (pd.notna(ops_edge) and ops_edge <= -0.035) or (pd.notna(runs_edge) and runs_edge <= -0.35):
        label = "context drag"
    else:
        label = "neutral"

    return {
        "team": team_name,
        "context": context,
        "has_data": True,
        "overall": overall,
        "home": home,
        "away": away,
        "context_split": context_split,
        "ops_edge": ops_edge,
        "obp_edge": obp_edge,
        "runs_edge": runs_edge,
        "label": label,
    }

def summarize_lineup_strength(lineup_rows: list[dict]) -> dict:
    hot = [r for r in lineup_rows if r.get("L7 Form") == "hot"]
    great = [r for r in lineup_rows if r.get("Season Tier") == "great"]
    l7_great = [r for r in lineup_rows if r.get("L7 Form") in {"great", "hot"}]
    onbase = [r for r in lineup_rows if pd.notna(r.get("OBP")) and r["OBP"] >= 0.340]
    weak = [r for r in lineup_rows if r.get("Season Tier") == "weak"]
    return {
        "hot_count": len(hot),
        "great_count": len(great),
        "l7_great_count": len(l7_great),
        "onbase_count": len(onbase),
        "weak_count": len(weak),
    }


def format_lineup_cell(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)

def render_lineup_html_table(lineup_rows: list[dict]) -> str:
    headers = [
        ("Spot", "4%"),
        ("Player", "21%"),
        ("Pos", "4%"),
        ("B", "4%"),
        ("AVG", "8%"),
        ("OBP", "8%"),
        ("OPS", "8%"),
        ("Season", "9%"),
        ("L7 OPS", "8%"),
        ("L7 Form", "9%"),
        ("HR", "5%"),
        ("BB", "5%"),
        ("SO", "5%"),
    ]
    head_html = "".join(
        f'<th style="width:{width}; text-align:left; padding:0.34rem 0.12rem; font-size:0.63rem; color:#666; border-bottom:1px solid #e5e5e5; white-space:nowrap;">{label}</th>'
        for label, width in headers
    )

    body_rows = []
    for row in lineup_rows:
        season_tier = row.get("Season Tier", "")
        l7_form = row.get("L7 Form", "")

        def badge(value: str) -> str:
            bg = "#e8f5eb" if value in {"great", "hot"} else ("#fdeaea" if value == "weak" else "#f1f1f1")
            color = "#17803d" if value in {"great", "hot"} else ("#c23b36" if value == "weak" else "#666")
            return f'<span style="display:inline-block; padding:0.12rem 0.3rem; border-radius:999px; background:{bg}; color:{color}; font-size:0.62rem; font-weight:650; line-height:1.1;">{value}</span>'

        cells = [
            (row.get("Spot", ""), "white-space:nowrap;"),
            (row.get("Player", ""), "white-space:normal; word-break:normal; overflow-wrap:anywhere; font-weight:650;"),
            (row.get("Pos", ""), "white-space:nowrap;"),
            (row.get("Bats", ""), "white-space:nowrap;"),
            (format_lineup_cell(row.get("AVG"), 3), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (format_lineup_cell(row.get("OBP"), 3), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (format_lineup_cell(row.get("OPS"), 3), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (badge(season_tier), "white-space:nowrap;"),
            (format_lineup_cell(row.get("Last7 OPS"), 3), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (badge(l7_form), "white-space:nowrap;"),
            (row.get("HR", ""), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (row.get("BB", ""), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
            (row.get("SO", ""), "white-space:nowrap; font-variant-numeric:tabular-nums;"),
        ]
        row_html = "<tr>" + "".join(
            f'<td style="padding:0.34rem 0.12rem; font-size:0.66rem; border-bottom:1px solid #f0f0f0; vertical-align:middle; line-height:1.2; {style}">{cell}</td>'
            for cell, style in cells
        ) + "</tr>"
        body_rows.append(row_html)

    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.75rem 0.55rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; overflow-x:auto; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <table style="width:100%; table-layout:fixed; border-collapse:collapse;">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>
    """

def render_hitter_consistency_table(lineup_rows: list[dict], team_name: str, limit: int | None = None) -> str:
    rows = []
    for row in lineup_rows:
        profile = row.get("Hit Consistency", {}) or {}
        windows = profile.get("windows", {}) or {}
        if not windows:
            continue
        rows.append((safe_float(profile.get("score")), row, profile, windows))
    rows = sorted(rows, key=lambda item: (item[0] if pd.notna(item[0]) else -999), reverse=True)
    if limit:
        rows = rows[:limit]

    if not rows:
        return f"""
        <div style="background:#ffffff; color:#172033; padding:0.8rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
          <div style="font-weight:800; margin-bottom:0.25rem;">{team_name}</div>
          <div style="color:#667085; font-size:0.82rem;">No hitter consistency data available.</div>
        </div>
        """

    tone_styles = {
        "stable": ("#e8f5eb", "#17803d"),
        "heating": ("#e6f4f1", "#0f766e"),
        "cooling": ("#fff3e6", "#9a5a00"),
        "volatile": ("#fff3e6", "#9a5a00"),
        "cold": ("#fdeaea", "#c23b36"),
        "neutral": ("#f1f5f9", "#334155"),
    }

    def avg_cell(split: dict) -> str:
        avg = format_lineup_cell(split.get("avg"), 3)
        hits = safe_int(split.get("h"))
        ab = safe_int(split.get("ab"))
        games = safe_int(split.get("games"))
        return (
            f'<div style="font-weight:850; white-space:nowrap; font-variant-numeric:tabular-nums;">{avg}</div>'
            f'<div style="font-size:0.62rem; color:#667085; white-space:nowrap; font-variant-numeric:tabular-nums;">{hits}/{ab}</div>'
            f'<div style="font-size:0.6rem; color:#98a2b3; white-space:nowrap; font-variant-numeric:tabular-nums;">{games}g</div>'
        )

    body = []
    for _, row, profile, windows in rows:
        label = str(profile.get("label", "n/a"))
        tone = str(profile.get("tone", "neutral"))
        bg, color = tone_styles.get(tone, tone_styles["neutral"])
        hpg_values = [safe_float(w.get("hpg")) for w in windows.values()]
        hpg_values = [v for v in hpg_values if pd.notna(v)]
        hpg_floor = min(hpg_values) if hpg_values else float("nan")
        note = profile.get("note", "")
        badge = f'<span style="display:inline-block; padding:0.13rem 0.38rem; border-radius:999px; background:{bg}; color:{color}; font-size:0.62rem; font-weight:800; line-height:1.15;">{label}</span>'
        trend_cell = (
            f'{badge}'
            f'<div style="font-size:0.61rem; color:#667085; line-height:1.15; margin-top:0.18rem;">{note}</div>'
            f'<div style="font-size:0.6rem; color:#98a2b3; margin-top:0.12rem;">floor {format_lineup_cell(hpg_floor, 2)} H/G</div>'
        )
        cells = [
            (row.get("Spot", ""), "width:5%; white-space:nowrap;"),
            (row.get("Player", ""), "width:21%; font-weight:750; overflow-wrap:anywhere;"),
            (avg_cell(windows.get("season", {})), "width:13%;"),
            (avg_cell(windows.get("last30", {})), "width:13%;"),
            (avg_cell(windows.get("last15", {})), "width:13%;"),
            (avg_cell(windows.get("last7", {})), "width:13%;"),
            (trend_cell, "width:22%;"),
        ]
        body.append(
            "<tr>"
            + "".join(
                f'<td style="padding:0.38rem 0.16rem; border-bottom:1px solid #f0f0f0; vertical-align:middle; font-size:0.67rem; line-height:1.16; {style}">{cell}</td>'
                for cell, style in cells
            )
            + "</tr>"
        )

    headers = [
        ("#", "5%"),
        ("Player", "21%"),
        ("Season", "13%"),
        ("30D", "13%"),
        ("15D", "13%"),
        ("7D", "13%"),
        ("Trend", "22%"),
    ]
    head_html = "".join(
        f'<th style="width:{width}; text-align:left; padding:0.36rem 0.16rem; font-size:0.63rem; color:#667085; border-bottom:1px solid #e5e5e5; white-space:nowrap;">{label}</th>'
        for label, width in headers
    )
    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.75rem 0.55rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; overflow-x:auto; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="font-size:0.95rem; font-weight:800; margin-bottom:0.12rem;">{team_name}</div>
      <div style="font-size:0.72rem; color:#667085; margin-bottom:0.45rem;">Batting average trend from completed MLB game logs.</div>
      <table style="width:100%; table-layout:fixed; border-collapse:collapse;">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>
    """

def render_context_production_table(rows: list[dict], team_name: str, context: str) -> str:
    context_label = "home" if context == "home" else "away"
    if not rows:
        return f"""
        <div style="background:#ffffff; color:#667085; padding:0.85rem 0.9rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
          <div style="font-size:1rem; font-weight:800; color:#172033; margin-bottom:0.25rem;">{team_name}</div>
          No last-5 {context_label} production found for the listed hitters.
        </div>
        """

    body = []
    for row in rows:
        body.append(
            "<tr>"
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; font-weight:700;">{row.get("Player", "")}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-variant-numeric:tabular-nums;">{row.get("games", 0)}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-weight:800; font-variant-numeric:tabular-nums;">{row.get("production", 0)}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-variant-numeric:tabular-nums;">{row.get("rbi", 0)}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-variant-numeric:tabular-nums;">{row.get("runs", 0)}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-variant-numeric:tabular-nums;">{row.get("hits", 0)}</td>'
            f'<td style="padding:0.42rem 0.28rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-variant-numeric:tabular-nums;">{row.get("tb", 0)}</td>'
            "</tr>"
        )

    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.85rem 0.9rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.6rem; margin-bottom:0.5rem;">
        <div style="font-size:1rem; font-weight:800;">{team_name}</div>
        <div style="display:inline-block; padding:0.16rem 0.48rem; border-radius:999px; background:#f1f5f9; color:#334155; font-size:0.72rem; font-weight:700;">last 5 {context_label}</div>
      </div>
      <table style="width:100%; border-collapse:collapse; font-size:0.78rem;">
        <thead>
          <tr>
            <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Player</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">G</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">R+RBI</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">RBI</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">R</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">H</th>
            <th style="text-align:left; padding:0.38rem 0.28rem; border-bottom:1px solid #e5e5e5; color:#666; white-space:nowrap;">TB</th>
          </tr>
        </thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>
    """

def render_batting_profile_card(profile: dict) -> str:
    profile = profile or {}
    recent = profile.get("recent", {}) or {}
    tone = profile.get("tone", "neutral")
    tone_styles = {
        "power": ("#eef2ff", "#3730a3"),
        "contact": ("#e8f5eb", "#17803d"),
        "balanced": ("#e6f4f1", "#0f766e"),
        "volatile": ("#fff3e6", "#9a5a00"),
        "cold": ("#fdeaea", "#c23b36"),
        "neutral": ("#f1f5f9", "#334155"),
    }
    bg, color = tone_styles.get(tone, tone_styles["neutral"])

    def pct(value: Any) -> str:
        value = safe_float(value)
        return "n/a" if pd.isna(value) else f"{value:.1%}"

    return f"""
    <div style="background:#fbfcfd; border:1px solid #e5ebf2; border-radius:8px; padding:0.65rem 0.7rem; margin:0.2rem 0 0.75rem;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.55rem; margin-bottom:0.45rem;">
        <div>
          <div style="font-size:0.72rem; color:#667085; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Batting profile - last 7</div>
          <div style="font-size:0.8rem; color:#475467; line-height:1.35; margin-top:0.14rem;">{profile.get("note", "No profile available.")}</div>
        </div>
        <div style="display:inline-block; padding:0.16rem 0.5rem; border-radius:999px; background:{bg}; color:{color}; font-size:0.72rem; font-weight:800; white-space:nowrap;">{profile.get("label", "n/a")}</div>
      </div>
      <div style="display:grid; grid-template-columns:repeat(6,1fr); gap:0.45rem;">
        <div><div style="font-size:0.66rem; color:#777;">AVG</div><div style="font-size:0.96rem; font-weight:750;">{format_stat(recent.get("avg"), digits=3)}</div></div>
        <div><div style="font-size:0.66rem; color:#777;">SLG</div><div style="font-size:0.96rem; font-weight:750;">{format_stat(recent.get("slg"), digits=3)}</div></div>
        <div><div style="font-size:0.66rem; color:#777;">ISO</div><div style="font-size:0.96rem; font-weight:750;">{format_stat(recent.get("iso"), digits=3)}</div></div>
        <div><div style="font-size:0.66rem; color:#777;">K%</div><div style="font-size:0.96rem; font-weight:750;">{pct(recent.get("k_pct"))}</div></div>
        <div><div style="font-size:0.66rem; color:#777;">BB%</div><div style="font-size:0.96rem; font-weight:750;">{pct(recent.get("bb_pct"))}</div></div>
        <div><div style="font-size:0.66rem; color:#777;">XBH%</div><div style="font-size:0.96rem; font-weight:750;">{pct(recent.get("xbh_pct"))}</div></div>
      </div>
    </div>
    """

def momentum_stat_value(value: Any) -> float | None:
    value = safe_float(value)
    if pd.isna(value):
        return None
    return value

def format_momentum_stat(value: Any, digits: int = 3) -> str:
    value = momentum_stat_value(value)
    if value is None:
        return "n/a"
    text = f"{value:.{digits}f}"
    if digits == 3 and 0 <= value < 1:
        return text[1:]
    return text

def format_signed_momentum_stat(value: Any, digits: int = 3) -> str:
    value = momentum_stat_value(value)
    if value is None:
        return "n/a"
    sign = "+" if value > 0 else ("-" if value < 0 else "")
    magnitude = abs(value)
    text = f"{magnitude:.{digits}f}"
    if digits == 3 and magnitude < 1:
        text = text[1:]
    return f"{sign}{text}"

def team_abbreviation(team_name: Any) -> str:
    team = str(team_name or "").strip()
    if team in TEAM_ABBREVIATIONS:
        return TEAM_ABBREVIATIONS[team]
    words = [word for word in team.replace(".", "").split() if word]
    if not words:
        return "MLB"
    if len(words) == 1:
        return words[0][:3].upper()
    return "".join(word[0] for word in words[-2:]).upper()[:3]

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    value = str(hex_color or "").strip().lstrip("#")
    if len(value) != 6:
        return f"rgba(45, 212, 191, {alpha:.2f})"
    try:
        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)
    except ValueError:
        return f"rgba(45, 212, 191, {alpha:.2f})"
    return f"rgba({red}, {green}, {blue}, {alpha:.2f})"

def h2h_format_value(value: Any, value_type: str, digits: int) -> str:
    numeric = momentum_stat_value(value)
    if numeric is None:
        return "n/a"
    if value_type == "pct":
        return f"{numeric:.1%}"
    return format_momentum_stat(numeric, digits=digits)

def h2h_trend_html(value: Any, baseline: Any, lower_is_better: bool = False, tolerance: float = 0.0) -> str:
    current = momentum_stat_value(value)
    base = momentum_stat_value(baseline)
    if current is None or base is None or abs(current - base) <= tolerance:
        return '<span class="h2h-stat__trend h2h-stat__trend--neutral">&bull;</span>'
    improved = current < base if lower_is_better else current > base
    arrow = "&darr;" if current < base else "&uarr;"
    tone = "good" if improved else "bad"
    return f'<span class="h2h-stat__trend h2h-stat__trend--{tone}">{arrow}</span>'

def h2h_value_html(value: Any, baseline: Any, value_type: str, digits: int, side: str, lower_is_better: bool, tolerance: float) -> str:
    trend = h2h_trend_html(value, baseline, lower_is_better=lower_is_better, tolerance=tolerance)
    text = html.escape(h2h_format_value(value, value_type, digits))
    if side == "home":
        inner = f"<span>{text}</span>{trend}"
    else:
        inner = f"{trend}<span>{text}</span>"
    return f'<div class="h2h-stat__value h2h-stat__value--{side}">{inner}</div>'

def h2h_bar_width(value: Any, scale: float) -> float:
    numeric = momentum_stat_value(value)
    if numeric is None or numeric <= 0 or not scale:
        return 0.0
    return max(3.0, min(100.0, (numeric / scale) * 100))

def h2h_metric_tone(stat_key: str, value: Any, lower_is_better: bool = False) -> str:
    numeric = momentum_stat_value(value)
    if numeric is None:
        return "neutral"
    key = str(stat_key or "").lower()

    if key == "ops":
        if numeric < 0.700:
            return "weak"
        if numeric <= 0.760:
            return "average"
        return "strong"
    if key == "obp":
        if numeric < 0.310:
            return "weak"
        if numeric <= 0.330:
            return "average"
        return "strong"
    if key == "runs_per_game":
        if numeric < 4.00:
            return "weak"
        if numeric <= 5.00:
            return "average"
        return "strong"
    if key == "avg":
        if numeric < 0.235:
            return "weak"
        if numeric <= 0.265:
            return "average"
        return "strong"
    if key == "hr_per_game":
        if numeric < 0.80:
            return "weak"
        if numeric <= 1.20:
            return "average"
        return "strong"
    if key == "walks_drawn":
        if numeric < 2.80:
            return "weak"
        if numeric <= 4.00:
            return "average"
        return "strong"
    if key == "batting_strikeouts":
        if numeric < 7.00:
            return "strong"
        if numeric <= 9.50:
            return "average"
        return "weak"
    if key == "runs_allowed_per_game":
        if numeric <= 3.70:
            return "strong"
        if numeric <= 4.75:
            return "average"
        return "weak"
    if key == "era":
        if numeric <= 3.60:
            return "strong"
        if numeric <= 4.50:
            return "average"
        return "weak"
    if key == "whip":
        if numeric <= 1.24:
            return "strong"
        if numeric <= 1.38:
            return "average"
        return "weak"
    if key == "k9":
        if numeric >= 9.00:
            return "strong"
        if numeric >= 7.50:
            return "average"
        return "weak"
    if key in {"bb9", "h9", "hr9"}:
        limits = {
            "bb9": (3.00, 3.80),
            "h9": (8.00, 9.20),
            "hr9": (0.90, 1.25),
        }
        strong_limit, average_limit = limits[key]
        if numeric <= strong_limit:
            return "strong"
        if numeric <= average_limit:
            return "average"
        return "weak"
    if lower_is_better:
        return "strong"
    return "neutral"

def h2h_team_header(snapshot: dict, side: str) -> str:
    team = str((snapshot or {}).get("team", "Team"))
    team_color = TEAM_COLORS.get(team, "#2dd4bf")
    glow = hex_to_rgba(team_color, 0.18)
    record = (snapshot or {}).get("last5_record", {}) or {}
    profile = ((snapshot or {}).get("batting_profile", {}) or {})
    record_text = f"L5 {record.get('label', '0-0')}"
    form = str(record.get("form", ""))
    if form:
        record_text += f" {form}"
    profile_label = str(profile.get("label", "Profile n/a"))
    return compact_html(f"""
    <div class="h2h-team h2h-team--{side}" style="--team-color:{html.escape(team_color)}; --team-glow:{html.escape(glow)};">
      <div class="h2h-team__logo">{html.escape(team_abbreviation(team))}</div>
      <div class="h2h-team__body">
        <div class="h2h-team__name">{html.escape(team)}</div>
        <div class="h2h-team__meta">{html.escape(record_text)} &middot; {html.escape(profile_label)}</div>
      </div>
    </div>
    """)

def h2h_stat_row_html(
    label: str,
    sublabel: str,
    away_value: Any,
    home_value: Any,
    away_baseline: Any,
    home_baseline: Any,
    value_type: str = "number",
    digits: int = 3,
    lower_is_better: bool = False,
    tolerance: float = 0.0,
    scale_floor: float = 1.0,
    spaced: bool = False,
    stat_key: str = "",
) -> str:
    values = [momentum_stat_value(away_value), momentum_stat_value(home_value)]
    real_values = [value for value in values if value is not None]
    scale = max(scale_floor, max(real_values) * 1.08) if real_values else scale_floor
    away_width = h2h_bar_width(away_value, scale)
    home_width = h2h_bar_width(home_value, scale)
    away_tone = f" h2h-stat__fill--{h2h_metric_tone(stat_key, away_value, lower_is_better=lower_is_better)}" if stat_key else ""
    home_tone = f" h2h-stat__fill--{h2h_metric_tone(stat_key, home_value, lower_is_better=lower_is_better)}" if stat_key else ""
    spaced_class = " h2h-stat-row--spaced" if spaced else ""
    return compact_html(f"""
    <div class="h2h-stat-row{spaced_class}">
      {h2h_value_html(away_value, away_baseline, value_type, digits, "away", lower_is_better, tolerance)}
      <div class="h2h-stat__track"><div class="h2h-stat__fill h2h-stat__fill--away{away_tone}" style="width:{away_width:.1f}%;"></div></div>
      <div class="h2h-stat__center">
        <div class="h2h-stat__label">{html.escape(label)}</div>
        <div class="h2h-stat__sub">{html.escape(sublabel)}</div>
      </div>
      <div class="h2h-stat__track"><div class="h2h-stat__fill h2h-stat__fill--home{home_tone}" style="width:{home_width:.1f}%;"></div></div>
      {h2h_value_html(home_value, home_baseline, value_type, digits, "home", lower_is_better, tolerance)}
    </div>
    """)

def h2h_snapshot_window_value(snapshot: dict, window_key: str, metric: str) -> Any:
    if window_key == "season":
        return (snapshot or {}).get(f"season_{metric}")
    return (snapshot or {}).get(f"{window_key}_{metric}")

def h2h_selected_batting_profile(snapshot: dict, window_key: str) -> dict:
    profiles = (snapshot or {}).get("batting_profiles", {}) or {}
    return profiles.get(window_key) or (snapshot or {}).get("batting_profile", {}) or {}

def expected_profile_count(season_profile: dict, selected_profile: dict, key: str) -> float:
    season_games = safe_float((season_profile or {}).get("games"))
    selected_games = safe_float((selected_profile or {}).get("games"))
    season_total = safe_float((season_profile or {}).get(key))
    if pd.isna(season_games) or season_games <= 0 or pd.isna(selected_games) or pd.isna(season_total):
        return float("nan")
    return (season_total / season_games) * selected_games

def render_h2h_team_stat_sheet(
    away_snapshot: dict,
    home_snapshot: dict,
    away_pitching: dict | None = None,
    home_pitching: dict | None = None,
    window_key: str = "last7",
    window_label: str = "Last 7 games",
) -> str:
    away_profile = h2h_selected_batting_profile(away_snapshot, window_key)
    home_profile = h2h_selected_batting_profile(home_snapshot, window_key)
    away_recent = (away_profile.get("recent", {}) or {})
    home_recent = (home_profile.get("recent", {}) or {})
    away_season = (((away_snapshot or {}).get("batting_profile", {}) or {}).get("season", {}) or {})
    home_season = (((home_snapshot or {}).get("batting_profile", {}) or {}).get("season", {}) or {})
    away_period = str(window_label).lower()
    home_period = away_period

    away_games = max(1, safe_int(away_recent.get("games")))
    home_games = max(1, safe_int(home_recent.get("games")))

    hitting_rows = [
        h2h_stat_row_html(
            "Runs / Game",
            f"avg scored - {away_period}",
            h2h_snapshot_window_value(away_snapshot, window_key, "runs"),
            h2h_snapshot_window_value(home_snapshot, window_key, "runs"),
            (away_snapshot or {}).get("season_runs"),
            (home_snapshot or {}).get("season_runs"),
            value_type="number",
            digits=2,
            tolerance=0.15,
            scale_floor=7.0,
            stat_key="runs_per_game",
        ),
        h2h_stat_row_html(
            "OBP",
            "on-base percentage",
            h2h_snapshot_window_value(away_snapshot, window_key, "obp"),
            h2h_snapshot_window_value(home_snapshot, window_key, "obp"),
            (away_snapshot or {}).get("season_obp"),
            (home_snapshot or {}).get("season_obp"),
            value_type="number",
            digits=3,
            tolerance=0.010,
            scale_floor=0.380,
            stat_key="obp",
        ),
        h2h_stat_row_html(
            "OPS",
            "on-base + slugging",
            h2h_snapshot_window_value(away_snapshot, window_key, "ops"),
            h2h_snapshot_window_value(home_snapshot, window_key, "ops"),
            (away_snapshot or {}).get("season_ops"),
            (home_snapshot or {}).get("season_ops"),
            value_type="number",
            digits=3,
            tolerance=0.018,
            scale_floor=0.900,
            stat_key="ops",
        ),
        h2h_stat_row_html(
            "AVG",
            "batting average",
            away_recent.get("avg"),
            home_recent.get("avg"),
            away_season.get("avg"),
            home_season.get("avg"),
            value_type="number",
            digits=3,
            tolerance=0.010,
            scale_floor=0.320,
            stat_key="avg",
        ),
        h2h_stat_row_html(
            "HR",
            "home runs",
            away_recent.get("home_runs"),
            home_recent.get("home_runs"),
            expected_profile_count(away_season, away_recent, "home_runs"),
            expected_profile_count(home_season, home_recent, "home_runs"),
            value_type="number",
            digits=0,
            tolerance=0.40,
            scale_floor=max(3.0, max(away_games, home_games) * 1.55),
            spaced=True,
        ),
        h2h_stat_row_html(
            "Runs",
            "runs scored",
            away_recent.get("runs"),
            home_recent.get("runs"),
            expected_profile_count(away_season, away_recent, "runs"),
            expected_profile_count(home_season, home_recent, "runs"),
            value_type="number",
            digits=0,
            tolerance=1.25,
            scale_floor=max(15.0, max(away_games, home_games) * 6.5),
        ),
        h2h_stat_row_html(
            "K",
            "batting strikeouts",
            away_recent.get("strikeouts"),
            home_recent.get("strikeouts"),
            expected_profile_count(away_season, away_recent, "strikeouts"),
            expected_profile_count(home_season, home_recent, "strikeouts"),
            value_type="number",
            digits=0,
            lower_is_better=True,
            tolerance=1.25,
            scale_floor=max(24.0, max(away_games, home_games) * 9.5),
        ),
        h2h_stat_row_html(
            "BB",
            "walks drawn",
            away_recent.get("walks"),
            home_recent.get("walks"),
            expected_profile_count(away_season, away_recent, "walks"),
            expected_profile_count(home_season, home_recent, "walks"),
            value_type="number",
            digits=0,
            tolerance=0.90,
            scale_floor=max(10.0, max(away_games, home_games) * 4.5),
        ),
    ]

    away_pitching = away_pitching or {}
    home_pitching = home_pitching or {}
    pitching_rows = [
        h2h_stat_row_html(
            "Runs Allowed / Game",
            f"allowed - {away_period}",
            away_pitching.get("runs_per_game"),
            home_pitching.get("runs_per_game"),
            away_pitching.get("runs_per_game"),
            home_pitching.get("runs_per_game"),
            value_type="number",
            digits=2,
            lower_is_better=True,
            tolerance=0.15,
            scale_floor=6.5,
            stat_key="runs_allowed_per_game",
        ),
        h2h_stat_row_html(
            "ERA",
            "earned run average",
            away_pitching.get("era"),
            home_pitching.get("era"),
            away_pitching.get("era"),
            home_pitching.get("era"),
            value_type="number",
            digits=2,
            lower_is_better=True,
            tolerance=0.10,
            scale_floor=6.0,
            stat_key="era",
        ),
        h2h_stat_row_html(
            "WHIP",
            "walks + hits per IP",
            away_pitching.get("whip"),
            home_pitching.get("whip"),
            away_pitching.get("whip"),
            home_pitching.get("whip"),
            value_type="number",
            digits=3,
            lower_is_better=True,
            tolerance=0.020,
            scale_floor=1.7,
            stat_key="whip",
        ),
        h2h_stat_row_html(
            "K/9",
            "strikeouts per 9 IP",
            away_pitching.get("k9"),
            home_pitching.get("k9"),
            away_pitching.get("k9"),
            home_pitching.get("k9"),
            value_type="number",
            digits=2,
            tolerance=0.20,
            scale_floor=11.5,
            stat_key="k9",
        ),
        h2h_stat_row_html(
            "BB/9",
            "walks per 9 IP",
            away_pitching.get("bb9"),
            home_pitching.get("bb9"),
            away_pitching.get("bb9"),
            home_pitching.get("bb9"),
            value_type="number",
            digits=2,
            lower_is_better=True,
            tolerance=0.12,
            scale_floor=5.0,
            stat_key="bb9",
        ),
        h2h_stat_row_html(
            "H/9",
            "hits allowed per 9 IP",
            away_pitching.get("h9"),
            home_pitching.get("h9"),
            away_pitching.get("h9"),
            home_pitching.get("h9"),
            value_type="number",
            digits=2,
            lower_is_better=True,
            tolerance=0.20,
            scale_floor=11.0,
            stat_key="h9",
        ),
        h2h_stat_row_html(
            "HR/9",
            "home runs allowed",
            away_pitching.get("hr9"),
            home_pitching.get("hr9"),
            away_pitching.get("hr9"),
            home_pitching.get("hr9"),
            value_type="number",
            digits=2,
            lower_is_better=True,
            tolerance=0.08,
            scale_floor=1.8,
            stat_key="hr9",
        ),
    ]

    return compact_html(f"""
    <div class="h2h-sheet">
      <div class="h2h-sheet__top">
        <div class="h2h-sheet__title"><span class="h2h-sheet__dot"></span><span>Head-to-head - team stat sheet</span></div>
        <div class="h2h-sheet__period">{html.escape(window_label)}</div>
      </div>
      <div class="h2h-sheet__teams">
        {h2h_team_header(away_snapshot, "away")}
        <div class="h2h-sheet__vs">VS</div>
        {h2h_team_header(home_snapshot, "home")}
      </div>
      <div class="h2h-sheet__section">Lineup - Production</div>
      <div class="h2h-stat-rows">{''.join(hitting_rows)}</div>
      <div class="h2h-sheet__section h2h-sheet__section--pitching">Pitching - Staff</div>
      <div class="h2h-stat-rows">{''.join(pitching_rows)}</div>
      <div class="h2h-sheet__footer">Completed MLB game logs from latest update.</div>
    </div>
    """)

def compact_html(markup: str) -> str:
    return "".join(line.strip() for line in str(markup).splitlines())

def comparison_stat_tone(stat_key: str, value: Any) -> str:
    value = momentum_stat_value(value)
    if value is None:
        return "neutral"
    if stat_key == "ops":
        if value < 0.700:
            return "weak"
        if value <= 0.760:
            return "average"
        return "strong"
    if stat_key == "obp":
        if value < 0.310:
            return "weak"
        if value <= 0.330:
            return "average"
        return "strong"
    if stat_key == "runs":
        if value < 4.00:
            return "weak"
        if value <= 5.00:
            return "average"
        return "strong"
    return "neutral"

def comparison_scale_floor(stat_key: str) -> float:
    if stat_key == "ops":
        return 0.900
    if stat_key == "obp":
        return 0.380
    if stat_key == "runs":
        return 7.00
    return 1.00

def render_team_comparison_chart(
    title: str,
    stat_key: str,
    away_snapshot: dict,
    home_snapshot: dict,
    keys: tuple[str, str, str],
    digits: int = 3,
) -> str:
    windows = [
        ("Season", keys[0]),
        ("L7", keys[1]),
        ("L3", keys[2]),
    ]
    rows = [(label, away_snapshot.get(key), home_snapshot.get(key)) for label, key in windows]
    return render_double_bar_comparison_chart(
        title,
        stat_key,
        str(away_snapshot.get("team", "Away team")),
        str(home_snapshot.get("team", "Home team")),
        rows,
        digits=digits,
    )

def render_double_bar_comparison_chart(
    title: str,
    stat_key: str,
    away_team: str,
    home_team: str,
    rows: list[tuple[str, Any, Any]],
    digits: int = 3,
) -> str:
    values = []
    for _, away_value, home_value in rows:
        values.extend([momentum_stat_value(away_value), momentum_stat_value(home_value)])
    real_values = [value for value in values if value is not None]
    max_value = max(real_values) if real_values else 0
    scale = max(comparison_scale_floor(stat_key), max_value * 1.08)

    def side_track(value: Any, side: str) -> str:
        numeric = momentum_stat_value(value)
        is_empty = numeric is None
        width = 0 if is_empty or numeric <= 0 else max(3.0, min(100.0, (numeric / scale) * 100))
        tone = comparison_stat_tone(stat_key, numeric)
        empty_class = " compare-chart__value--empty" if is_empty else ""
        value_text = "n/a" if is_empty else format_momentum_stat(numeric, digits=digits)
        return (
            f'<div class="compare-chart__track compare-chart__track--{side}">'
            f'<div class="compare-chart__fill compare-chart__fill--{side} compare-chart__fill--{tone}" style="width:{width:.1f}%;"></div>'
            f'<div class="compare-chart__value compare-chart__value--{side}{empty_class}">{html.escape(value_text)}</div>'
            f'</div>'
        )

    row_html = []
    for label, away_value, home_value in rows:
        row_html.append(
            f'<div class="compare-chart__row">'
            f'{side_track(away_value, "away")}'
            f'<div class="compare-chart__label">{html.escape(label)}</div>'
            f'{side_track(home_value, "home")}'
            f'</div>'
        )

    away_team = html.escape(str(away_team))
    home_team = html.escape(str(home_team))
    return compact_html(f"""
    <div class="compare-chart">
      <div class="compare-chart__title">{html.escape(title)} Analysis</div>
      <div class="compare-chart__legend">
        <div class="compare-chart__side compare-chart__side--away">
          <span class="compare-chart__team">{away_team}</span>
        </div>
        <div class="compare-chart__middle">Window</div>
        <div class="compare-chart__side compare-chart__side--home">
          <span class="compare-chart__team">{home_team}</span>
        </div>
      </div>
      <div class="compare-chart__rows">{''.join(row_html)}</div>
    </div>
    """)

def render_team_momentum_comparison(
    away_snapshot: dict,
    home_snapshot: dict,
    away_pitching: dict | None = None,
    home_pitching: dict | None = None,
    window_key: str = "last7",
    window_label: str = "Last 7 games",
) -> str:
    return render_h2h_team_stat_sheet(away_snapshot, home_snapshot, away_pitching, home_pitching, window_key, window_label)

def split_other_context(split: dict) -> dict:
    context = str((split or {}).get("context", "home"))
    return (split or {}).get("away" if context == "home" else "home", {}) or {}

def split_context_label(split: dict) -> str:
    context = str((split or {}).get("context", "home"))
    return "Home" if context == "home" else "Away"

def render_home_away_split_comparison_chart(
    title: str,
    stat_key: str,
    away_split: dict,
    home_split: dict,
    metric_key: str,
    digits: int = 3,
) -> str:
    rows = [
        ("Overall", (away_split.get("overall", {}) or {}).get(metric_key), (home_split.get("overall", {}) or {}).get(metric_key)),
        ("Current split", (away_split.get("context_split", {}) or {}).get(metric_key), (home_split.get("context_split", {}) or {}).get(metric_key)),
        ("Other", split_other_context(away_split).get(metric_key), split_other_context(home_split).get(metric_key)),
    ]
    return render_double_bar_comparison_chart(
        title,
        stat_key,
        str(away_split.get("team", "Away team")),
        str(home_split.get("team", "Home team")),
        rows,
        digits=digits,
    )

def render_home_away_split_comparison(away_split: dict, home_split: dict) -> str:
    return compact_html(f"""
    <div class="team-comparison-stack">
      {render_home_away_split_comparison_chart("Split OPS", "ops", away_split, home_split, "ops")}
      {render_home_away_split_comparison_chart("Split OBP", "obp", away_split, home_split, "obp")}
      {render_home_away_split_comparison_chart("Split RUN AVG", "runs", away_split, home_split, "runs", digits=2)}
    </div>
    """)

def split_label_tone(label: str) -> str:
    label = str(label or "").lower()
    if label == "context boost":
        return "balanced"
    if label == "context drag":
        return "cold"
    if label == "update needed":
        return "volatile"
    return "neutral"

def render_home_away_context_note_card(split: dict, side: str) -> str:
    split = split or {}
    context_title = split_context_label(split)
    today = split.get("context_split", {}) or {}
    label = str(split.get("label", "n/a"))
    tone = split_label_tone(label)
    note = (
        "Update team logs once to populate home/away splits."
        if not split.get("has_data")
        else f"Current {context_title.lower()} split compared with the team's overall season baseline."
    )
    metrics = [
        render_profile_metric("Context", context_title),
        render_profile_metric("Split G", str(safe_int(today.get("games")))),
        render_profile_metric("OPS diff", format_signed_momentum_stat(split.get("ops_edge"), digits=3)),
        render_profile_metric("OBP diff", format_signed_momentum_stat(split.get("obp_edge"), digits=3)),
        render_profile_metric("R/G diff", format_signed_momentum_stat(split.get("runs_edge"), digits=2)),
        render_profile_metric("Split OPS", format_momentum_stat(today.get("ops"), digits=3)),
        render_profile_metric("Split OBP", format_momentum_stat(today.get("obp"), digits=3)),
        render_profile_metric("Split R/G", format_momentum_stat(today.get("runs"), digits=2)),
    ]
    team = html.escape(str(split.get("team", "Team")))
    return compact_html(f"""
    <div class="team-profile-card team-profile-card--{side}">
      <div class="team-profile-card__head">
        <div>
          <div class="team-profile-card__kicker">Split context</div>
          <div class="team-profile-card__team">{team}</div>
        </div>
        <div class="team-profile-card__badge team-profile-card__badge--{tone}">{html.escape(_friendly_signal_label(label))}</div>
      </div>
      <div class="team-profile-card__note">{html.escape(note)}</div>
      <div class="team-profile-metrics">{''.join(metrics)}</div>
    </div>
    """)

def render_home_away_context_notes(away_split: dict, home_split: dict) -> str:
    return compact_html(f"""
    <div class="team-profile-grid">
      {render_home_away_context_note_card(away_split, "away")}
      {render_home_away_context_note_card(home_split, "home")}
    </div>
    """)

def format_profile_pct(value: Any) -> str:
    value = safe_float(value)
    return "n/a" if pd.isna(value) else f"{value:.1%}"

def render_profile_metric(label: str, value: str) -> str:
    return (
        f'<div class="team-profile-metric">'
        f'<div class="team-profile-metric__label">{html.escape(label)}</div>'
        f'<div class="team-profile-metric__value">{html.escape(value)}</div>'
        f'</div>'
    )

def pitcher_hand_context_label(pitcher_hand: Any) -> tuple[str, str]:
    hand = str(pitcher_hand or "").strip().upper()
    if hand in {"R", "RHP", "RIGHT"}:
        return "vs RHP", ""
    if hand in {"L", "LHP", "LEFT"}:
        return "vs LHP", ""
    return "vs hand n/a", " team-profile-card__context--unknown"

def render_team_hitting_profile_card(snapshot: dict, side: str, opposing_pitcher_hand: Any = None) -> str:
    profile = (snapshot or {}).get("batting_profile", {}) or {}
    recent = profile.get("recent", {}) or {}
    season = profile.get("season", {}) or {}
    tone = str(profile.get("tone", "neutral"))
    if tone not in {"balanced", "contact", "power", "volatile", "cold", "neutral"}:
        tone = "neutral"

    metrics = [
        render_profile_metric("AVG", format_momentum_stat(recent.get("avg"), digits=3)),
        render_profile_metric("SLG", format_momentum_stat(recent.get("slg"), digits=3)),
        render_profile_metric("ISO", format_momentum_stat(recent.get("iso"), digits=3)),
        render_profile_metric("K%", format_profile_pct(recent.get("k_pct"))),
        render_profile_metric("BB%", format_profile_pct(recent.get("bb_pct"))),
        render_profile_metric("XBH%", format_profile_pct(recent.get("xbh_pct"))),
        render_profile_metric("HR/G", format_momentum_stat(recent.get("hr_per_game"), digits=2)),
        render_profile_metric("Season BB%", format_profile_pct(season.get("bb_pct"))),
    ]

    team = html.escape(str((snapshot or {}).get("team", "Team")))
    label = html.escape(str(profile.get("label", "n/a")))
    note = html.escape(str(profile.get("note", "No profile available.")))
    context_label, context_modifier = pitcher_hand_context_label(opposing_pitcher_hand)
    games = safe_int(recent.get("games"))
    return compact_html(f"""
    <div class="team-profile-card team-profile-card--{side}">
      <div class="team-profile-card__head">
        <div>
          <div class="team-profile-card__kicker">Hitting profile - last {games or 7}</div>
          <div class="team-profile-card__team">{team}</div>
        </div>
        <div class="team-profile-card__badges">
          <div class="team-profile-card__context{context_modifier}">{html.escape(context_label)}</div>
          <div class="team-profile-card__badge team-profile-card__badge--{tone}">{label}</div>
        </div>
      </div>
      <div class="team-profile-card__note">{note}</div>
      <div class="team-profile-metrics">{''.join(metrics)}</div>
    </div>
    """)

def render_team_hitting_profile_comparison(
    away_snapshot: dict,
    home_snapshot: dict,
    away_opposing_pitcher_hand: Any = None,
    home_opposing_pitcher_hand: Any = None,
) -> str:
    return compact_html(f"""
    <div class="team-profile-grid">
      {render_team_hitting_profile_card(away_snapshot, "away", away_opposing_pitcher_hand)}
      {render_team_hitting_profile_card(home_snapshot, "home", home_opposing_pitcher_hand)}
    </div>
    """)

def lefty_leverage_tone_style(tone: str) -> tuple[str, str, str]:
    if tone == "good":
        return "#0f2e25", "#22c55e", "#bbf7d0"
    if tone == "warning":
        return "#2a1608", "#f59e0b", "#fde68a"
    return "#172033", "#334155", "#cbd5e1"

def render_lefty_leverage_card(profile: dict, team_name: str, side: str) -> str:
    profile = profile or {}
    bg, border, color = lefty_leverage_tone_style(str(profile.get("tone", "neutral")))
    pitcher_split = profile.get("pitcher_split", {}) or {}
    team_split = profile.get("team_split", {}) or {}
    arsenal = profile.get("arsenal", {}) or {}
    lineup = profile.get("lineup", {}) or {}
    top_mix = arsenal.get("top_mix", []) or []
    damage = arsenal.get("damage", []) or []
    reasons = profile.get("reasons", []) or []

    mix_text = ", ".join(f"{item.get('code')} {format_stat(item.get('usage'), 0)}%" for item in top_mix[:3]) or "n/a"
    damage_text = ", ".join(f"{item.get('code')} {format_stat(item.get('woba'), 3)} wOBA" for item in damage[:2]) or "none flagged"
    lineup_label = (
        f"{safe_int(lineup.get('count'))}/{safe_int(lineup.get('total'))} L/S"
        if lineup.get("available")
        else "lineup n/a"
    )
    if lineup.get("posted") and safe_int(lineup.get("top5")):
        lineup_label += f" | top5 {safe_int(lineup.get('top5'))}"
    elif not lineup.get("posted") and lineup.get("available"):
        lineup_label += " | projected"

    metrics = [
        render_profile_metric("Pitcher vs LHB OPS", format_stat(pitcher_split.get("ops"), digits=3)),
        render_profile_metric("vs LHB OBP", format_stat(pitcher_split.get("obp"), digits=3)),
        render_profile_metric("vs LHB SLG", format_stat(pitcher_split.get("slg"), digits=3)),
        render_profile_metric("vs LHB WHIP", format_stat(pitcher_split.get("whip"), digits=2)),
        render_profile_metric("vs LHB HR/9", format_stat(pitcher_split.get("homeRunsPer9"), digits=2)),
        render_profile_metric("Team vs RHP OPS", format_stat(team_split.get("ops"), digits=3)),
        render_profile_metric("Team vs RHP OBP", format_stat(team_split.get("obp"), digits=3)),
        render_profile_metric("Lineup", lineup_label),
    ]
    reason_text = "; ".join(str(reason) for reason in reasons[:3]) if reasons else str(profile.get("note", "No lefty leverage note available."))
    team = html.escape(str(team_name or "Team"))
    return compact_html(f"""
    <div class="team-profile-card team-profile-card--{side}">
      <div class="team-profile-card__head">
        <div>
          <div class="team-profile-card__kicker">Lefty leverage</div>
          <div class="team-profile-card__team">{team}</div>
        </div>
        <div class="team-profile-card__badges">
          <div class="team-profile-card__badge" style="background:{bg}; border:1px solid {border}; color:{color};">{html.escape(str(profile.get("label", "n/a")))}</div>
        </div>
      </div>
      <div class="team-profile-card__note">{html.escape(str(profile.get("note", "")))}</div>
      <div class="team-profile-metrics">{''.join(metrics)}</div>
      <div style="margin-top:0.55rem; display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:0.5rem;">
        <div style="background:#0b1220; border:1px solid #26364a; border-radius:8px; padding:0.5rem 0.6rem;">
          <div style="font-size:0.68rem; color:#94a3b8; font-weight:850; text-transform:uppercase; letter-spacing:0.04em;">Arsenal</div>
          <div style="font-size:0.82rem; color:#e5edf7; margin-top:0.12rem;">{html.escape(mix_text)}</div>
          <div style="font-size:0.72rem; color:#94a3b8; margin-top:0.12rem;">Breaking {format_stat(arsenal.get("breaking"), 0)}% | slider group {format_stat(arsenal.get("slider_group"), 0)}%</div>
        </div>
        <div style="background:#0b1220; border:1px solid #26364a; border-radius:8px; padding:0.5rem 0.6rem;">
          <div style="font-size:0.68rem; color:#94a3b8; font-weight:850; text-transform:uppercase; letter-spacing:0.04em;">Why</div>
          <div style="font-size:0.82rem; color:#e5edf7; margin-top:0.12rem; line-height:1.3;">{html.escape(reason_text)}</div>
          <div style="font-size:0.72rem; color:#94a3b8; margin-top:0.12rem;">Damage pitches: {html.escape(damage_text)}</div>
        </div>
      </div>
    </div>
    """)

def render_lefty_leverage_comparison(
    away_profile: dict,
    home_profile: dict,
    away_team: str,
    home_team: str,
) -> str:
    return compact_html(f"""
    <div class="team-profile-grid">
      {render_lefty_leverage_card(away_profile, away_team, "away")}
      {render_lefty_leverage_card(home_profile, home_team, "home")}
    </div>
    """)

def render_weather_card(weather: dict) -> str:
    profile = weather.get("profile", {}) or {}
    reasons = weather.get("reasons", []) or []
    reason_text = ", ".join(reasons) if reasons else "no major weather edge"
    score = safe_int(weather.get("score"))
    if score > 0:
        tone_bg, tone_color = "#e8f5eb", "#17803d"
    elif score < 0:
        tone_bg, tone_color = "#fdeaea", "#c23b36"
    else:
        tone_bg, tone_color = "#eef2f7", "#475467"
    return f"""
    <div class="quick-read">
      <div class="quick-read__top">
        <div>
          <div class="quick-read__title">Weather / park total context</div>
          <div class="quick-read__meta">{profile.get("venue", "Venue n/a")} | roof: {profile.get("roof", "unknown")}</div>
        </div>
        <div style="padding:0.25rem 0.65rem; border-radius:999px; background:{tone_bg}; color:{tone_color}; font-size:0.78rem; font-weight:800;">{weather.get("label", "neutral")}</div>
      </div>
      <div class="quick-read__grid">
        <div class="quick-tile">
          <div class="quick-tile__label">Weather</div>
          <div class="quick-tile__value">{weather.get("summary", "n/a")}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Wind read</div>
          <div class="quick-tile__value">{weather.get("wind_label", "n/a")}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Park tilt</div>
          <div class="quick-tile__value">Run {profile.get("run", 0)} | HR {profile.get("hr", 0)}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Why</div>
          <div class="quick-tile__value">{reason_text}</div>
        </div>
      </div>
    </div>
    """

def render_section_intro(title: str, note: str) -> None:
    st.subheader(title)
    st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)

def record_badge(record: dict) -> str:
    label = record.get("label", "0-0")
    form = record.get("form", "")
    wins = safe_int(record.get("wins"))
    losses = safe_int(record.get("losses"))
    bg = "#e8f5eb" if wins > losses else ("#fdeaea" if losses > wins else "#f1f5f9")
    color = "#17803d" if wins > losses else ("#c23b36" if losses > wins else "#334155")
    detail = f" L5 {label}" + (f" ({form})" if form else "")
    return f'<span style="display:inline-block; margin-left:0.45rem; padding:0.16rem 0.48rem; border-radius:999px; background:{bg}; color:{color}; font-size:0.72rem; font-weight:750; vertical-align:middle; white-space:nowrap;">{detail}</span>'

def _friendly_signal_label(label: str) -> str:
    labels = {
        "strong": "Strong",
        "good": "Good",
        "mixed": "Mixed",
        "cooling": "Cooling",
        "weak": "Weak",
        "steady": "Steady",
        "neutral": "Neutral",
        "run risk": "Run risk",
        "high traffic": "High traffic",
        "context boost": "Context boost",
        "context drag": "Context drag",
        "update needed": "Update needed",
        "n/a": "No data",
    }
    return labels.get(str(label), str(label).title())

def render_quick_read_card(game: dict, away_snapshot: dict, home_snapshot: dict, away_bullpen: dict, home_bullpen: dict, away_home_away: dict, home_home_away: dict) -> str:
    away_team = game.get("away_team_name", "Away")
    home_team = game.get("home_team_name", "Home")
    return f"""
    <div class="quick-read">
      <div class="quick-read__top">
        <div>
          <div class="quick-read__title">{away_team} @ {home_team}</div>
          <div class="quick-read__meta">{game.get("status") or "Scheduled"} | {game.get("venue") or "Venue n/a"}</div>
        </div>
      </div>
      <div class="quick-read__grid">
        <div class="quick-tile">
          <div class="quick-tile__label">Away offense</div>
          <div class="quick-tile__value">{_friendly_signal_label(away_snapshot.get("offense_signal", "n/a"))}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Home offense</div>
          <div class="quick-tile__value">{_friendly_signal_label(home_snapshot.get("offense_signal", "n/a"))}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Bullpen risk</div>
          <div class="quick-tile__value">{away_team}: {_friendly_signal_label(away_bullpen.get("label", "n/a"))}<br>{home_team}: {_friendly_signal_label(home_bullpen.get("label", "n/a"))}</div>
        </div>
        <div class="quick-tile">
          <div class="quick-tile__label">Context</div>
          <div class="quick-tile__value">{away_team}: {_friendly_signal_label(away_home_away.get("label", "n/a"))}<br>{home_team}: {_friendly_signal_label(home_home_away.get("label", "n/a"))}</div>
        </div>
      </div>
    </div>
    """

def render_bullpen_html_card(bullpen: dict, show_game_log: bool = True) -> str:
    label = bullpen.get("label", "n/a")
    label_bg = "#e8f5eb" if label == "steady" else ("#fdeaea" if label in {"high traffic", "run risk"} else "#f1f1f1")
    label_color = "#17803d" if label == "steady" else ("#c23b36" if label in {"high traffic", "run risk"} else "#666")
    rows = bullpen.get("rows", [])
    body = []
    for row in rows:
        outs = safe_int(row.get("outs"))
        row_era = _rate_per_nine(safe_int(row.get("earned_runs")), outs)
        row_whip = _whip(safe_int(row.get("hits")), safe_int(row.get("walks")), outs)
        body.append(
            "<tr>"
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{row.get("date", "")}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{row.get("opponent", "")}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{format_outs_as_ip(outs)}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{safe_int(row.get("runs"))}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{safe_int(row.get("earned_runs"))}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{safe_int(row.get("hits"))}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{safe_int(row.get("walks"))}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{format_stat(row_era, digits=2)}</td>'
            f'<td style="padding:0.38rem 0.35rem; border-bottom:1px solid #f0f0f0;">{format_stat(row_whip, digits=3)}</td>'
            "</tr>"
        )

    table_html = "".join(body) if body else '<tr><td colspan="9" style="padding:0.45rem 0.35rem;">No completed recent games found.</td></tr>'
    game_log_html = f"""
      <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:0.78rem;">
          <thead>
            <tr>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Date</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Opp</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">IP</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">R</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">ER</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">H</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">BB</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">ERA</th>
              <th style="text-align:left; padding:0.38rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">WHIP</th>
            </tr>
          </thead>
          <tbody>{table_html}</tbody>
        </table>
      </div>
    """ if show_game_log else ""

    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.9rem 1rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.7rem; margin-bottom:0.55rem;">
        <div style="font-size:1.05rem; font-weight:700;">{bullpen.get("team", "")}</div>
        <div style="display:inline-block; padding:0.2rem 0.55rem; border-radius:999px; background:{label_bg}; color:{label_color}; font-size:0.76rem; font-weight:700; white-space:nowrap;">{label}</div>
      </div>
      <div style="font-size:0.78rem; color:#666; margin-bottom:0.65rem;">Official MLB boxscores, last {bullpen.get("games", 0)} completed team games before selected date</div>
      <div style="display:grid; grid-template-columns:repeat(6,1fr); gap:0.65rem; margin-bottom:0.85rem;">
        <div><div style="font-size:0.75rem; color:#777;">IP</div><div style="font-size:1.35rem; font-weight:700;">{format_outs_as_ip(safe_int(bullpen.get("outs")))}</div></div>
        <div><div style="font-size:0.75rem; color:#777;">ERA</div><div style="font-size:1.35rem; font-weight:700;">{format_stat(bullpen.get("era"), digits=2)}</div></div>
        <div><div style="font-size:0.75rem; color:#777;">WHIP</div><div style="font-size:1.35rem; font-weight:700;">{format_stat(bullpen.get("whip"), digits=3)}</div></div>
        <div><div style="font-size:0.75rem; color:#777;">R/G</div><div style="font-size:1.35rem; font-weight:700;">{format_stat(bullpen.get("runs_per_game"), digits=2)}</div></div>
        <div><div style="font-size:0.75rem; color:#777;">BB/9</div><div style="font-size:1.35rem; font-weight:700;">{format_stat(bullpen.get("bb9"), digits=2)}</div></div>
        <div><div style="font-size:0.75rem; color:#777;">K/9</div><div style="font-size:1.35rem; font-weight:700;">{format_stat(bullpen.get("k9"), digits=2)}</div></div>
      </div>
      {game_log_html}
    </div>
    """

def render_bullpens_page(team_logs: pd.DataFrame, selected_date: Any, recent_games: int, show_game_log: bool) -> None:
    render_section_intro(
        "Bullpen comparison",
        "League-wide bullpen form from recent official MLB boxscores. This page does not load today's matchups, lineups, weather, or odds.",
    )
    st.caption("Availability is estimated from recent relief usage, rest days, and last outing pitch count.")

    with st.spinner("Building bullpen comparison from recent boxscores..."):
        comparison = bullpen_comparison_df(team_logs, selected_date, recent_games)

    if comparison.empty:
        st.warning("No bullpen data found. Update team logs first, then try again.")
        return

    c1, c2, c3 = st.columns([1.1, 1.1, 1.5])
    with c1:
        sort_mode = st.selectbox("Sort", ["Risk First", "Worst ERA", "Best ERA", "Most Available"], index=0)
    with c2:
        status_options = sorted(comparison["Status"].dropna().unique())
        status_filter = st.multiselect("Status", status_options, default=status_options)
    with c3:
        team_filter = st.multiselect("Teams", sorted(comparison["Team"].dropna().unique()), default=[])

    display_df = sort_bullpen_comparison(comparison, sort_mode)
    if status_filter:
        display_df = display_df[display_df["Status"].isin(status_filter)]
    if team_filter:
        display_df = display_df[display_df["Team"].isin(team_filter)]

    risk_count = int(comparison["Status"].isin(["High traffic", "Run risk"]).sum())
    best_era = comparison.sort_values("ERA", ascending=True, na_position="last").head(1)
    worst_era = comparison.sort_values("ERA", ascending=False, na_position="last").head(1)
    available_total = int(comparison["Likely Available"].fillna(0).sum())
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Risk bullpens", risk_count)
    k2.metric("Likely available arms", available_total)
    k3.metric("Best recent ERA", f'{best_era.iloc[0]["Team"]}: {best_era.iloc[0]["ERA"]:.2f}' if not best_era.empty and pd.notna(best_era.iloc[0]["ERA"]) else "n/a")
    k4.metric("Worst recent ERA", f'{worst_era.iloc[0]["Team"]}: {worst_era.iloc[0]["ERA"]:.2f}' if not worst_era.empty and pd.notna(worst_era.iloc[0]["ERA"]) else "n/a")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ERA": st.column_config.NumberColumn("ERA", format="%.2f"),
            "WHIP": st.column_config.NumberColumn("WHIP", format="%.3f"),
            "R/G": st.column_config.NumberColumn("R/G", format="%.2f"),
            "BB/9": st.column_config.NumberColumn("BB/9", format="%.2f"),
            "K/9": st.column_config.NumberColumn("K/9", format="%.2f"),
            "HR/9": st.column_config.NumberColumn("HR/9", format="%.2f"),
        },
    )

    default_detail_teams = display_df["Team"].head(2).tolist()
    selected_teams = st.multiselect(
        "Team detail cards",
        sorted(comparison["Team"].dropna().unique()),
        default=default_detail_teams,
    )
    if not selected_teams:
        return

    detail_cols = st.columns(2)
    for idx, team_name in enumerate(selected_teams):
        bullpen = build_bullpen_card(team_logs, team_name, selected_date, recent_games)
        arms = build_bullpen_arms(team_logs, team_name, selected_date, recent_games)
        with detail_cols[idx % 2]:
            st.markdown(render_bullpen_html_card(bullpen, show_game_log=show_game_log), unsafe_allow_html=True)
            arms_df = bullpen_arms_display_df(arms)
            if arms_df.empty:
                st.info("No recent relief appearances found for this team.")
            else:
                st.dataframe(
                    arms_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ERA": st.column_config.NumberColumn("ERA", format="%.2f"),
                        "WHIP": st.column_config.NumberColumn("WHIP", format="%.3f"),
                        "BB/9": st.column_config.NumberColumn("BB/9", format="%.2f"),
                        "K/9": st.column_config.NumberColumn("K/9", format="%.2f"),
                    },
                )

def render_home_away_html_card(split: dict) -> str:
    label = split.get("label", "n/a")
    label_bg = "#e8f5eb" if label == "context boost" else ("#fdeaea" if label == "context drag" else "#f1f1f1")
    label_color = "#17803d" if label == "context boost" else ("#c23b36" if label == "context drag" else "#666")
    context = split.get("context", "home")
    context_title = "Home" if context == "home" else "Away"
    overall = split.get("overall", {})
    home = split.get("home", {})
    away = split.get("away", {})
    note = "Update team logs once to populate home/away splits." if not split.get("has_data") else f"Today's context: {context_title}"
    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.9rem 1rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.7rem; margin-bottom:0.55rem;">
        <div style="font-size:1.05rem; font-weight:700;">{split.get("team", "")}</div>
        <div style="display:inline-block; padding:0.2rem 0.55rem; border-radius:999px; background:{label_bg}; color:{label_color}; font-size:0.76rem; font-weight:700; white-space:nowrap;">{label}</div>
      </div>
      <div style="font-size:0.78rem; color:#666; margin-bottom:0.65rem;">{note}</div>
      <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.65rem;">
        <div>
          <div style="font-size:0.75rem; color:#777;">Overall</div>
          <div style="font-size:1.35rem; font-weight:700;">{format_stat(overall.get("ops"))}</div>
          <div style="font-size:0.76rem; color:#666;">R/G {format_stat(overall.get("runs"), digits=2)} | G {overall.get("games", 0)}</div>
        </div>
        <div>
          <div style="font-size:0.75rem; color:#777;">Home</div>
          <div style="font-size:1.35rem; font-weight:700;">{format_stat(home.get("ops"))}</div>
          <div style="font-size:0.76rem; color:#666;">R/G {format_stat(home.get("runs"), digits=2)} | G {home.get("games", 0)}</div>
        </div>
        <div>
          <div style="font-size:0.75rem; color:#777;">Away</div>
          <div style="font-size:1.35rem; font-weight:700;">{format_stat(away.get("ops"))}</div>
          <div style="font-size:0.76rem; color:#666;">R/G {format_stat(away.get("runs"), digits=2)} | G {away.get("games", 0)}</div>
        </div>
      </div>
      <div style="font-size:0.78rem; color:#666; margin-top:0.65rem;">Context edge: OPS {format_stat(split.get("ops_edge"))} | R/G {format_stat(split.get("runs_edge"), digits=2)}</div>
    </div>
    """

def render_notes_html_card(title: str, notes: list[str]) -> str:
    note_items = "".join(
        f'<li style="margin-bottom:0.45rem; line-height:1.4;">{note}</li>'
        for note in notes
    )
    if not note_items:
        note_items = '<li style="margin-bottom:0.45rem; line-height:1.4;">No betting notes available.</li>'
    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.95rem 1rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="font-size:0.78rem; color:#667085; font-weight:800; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.35rem;">Betting read</div>
      <div style="font-size:1.02rem; font-weight:800; margin-bottom:0.65rem;">{title}</div>
      <ul style="padding-left:1.1rem; margin:0; color:#334155; font-size:0.9rem;">{note_items}</ul>
    </div>
    """

def render_odds_html_table(rows: list[dict]) -> str:
    if not rows:
        return """
        <div style="background:#ffffff; color:#667085; padding:0.9rem 1rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
          No odds found for this matchup/market selection.
        </div>
        """
    table_rows = []
    for row in rows:
        implied = row.get("implied_prob")
        implied_text = f"{implied * 100:.1f}%" if pd.notna(implied) else "n/a"
        line = row.get("line")
        open_line = row.get("open_line")
        open_price = row.get("open_price")
        movement_dir = row.get("movement_dir", "neutral")
        move_color = "#17803d" if movement_dir == "up" else ("#c23b36" if movement_dir == "down" else "#667085")
        move_arrow = "↑" if movement_dir == "up" else ("↓" if movement_dir == "down" else "→")
        movement_text = row.get("movement", "")
        movement_html = f'<span style="color:{move_color}; font-weight:750;">{move_arrow} {movement_text}</span>' if movement_text else ""
        table_rows.append(
            "<tr>"
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap; font-weight:750;">{row.get("signal", "")}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{row.get("market", "")}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{row.get("side", "")}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{row.get("book", "")}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0;">{line if line not in [None, ""] else "-"}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; font-weight:750;">{row.get("price", "n/a")}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0;">{implied_text}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0;">{open_line if open_line not in [None, ""] else "-"}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0;">{open_price if open_price not in [None, ""] else "-"}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0;">{movement_html}</td>'
            f'<td style="padding:0.42rem 0.35rem; border-bottom:1px solid #f0f0f0; color:#667085; min-width:220px;">{row.get("signal_reasons", "")}</td>'
            "</tr>"
        )
    return f"""
    <div style="background:#ffffff; color:#172033; padding:0.9rem 1rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; overflow-x:auto; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <table style="width:100%; border-collapse:collapse; font-size:0.82rem;">
        <thead>
          <tr>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Signal</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Market</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Side</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Book</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Line</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Price</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Impl.</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Open line</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Open price</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Move</th>
            <th style="text-align:left; padding:0.42rem 0.35rem; border-bottom:1px solid #e5e5e5; color:#666;">Why</th>
          </tr>
        </thead>
        <tbody>{''.join(table_rows)}</tbody>
      </table>
    </div>
    """

def render_last3_pitcher_rows(games: list[dict]) -> str:
    if not games:
        return '<tr><td colspan="11" style="padding:0.4rem 0.35rem;">No recent starts available.</td></tr>'
    rows = []
    for game in games:
        is_home = game.get("is_home")
        is_away = (is_home is False) or (isinstance(is_home, str) and is_home.lower() == "false")
        opponent = str(game.get("opponent") or "")
        opponent_label = f"@ {opponent}" if is_away and opponent else opponent
        rows.append(
            "<tr>"
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{game.get("date") or ""}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{html.escape(opponent_label)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_outs_as_ip(safe_int(game.get("outs")))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("pitches")) or "n/a"}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(game.get("pitches_per_out"), digits=1)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("er"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("hits"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("walks"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("strikeouts"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(game.get("home_runs"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(game.get("whip"), digits=3)}</td>'
            "</tr>"
        )
    return "".join(rows)

def render_pitcher_vs_roster(vs_roster: dict) -> str:
    summary = (vs_roster or {}).get("summary", {})
    rows = (vs_roster or {}).get("rows", [])
    alerts = (vs_roster or {}).get("alerts", [])
    if not rows:
        return '<div style="font-size:0.74rem; color:#667085; margin-top:0.35rem;">No batter-vs-pitcher history found for the listed roster.</div>'
    alert_html = ""
    if alerts:
        alert_rows = []
        for row in alerts[:4]:
            alert_rows.append(
                "<tr>"
                f'<td style="padding:0.42rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.2); font-weight:800;">{row.get("player", "")}</td>'
                f'<td style="padding:0.42rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.2);">{safe_int(row.get("ab"))}</td>'
                f'<td style="padding:0.42rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.2);">{format_stat(row.get("avg"), digits=3)}</td>'
                f'<td style="padding:0.42rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.2);">{format_stat(row.get("last7_ops"), digits=3)}</td>'
                f'<td style="padding:0.42rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.2); line-height:1.35;">{row.get("reason", "")}</td>'
                "</tr>"
            )
        alert_html = (
            '<div style="background:#2a1608; border:1px solid #b45309; border-radius:8px; padding:0.75rem 0.8rem; margin-top:0.75rem; box-shadow:0 12px 26px rgba(0,0,0,0.22);">'
            '<div style="font-size:0.82rem; color:#fbbf24; font-weight:900; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.45rem;">Roster matchup alert</div>'
            '<table style="width:100%; border-collapse:collapse; font-size:0.74rem;">'
            '<thead><tr>'
            '<th style="text-align:left; padding:0.36rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.38);">Hitter</th>'
            '<th style="text-align:left; padding:0.36rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.38);">BvP AB</th>'
            '<th style="text-align:left; padding:0.36rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.38);">BvP AVG</th>'
            '<th style="text-align:left; padding:0.36rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.38);">L7 OPS</th>'
            '<th style="text-align:left; padding:0.36rem 0.4rem; border-bottom:1px solid rgba(251,191,36,0.38);">Why</th>'
            f'</tr></thead><tbody>{"".join(alert_rows)}</tbody></table></div>'
        )
    return (
        '<div style="display:grid; grid-template-columns:repeat(6,1fr); gap:0.45rem; margin-top:0.35rem;">'
        f'<div><div style="font-size:0.68rem; color:#777;">Hitters</div><div style="font-size:1.05rem; font-weight:700;">{len(rows)}</div></div>'
        f'<div><div style="font-size:0.68rem; color:#777;">AB</div><div style="font-size:1.05rem; font-weight:700;">{safe_int(summary.get("ab"))}</div></div>'
        f'<div><div style="font-size:0.68rem; color:#777;">H</div><div style="font-size:1.05rem; font-weight:700;">{safe_int(summary.get("h"))}</div></div>'
        f'<div><div style="font-size:0.68rem; color:#777;">HR</div><div style="font-size:1.05rem; font-weight:700;">{safe_int(summary.get("hr"))}</div></div>'
        f'<div><div style="font-size:0.68rem; color:#777;">SO</div><div style="font-size:1.05rem; font-weight:700;">{safe_int(summary.get("so"))}</div></div>'
        f'<div><div style="font-size:0.68rem; color:#777;">OPS</div><div style="font-size:1.05rem; font-weight:700;">{format_stat(summary.get("ops"), digits=3)}</div></div>'
        f'</div>{alert_html}'
    )

def render_pitcher_home_away_split(home_away: dict) -> str:
    if not (home_away or {}).get("has_data"):
        return '<div style="font-size:0.74rem; color:#667085; margin-bottom:0.65rem;">Home/away pitching splits unavailable from MLB game logs.</div>'

    def split_row(label: str, split: dict) -> str:
        return (
            "<tr>"
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0; font-weight:750;">{label}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{safe_int(split.get("games"))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_outs_as_ip(safe_int(split.get("outs")))}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("era"), digits=2)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("whip"), digits=3)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("h9"), digits=2)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("bb9"), digits=2)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("k9"), digits=2)}</td>'
            f'<td style="padding:0.34rem 0.3rem; border-bottom:1px solid #f0f0f0;">{format_stat(split.get("hr9"), digits=2)}</td>'
            "</tr>"
        )

    return f"""
    <div style="font-size:0.75rem; color:#667085; margin-bottom:0.2rem; font-weight:700;">Home / away</div>
    <div style="overflow-x:auto; margin-bottom:0.65rem;">
      <table style="width:100%; border-collapse:collapse; font-size:0.74rem;">
        <thead><tr>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">Split</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">G</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">IP</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">ERA</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">WHIP</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">H/9</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">BB/9</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">K/9</th>
          <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">HR/9</th>
        </tr></thead>
        <tbody>
          {split_row("Home", home_away.get("home", {}))}
          {split_row("Away", home_away.get("away", {}))}
        </tbody>
      </table>
    </div>
    """

def profile_tone_colors(tone: str) -> tuple[str, str, str]:
    if tone == "bad":
        return "#3b1111", "#ef4444", "#fecaca"
    if tone == "warning":
        return "#2a1608", "#f59e0b", "#fde68a"
    if tone == "good":
        return "#0f2e25", "#22c55e", "#bbf7d0"
    return "#172033", "#334155", "#cbd5e1"

def render_pitcher_profile_html(profile: dict) -> str:
    bg, border, color = profile_tone_colors(str(profile.get("tone", "neutral")))
    items = []
    for label, item in (profile.get("components", {}) or {}).items():
        item_bg, item_border, item_color = profile_tone_colors(str(item.get("tone", "neutral")))
        items.append(
            f'''
            <div style="background:{item_bg}; border:1px solid {item_border}; border-radius:8px; padding:0.48rem 0.55rem;">
              <div style="font-size:0.68rem; color:{item_color}; font-weight:850; text-transform:uppercase; letter-spacing:0.04em;">{label}</div>
              <div style="font-size:0.95rem; font-weight:850; margin-top:0.1rem;">{item.get("label", "n/a")}</div>
              <div style="font-size:0.78rem; color:#cbd5e1; margin-top:0.1rem;">{format_stat(item.get("value"), digits=2)} {item.get("stat", "")}</div>
            </div>
            '''
        )
    return f'''
      <div style="background:#0f172a; border:1px solid #26364a; border-radius:8px; padding:0.7rem 0.75rem; margin-bottom:0.65rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:0.65rem; margin-bottom:0.55rem;">
          <div style="font-size:0.78rem; color:#cbd5e1; font-weight:900; text-transform:uppercase; letter-spacing:0.05em;">Pitcher profile</div>
          <div style="display:inline-block; padding:0.18rem 0.52rem; border-radius:999px; background:{bg}; border:1px solid {border}; color:{color}; font-size:0.76rem; font-weight:850; white-space:nowrap;">{profile.get("label", "balanced profile")}</div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:0.5rem;">{"".join(items)}</div>
      </div>
    '''

def render_pitcher_html_card(p: dict) -> str:
    last3_rows = render_last3_pitcher_rows(p.get("last3_games", []))
    vs_roster_html = render_pitcher_vs_roster(p.get("vs_roster", {}))
    home_away_html = render_pitcher_home_away_split(p.get("home_away", {}))
    profile = pitcher_profile_signal(p)
    profile_html = render_pitcher_profile_html(profile)
    profile_bg, profile_border, profile_color = profile_tone_colors(str(profile.get("tone", "neutral")))
    era_truth = p.get("era_truth", {}) or {}
    truth_label = era_truth.get("label", "n/a")
    truth_tone = era_truth.get("tone", "neutral")
    truth_bg = "#fdeaea" if truth_tone == "bad" else ("#fff3e6" if truth_tone == "warning" else ("#e8f5eb" if truth_tone == "good" else "#f1f5f9"))
    truth_color = "#c23b36" if truth_tone == "bad" else ("#9a5a00" if truth_tone == "warning" else ("#17803d" if truth_tone == "good" else "#334155"))
    pitch_leash = p.get("pitch_leash", {}) or {}
    leash_bg, leash_border, leash_color = profile_tone_colors(str(pitch_leash.get("tone", "neutral")))
    card_html = f'''
    <div style="background:#ffffff; color:#172033; padding:0.85rem 0.95rem; border:1px solid #d9e0e8; border-radius:8px; margin-bottom:0.6rem; box-shadow:0 10px 26px rgba(17,24,39,0.07);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.65rem; margin-bottom:0.5rem;">
        <div style="font-size:0.98rem; font-weight:800;">{p.get("name", "TBD")}</div>
        <div style="display:flex; gap:0.35rem; flex-wrap:wrap; justify-content:flex-end;">
          <div style="display:inline-block; padding:0.16rem 0.48rem; border-radius:999px; background:{profile_bg}; border:1px solid {profile_border}; color:{profile_color}; font-size:0.72rem; font-weight:700; white-space:nowrap;">{profile.get("label", "balanced profile")}</div>
          <div style="display:inline-block; padding:0.16rem 0.48rem; border-radius:999px; background:{truth_bg}; color:{truth_color}; font-size:0.72rem; font-weight:700; white-space:nowrap;">{truth_label}</div>
          <div style="display:inline-block; padding:0.16rem 0.48rem; border-radius:999px; background:{leash_bg}; border:1px solid {leash_border}; color:{leash_color}; font-size:0.72rem; font-weight:700; white-space:nowrap;">{pitch_leash.get("label", "n/a")}</div>
        </div>
      </div>

      {profile_html}

      <div style="background:#fbfcfd; border:1px solid #e5ebf2; border-radius:8px; padding:0.55rem 0.65rem; margin-bottom:0.65rem;">
        <div style="font-size:0.72rem; color:#667085; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.18rem;">ERA truth</div>
        <div style="font-size:0.82rem; color:#334155; line-height:1.35;">{era_truth.get("note", "No ERA truth signal available.")}</div>
      </div>

      <div style="background:#fbfcfd; border:1px solid #e5ebf2; border-radius:8px; padding:0.55rem 0.65rem; margin-bottom:0.65rem;">
        <div style="font-size:0.72rem; color:#667085; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.18rem;">Pitch-count leash</div>
        <div style="font-size:0.82rem; color:#334155; line-height:1.35;">{pitch_leash.get("note", "No pitch-count signal available.")}</div>
      </div>

      <div style="font-size:0.75rem; color:#667085; margin-bottom:0.2rem; font-weight:700;">Season</div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(72px,1fr)); gap:0.45rem; margin-bottom:0.65rem;">
        <div><div style="font-size:0.68rem; color:#777;">ERA</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("era"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">WHIP</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("whip"), digits=3)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">H/9</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("h9"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">BB/9</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("bb9"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">K/9</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("k9"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">HR</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{safe_int(p.get("home_runs"))}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">HR/9</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(p.get("hr9"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">QS <=3R</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{p.get("quality_start_label", "n/a")}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">P/start</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(pitch_leash.get("season_pitches_per_start"), digits=0)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">P/out</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_stat(pitch_leash.get("season_pitches_per_out"), digits=1)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">6IP%</div><div style="font-size:1.15rem; font-weight:750; color:#111827;">{format_percent(pitch_leash.get("season_6ip_rate"))}</div></div>
      </div>

      {home_away_html}

      <div style="font-size:0.75rem; color:#667085; margin-bottom:0.2rem; font-weight:700;">Last 3 starts</div>
      <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(72px,1fr)); gap:0.45rem; margin-bottom:0.55rem;">
        <div><div style="font-size:0.68rem; color:#777;">ERA</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(p.get("last3_era"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">WHIP</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(p.get("last3_whip"), digits=3)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">Hits</div><div style="font-size:1.12rem; font-weight:750;">{p.get("last3_hits", 0)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">Walks</div><div style="font-size:1.12rem; font-weight:750;">{p.get("last3_walks", 0)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">HR</div><div style="font-size:1.12rem; font-weight:750;">{p.get("last3_home_runs", 0)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">HR/9</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(p.get("last3_hr9"), digits=2)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">IP/start</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(p.get("last3_ip_per_start"), digits=1)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">P/start</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(pitch_leash.get("last3_pitches_per_start"), digits=0)}</div></div>
        <div><div style="font-size:0.68rem; color:#777;">P/out</div><div style="font-size:1.12rem; font-weight:750;">{format_stat(pitch_leash.get("last3_pitches_per_out"), digits=1)}</div></div>
      </div>
      <div style="overflow-x:auto; margin-bottom:0.65rem;">
        <table style="width:100%; border-collapse:collapse; font-size:0.74rem;">
          <thead><tr>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">Date</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">Opp</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">IP</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">P</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">P/out</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">ER</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">H</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">BB</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">K</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">HR</th>
            <th style="text-align:left; padding:0.32rem 0.3rem; border-bottom:1px solid #e5e5e5; color:#666;">WHIP</th>
          </tr></thead>
          <tbody>{last3_rows}</tbody>
        </table>
      </div>

      <div style="font-size:0.75rem; color:#667085; margin-bottom:0.15rem; font-weight:700;">Vs listed roster</div>
      {vs_roster_html}
    </div>
    '''
    return "".join(line.strip() for line in card_html.splitlines())

def build_pitcher_era_figure(pitcher: dict, color: str) -> go.Figure | None:
    trend = pd.DataFrame((pitcher or {}).get("era_trend", []) or [])
    if trend.empty:
        return None

    trend["date"] = pd.to_datetime(trend["date"], errors="coerce")
    trend = trend.dropna(subset=["date"]).sort_values("date")
    if trend.empty:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend["date"],
            y=trend["game_era"],
            mode="lines+markers",
            name="Game ERA",
            line=dict(color=color, width=1.7, dash="dot"),
            marker=dict(size=5),
            opacity=0.45,
            hovertemplate="%{x|%Y-%m-%d}<br>Game ERA: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend["date"],
            y=trend["rolling_era"],
            mode="lines+markers",
            name="Rolling 3-start ERA",
            line=dict(color=color, width=4),
            marker=dict(size=6),
            hovertemplate="%{x|%Y-%m-%d}<br>Rolling ERA: %{y:.2f}<extra></extra>",
        )
    )

    season_era = safe_float((pitcher or {}).get("era"))
    if pd.notna(season_era):
        fig.add_hline(
            y=season_era,
            line_dash="dash",
            line_color="#cbd5e1",
            opacity=0.55,
            annotation_text=f"Season {season_era:.2f}",
            annotation_position="top left",
            annotation_font_color="#cbd5e1",
        )

    y_values = pd.concat([trend["game_era"], trend["rolling_era"]]).dropna()
    y_range = None
    if not y_values.empty:
        upper = min(15, max(6, float(y_values.quantile(0.92)) + 1.0))
        y_range = [0, upper]

    fig.update_layout(
        title=f'{pitcher.get("name", "Pitcher")} ERA trend',
        height=285,
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="#070d18",
        plot_bgcolor="#0b1220",
        font=dict(color="#f8fafc", size=12),
        margin=dict(l=12, r=12, t=42, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#26364a", zerolinecolor="#334155", color="#cbd5e1", title_text="")
    fig.update_yaxes(title_text="ERA", gridcolor="#26364a", zerolinecolor="#334155", color="#cbd5e1", range=y_range)
    return fig

def build_betting_notes(
    offense: dict,
    opp_pitcher: dict,
    own_pitcher: dict,
    lineup_rows: list[dict],
    opponent_name: str,
    opp_bullpen: dict | None = None,
    own_bullpen: dict | None = None,
) -> list[str]:
    notes = []
    lineup_summary = summarize_lineup_strength(lineup_rows)
    opp_pitcher_state = pitcher_recent_label(opp_pitcher)
    own_pitcher_state = pitcher_recent_label(own_pitcher)
    opp_bullpen_state = (opp_bullpen or {}).get("label", "n/a")
    own_bullpen_state = (own_bullpen or {}).get("label", "n/a")

    notes.append(f"OPS ladder: Last 3 {format_stat(offense.get('last3_ops'))} | Last 7 {format_stat(offense.get('last7_ops'))} | Season {format_stat(offense.get('season_ops'))} ({offense.get('ops_label', 'n/a')}).")
    notes.append(f"Runs ladder: Last 3 {format_stat(offense.get('last3_runs'), digits=2)} | Last 7 {format_stat(offense.get('last7_runs'), digits=2)} | Season {format_stat(offense.get('season_runs'), digits=2)} ({offense.get('runs_label', 'n/a')}).")

    if opp_pitcher_state == "worse than season":
        notes.append(f"{opp_pitcher.get('name', opponent_name)} is trending worse than his season baseline.")
    elif opp_pitcher_state == "better than season":
        notes.append(f"{opp_pitcher.get('name', opponent_name)} is in better recent form than his season baseline.")

    opp_truth = (opp_pitcher or {}).get("era_truth", {})
    if opp_truth.get("label") in {"danger spot", "lucky ERA", "regression risk", "watch traffic"}:
        notes.append(f"Starter ERA truth: {opp_truth.get('label')} - {opp_truth.get('note')}")

    if lineup_summary["hot_count"] >= 2:
        notes.append(f"Lineup support: {lineup_summary['hot_count']} hot bats active.")
    elif lineup_summary["l7_great_count"] >= 3:
        notes.append(f"Lineup support: {lineup_summary['l7_great_count']} bats are at .800+ OPS over the last 7.")
    elif lineup_summary["great_count"] >= 3:
        notes.append("Lineup support: multiple season-long .800+ OPS bats active.")

    if opp_bullpen_state in {"high traffic", "run risk"}:
        notes.append(f"{opponent_name} bullpen last 5: {opp_bullpen_state} ({format_stat((opp_bullpen or {}).get('era'), digits=2)} ERA, {format_stat((opp_bullpen or {}).get('whip'), digits=3)} WHIP).")

    if offense.get("offense_signal") in {"strong", "good"} and opp_pitcher_state == "worse than season" and lineup_summary["hot_count"] >= 2:
        notes.append("Strong batter-prop signal: offense momentum + hot bats + vulnerable recent pitcher form.")
    elif offense.get("offense_signal") in {"strong", "good"} and opp_pitcher_state == "worse than season":
        notes.append("Good batter-prop signal: offense momentum lines up with pitcher slippage.")

    if offense.get("offense_signal") in {"strong", "good"} and opp_bullpen_state in {"high traffic", "run risk"}:
        notes.append("Late-game scoring angle: offense form lines up with recent bullpen traffic.")

    if offense.get("offense_signal") == "strong" and own_pitcher_state in {"better than season", "near season"} and opp_pitcher_state == "worse than season" and own_bullpen_state != "high traffic":
        notes.append("Strong moneyline/run-line support: offense is building and starting pitching edge leans this side.")
    elif offense.get("offense_signal") == "good" and opp_pitcher_state == "worse than season":
        notes.append("Side-bet support: offense is above baseline and opposing starter is below recent baseline.")

    return notes[:6]

def default_slate_date() -> Any:
    now = pd.Timestamp.now()
    if now.hour < 6:
        return (now - pd.Timedelta(days=1)).date()
    return now.date()


with st.sidebar:
    st.subheader("Setup")
    selected_date = st.date_input("Date", value=default_slate_date())
    season = selected_date.year
    stale_logs, latest_log_date, expected_log_date = team_logs_are_stale(pd.Timestamp(selected_date))

    if REAL_DATA_PATH.exists():
        st.caption(f"Data file: {REAL_DATA_PATH.name}")
        st.caption(f"File saved: {pd.Timestamp(REAL_DATA_PATH.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("Demo data is active until real data is downloaded.")

    latest_label = latest_log_date.strftime("%Y-%m-%d") if latest_log_date is not None else "none"
    expected_label = expected_log_date.strftime("%Y-%m-%d")
    if stale_logs:
        st.error(f"Results log outdated. Latest saved result: {latest_label}. Expected through: {expected_label}.")
    else:
        st.success(f"Results log fresh through {latest_label}.")

    if st.button("Update team logs", use_container_width=True):
        if not stale_logs:
            ok = True
            message = f"Team logs already up to date through {latest_label}."
        else:
            with st.spinner("Downloading new team logs..."):
                ok, message = update_team_game_logs(season)
        st.session_state["update_message"] = ("success" if ok else "error", message)
        st.cache_data.clear()
        st.rerun()

    if "update_message" in st.session_state:
        kind, msg = st.session_state["update_message"]
        if kind == "success":
            st.success("Team logs updated.")
        else:
            st.error("Update failed.")
        with st.expander("Update log"):
            st.text(msg)

    st.subheader("View")
    page_mode = st.radio("Page", ["Matchups", "Bullpens", "Pitchers", "Hitters"], index=0)
    view_mode = st.radio("Detail level", ["Simple", "Detailed"], index=0)
    show_detail_tables = view_mode == "Detailed"
    bullpen_recent_games = 5
    show_best_bet_shortlist = True
    show_pitcher_detail_cards = True
    show_hitter_detail_cards = True

    if page_mode == "Bullpens":
        bullpen_recent_games = st.slider("Recent bullpen games", min_value=3, max_value=10, value=5)
    elif page_mode == "Pitchers":
        show_pitcher_detail_cards = st.toggle("Pitcher detail cards", value=True)
    elif page_mode == "Hitters":
        show_hitter_detail_cards = st.toggle("Hitter detail cards", value=True)
    else:
        show_best_bet_shortlist = st.toggle("Best-bet shortlist", value=True)
        with st.expander("Chart settings"):
            metric = st.selectbox("Metric", ["ops", "obp"], index=0)
            window = st.slider("Rolling window", min_value=3, max_value=14, value=7)
            chart_mode = st.radio("Chart style", ["Rolling trend only", "Rolling + daily"], index=0)
            smooth_lines = st.toggle("Smooth lines", value=False)

    with st.expander("Signal guide"):
        st.markdown(
            """
            **Offense** compares season, last 7, and last 3.

            **Bullpen** uses official boxscores from the last 5 completed games.

            **Hitter OPS bands**: below .700 is weak, .700-.799 is average, and .800+ is great. A hitter is only hot when Last 7 OPS is .800+ and above his season OPS.

            **Hitter consistency** compares batting average for season, last 30 days, last 15 days, and last 7 days. It flags hitters as stable, heating, cooling, volatile, or small sample.

            **Batting profile** uses the last 7 team games: AVG, SLG/ISO, K%, BB%, and extra-base-hit share. The green vs RHP/LHP badge shows the opposing starter hand for the selected matchup.

            **Lefty leverage** activates against right-handed starters when pitcher vs-left splits, team vs-RHP production, recent offense, arsenal mix, and posted lefty/switch bats line up. It is a context boost, not a standalone bet rule.

            **Hottest hitters** ranks listed hitters by last 7 OPS, season OPS baseline, OBP, AVG, and batting-average consistency windows.

            **Pitcher QS <=3R** counts starts where the pitcher allowed 3 or fewer total runs.

            **Best-bet shortlist** ignores price and requires strong recent OPS/OBP, a steady own bullpen, own starter form at or above season level, weak opponent offense, a targetable opponent starter, and a risky opponent bullpen.
            """
        )

    if page_mode == "Matchups":
        st.subheader("Odds")
        odds_markets = st.multiselect(
            "Markets",
            ["Moneyline", "Run line", "Game total"],
            default=["Moneyline", "Run line", "Game total"],
        )
        odds_books_text = st.text_input("Books", value="bet365,draftkings,fanduel,betmgm,caesars")
        save_odds_snapshot = st.toggle("Save odds snapshots", value=True)

data_signature = get_data_signature()
team_logs = prepare_team_logs(load_team_logs(data_signature))

if stale_logs:
    latest_label = latest_log_date.strftime("%Y-%m-%d") if latest_log_date is not None else "none"
    expected_label = expected_log_date.strftime("%Y-%m-%d")
    st.warning(
        f"Season results are outdated. Last saved result is {latest_label}, but this view expects results through {expected_label}. "
        "Update team logs before trusting season, last 7, last 3, W-L streaks, or bet grading."
    )

if page_mode == "Bullpens":
    render_bullpens_page(team_logs, selected_date, bullpen_recent_games, show_detail_tables)
    st.stop()

if page_mode == "Pitchers":
    games = fetch_schedule_for_date(str(selected_date))
    render_pitchers_page(games, season, show_pitcher_detail_cards)
    st.stop()

if page_mode == "Hitters":
    games = fetch_schedule_for_date(str(selected_date))
    render_hitters_page(games, season, selected_date, show_hitter_detail_cards)
    st.stop()

games = fetch_schedule_for_date(str(selected_date))
if not games:
    st.warning("No MLB games found for that date.")
    st.stop()

if show_best_bet_shortlist:
    render_section_intro(
        "Best-bet shortlist",
        "Manual rule-based scan after the current team logs are loaded. Nothing is saved or graded unless you press a button.",
    )
    scan_key = f"best_bet_shortlist_scan_{selected_date}"
    best_bet_tracker = read_best_bet_tracker()
    if stale_logs:
        st.info("Best-bet shortlist waits for fresh season team logs. Press Update team logs when you want to refresh the results.")
    else:
        action_cols = st.columns(3)
        if action_cols[0].button("Scan shortlist", use_container_width=True):
            with st.spinner("Scanning matchups for full-rule best-bet signals..."):
                st.session_state[scan_key] = build_best_bet_shortlist(games, team_logs, selected_date, season)
        if action_cols[2].button("Grade saved results", use_container_width=True):
            best_bet_tracker, graded_best_bets = grade_best_bet_tracker(best_bet_tracker)
            if graded_best_bets:
                save_best_bet_tracker(best_bet_tracker)
                st.success(f"Graded {graded_best_bets} saved shortlist row(s).")
            else:
                st.info("No saved shortlist rows needed grading.")
        best_bet_rows = st.session_state.get(scan_key)
        if best_bet_rows is None:
            st.info("Press Scan shortlist when you want to refresh today's automated reads. Opening the app will not scan or save by itself.")
        else:
            shortlist_rows = best_bet_rows if isinstance(best_bet_rows, list) else best_bet_rows.get("shortlist", [])
            if action_cols[1].button("Save scan to history", use_container_width=True, disabled=not bool(shortlist_rows)):
                saved_best_bets = append_best_bet_suggestions(best_bet_rows, selected_date)
                best_bet_tracker = read_best_bet_tracker()
                if saved_best_bets:
                    st.success(f"Saved {saved_best_bets} new automated shortlist row(s) to local history.")
                else:
                    st.info("No new rows saved. These shortlist rows were already in history.")
            st.markdown(render_best_bet_shortlist(best_bet_rows), unsafe_allow_html=True)

    suggested_summary = best_bet_tracker_summary(best_bet_tracker, "Suggested")
    overall_summary = best_bet_tracker_summary(best_bet_tracker)
    summary_cols = st.columns(4)
    suggested_rate = suggested_summary["win_rate"]
    summary_cols[0].metric("Suggested W-L", f"{suggested_summary['wins']}-{suggested_summary['losses']}")
    summary_cols[1].metric("Suggested hit rate", "n/a" if pd.isna(suggested_rate) else f"{suggested_rate:.1%}")
    summary_cols[2].metric("Shortlist W-L", f"{overall_summary['wins']}-{overall_summary['losses']}")
    summary_cols[3].metric("Pending", str(overall_summary["pending"]))
    with st.expander("Saved shortlist history"):
        if best_bet_tracker.empty:
            st.caption("No automated shortlist rows saved yet.")
        else:
            st.dataframe(best_bet_tracker_display_df(best_bet_tracker), use_container_width=True, hide_index=True)

game_by_key = {game_state_key(g): g for g in games}
game_keys = list(game_by_key.keys())
selected_game_key = st.selectbox(
    "Select Game",
    game_keys,
    index=0,
    format_func=lambda key: game_display_label(game_by_key[key]),
)
game = game_by_key[selected_game_key]
current_game_key = game_state_key(game)
current_game_label = game_display_label(game)

away_snapshot = team_snapshot(team_logs, game["away_team_name"])
home_snapshot = team_snapshot(team_logs, game["home_team_name"])
away_record_badge = record_badge(away_snapshot.get("last5_record", {}))
home_record_badge = record_badge(home_snapshot.get("last5_record", {}))
away_pitcher = build_pitcher_card(game.get("away_pitcher_id"), game.get("away_pitcher_name"), season)
home_pitcher = build_pitcher_card(game.get("home_pitcher_id"), game.get("home_pitcher_name"), season)
away_pitcher["era_truth"] = pitcher_era_truth_signal(away_pitcher)
home_pitcher["era_truth"] = pitcher_era_truth_signal(home_pitcher)
away_home_away = home_away_snapshot(team_logs, game["away_team_name"], "away")
home_home_away = home_away_snapshot(team_logs, game["home_team_name"], "home")
away_lineup, away_posted = fetch_lineup_rows(game["game_id"], "away", season, selected_date)
home_lineup, home_posted = fetch_lineup_rows(game["game_id"], "home", season, selected_date)
away_context_production = build_context_production_rows(away_lineup, season, "away", n=5, limit=5)
home_context_production = build_context_production_rows(home_lineup, season, "home", n=5, limit=5)
away_bullpen = build_bullpen_card(team_logs, game["away_team_name"], selected_date, 5)
home_bullpen = build_bullpen_card(team_logs, game["home_team_name"], selected_date, 5)
away_lefty_leverage = build_lefty_leverage_profile(
    away_snapshot,
    game.get("away_team_id"),
    home_pitcher,
    season,
    away_lineup,
)
home_lefty_leverage = build_lefty_leverage_profile(
    home_snapshot,
    game.get("home_team_id"),
    away_pitcher,
    season,
    home_lineup,
)
away_pitcher["vs_roster"] = build_pitcher_vs_roster(game.get("away_pitcher_id"), home_lineup, season)
home_pitcher["vs_roster"] = build_pitcher_vs_roster(game.get("home_pitcher_id"), away_lineup, season)
away_pitcher["vs_roster"] = add_pitcher_vs_roster_alerts(away_pitcher)
home_pitcher["vs_roster"] = add_pitcher_vs_roster_alerts(home_pitcher)
weather_context = fetch_weather_context(game.get("venue"), game.get("game_time"))

st.markdown(
    render_quick_read_card(game, away_snapshot, home_snapshot, away_bullpen, home_bullpen, away_home_away, home_home_away),
    unsafe_allow_html=True,
)

render_section_intro("Game overview", "Start here: teams, status, venue and probable starters.")
g1, g2, g3 = st.columns([1.2, 0.8, 1.2])
with g1:
    st.markdown(
        f"""
        <div class="game-card">
          <div class="game-card__label">Away</div>
          <div class="game-card__team">{game['away_team_name']}{away_record_badge}</div>
          <div class="game-card__meta">Probable SP: {game.get('away_pitcher_name') or 'TBD'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with g2:
    st.markdown(
        f"""
        <div class="game-card">
          <div class="game-card__label">Status</div>
          <div class="game-card__team">{game.get("status") or "Scheduled"}</div>
          <div class="game-card__meta">{game.get("venue") or ""}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with g3:
    st.markdown(
        f"""
        <div class="game-card">
          <div class="game-card__label">Home</div>
          <div class="game-card__team">{game['home_team_name']}{home_record_badge}</div>
          <div class="game-card__meta">Probable SP: {game.get('home_pitcher_name') or 'TBD'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(render_weather_card(weather_context), unsafe_allow_html=True)

render_section_intro("Odds / line movement", "Fetch selected SportsGameOdds markets and save snapshots to track movement over time.")
sgo_api_key = get_sportsgameodds_api_key()
odd_ids = sgo_selected_odd_ids(odds_markets)
selected_books = [book.strip() for book in odds_books_text.split(",") if book.strip()]
odds_rows = []
if not sgo_api_key:
    st.info("Add SPORTSGAMEODDS_API_KEY to Streamlit secrets or your environment to enable odds.")
else:
    if st.button("Fetch latest odds", use_container_width=True):
        with st.spinner("Fetching SportsGameOdds markets..."):
            sgo_events, odds_error = fetch_sgo_events_for_date(sgo_api_key, str(selected_date), tuple(odd_ids))
        if odds_error:
            st.error(f"Odds fetch failed: {odds_error}")
        else:
            sgo_event = find_sgo_event(sgo_events, game["away_team_name"], game["home_team_name"], game)
            if not sgo_event:
                st.warning("SportsGameOdds returned MLB events, but I could not match this exact game.")
                with st.expander("Returned odds events"):
                    st.text(describe_sgo_events(sgo_events) or "No event names returned.")
            else:
                odds_rows = flatten_sgo_odds(sgo_event, selected_books)
                snapshots = read_odds_snapshots()
                odds_rows = add_odds_movement(odds_rows, snapshots)
                odds_rows = add_betting_signals_to_odds(
                    odds_rows,
                    game,
                    away_snapshot,
                    home_snapshot,
                    away_pitcher,
                    home_pitcher,
                    away_bullpen,
                    home_bullpen,
                    away_home_away,
                    home_home_away,
                    weather_context,
                )
                if save_odds_snapshot:
                    saved_count = append_odds_snapshots(odds_rows, current_game_label)
                    st.caption(f"Saved {saved_count} odds rows to local movement history.")
                st.session_state["latest_odds_rows"] = odds_rows
                st.session_state["latest_odds_game_key"] = current_game_key
    if "latest_odds_rows" in st.session_state and st.session_state.get("latest_odds_game_key") == current_game_key:
        st.markdown(render_odds_html_table(st.session_state["latest_odds_rows"]), unsafe_allow_html=True)

render_section_intro("Pitcher ER lines", "Fetch pitcher earned-run lines and prices. This section does not suggest plays or grade results.")
current_prop_pitchers = [
    {
        "team": game["away_team_name"],
        "opponent": game["home_team_name"],
        "pitcher_id": game.get("away_pitcher_id"),
        "pitcher_name": game.get("away_pitcher_name") or "TBD",
    },
    {
        "team": game["home_team_name"],
        "opponent": game["away_team_name"],
        "pitcher_id": game.get("home_pitcher_id"),
        "pitcher_name": game.get("home_pitcher_name") or "TBD",
    },
]
current_prop_pitchers = [p for p in current_prop_pitchers if p["pitcher_name"] != "TBD"]

if not current_prop_pitchers:
    st.info("No probable starters listed for this game yet.")
elif not sgo_api_key:
    st.info("Add SPORTSGAMEODDS_API_KEY to enable automatic pitcher ER line fetching.")
else:
    if st.button("Fetch ER lines", use_container_width=True):
        with st.spinner("Fetching pitcher earned-runs lines..."):
            prop_events, prop_error = fetch_sgo_events_for_pitcher_props(sgo_api_key, str(selected_date), tuple(selected_books))
        if prop_error:
            st.error(f"Pitcher ER line fetch failed: {prop_error}")
        else:
            prop_discovery_event = find_sgo_event(prop_events, game["away_team_name"], game["home_team_name"], game)
            if not prop_discovery_event:
                st.warning("SportsGameOdds returned MLB events, but I could not match this exact game for pitcher ER lines.")
                with st.expander("Returned prop events"):
                    st.text(describe_sgo_events(prop_events) or "No event names returned.")
            else:
                prop_event, prop_detail_error = fetch_sgo_event_full_odds(sgo_api_key, str(prop_discovery_event.get("eventID") or ""))
                if prop_detail_error:
                    st.error(f"Pitcher ER board fetch failed: {prop_detail_error}")
                    prop_rows = []
                else:
                    prop_rows = flatten_sgo_pitcher_er_props(prop_event, game, current_prop_pitchers, selected_books)
                prop_rows = add_pitcher_er_prop_movement(prop_rows, read_pitcher_er_prop_snapshots())
                saved_prop_snapshots = append_pitcher_er_prop_snapshots(prop_rows)
                st.session_state["latest_pitcher_er_props"] = prop_rows
                st.session_state["latest_pitcher_er_props_game_key"] = current_game_key
                if prop_rows:
                    st.caption(f"Saved {saved_prop_snapshots} pitcher ER line snapshot rows for movement tracking.")
                else:
                    st.warning("No earned-runs lines found for the listed probable starters. Lines may not be posted yet, or this book list may not carry them.")

    latest_er_props = []
    if st.session_state.get("latest_pitcher_er_props_game_key") == current_game_key:
        latest_er_props = st.session_state.get("latest_pitcher_er_props", []) or []
    if latest_er_props:
        st.dataframe(pitcher_er_props_display_df(latest_er_props), use_container_width=True, hide_index=True)

render_section_intro("Team form", "Away team is shown on the left. Home team is shown on the right. Pick the recent window, then compare hitting first and team pitching underneath.")
team_stat_window_choice = st.radio(
    "Stats window",
    ["Last 3", "Last 7", "Last 15"],
    index=1,
    horizontal=True,
    key="team_stat_window_choice",
)
team_stat_window_key, team_stat_recent_games, team_stat_window_label = {
    "Last 3": ("last3", 3, "Last 3 games"),
    "Last 7": ("last7", 7, "Last 7 games"),
    "Last 15": ("last15", 15, "Last 15 games"),
}[team_stat_window_choice]
away_team_pitching = build_team_pitching_card(team_logs, game["away_team_name"], selected_date, team_stat_recent_games)
home_team_pitching = build_team_pitching_card(team_logs, game["home_team_name"], selected_date, team_stat_recent_games)
st.markdown(
    render_team_momentum_comparison(
        away_snapshot,
        home_snapshot,
        away_team_pitching,
        home_team_pitching,
        team_stat_window_key,
        team_stat_window_label,
    ),
    unsafe_allow_html=True,
)
st.markdown(
    render_team_hitting_profile_comparison(
        away_snapshot,
        home_snapshot,
        home_pitcher.get("pitch_hand"),
        away_pitcher.get("pitch_hand"),
    ),
    unsafe_allow_html=True,
)

render_section_intro("Lefty leverage", "Checks whether a right-handed opposing starter is vulnerable to left-handed bats, then confirms with team vs RHP splits, recent form, arsenal mix, and listed lineup handedness.")
st.markdown(
    render_lefty_leverage_comparison(
        away_lefty_leverage,
        home_lefty_leverage,
        game["away_team_name"],
        game["home_team_name"],
    ),
    unsafe_allow_html=True,
)

render_section_intro("Home / away splits", "Shows whether the current home/away context is helping or hurting each offense.")
st.markdown(render_home_away_split_comparison(away_home_away, home_home_away), unsafe_allow_html=True)
st.markdown(render_home_away_context_notes(away_home_away, home_home_away), unsafe_allow_html=True)

render_section_intro("Starting pitcher form", "Season profile plus recent form for the listed probable starters.")
pitch_cols = st.columns(2)
for idx, (col, p) in enumerate(zip(pitch_cols, [away_pitcher, home_pitcher])):
    with col:
        st.markdown(render_pitcher_html_card(p), unsafe_allow_html=True)
        pitcher_fig = build_pitcher_era_figure(p, GRAPH_AWAY_COLOR if idx == 0 else GRAPH_HOME_COLOR)
        if pitcher_fig is not None:
            st.plotly_chart(pitcher_fig, use_container_width=True)

render_section_intro("Bullpen form - last 5 games", "Recent bullpen workload and traffic from official MLB boxscores.")
bullpen_cols = st.columns(2)
for col, bullpen in zip(bullpen_cols, [away_bullpen, home_bullpen]):
    with col:
        st.markdown(render_bullpen_html_card(bullpen, show_game_log=show_detail_tables), unsafe_allow_html=True)

render_section_intro("Top run producers - last 5 context games", "Listed hitters ranked by RBI + runs in their last 5 home/away games matching today's venue.")
prod_cols = st.columns(2)
for col, team_name, rows, context in zip(
    prod_cols,
    [game["away_team_name"], game["home_team_name"]],
    [away_context_production, home_context_production],
    ["away", "home"],
):
    with col:
        st.markdown(render_context_production_table(rows, team_name, context), unsafe_allow_html=True)

render_section_intro("Expected lineup form", "Posted lineup when available; otherwise the best currently active bats.")
lineup_cols = st.columns(2)
for col, team_name, lineup_rows, posted in zip(
    lineup_cols,
    [game["away_team_name"], game["home_team_name"]],
    [away_lineup, home_lineup],
    [away_posted, home_posted],
):
    with col:
        st.markdown(f"#### {team_name}")
        st.caption("Posted lineup" if posted else "Lineup not posted yet — showing best current active bats")
        if not lineup_rows:
            st.info("No lineup or hitter data available.")
        else:
            if show_detail_tables:
                st.markdown(render_lineup_html_table(lineup_rows), unsafe_allow_html=True)
            else:
                compact_rows = lineup_rows[:5]
                st.markdown(render_lineup_html_table(compact_rows), unsafe_allow_html=True)
                if len(lineup_rows) > len(compact_rows):
                    st.caption("Showing top 5 in Simple mode. Switch to Detailed for the full table.")

render_section_intro("Hitter consistency", "Season batting average compared with 30-day, 15-day, and 7-day hit form.")
consistency_cols = st.columns(2)
for col, team_name, lineup_rows in zip(
    consistency_cols,
    [game["away_team_name"], game["home_team_name"]],
    [away_lineup, home_lineup],
):
    with col:
        shown_rows = None if show_detail_tables else 5
        st.markdown(render_hitter_consistency_table(lineup_rows, team_name, limit=shown_rows), unsafe_allow_html=True)

render_section_intro("Betting notes", "Plain-language notes based on the signals above.")
away_notes = build_betting_notes(away_snapshot, home_pitcher, away_pitcher, away_lineup, game["home_team_name"], home_bullpen, away_bullpen)
home_notes = build_betting_notes(home_snapshot, away_pitcher, home_pitcher, home_lineup, game["away_team_name"], away_bullpen, home_bullpen)
n1, n2 = st.columns(2)
with n1:
    st.markdown(
        render_notes_html_card(f"{game['away_team_name']} offense vs {home_pitcher.get('name', 'TBD')}", away_notes),
        unsafe_allow_html=True,
    )
with n2:
    st.markdown(
        render_notes_html_card(f"{game['home_team_name']} offense vs {away_pitcher.get('name', 'TBD')}", home_notes),
        unsafe_allow_html=True,
    )

render_section_intro("OBP / OPS trend chart", "Rolling offensive trend for the two teams in this matchup.")
range_choice = st.radio(
    "Chart range",
    ["Full season", "Last 30", "Last 14", "Last 7", "Custom"],
    horizontal=True,
)

selected_teams = [game["away_team_name"], game["home_team_name"]]
plot_df = team_logs[team_logs["team"].isin(selected_teams)].copy()
plot_df = add_rolling_team_metric(plot_df, metric, window)

if not plot_df.empty:
    min_date = plot_df["date"].min().date()
    max_date = plot_df["date"].max().date()

    if range_choice == "Full season":
        start_date, end_date = min_date, max_date
    elif range_choice == "Last 30":
        start_date = max(min_date, max_date - pd.Timedelta(days=29))
        end_date = max_date
    elif range_choice == "Last 14":
        start_date = max(min_date, max_date - pd.Timedelta(days=13))
        end_date = max_date
    elif range_choice == "Last 7":
        start_date = max(min_date, max_date - pd.Timedelta(days=6))
        end_date = max_date
    else:
        start_date, end_date = st.slider(
            "Custom chart range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
        )

    plot_df = plot_df[(plot_df["date"].dt.date >= start_date) & (plot_df["date"].dt.date <= end_date)].copy()

line_shape = "spline" if smooth_lines else "linear"
fig = go.Figure()
for idx, team in enumerate(selected_teams):
    team_df = plot_df[plot_df["team"] == team].sort_values("date")
    color = GRAPH_AWAY_COLOR if idx == 0 else GRAPH_HOME_COLOR
    if chart_mode == "Rolling + daily":
        fig.add_trace(
            go.Scatter(
                x=team_df["date"],
                y=team_df[metric],
                mode="lines",
                name=f"{team} daily",
                line=dict(color=color, width=2, dash="dot", shape=line_shape),
                opacity=0.38,
                showlegend=False,
                hovertemplate="%{x|%Y-%m-%d}<br>Daily: %{y:.3f}<extra></extra>",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=team_df["date"],
            y=team_df["rolling_value"],
            mode="lines",
            name=f"{team} ({'Away' if idx == 0 else 'Home'})",
            line=dict(color=color, width=4.5, shape=line_shape),
            hovertemplate="%{x|%Y-%m-%d}<br>Rolling: %{y:.3f}<extra></extra>",
        )
    )

all_y = pd.concat([plot_df["rolling_value"], plot_df[metric]]) if chart_mode == "Rolling + daily" else plot_df["rolling_value"]
all_y = all_y.dropna()
y_range = None
if not all_y.empty:
    y_range = [max(0, float(all_y.min()) - 0.015), float(all_y.max()) + 0.015]

fig.update_layout(
    title=f"{metric.upper()} trend comparison",
    height=560,
    hovermode="x unified",
    legend_title_text="Team",
    template="plotly_dark",
    paper_bgcolor="#070d18",
    plot_bgcolor="#0b1220",
    font=dict(color="#f8fafc", size=15),
    margin=dict(l=20, r=20, t=60, b=20),
)
fig.update_xaxes(gridcolor="#26364a", zerolinecolor="#334155", color="#cbd5e1")
fig.update_yaxes(title_text=metric.upper(), tickformat=".3f", range=y_range)
fig.update_yaxes(gridcolor="#26364a", zerolinecolor="#334155", color="#cbd5e1")
fig.update_xaxes(title_text="Date")
st.plotly_chart(fig, use_container_width=True)
