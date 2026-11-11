
from __future__ import annotations

import os
import io
import math
import html
import textwrap
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="Sports Betting Dashboard", layout="wide")

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
NCAAF_TEAM_LOG_PATH = APP_DIR / "data" / "ncaaf_team_game_logs.csv"
NCAAF_FAMILIARITY_FLAGS_PATH = APP_DIR / "data" / "ncaaf_familiarity_flags.csv"
NCAAF_INJURY_REPORT_PATH = APP_DIR / "data" / "ncaaf_injury_report.csv"
NCAAF_OL_CONTINUITY_PATH = APP_DIR / "data" / "ncaaf_ol_continuity_flags.csv"
NFL_TEAM_LOG_PATH = APP_DIR / "data" / "nfl_team_game_logs.csv"
NFL_FAMILIARITY_FLAGS_PATH = APP_DIR / "data" / "nfl_familiarity_flags.csv"
NFL_INJURY_REPORT_PATH = APP_DIR / "data" / "nfl_injury_report.csv"
NFL_OL_CONTINUITY_PATH = APP_DIR / "data" / "nfl_ol_continuity_flags.csv"
NFL_SNAP_COUNTS_PATH = APP_DIR / "data" / "nfl_player_snap_counts.csv"
ESPN_CFB_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
ESPN_CFB_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary"
ESPN_NFL_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
ESPN_NFL_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
ESPN_FOOTBALL_POWER_INDEX_URL = "https://site.web.api.espn.com/apis/fitt/v3/sports/football/{league}/powerindex"
CFBD_BASE_URL = "https://api.collegefootballdata.com"
COVERS_NCAAF_INJURIES_URL = "https://www.covers.com/sport/football/ncaaf/injuries"
ACC_AVAILABILITY_REPORT_URL = "https://theacc.com/sports/2025/8/28/availability-reporting-football.aspx"
ACC_AVAILABILITY_API_URL = "https://app.hdintelligence.com/api/get-publish-public"
COVERS_NFL_INJURIES_URL = "https://www.covers.com/sport/football/nfl/injuries"
COVERS_BASE_URL = "https://www.covers.com"
NFLVERSE_SNAP_COUNTS_URL = "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv"
NFLVERSE_INJURIES_URL = "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv"
NFLVERSE_INJURIES_INFO_URL = "https://nflreadr.nflverse.com/articles/dictionary_injuries.html"
NFL_OFFICIAL_INACTIVES_URL = "https://www.nfl.com/news/nfl-week-{week}-inactives-players-ruled-out-sunday-{season}-season"

NCAAF_TEAM_LOG_COLUMNS = [
    "game_id",
    "date",
    "season",
    "week",
    "season_type",
    "team",
    "team_id",
    "opponent",
    "opponent_id",
    "home_away",
    "neutral_site",
    "points",
    "opponent_points",
    "win",
    "total_yards",
    "yards_allowed",
    "plays",
    "plays_allowed",
    "pass_attempts",
    "pass_attempts_allowed",
    "sacks_allowed",
    "sacks_made",
    "sack_rate_allowed",
    "sack_rate_made",
    "yards_per_play",
    "yards_per_play_allowed",
    "plays_per_point",
    "plays_per_point_allowed",
    "points_per_play",
    "points_per_play_allowed",
    "yards_per_point",
    "yards_per_point_allowed",
    "passing_yards",
    "passing_yards_allowed",
    "rushing_yards",
    "rushing_yards_allowed",
    "rushing_attempts",
    "rushing_attempts_allowed",
    "run_rate",
    "run_rate_allowed",
    "pass_rate",
    "pass_rate_allowed",
    "yards_per_rush",
    "yards_per_pass",
    "first_downs",
    "third_down_conv",
    "third_down_att",
    "third_down_pct",
    "third_down_conv_allowed",
    "third_down_att_allowed",
    "third_down_pct_allowed",
    "red_zone_td",
    "red_zone_trips",
    "red_zone_td_pct",
    "red_zone_td_allowed",
    "red_zone_trips_allowed",
    "red_zone_td_pct_allowed",
    "goal_to_go_td",
    "goal_to_go_trips",
    "goal_to_go_td_pct",
    "goal_to_go_td_allowed",
    "goal_to_go_trips_allowed",
    "goal_to_go_td_pct_allowed",
    "goal_to_go_stop_pct",
    "short_yardage_conv",
    "short_yardage_att",
    "short_yardage_pct",
    "short_yardage_conv_allowed",
    "short_yardage_att_allowed",
    "short_yardage_pct_allowed",
    "short_yardage_stop_pct",
    "rush_stuffed",
    "rush_attempts_charted",
    "rush_stuffed_rate",
    "rush_stuffs",
    "rush_stuff_opportunities",
    "rush_stuff_rate",
    "fourth_down_conv",
    "fourth_down_att",
    "turnovers",
    "takeaways",
    "turnover_margin",
    "possession_seconds",
]

NCAAF_FAMILIARITY_COLUMNS = [
    "game_date",
    "season",
    "week",
    "team",
    "opponent",
    "person",
    "role",
    "connection_team",
    "connection_type",
    "impact",
    "confidence",
    "source_url",
    "note",
]

NCAAF_OL_CONTINUITY_COLUMNS = [
    "updated_at",
    "season",
    "team",
    "status",
    "line_combinations",
    "penalty_points",
    "source_url",
    "note",
]

NCAAF_INJURY_COLUMNS = [
    "updated_at",
    "game_date",
    "team",
    "opponent",
    "player",
    "position",
    "status",
    "injury",
    "news_date",
    "role",
    "role_basis",
    "role_checked_at",
    "production",
    "impact",
    "impact_points",
    "source_url",
    "team_url",
    "note",
    "snap_week",
    "snap_games",
    "offense_snaps",
    "offense_pct",
    "recent_offense_pct",
    "defense_snaps",
    "defense_pct",
    "recent_defense_pct",
    "st_snaps",
    "st_pct",
    "recent_st_pct",
    "snap_source_url",
]

NFL_SNAP_COUNT_COLUMNS = [
    "game_id",
    "pfr_game_id",
    "season",
    "game_type",
    "week",
    "player",
    "pfr_player_id",
    "position",
    "team",
    "opponent",
    "offense_snaps",
    "offense_pct",
    "defense_snaps",
    "defense_pct",
    "st_snaps",
    "st_pct",
]

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
DEFAULT_ODDS_BOOKS = "bet365,draftkings,fanduel,betmgm,caesars"

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
      <div class="dashboard-hero__eyebrow">Sports analytics workspace</div>
      <div class="dashboard-hero__title">MLB / NCAAF / NFL Betting Dashboard</div>
      <div class="dashboard-hero__subtitle">Slate context, team momentum, matchup profiles, odds movement and rule-based shortlist reads in one view.</div>
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

def sportsgameodds_get_all_events(
    api_key: str,
    params: dict,
    max_pages: int = 6,
) -> tuple[list[dict], str]:
    """Fetch every event page while preserving the exact cursor query."""
    events = []
    seen_event_ids = set()
    seen_cursors = set()
    cursor = ""
    for _ in range(max_pages):
        page_params = dict(params)
        if cursor:
            page_params["cursor"] = cursor
        try:
            data = sportsgameodds_get("/events", api_key, page_params)
        except requests.HTTPError as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if events and status_code == 404:
                break
            return events, str(exc)
        except Exception as exc:
            return events, str(exc)
        if not data.get("success", True):
            return events, str(data.get("error", "SportsGameOdds request failed."))

        page_events = data.get("data", []) or []
        if not page_events and cursor:
            break
        for event in page_events:
            event_id = str((event or {}).get("eventID") or "")
            dedupe_key = event_id or f"anonymous-{len(events)}"
            if dedupe_key in seen_event_ids:
                continue
            seen_event_ids.add(dedupe_key)
            events.append(event)

        next_cursor = str(data.get("nextCursor") or "").strip()
        if not next_cursor or next_cursor in seen_cursors:
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return events, ""

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

NCAAF_TEAM_NAME_ALIASES = {
    "appalachianstate": {"appalachianstate", "appstate", "appstatemountaineers"},
    "california": {"california", "cal", "calgoldenbears"},
    "connecticut": {"connecticut", "uconn", "uconnhuskies"},
    "floridaatlantic": {"floridaatlantic", "fau", "fauowls"},
    "floridainternational": {"floridainternational", "fiu", "fiupanthers"},
    "louisianamonroe": {"louisianamonroe", "ulmonroe", "ulm", "ulmonroewarhawks"},
    "massachusetts": {"massachusetts", "umass", "massachusettsminutemen"},
    "miamiflorida": {"miamiflorida", "miamifl", "miamihurricanes"},
    "miamiohio": {"miamiohio", "miamioh", "miamiohredhawks"},
    "middletennessee": {"middletennessee", "middletennesseestate", "middletennesseeblueraiders"},
    "mississippi": {"mississippi", "olemiss", "olemissrebels"},
    "northcarolinastate": {"northcarolinastate", "ncstate", "ncstatewolfpack"},
    "pittsburgh": {"pittsburgh", "pitt", "pittpanthers"},
    "sanjosestate": {"sanjosestate", "sanjosestatespartans", "sanjoséstate", "sanjoséstatespartans"},
    "southerncalifornia": {"southerncalifornia", "usc", "usctrojans"},
    "southernmississippi": {"southernmississippi", "southernmiss", "southernmissgoldeneagles"},
    "tennesseemartin": {"tennesseemartin", "utmartin", "utmartinskyhawks"},
    "texasriograndevalley": {"texasriograndevalley", "utrgv", "utrgvvaqueros"},
}

NFL_TEAM_ABBREVIATION_ALIASES = {
    "ARI": {"arizona", "arizonacardinals", "cardinals"},
    "ATL": {"atlanta", "atlantafalcons", "falcons"},
    "BAL": {"baltimore", "baltimoreravens", "ravens"},
    "BUF": {"buffalo", "buffalobills", "bills"},
    "CAR": {"carolina", "carolinapanthers", "panthers"},
    "CHI": {"chicago", "chicagobears", "bears"},
    "CIN": {"cincinnati", "cincinnatibengals", "bengals"},
    "CLE": {"cleveland", "clevelandbrowns", "browns"},
    "DAL": {"dallas", "dallascowboys", "cowboys"},
    "DEN": {"denver", "denverbroncos", "broncos"},
    "DET": {"detroit", "detroitlions", "lions"},
    "GB": {"greenbay", "greenbaypackers", "packers"},
    "HOU": {"houston", "houstontexans", "texans"},
    "IND": {"indianapolis", "indianapoliscolts", "colts"},
    "JAX": {"jacksonville", "jacksonvillejaguars", "jaguars"},
    "KC": {"kansascity", "kansascitychiefs", "chiefs"},
    "LV": {"lasvegas", "lasvegasraiders", "raiders"},
    "LAC": {"lachargers", "losangeleschargers", "chargers"},
    "LAR": {"la", "larams", "losangelesrams", "rams"},
    "MIA": {"miami", "miamidolphins", "dolphins"},
    "MIN": {"minnesota", "minnesotavikings", "vikings"},
    "NE": {"newengland", "newenglandpatriots", "patriots"},
    "NO": {"neworleans", "neworleanssaints", "saints"},
    "NYG": {"nygiants", "newyorkgiants", "giants"},
    "NYJ": {"nyjets", "newyorkjets", "jets"},
    "PHI": {"philadelphia", "philadelphiaeagles", "eagles"},
    "PIT": {"pittsburgh", "pittsburghsteelers", "steelers"},
    "SF": {"sanfrancisco", "sanfrancisco49ers", "49ers"},
    "SEA": {"seattle", "seattleseahawks", "seahawks"},
    "TB": {"tampabay", "tampabaybuccaneers", "buccaneers", "bucs"},
    "TEN": {"tennessee", "tennesseetitans", "titans"},
    "WAS": {"washington", "washingtoncommanders", "commanders"},
}

NFL_TEAM_DISPLAY_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LA": "Los Angeles Rams", "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

def nfl_team_abbreviation(value: Any) -> str:
    normalized = normalize_name(value)
    for abbreviation, aliases in NFL_TEAM_ABBREVIATION_ALIASES.items():
        if normalized == normalize_name(abbreviation) or normalized in aliases:
            return abbreviation
    return ""

def ncaaf_team_name_keys(value: Any) -> set[str]:
    normalized = normalize_name(value)
    for league_suffix in ("ncaaf", "nfl"):
        if normalized.endswith(league_suffix):
            normalized = normalized[: -len(league_suffix)]
            break
    keys = {normalized}
    for canonical, aliases in NCAAF_TEAM_NAME_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            keys.update(aliases)
            keys.add(canonical)
            break
    return {key for key in keys if key}

def ncaaf_team_names_match(expected: str, candidates: list[str]) -> bool:
    expected_keys = ncaaf_team_name_keys(expected)
    ambiguous_school_suffixes = (
        "state",
        "tech",
        "international",
        "atlantic",
        "southern",
        "northern",
        "western",
        "eastern",
        "central",
        "christian",
        "aandm",
    )
    for candidate in candidates:
        candidate_keys = ncaaf_team_name_keys(candidate)
        if expected_keys & candidate_keys:
            return True
        for expected_key in expected_keys:
            for candidate_key in candidate_keys:
                # ESPN normally appends the mascot while SGO supplies the
                # school name or abbreviation (USC, UAB, BYU, TCU, etc.).
                remainder = expected_key[len(candidate_key):] if expected_key.startswith(candidate_key) else ""
                ambiguous_extension = any(remainder.startswith(suffix) for suffix in ambiguous_school_suffixes)
                if len(candidate_key) >= 3 and remainder and not ambiguous_extension:
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

def find_sgo_event(
    events: list[dict],
    away_team: str,
    home_team: str,
    game: dict | None = None,
    name_matcher: Any = None,
) -> dict:
    matcher = name_matcher or team_names_match
    matches = []
    for event in events:
        away_names = sgo_team_names(event, "away")
        home_names = sgo_team_names(event, "home")
        if matcher(away_team, away_names) and matcher(home_team, home_names):
            matches.append(event)
    if not matches:
        return {}
    if len(matches) == 1:
        return matches[0]

    target_start = parse_timestamp_utc((game or {}).get("game_time") or (game or {}).get("date"))
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

@st.cache_data(ttl=120)
def fetch_sgo_ncaaf_events_for_date(api_key: str, game_date: str) -> tuple[list[dict], str]:
    """Fetch the two side markets needed by the NCAAF matchup signals."""
    if not api_key:
        return [], "Missing SportsGameOdds API key."
    start = f"{game_date}T00:00:00Z"
    # A US Saturday slate can run into Sunday morning UTC, but a two-day
    # window also pulls the following slate and can push relevant games off
    # the first API page. Noon UTC the next day safely covers late kickoffs.
    end = (pd.Timestamp(game_date) + pd.Timedelta(days=1, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "leagueID": "NCAAF",
        "startsAfter": start,
        "startsBefore": end,
        "oddID": ",".join(
            [
                "points-away-game-ml-away",
                "points-home-game-ml-home",
                "points-away-game-sp-away",
                "points-home-game-sp-home",
            ]
        ),
        "includeOpposingOdds": "true",
        "includeOpenCloseOdds": "true",
        "limit": 100,
    }
    return sportsgameodds_get_all_events(api_key, params)

@st.cache_data(ttl=120)
def fetch_sgo_nfl_events_for_date(api_key: str, game_date: str) -> tuple[list[dict], str]:
    """Fetch NFL spread and moneyline markets for the selected slate date."""
    if not api_key:
        return [], "Missing SportsGameOdds API key."
    start = f"{game_date}T00:00:00Z"
    end = (pd.Timestamp(game_date) + pd.Timedelta(days=1, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "leagueID": "NFL",
        "startsAfter": start,
        "startsBefore": end,
        "oddID": ",".join(
            [
                "points-away-game-ml-away",
                "points-home-game-ml-home",
                "points-away-game-sp-away",
                "points-home-game-sp-home",
            ]
        ),
        "includeOpposingOdds": "true",
        "includeOpenCloseOdds": "true",
        "limit": 100,
    }
    return sportsgameodds_get_all_events(api_key, params)

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
    # Matchup analysis should use pregame context for the selected slate.
    # After midnight in Europe, the US slate is often still active, so requiring
    # same-date results would hide saved shortlist reads before games are done.
    return min(selected - pd.Timedelta(days=1), today - pd.Timedelta(days=1))

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

def ncaaf_season_for_date(selected_date: Any) -> int:
    date = pd.Timestamp(selected_date)
    return date.year if date.month >= 7 else date.year - 1

def ncaaf_season_start(season: int) -> pd.Timestamp:
    return pd.Timestamp(f"{season}-08-01")

def ncaaf_season_end(season: int) -> pd.Timestamp:
    return pd.Timestamp(f"{season + 1}-01-31")

def nfl_season_for_date(selected_date: Any) -> int:
    date = pd.Timestamp(selected_date)
    return date.year if date.month >= 3 else date.year - 1

def nfl_season_start(season: int) -> pd.Timestamp:
    return pd.Timestamp(f"{season}-08-01")

def nfl_season_end(season: int) -> pd.Timestamp:
    return pd.Timestamp(f"{season + 1}-02-28")

def ncaaf_date_code(selected_date: Any) -> str:
    return pd.Timestamp(selected_date).strftime("%Y%m%d")

def ncaaf_empty_team_logs() -> pd.DataFrame:
    return pd.DataFrame(columns=NCAAF_TEAM_LOG_COLUMNS)

def ncaaf_data_signature() -> float:
    if NCAAF_TEAM_LOG_PATH.exists():
        return NCAAF_TEAM_LOG_PATH.stat().st_mtime
    return 0.0

def ncaaf_familiarity_signature() -> float:
    if NCAAF_FAMILIARITY_FLAGS_PATH.exists():
        return NCAAF_FAMILIARITY_FLAGS_PATH.stat().st_mtime
    return 0.0

def ncaaf_injury_signature() -> float:
    if NCAAF_INJURY_REPORT_PATH.exists():
        return NCAAF_INJURY_REPORT_PATH.stat().st_mtime
    return 0.0

def ncaaf_ol_continuity_signature() -> float:
    if NCAAF_OL_CONTINUITY_PATH.exists():
        return NCAAF_OL_CONTINUITY_PATH.stat().st_mtime
    return 0.0

def nfl_data_signature() -> float:
    return NFL_TEAM_LOG_PATH.stat().st_mtime if NFL_TEAM_LOG_PATH.exists() else 0.0

def nfl_familiarity_signature() -> float:
    return NFL_FAMILIARITY_FLAGS_PATH.stat().st_mtime if NFL_FAMILIARITY_FLAGS_PATH.exists() else 0.0

def nfl_injury_signature() -> float:
    return NFL_INJURY_REPORT_PATH.stat().st_mtime if NFL_INJURY_REPORT_PATH.exists() else 0.0

def nfl_ol_continuity_signature() -> float:
    return NFL_OL_CONTINUITY_PATH.stat().st_mtime if NFL_OL_CONTINUITY_PATH.exists() else 0.0

def nfl_snap_counts_signature() -> float:
    return NFL_SNAP_COUNTS_PATH.stat().st_mtime if NFL_SNAP_COUNTS_PATH.exists() else 0.0

def get_cfbd_api_key() -> str:
    try:
        key = st.secrets.get("CFBD_API_KEY", "")
    except Exception:
        key = ""
    return str(key or os.getenv("CFBD_API_KEY", "") or "").strip()

@st.cache_data
def load_ncaaf_team_logs(data_signature: float) -> pd.DataFrame:
    if NCAAF_TEAM_LOG_PATH.exists():
        return pd.read_csv(NCAAF_TEAM_LOG_PATH)
    return ncaaf_empty_team_logs()

@st.cache_data
def load_ncaaf_familiarity_flags(data_signature: float) -> pd.DataFrame:
    if NCAAF_FAMILIARITY_FLAGS_PATH.exists():
        return pd.read_csv(NCAAF_FAMILIARITY_FLAGS_PATH)
    return pd.DataFrame(columns=NCAAF_FAMILIARITY_COLUMNS)

@st.cache_data
def load_ncaaf_injury_report(data_signature: float) -> pd.DataFrame:
    if NCAAF_INJURY_REPORT_PATH.exists():
        return pd.read_csv(NCAAF_INJURY_REPORT_PATH)
    return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)

@st.cache_data
def load_ncaaf_ol_continuity_flags(data_signature: float) -> pd.DataFrame:
    if NCAAF_OL_CONTINUITY_PATH.exists():
        return pd.read_csv(NCAAF_OL_CONTINUITY_PATH)
    return pd.DataFrame(columns=NCAAF_OL_CONTINUITY_COLUMNS)

@st.cache_data
def load_nfl_team_logs(data_signature: float) -> pd.DataFrame:
    if NFL_TEAM_LOG_PATH.exists():
        return pd.read_csv(NFL_TEAM_LOG_PATH)
    return ncaaf_empty_team_logs()

@st.cache_data
def load_nfl_familiarity_flags(data_signature: float) -> pd.DataFrame:
    if NFL_FAMILIARITY_FLAGS_PATH.exists():
        return pd.read_csv(NFL_FAMILIARITY_FLAGS_PATH)
    return pd.DataFrame(columns=NCAAF_FAMILIARITY_COLUMNS)

@st.cache_data
def load_nfl_injury_report(data_signature: float) -> pd.DataFrame:
    if NFL_INJURY_REPORT_PATH.exists():
        return pd.read_csv(NFL_INJURY_REPORT_PATH)
    return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)

@st.cache_data
def load_nfl_ol_continuity_flags(data_signature: float) -> pd.DataFrame:
    if NFL_OL_CONTINUITY_PATH.exists():
        return pd.read_csv(NFL_OL_CONTINUITY_PATH)
    return pd.DataFrame(columns=NCAAF_OL_CONTINUITY_COLUMNS)

@st.cache_data
def load_nfl_snap_counts(data_signature: float) -> pd.DataFrame:
    if NFL_SNAP_COUNTS_PATH.exists():
        return pd.read_csv(NFL_SNAP_COUNTS_PATH)
    return pd.DataFrame(columns=NFL_SNAP_COUNT_COLUMNS)

def prepare_nfl_snap_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=NFL_SNAP_COUNT_COLUMNS)
    out = df.copy()
    out.columns = [str(col).strip().lower() for col in out.columns]
    for col in NFL_SNAP_COUNT_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in ["game_id", "pfr_game_id", "game_type", "player", "pfr_player_id", "position", "team", "opponent"]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    for col in ["season", "week", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct", "st_snaps", "st_pct"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[NFL_SNAP_COUNT_COLUMNS].sort_values(["season", "week", "game_id", "player"]).reset_index(drop=True)

def update_nfl_snap_counts(season: int) -> tuple[bool, str]:
    try:
        source_url = NFLVERSE_SNAP_COUNTS_URL.format(season=int(season))
        response = requests.get(source_url, timeout=60)
        response.raise_for_status()
        snaps = prepare_nfl_snap_counts(pd.read_csv(io.StringIO(response.text)))
        if snaps.empty:
            return False, "nflverse returned an empty snap-count file; the saved file was left unchanged."
        snaps = snaps[pd.to_numeric(snaps["season"], errors="coerce") == int(season)].copy()
        NFL_SNAP_COUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        snaps.to_csv(NFL_SNAP_COUNTS_PATH, index=False)
        latest_week = safe_int(snaps["week"].max())
        return True, f"Saved {len(snaps)} NFL player-game snap rows through Week {latest_week} from nflverse."
    except Exception as exc:
        return False, str(exc)

def nfl_enrich_injuries_with_snap_counts(injuries: pd.DataFrame, snaps: pd.DataFrame) -> pd.DataFrame:
    out = prepare_ncaaf_injury_report(injuries)
    snap_data = prepare_nfl_snap_counts(snaps)
    if out.empty or snap_data.empty:
        return out
    regular = snap_data[snap_data["game_type"].str.upper().eq("REG")].copy()
    if regular.empty:
        regular = snap_data.copy()
    source_url = NFLVERSE_SNAP_COUNTS_URL.format(season=safe_int(regular["season"].max()))
    ol_positions = {"OL", "OT", "OG", "C", "T", "G", "LT", "RT", "LG", "RG"}

    for index, injury in out.iterrows():
        team_abbr = nfl_team_abbreviation(injury.get("team"))
        if not team_abbr:
            continue
        candidates = regular[
            regular["team"].map(nfl_team_abbreviation).eq(team_abbr)
            & regular["player"].map(lambda value: ncaaf_player_names_match(injury.get("player"), value))
        ].sort_values(["season", "week", "game_id"])
        if candidates.empty:
            continue
        active = candidates[
            candidates[["offense_snaps", "defense_snaps", "st_snaps"]].fillna(0).sum(axis=1) > 0
        ]
        if active.empty:
            continue
        recent = active.tail(3)
        latest = active.iloc[-1]
        out.at[index, "snap_week"] = safe_int(latest.get("week"))
        out.at[index, "snap_games"] = len(recent)
        injury_factor = ncaaf_injury_status_factor(injury.get("status"))
        for unit in ["offense", "defense", "st"]:
            out.at[index, f"{unit}_snaps"] = safe_float(latest.get(f"{unit}_snaps"))
            out.at[index, f"{unit}_pct"] = safe_float(latest.get(f"{unit}_pct"))
            usage_series = pd.to_numeric(recent[f"{unit}_pct"], errors="coerce").dropna()
            recent_usage = safe_float(usage_series.mean())
            if injury_factor > 0 and len(usage_series) >= 2:
                prior_usage = safe_float(usage_series.iloc[:-1].mean())
                latest_usage = safe_float(usage_series.iloc[-1])
                if pd.notna(prior_usage) and pd.notna(latest_usage) and latest_usage < prior_usage * 0.55:
                    recent_usage = prior_usage
            out.at[index, f"recent_{unit}_pct"] = recent_usage
        out.at[index, "snap_source_url"] = source_url

        unit_values = {
            "offense": safe_float(out.at[index, "recent_offense_pct"]),
            "defense": safe_float(out.at[index, "recent_defense_pct"]),
            "special teams": safe_float(out.at[index, "recent_st_pct"]),
        }
        unit, usage = max(unit_values.items(), key=lambda item: -1 if pd.isna(item[1]) else item[1])
        if pd.isna(usage):
            continue
        latest_pct = safe_float(out.at[index, f"{unit.replace('special teams', 'st')}_pct"])
        latest_snaps = safe_float(out.at[index, f"{unit.replace('special teams', 'st')}_snaps"])
        snap_summary = (
            f"Last active W{safe_int(latest.get('week'))}: {safe_int(latest_snaps)} {unit} snaps "
            f"({latest_pct:.0%}); recent share {usage:.0%}"
        )
        existing_production = str(out.at[index, "production"] or "").strip()
        if snap_summary not in existing_production:
            out.at[index, "production"] = " · ".join(filter(None, [existing_production, snap_summary]))

        position = str(injury.get("position") or "").upper()
        if position in ol_positions and unit == "offense":
            out.at[index, "role"] = (
                f"Starting offensive lineman — {usage:.0%} recent offensive snaps"
                if usage >= 0.65
                else f"Rotational offensive lineman — {usage:.0%} recent offensive snaps"
            )
            out.at[index, "role_basis"] = "nflverse game-level snap counts; modeled in pass-protection adjustment"
        elif usage >= 0.20:
            if unit == "special teams":
                if usage >= 0.75:
                    role_label, base_impact = "Full-time special-teams contributor", 0.25
                elif usage >= 0.45:
                    role_label, base_impact = "Primary special-teams contributor", 0.15
                else:
                    role_label, base_impact = "Rotational special-teams contributor", 0.05
            elif usage >= 0.75:
                role_label, base_impact = f"Full-time {unit} starter", 1.25
            elif usage >= 0.45:
                role_label, base_impact = f"Primary {unit} contributor", 0.80
            else:
                role_label, base_impact = f"Rotational {unit} contributor", 0.35

            injury_factor = ncaaf_injury_status_factor(injury.get("status"))
            snap_impact = base_impact * injury_factor
            existing_impact = safe_float(out.at[index, "impact_points"])
            existing_impact = 0.0 if pd.isna(existing_impact) else existing_impact
            impact_points = max(existing_impact, snap_impact)
            if existing_impact <= 0:
                out.at[index, "role"] = f"{role_label} — {usage:.0%} recent snaps"
                out.at[index, "role_basis"] = "nflverse game-level snap counts"
            elif "nflverse" not in str(out.at[index, "role_basis"] or "").lower():
                out.at[index, "role_basis"] = " · ".join(
                    filter(None, [str(out.at[index, "role_basis"] or "").strip(), "nflverse snap share cross-check"])
                )
            out.at[index, "impact_points"] = round(impact_points, 2)
            out.at[index, "impact"] = (
                "critical" if impact_points >= 3.0 else (
                    "high" if impact_points >= 1.0 else ("medium" if impact_points > 0 else "listed")
                )
            )
    return prepare_ncaaf_injury_report(out)

def prepare_ncaaf_team_logs(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return ncaaf_empty_team_logs()
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    for col in NCAAF_TEAM_LOG_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in ["team", "opponent", "home_away", "season_type"]:
        out[col] = out[col].astype(str).str.strip()
    numeric_cols = [
        "game_id",
        "season",
        "week",
        "team_id",
        "opponent_id",
        "points",
        "opponent_points",
        "total_yards",
        "yards_allowed",
        "plays",
        "plays_allowed",
        "pass_attempts",
        "pass_attempts_allowed",
        "sacks_allowed",
        "sacks_made",
        "sack_rate_allowed",
        "sack_rate_made",
        "yards_per_play",
        "yards_per_play_allowed",
        "plays_per_point",
        "plays_per_point_allowed",
        "points_per_play",
        "points_per_play_allowed",
        "yards_per_point",
        "yards_per_point_allowed",
        "passing_yards",
        "passing_yards_allowed",
        "rushing_yards",
        "rushing_yards_allowed",
        "rushing_attempts",
        "rushing_attempts_allowed",
        "run_rate",
        "run_rate_allowed",
        "pass_rate",
        "pass_rate_allowed",
        "yards_per_rush",
        "yards_per_pass",
        "first_downs",
        "third_down_conv",
        "third_down_att",
        "third_down_pct",
        "third_down_conv_allowed",
        "third_down_att_allowed",
        "third_down_pct_allowed",
        "red_zone_td",
        "red_zone_trips",
        "red_zone_td_pct",
        "red_zone_td_allowed",
        "red_zone_trips_allowed",
        "red_zone_td_pct_allowed",
        "goal_to_go_td",
        "goal_to_go_trips",
        "goal_to_go_td_pct",
        "goal_to_go_td_allowed",
        "goal_to_go_trips_allowed",
        "goal_to_go_td_pct_allowed",
        "goal_to_go_stop_pct",
        "short_yardage_conv",
        "short_yardage_att",
        "short_yardage_pct",
        "short_yardage_conv_allowed",
        "short_yardage_att_allowed",
        "short_yardage_pct_allowed",
        "short_yardage_stop_pct",
        "rush_stuffed",
        "rush_attempts_charted",
        "rush_stuffed_rate",
        "rush_stuffs",
        "rush_stuff_opportunities",
        "rush_stuff_rate",
        "fourth_down_conv",
        "fourth_down_att",
        "turnovers",
        "takeaways",
        "turnover_margin",
        "possession_seconds",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    # Older saved logs already contain both teams' offensive third-down data.
    # Backfill the defensive view from the opponent row so this stat appears
    # immediately without forcing a full historical re-download.
    third_down_lookup = {
        (str(row.get("game_id")), str(row.get("team") or "").strip().lower()): (
            row.get("third_down_conv"),
            row.get("third_down_att"),
            row.get("third_down_pct"),
        )
        for _, row in out.iterrows()
    }
    derived_allowed = [
        third_down_lookup.get(
            (str(row.get("game_id")), str(row.get("opponent") or "").strip().lower()),
            (float("nan"), float("nan"), float("nan")),
        )
        for _, row in out.iterrows()
    ]
    for idx, col in enumerate(
        ["third_down_conv_allowed", "third_down_att_allowed", "third_down_pct_allowed"]
    ):
        derived = pd.Series([values[idx] for values in derived_allowed], index=out.index, dtype="float64")
        out[col] = out[col].fillna(derived)
    out["win"] = out["win"].fillna(False).astype(bool)
    out["neutral_site"] = out["neutral_site"].fillna(False).astype(bool)
    return out[NCAAF_TEAM_LOG_COLUMNS].sort_values(["team", "date", "game_id"]).reset_index(drop=True)

def prepare_ncaaf_ol_continuity_flags(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=NCAAF_OL_CONTINUITY_COLUMNS)
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    for col in NCAAF_OL_CONTINUITY_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    out["updated_at"] = pd.to_datetime(out["updated_at"], errors="coerce", utc=True)
    out["season"] = pd.to_numeric(out["season"], errors="coerce")
    out["line_combinations"] = pd.to_numeric(out["line_combinations"], errors="coerce")
    out["penalty_points"] = pd.to_numeric(out["penalty_points"], errors="coerce").fillna(0.0)
    for col in ["team", "status", "source_url", "note"]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    return out[NCAAF_OL_CONTINUITY_COLUMNS].reset_index(drop=True)

def prepare_ncaaf_familiarity_flags(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=NCAAF_FAMILIARITY_COLUMNS)
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    for col in NCAAF_FAMILIARITY_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    out["game_date"] = pd.to_datetime(out["game_date"], errors="coerce")
    for col in ["team", "opponent", "person", "role", "connection_team", "connection_type", "impact", "confidence", "source_url", "note"]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    for col in ["season", "week"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[NCAAF_FAMILIARITY_COLUMNS].reset_index(drop=True)

def prepare_ncaaf_injury_report(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    for col in NCAAF_INJURY_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    out["updated_at"] = pd.to_datetime(out["updated_at"], errors="coerce", utc=True)
    out["role_checked_at"] = pd.to_datetime(out["role_checked_at"], errors="coerce", utc=True)
    reusable_role = ~out["role"].fillna("").astype(str).str.startswith(("Role not checked", "Role unavailable"))
    out.loc[out["role_checked_at"].isna() & reusable_role, "role_checked_at"] = out.loc[
        out["role_checked_at"].isna() & reusable_role, "updated_at"
    ]
    out["game_date"] = pd.to_datetime(out["game_date"], errors="coerce")
    for col in [
        "team",
        "opponent",
        "player",
        "position",
        "status",
        "injury",
        "news_date",
        "role",
        "role_basis",
        "production",
        "impact",
        "source_url",
        "team_url",
        "note",
        "snap_source_url",
    ]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    out["impact_points"] = pd.to_numeric(out["impact_points"], errors="coerce").fillna(0.0)
    for col in [
        "snap_week",
        "snap_games",
        "offense_snaps",
        "offense_pct",
        "recent_offense_pct",
        "defense_snaps",
        "defense_pct",
        "recent_defense_pct",
        "st_snaps",
        "st_pct",
        "recent_st_pct",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[NCAAF_INJURY_COLUMNS].reset_index(drop=True)

def latest_ncaaf_log_date() -> pd.Timestamp | None:
    if not NCAAF_TEAM_LOG_PATH.exists():
        return None
    try:
        dates = pd.read_csv(NCAAF_TEAM_LOG_PATH, usecols=["date"])["date"]
    except Exception:
        return None
    parsed = pd.to_datetime(dates, errors="coerce").dropna()
    if parsed.empty:
        return None
    return parsed.max().normalize()

def expected_latest_ncaaf_result_date(selected_date: pd.Timestamp) -> pd.Timestamp:
    today = pd.Timestamp.today().normalize()
    selected = pd.Timestamp(selected_date).normalize()
    return min(selected - pd.Timedelta(days=1), today - pd.Timedelta(days=1))

def ncaaf_logs_are_stale(selected_date: pd.Timestamp) -> tuple[bool, pd.Timestamp | None, pd.Timestamp]:
    latest = latest_ncaaf_log_date()
    expected = expected_latest_ncaaf_result_date(selected_date)
    if latest is None:
        return True, latest, expected
    return latest < expected, latest, expected

def latest_nfl_log_date() -> pd.Timestamp | None:
    if not NFL_TEAM_LOG_PATH.exists():
        return None
    try:
        dates = pd.read_csv(NFL_TEAM_LOG_PATH, usecols=["date"])["date"]
    except Exception:
        return None
    parsed = pd.to_datetime(dates, errors="coerce").dropna()
    return parsed.max().normalize() if not parsed.empty else None

def nfl_logs_are_stale(selected_date: pd.Timestamp) -> tuple[bool, pd.Timestamp | None, pd.Timestamp]:
    latest = latest_nfl_log_date()
    expected = expected_latest_ncaaf_result_date(selected_date)
    if latest is None:
        return True, latest, expected
    # NFL games are clustered on Thursday/Sunday/Monday. A log can be fully
    # current even when the most recent calendar day had no completed game.
    return latest < expected - pd.Timedelta(days=4), latest, expected

def espn_cfb_get(params: dict, timeout: int = 30) -> dict:
    response = requests.get(ESPN_CFB_SCOREBOARD_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()

def espn_cfb_summary(event_id: str | int, timeout: int = 30) -> dict:
    response = requests.get(ESPN_CFB_SUMMARY_URL, params={"event": str(event_id)}, timeout=timeout)
    response.raise_for_status()
    return response.json()

def espn_nfl_get(params: dict, timeout: int = 30) -> dict:
    response = requests.get(ESPN_NFL_SCOREBOARD_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()

def espn_nfl_summary(event_id: str | int, timeout: int = 30) -> dict:
    response = requests.get(ESPN_NFL_SUMMARY_URL, params={"event": str(event_id)}, timeout=timeout)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=900)
def fetch_ncaaf_scoreboard_data(game_date: str) -> dict:
    try:
        return espn_cfb_get({"dates": ncaaf_date_code(game_date), "groups": 80, "limit": 300})
    except Exception as exc:
        return {"events": [], "_error": str(exc)}

@st.cache_data(ttl=1800)
def fetch_ncaaf_game_summary(event_id: str | int) -> dict:
    try:
        return espn_cfb_summary(event_id)
    except Exception as exc:
        return {"_error": str(exc)}

@st.cache_data(ttl=900)
def fetch_nfl_scoreboard_data(game_date: str) -> dict:
    try:
        return espn_nfl_get({"dates": ncaaf_date_code(game_date), "limit": 100})
    except Exception as exc:
        return {"events": [], "_error": str(exc)}

@st.cache_data(ttl=1800)
def fetch_nfl_game_summary(event_id: str | int) -> dict:
    try:
        return espn_nfl_summary(event_id)
    except Exception as exc:
        return {"_error": str(exc)}

@st.cache_data(ttl=21600)
def fetch_espn_football_sos_ranks(season: int, league_label: str = "NCAAF") -> dict:
    """Fetch ESPN FPI's published average schedule-strength rank.

    ESPN exposes the field as ``avgsosrank``. Its position differs between the
    college and NFL payloads, so the category metadata is used instead of a
    hard-coded list index.
    """
    league = "nfl" if str(league_label).upper() == "NFL" else "college-football"
    try:
        response = requests.get(
            ESPN_FOOTBALL_POWER_INDEX_URL.format(league=league),
            params={
                "region": "us",
                "lang": "en",
                "season": int(season),
                "sort": "fpi.fpi:desc",
                "limit": 200,
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        category_positions: dict[str, int] = {}
        for category in payload.get("categories", []) or []:
            names = category.get("names", []) or []
            if "avgsosrank" in names:
                category_positions[str(category.get("name") or "")] = names.index("avgsosrank")

        rows = []
        for entry in payload.get("teams", []) or []:
            team = entry.get("team", {}) or {}
            rank = None
            for category in entry.get("categories", []) or []:
                index = category_positions.get(str(category.get("name") or ""))
                values = category.get("values", []) or []
                if index is not None and index < len(values):
                    numeric = safe_float(values[index])
                    if pd.notna(numeric) and numeric > 0:
                        rank = int(numeric)
                        break
            if rank is not None:
                rows.append(
                    {
                        "team": str(team.get("displayName") or team.get("shortDisplayName") or "").strip(),
                        "short_name": str(team.get("shortDisplayName") or team.get("nickname") or "").strip(),
                        "abbreviation": str(team.get("abbreviation") or "").strip(),
                        "rank": rank,
                    }
                )
        return {
            "rows": rows,
            "source": "ESPN FPI AvgInSOS",
            "updated_at": payload.get("lastUpdated"),
            "season": safe_int((payload.get("requestedSeason") or {}).get("year")) or int(season),
            "_error": "" if rows else "ESPN returned no AvgInSOS ranks.",
        }
    except Exception as exc:
        return {"rows": [], "source": "ESPN FPI AvgInSOS", "updated_at": None, "season": int(season), "_error": str(exc)}

def ncaaf_clean_source_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return " ".join(html.unescape(text).split())

def ncaaf_parse_covers_injuries(markup: str, updated_at: pd.Timestamp | None = None) -> pd.DataFrame:
    """Parse the server-rendered team injury tables without adding a scraper dependency."""
    captured_at = updated_at or pd.Timestamp.now(tz="UTC")
    sections = re.findall(
        r'<a\s+id="([^"]+)"\s*></a>\s*<section>(.*?)</section>',
        str(markup or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    player_pattern = re.compile(
        r"<span\s+class=['\"]player-link['\"]>(.*?)</span>\s*</td>\s*"
        r"<td>(.*?)</td>\s*<td>\s*<b>(.*?)</b>\s*<br>\s*\(\s*(.*?)\s*\)</td>.*?"
        r"<div\s+class=['\"]col-xs-12 covers-CoversMatchups-injuryCopy['\"]>(.*?)</div>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for team_raw, section in sections:
        team = ncaaf_clean_source_text(team_raw)
        team_link_match = re.search(
            r'href=["\']([^"\']*/sport/football/ncaaf/teams/main/[^"\']+)["\']',
            section,
            flags=re.IGNORECASE,
        )
        team_path = str(team_link_match.group(1) if team_link_match else "").strip()
        team_url = team_path if team_path.startswith("http") else f"{COVERS_BASE_URL}{team_path}" if team_path else ""
        player_rows = player_pattern.findall(section)
        for player_raw, position_raw, status_raw, news_date_raw, note_raw in player_rows:
            status_injury = ncaaf_clean_source_text(status_raw)
            status, separator, injury = status_injury.partition(" - ")
            rows.append(
                {
                    "updated_at": captured_at.isoformat(),
                    "game_date": "",
                    "team": team,
                    "opponent": "",
                    "player": ncaaf_clean_source_text(player_raw),
                    "position": ncaaf_clean_source_text(position_raw).upper(),
                    "status": status.strip() if separator else status_injury,
                    "injury": injury.strip() if separator else "",
                    "news_date": ncaaf_clean_source_text(news_date_raw),
                    "role": "Role not checked",
                    "role_basis": "Covers team page not checked",
                    "role_checked_at": "",
                    "production": "",
                    "impact": "listed",
                    "impact_points": 0.0,
                    "source_url": COVERS_NCAAF_INJURIES_URL,
                    "team_url": team_url,
                    "note": ncaaf_clean_source_text(note_raw),
                }
            )
        if not player_rows:
            rows.append(
                {
                    "updated_at": captured_at.isoformat(),
                    "game_date": "",
                    "team": team,
                    "opponent": "",
                    "player": "__TEAM_REPORT_CHECKED__",
                    "position": "",
                    "status": "Checked",
                    "injury": "",
                    "news_date": "",
                    "role": "Team report coverage check",
                    "role_basis": "Covers injury board team section",
                    "role_checked_at": captured_at.isoformat(),
                    "production": "",
                    "impact": "listed",
                    "impact_points": 0.0,
                    "source_url": COVERS_NCAAF_INJURIES_URL,
                    "team_url": team_url,
                    "note": "Covers team section checked; no current player injury rows were listed.",
                }
            )
    return prepare_ncaaf_injury_report(pd.DataFrame(rows, columns=NCAAF_INJURY_COLUMNS))

def ncaaf_parse_acc_availability(
    payload: Any,
    game_date: Any = None,
    target_teams: set[str] | None = None,
) -> pd.DataFrame:
    """Parse the ACC's public game-day availability feed.

    The feed contains complete rosters. Only active designations are saved,
    plus one coverage marker per team so an empty official list is treated as
    checked rather than silently healthy.
    """
    reports = list(payload.values()) if isinstance(payload, dict) else list(payload or [])
    selected_day = pd.Timestamp(game_date).normalize() if game_date is not None else None
    target_names = {str(value) for value in (target_teams or set()) if str(value)}
    latest_by_team: dict[str, dict] = {}

    for report in reports:
        if not isinstance(report, dict):
            continue
        publish_date = pd.to_datetime(report.get("publishDate"), errors="coerce")
        posted_time = str(report.get("postedTime") or "00:00:00").strip()
        if pd.notna(publish_date):
            try:
                posted_at = pd.Timestamp(
                    f"{pd.Timestamp(publish_date).strftime('%Y-%m-%d')} {posted_time}",
                    tz="America/New_York",
                ).tz_convert("UTC")
            except Exception:
                posted_at = pd.Timestamp(publish_date, tz="UTC")
        else:
            posted_at = pd.Timestamp.now(tz="UTC").floor("s")
        report_teams = [
            str(team.get("teamDisplayName") or team.get("teamName") or "").strip()
            for team in (report.get("games") or [])
            if isinstance(team, dict)
        ]
        for team_block in report.get("games") or []:
            if not isinstance(team_block, dict):
                continue
            team = str(team_block.get("teamDisplayName") or team_block.get("teamName") or "").strip()
            if not team:
                continue
            if target_names and not any(ncaaf_team_names_match(target, [team]) for target in target_names):
                continue
            opponent = next(
                (candidate for candidate in report_teams if candidate and candidate != team),
                "",
            )
            team_key = normalize_name(team)
            previous = latest_by_team.get(team_key)
            if previous is None or posted_at >= previous["posted_at"]:
                latest_by_team[team_key] = {
                    "team": team,
                    "opponent": opponent,
                    "rows": team_block.get("rows") or [],
                    "posted_at": posted_at,
                    "publish_date": publish_date,
                    "report_type": str(report.get("ReportType") or "Game Day").strip(),
                }

    rows: list[dict] = []
    officially_available: list[tuple[str, str]] = []
    for report in latest_by_team.values():
        publish_date = report["publish_date"]
        report_day = selected_day or (
            pd.Timestamp(publish_date).normalize() if pd.notna(publish_date) else pd.NaT
        )
        news_date = pd.Timestamp(publish_date).strftime("%b %d") if pd.notna(publish_date) else ""
        posted_label = report["posted_at"].tz_convert("America/New_York").strftime("%b %d, %I:%M %p ET")
        base = {
            "updated_at": report["posted_at"].isoformat(),
            "game_date": report_day,
            "team": report["team"],
            "opponent": report["opponent"],
            "injury": "",
            "news_date": news_date,
            "role_checked_at": "",
            "production": "",
            "impact_points": 0.0,
            "source_url": ACC_AVAILABILITY_REPORT_URL,
            "team_url": "",
            "snap_week": pd.NA,
            "snap_games": pd.NA,
            "offense_snaps": pd.NA,
            "offense_pct": pd.NA,
            "recent_offense_pct": pd.NA,
            "defense_snaps": pd.NA,
            "defense_pct": pd.NA,
            "recent_defense_pct": pd.NA,
            "st_snaps": pd.NA,
            "st_pct": pd.NA,
            "recent_st_pct": pd.NA,
            "snap_source_url": "",
        }
        rows.append(
            {
                **base,
                "player": "__TEAM_REPORT_CHECKED__",
                "position": "",
                "status": "Checked",
                "role": "Official ACC availability coverage check",
                "role_basis": "Official ACC game-day report",
                "impact": "listed",
                "note": f"Official ACC {report['report_type']} report checked; posted {posted_label}.",
            }
        )
        for player_row in report["rows"]:
            if not isinstance(player_row, dict):
                continue
            status = str(player_row.get("status") or "").strip()
            if not status:
                continue
            raw_name = str(player_row.get("name") or "").strip()
            match = re.match(r"^([A-Za-z/]+)\s+(?:#\d+\s+)?(.+?)$", raw_name)
            position = match.group(1).upper() if match else ""
            player = match.group(2).strip() if match else raw_name
            if status.lower() == "available":
                officially_available.append((report["team"], player))
                continue
            if status.lower() == "exempt":
                continue
            rows.append(
                {
                    **base,
                    "player": player,
                    "position": position,
                    "status": status,
                    "role": "Role not checked",
                    "role_basis": "Official ACC status; Covers squad role not checked",
                    "impact": "listed",
                    "note": f"Official ACC {report['report_type']} designation; posted {posted_label}.",
                }
            )
    parsed = prepare_ncaaf_injury_report(pd.DataFrame(rows, columns=NCAAF_INJURY_COLUMNS))
    parsed.attrs["officially_available_players"] = officially_available
    return parsed

def ncaaf_fetch_acc_availability(
    game_date: Any = None,
    target_teams: set[str] | None = None,
) -> pd.DataFrame:
    response = requests.post(
        ACC_AVAILABILITY_API_URL,
        json={"sport": "Football", "organization": "ACC", "conference": "ACC"},
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NCAAF research dashboard)",
            "Referer": ACC_AVAILABILITY_REPORT_URL,
            "Content-Type": "application/json",
        },
        timeout=45,
    )
    response.raise_for_status()
    return ncaaf_parse_acc_availability(response.json(), game_date, target_teams)

def ncaaf_merge_injury_sources(covers: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    """Use official ACC availability as status truth and Covers as context."""
    officially_available = list(
        getattr(official, "attrs", {}).get("officially_available_players", [])
    )
    covers_report = prepare_ncaaf_injury_report(covers)
    official_report = prepare_ncaaf_injury_report(official)
    if official_report.empty:
        return covers_report

    for official_team, official_player in officially_available:
        cleared = covers_report.apply(
            lambda row: (
                ncaaf_team_names_match(str(official_team), [str(row.get("team") or "")])
                and ncaaf_player_names_match(official_player, row.get("player"))
            ),
            axis=1,
        )
        covers_report = covers_report[~cleared].copy()

    for index, official_row in official_report.iterrows():
        team_mask = covers_report["team"].map(
            lambda value: ncaaf_team_names_match(str(official_row.get("team") or ""), [str(value)])
        )
        team_rows = covers_report[team_mask]
        team_urls = [str(value) for value in team_rows["team_url"] if str(value).startswith("http")]
        if team_urls:
            official_report.at[index, "team_url"] = team_urls[0]
        if str(official_row.get("player") or "") == "__TEAM_REPORT_CHECKED__":
            covers_report = covers_report[~(team_mask & covers_report["player"].eq("__TEAM_REPORT_CHECKED__"))].copy()
            continue
        player_mask = covers_report["player"].map(
            lambda value: ncaaf_player_names_match(official_row.get("player"), value)
        )
        duplicates = covers_report[team_mask & player_mask]
        if not duplicates.empty:
            covers_row = duplicates.sort_values("updated_at", ascending=False).iloc[0]
            if not str(official_report.at[index, "injury"] or "").strip():
                official_report.at[index, "injury"] = covers_row.get("injury")
            covers_report = covers_report[~(team_mask & player_mask)].copy()

    combined = pd.concat([covers_report, official_report], ignore_index=True)
    return prepare_ncaaf_injury_report(combined)

def ncaaf_player_names_match(report_name: Any, leader_name: Any) -> bool:
    def parts(value: Any) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", str(value or "").lower())
        return [token for token in tokens if token not in {"jr", "sr", "ii", "iii", "iv"}]

    report_parts = parts(report_name)
    leader_parts = parts(leader_name)
    if not report_parts or not leader_parts or report_parts[-1] != leader_parts[-1]:
        return False
    return report_parts[0][0] == leader_parts[0][0]

def ncaaf_injury_status_factor(status: Any) -> float:
    value = str(status or "").strip().lower()
    if value.startswith("out") or "suspend" in value:
        return 1.0
    if value.startswith("doubtful"):
        return 0.70
    if value.startswith("questionable") or "game-time" in value or "game time" in value:
        return 0.35
    if value.startswith("probable"):
        return 0.12
    return 0.0

def ncaaf_injury_game_status_is_stale(row: pd.Series, max_age_days: int = 7) -> bool:
    """Reject old game-specific availability labels as evidence for a new matchup."""
    status = str(row.get("status") or "").strip().lower()
    if not status.startswith(("questionable", "probable", "doubtful")) and "game time" not in status and "game-time" not in status:
        return False
    news_text = str(row.get("news_date") or "").strip()
    if not news_text:
        return True
    updated_at = pd.to_datetime(row.get("updated_at"), errors="coerce", utc=True)
    reference = updated_at.tz_convert(None).normalize() if pd.notna(updated_at) else pd.Timestamp.today().normalize()
    parsed = pd.to_datetime(f"{news_text} {reference.year}", errors="coerce")
    if pd.isna(parsed):
        return True
    parsed = pd.Timestamp(parsed).normalize()
    if parsed > reference + pd.Timedelta(days=7):
        parsed = parsed - pd.DateOffset(years=1)
    return (reference - parsed).days > int(max_age_days)

def ncaaf_covers_stat_table(markup: str, table_name: str) -> list[dict]:
    match = re.search(
        rf'<table[^>]+id=["\']RegularSeasonPlayer-{re.escape(table_name)}["\'][^>]*>(.*?)</table>',
        str(markup or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []
    table = match.group(1)
    headers = [ncaaf_clean_source_text(value) for value in re.findall(r"<th[^>]*>(.*?)</th>", table, re.IGNORECASE | re.DOTALL)]
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.IGNORECASE | re.DOTALL):
        cells = [ncaaf_clean_source_text(value) for value in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)]
        if cells and headers:
            rows.append(dict(zip(headers, cells)))
    return rows

def ncaaf_covers_team_role_data(markup: str) -> dict:
    tables = {
        name: ncaaf_covers_stat_table(markup, name)
        for name in ["passing", "rushing", "receiving", "defense", "kicking", "punting"]
    }
    leaders = []
    leader_table = re.search(
        r"<th[^>]*>\s*Team Leaders\s*</th>.*?<tbody>(.*?)</tbody>",
        str(markup or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    if leader_table:
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", leader_table.group(1), re.IGNORECASE | re.DOTALL):
            cells = [ncaaf_clean_source_text(value) for value in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)]
            if len(cells) >= 3:
                leaders.append({"category": cells[0], "player": cells[1], "value": cells[2]})
    return {"tables": tables, "leaders": leaders}

def ncaaf_covers_stat_number(value: Any) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return safe_float(match.group(0)) if match else 0.0

def ncaaf_covers_player_row(rows: list[dict], player: Any) -> dict:
    return next((row for row in rows if ncaaf_player_names_match(player, row.get("Player"))), {})

def ncaaf_covers_player_rank(rows: list[dict], player: Any, metric: str) -> int | None:
    eligible = [row for row in rows if ncaaf_covers_stat_number(row.get(metric)) > 0]
    eligible.sort(key=lambda row: ncaaf_covers_stat_number(row.get(metric)), reverse=True)
    for rank, row in enumerate(eligible, start=1):
        if ncaaf_player_names_match(player, row.get("Player")):
            return rank
    return None

def ncaaf_covers_role_for_injury(row: pd.Series, role_data: dict) -> dict:
    player = str(row.get("player") or "")
    position = str(row.get("position") or "").upper()
    tables = (role_data or {}).get("tables", {}) or {}
    leaders = [
        leader
        for leader in ((role_data or {}).get("leaders", []) or [])
        if ncaaf_player_names_match(player, leader.get("player"))
    ]
    leader_categories = {str(leader.get("category") or "").lower() for leader in leaders}
    leader_text = ", ".join(
        f"{leader.get('category')} leader ({leader.get('value')})"
        for leader in leaders
    )
    role = f"{position or 'Player'} — no Covers production role"
    role_basis = "Position from Covers injury report; no matching player stats"
    production = leader_text
    base_impact = 0.0

    passing = ncaaf_covers_player_row(tables.get("passing", []), player)
    rushing = ncaaf_covers_player_row(tables.get("rushing", []), player)
    receiving = ncaaf_covers_player_row(tables.get("receiving", []), player)
    defense = ncaaf_covers_player_row(tables.get("defense", []), player)

    if position == "QB":
        rank = ncaaf_covers_player_rank(tables.get("passing", []), player, "ATT")
        total_attempts = sum(ncaaf_covers_stat_number(item.get("ATT")) for item in tables.get("passing", []))
        attempts = ncaaf_covers_stat_number(passing.get("ATT"))
        attempt_share = attempts / total_attempts if total_attempts else 0.0
        if rank:
            if rank == 1:
                role = "QB1 by workload — #1 in pass attempts"
                base_impact = 5.0
            elif rank == 2 and attempt_share >= 0.30:
                role = f"Co-primary QB — {attempt_share * 100:.0f}% of pass attempts"
                base_impact = 3.0
            else:
                role = f"QB{rank} by workload — #{rank} in pass attempts"
                base_impact = 0.8 if rank == 2 else 0.25
            role_basis = "Covers passing workload"
            production = f"{passing.get('ATT', '0')} att · {passing.get('YDS', '0')} pass yds · {passing.get('TD', '0')} TD · {attempt_share * 100:.0f}% share"
        elif "passing" in leader_categories:
            role = "QB1 by workload — Covers passing leader"
            role_basis = "Covers Team Leaders"
            base_impact = 5.0
    elif position in {"RB", "FB"}:
        rank = ncaaf_covers_player_rank(tables.get("rushing", []), player, "ATT")
        total_carries = sum(ncaaf_covers_stat_number(item.get("ATT")) for item in tables.get("rushing", []))
        carries = ncaaf_covers_stat_number(rushing.get("ATT"))
        carry_share = carries / total_carries if total_carries else 0.0
        if "rushing" in leader_categories:
            role = f"{position}1 — Covers rushing leader"
            role_basis = "Covers Team Leaders"
            base_impact = 1.8
        elif rank:
            role = f"Backfield role — #{rank} in team carries"
            role_basis = "Covers rushing workload"
            base_impact = 1.4 if carry_share >= 0.25 else (0.7 if carry_share >= 0.10 else 0.25)
        if rushing:
            production = f"{rushing.get('ATT', '0')} carries · {rushing.get('YDS', '0')} rush yds · {rushing.get('TD', '0')} TD"
    elif position in {"WR", "TE"}:
        rank = ncaaf_covers_player_rank(tables.get("receiving", []), player, "YDS")
        total_yards = sum(ncaaf_covers_stat_number(item.get("YDS")) for item in tables.get("receiving", []))
        yards = ncaaf_covers_stat_number(receiving.get("YDS"))
        yard_share = yards / total_yards if total_yards else 0.0
        if "receiving" in leader_categories:
            role = f"{position}1 — Covers receiving leader"
            role_basis = "Covers Team Leaders"
            base_impact = 1.6
        elif rank:
            role = f"Receiving role — #{rank} in team receiving yards"
            role_basis = "Covers receiving production"
            base_impact = 1.2 if rank <= 2 or yard_share >= 0.20 else (0.6 if yard_share >= 0.08 else 0.2)
        if receiving:
            production = f"{receiving.get('REC', '0')} rec · {receiving.get('YDS', '0')} rec yds · {receiving.get('TD', '0')} TD"
    elif position in {"DL", "DE", "DT", "NT", "LB", "OLB", "ILB", "CB", "DB", "S", "FS", "SS"}:
        tackle_metric = "TK" if any("TK" in item for item in tables.get("defense", [])) else "ATK"
        rank = ncaaf_covers_player_rank(tables.get("defense", []), player, tackle_metric)
        defensive_leads = leader_categories & {"sacks", "interceptions"}
        if defensive_leads:
            role = "Defensive production leader — " + "/".join(sorted(defensive_leads))
            role_basis = "Covers Team Leaders"
            base_impact = 1.1
        elif rank:
            role = f"Defensive production role — #{rank} in tackles"
            role_basis = "Covers defensive player stats"
            base_impact = 0.8 if rank <= 3 else (0.4 if rank <= 8 else 0.15)
        if defense:
            production = f"{defense.get('TK', '0')} tackles · {defense.get('Sacks', '0')} sacks · {defense.get('INT', '0')} INT"
    elif position in {"OT", "OG", "C", "OL", "G", "T"}:
        role = f"{position} — depth order not published by Covers"
        role_basis = "Covers roster position only"

    if "touchdowns" in leader_categories and position in {"RB", "FB", "WR", "TE"}:
        role = f"{role} · scoring leader"
        base_impact = max(base_impact, 1.8)
        production = " · ".join(filter(None, [production, leader_text]))

    impact_points = base_impact * ncaaf_injury_status_factor(row.get("status"))
    impact = "critical" if impact_points >= 3.0 else ("high" if impact_points >= 1.0 else ("medium" if impact_points > 0 else "listed"))
    return {
        "role": role,
        "role_basis": role_basis,
        "production": production,
        "impact": impact,
        "impact_points": round(impact_points, 2),
    }

def ncaaf_fetch_covers_role_data(team_url: str) -> dict:
    response = requests.get(
        team_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NCAAF research dashboard)"},
        timeout=8,
    )
    response.raise_for_status()
    return ncaaf_covers_team_role_data(response.text)

def ncaaf_enrich_injuries_from_covers(
    injuries: pd.DataFrame,
    existing: pd.DataFrame | None = None,
    target_teams: set[str] | None = None,
) -> pd.DataFrame:
    out = prepare_ncaaf_injury_report(injuries)
    if out.empty:
        return out
    cached = prepare_ncaaf_injury_report(existing)
    if not cached.empty:
        for index, row in out.iterrows():
            matches = cached[
                cached["team"].map(lambda value: ncaaf_team_names_match(str(row.get("team") or ""), [str(value)]))
                & cached["player"].map(lambda value: ncaaf_player_names_match(row.get("player"), value))
            ]
            if matches.empty:
                continue
            old = matches.sort_values("updated_at", ascending=False).iloc[0]
            for field in ["role", "role_basis", "role_checked_at", "production", "impact", "impact_points"]:
                out.at[index, field] = old.get(field)
            old_factor = ncaaf_injury_status_factor(old.get("status"))
            role_weight = safe_float(old.get("impact_points")) / old_factor if old_factor else 0.0
            fresh_points = role_weight * ncaaf_injury_status_factor(row.get("status"))
            out.at[index, "impact_points"] = round(fresh_points, 2)
            out.at[index, "impact"] = "critical" if fresh_points >= 3.0 else ("high" if fresh_points >= 1.0 else ("medium" if fresh_points > 0 else "listed"))

    now = pd.Timestamp.now(tz="UTC").floor("s")
    role_age_hours = (now - out["role_checked_at"]).dt.total_seconds() / 3600
    role_missing = out["role"].fillna("").astype(str).str.startswith(("Role not checked", "Role unavailable"))
    role_missing = role_missing | out["role"].fillna("").astype(str).str.match(r"QB\d+\s+—")
    needs_refresh = role_missing | out["role_checked_at"].isna()
    needs_refresh = needs_refresh & out["team_url"].fillna("").astype(str).str.startswith(COVERS_BASE_URL)
    needs_refresh = needs_refresh & out["player"].ne("__TEAM_REPORT_CHECKED__")
    if target_teams:
        target_mask = out["team"].map(
            lambda value: any(ncaaf_team_names_match(team, [str(value)]) for team in target_teams)
        )
        # A slate refresh should only fan out to the teams being displayed.
        # Previously every newly listed player on the national board triggered
        # a team-page request, which wasted requests and could contribute to
        # provider throttling before the selected games were enriched.
        needs_refresh = target_mask & (needs_refresh | (role_age_hours > 12))
    team_urls = sorted(
        {
            str(value)
            for value in out.loc[needs_refresh, "team_url"]
            if str(value).startswith("http")
        }
    )
    role_data_by_url = {}
    with ThreadPoolExecutor(max_workers=min(20, max(1, len(team_urls)))) as pool:
        pending = {pool.submit(ncaaf_fetch_covers_role_data, url): url for url in team_urls}
        for future in as_completed(pending):
            url = pending[future]
            try:
                role_data_by_url[url] = future.result()
            except Exception:
                role_data_by_url[url] = {}

    for index, row in out.iterrows():
        team_url = str(row.get("team_url") or "")
        if team_url not in role_data_by_url:
            continue
        role_data = role_data_by_url.get(team_url) or {}
        if not role_data:
            if str(row.get("role") or "").startswith(("Role not checked", "Role unavailable")):
                out.at[index, "role"] = "Role unavailable"
                out.at[index, "role_basis"] = "Covers team page unavailable"
            continue
        details = ncaaf_covers_role_for_injury(row, role_data)
        for key, value in details.items():
            out.at[index, key] = value
        out.at[index, "role_checked_at"] = now
    return prepare_ncaaf_injury_report(out)

def update_ncaaf_injury_report(_game_date: Any = None) -> tuple[bool, str]:
    try:
        schedule = fetch_ncaaf_schedule_for_date(_game_date) if _game_date is not None else []
        target_teams = {
            str(game.get(side) or "")
            for game in schedule
            for side in ["away_team", "home_team"]
            if str(game.get(side) or "")
        }
        covers_message = "Covers unavailable"
        try:
            response = requests.get(
                COVERS_NCAAF_INJURIES_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NCAAF research dashboard)"},
                timeout=30,
            )
            response.raise_for_status()
            covers_report = ncaaf_parse_covers_injuries(response.text)
            covers_message = f"{len(covers_report[covers_report['player'] != '__TEAM_REPORT_CHECKED__'])} Covers rows"
        except Exception as exc:
            covers_report = pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
            covers_message = f"Covers unavailable ({exc})"

        acc_message = "official ACC report unavailable"
        try:
            official_acc = ncaaf_fetch_acc_availability(_game_date, target_teams)
            acc_player_count = int((official_acc["player"] != "__TEAM_REPORT_CHECKED__").sum()) if not official_acc.empty else 0
            acc_team_count = int((official_acc["player"] == "__TEAM_REPORT_CHECKED__").sum()) if not official_acc.empty else 0
            acc_message = f"{acc_player_count} official ACC designations across {acc_team_count} teams"
        except Exception as exc:
            official_acc = pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
            acc_message = f"official ACC report unavailable ({exc})"

        parsed = ncaaf_merge_injury_sources(covers_report, official_acc)
        if parsed.empty:
            return False, "Covers and the official ACC feed returned no rows; the saved report was left unchanged."
        existing = prepare_ncaaf_injury_report(
            load_ncaaf_injury_report(ncaaf_injury_signature())
        )
        external_verified = existing[
            existing["source_url"].fillna("").astype(str).ne("")
            & existing["source_url"].fillna("").astype(str).ne(COVERS_NCAAF_INJURIES_URL)
            & existing["source_url"].fillna("").astype(str).ne(ACC_AVAILABILITY_REPORT_URL)
        ].copy()
        if _game_date is not None and not external_verified.empty:
            selected_day = pd.Timestamp(_game_date).normalize()
            external_verified = external_verified[
                external_verified["game_date"].notna()
                & (external_verified["game_date"].dt.normalize() >= selected_day)
            ]
        if not external_verified.empty:
            parsed = prepare_ncaaf_injury_report(
                pd.concat([parsed, external_verified], ignore_index=True)
            )
        enriched = ncaaf_enrich_injuries_from_covers(parsed, existing, target_teams)
        save_df = enriched.copy()
        save_df["updated_at"] = save_df["updated_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        save_df["role_checked_at"] = save_df["role_checked_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        save_df["game_date"] = save_df["game_date"].dt.strftime("%Y-%m-%d").fillna("")
        NCAAF_INJURY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_df.to_csv(NCAAF_INJURY_REPORT_PATH, index=False)
        verified = int(
            save_df.apply(
                lambda row: safe_float(row.get("impact_points")) > 0
                and not ncaaf_injury_game_status_is_stale(row),
                axis=1,
            ).sum()
        )
        roles_checked = int(
            (
                ~save_df["role_basis"].isin(
                    {"Covers team page unavailable", "Covers team page not checked", "Covers team page not requested"}
                )
            ).sum()
        )
        return True, (
            f"Saved {len(save_df[save_df['player'] != '__TEAM_REPORT_CHECKED__'])} listed NCAAF injuries: "
            f"{covers_message}; {acc_message}. "
            f"{roles_checked} squad roles were checked on "
            f"Covers team pages and {verified} availability entries affect the model."
        )
    except Exception as exc:
        return False, str(exc)

def nfl_parse_covers_injuries(markup: str, updated_at: pd.Timestamp | None = None) -> pd.DataFrame:
    """Parse the Covers NFL injury board into the shared football injury schema."""
    captured_at = updated_at or pd.Timestamp.now(tz="UTC")
    sections = re.findall(
        r'<a\s+id="([^"]+)"\s*></a>\s*<section>(.*?)</section>',
        str(markup or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    player_pattern = re.compile(
        r"<span\s+class=['\"]player-link['\"]>(.*?)</span>\s*</td>\s*"
        r"<td>(.*?)</td>\s*<td>\s*<b>(.*?)</b>\s*<br>\s*\(\s*(.*?)\s*\)</td>.*?"
        r"<div\s+class=['\"]col-xs-12 covers-CoversMatchups-injuryCopy['\"]>(.*?)</div>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for team_raw, section in sections:
        team = ncaaf_clean_source_text(team_raw)
        team_link_match = re.search(
            r'href=["\']([^"\']*/sport/football/nfl/teams/main/[^"\']+)["\']',
            section,
            flags=re.IGNORECASE,
        )
        team_path = str(team_link_match.group(1) if team_link_match else "").strip()
        team_url = team_path if team_path.startswith("http") else f"{COVERS_BASE_URL}{team_path}" if team_path else ""
        for player_raw, position_raw, status_raw, news_date_raw, note_raw in player_pattern.findall(section):
            status_injury = ncaaf_clean_source_text(status_raw)
            status, separator, injury = status_injury.partition(" - ")
            rows.append(
                {
                    "updated_at": captured_at.isoformat(),
                    "game_date": "",
                    "team": team,
                    "opponent": "",
                    "player": ncaaf_clean_source_text(player_raw),
                    "position": ncaaf_clean_source_text(position_raw).upper(),
                    "status": status.strip() if separator else status_injury,
                    "injury": injury.strip() if separator else "",
                    "news_date": ncaaf_clean_source_text(news_date_raw),
                    "role": "Role not checked",
                    "role_basis": "Covers team page not checked",
                    "role_checked_at": "",
                    "production": "",
                    "impact": "listed",
                    "impact_points": 0.0,
                    "source_url": COVERS_NFL_INJURIES_URL,
                    "team_url": team_url,
                    "note": ncaaf_clean_source_text(note_raw),
                }
            )
    return prepare_ncaaf_injury_report(pd.DataFrame(rows, columns=NCAAF_INJURY_COLUMNS))

def nfl_parse_nflverse_injuries(
    csv_text: str,
    season: int,
    week: int | None = None,
    target_teams: set[str] | None = None,
    updated_at: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Convert nflverse's official weekly NFL report to the shared injury schema.

    Covers can omit an entire team from its national board. nflverse preserves
    the league report status (Out/Doubtful/Questionable), so it is the primary
    source for game designations while Covers remains useful for IR/news rows.
    """
    try:
        raw = pd.read_csv(io.StringIO(str(csv_text or "")))
    except Exception:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
    if raw.empty:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)

    raw.columns = [str(column).strip().lower() for column in raw.columns]
    for column in [
        "season", "season_type", "team", "week", "position", "full_name",
        "report_primary_injury", "report_secondary_injury", "report_status",
        "practice_status",
    ]:
        if column not in raw.columns:
            raw[column] = pd.NA
    raw["season"] = pd.to_numeric(raw["season"], errors="coerce")
    raw["week"] = pd.to_numeric(raw["week"], errors="coerce")
    raw = raw[raw["season"].eq(int(season))].copy()
    regular_mask = raw["season_type"].fillna("").astype(str).str.upper().isin({"REG", "REGULAR"})
    if regular_mask.any():
        raw = raw[regular_mask].copy()
    if raw.empty:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)

    requested_week = safe_int(week)
    if requested_week:
        weekly = raw[raw["week"].eq(requested_week)].copy()
        # Never substitute a prior week's designation for the selected game.
        if weekly.empty:
            return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
    else:
        requested_week = safe_int(raw["week"].max())
        weekly = raw[raw["week"].eq(requested_week)].copy()

    captured_at = updated_at or pd.Timestamp.now(tz="UTC").floor("s")
    source_url = NFLVERSE_INJURIES_URL.format(season=int(season))
    actionable = weekly[
        weekly["report_status"].fillna("").astype(str).str.strip().str.lower().isin(
            {"out", "doubtful", "questionable"}
        )
    ].copy()
    rows = []
    for _, player in actionable.iterrows():
        abbreviation = str(player.get("team") or "").strip().upper()
        team = NFL_TEAM_DISPLAY_NAMES.get(abbreviation, abbreviation)
        injuries = []
        for column in ["report_primary_injury", "report_secondary_injury"]:
            value = str(player.get(column) or "").strip()
            if value and value.lower() != "nan" and value not in injuries:
                injuries.append(value)
        practice_status = str(player.get("practice_status") or "").strip()
        if practice_status.lower() == "nan":
            practice_status = ""
        rows.append(
            {
                "updated_at": captured_at.isoformat(),
                "game_date": "",
                "team": team,
                "opponent": "",
                "player": str(player.get("full_name") or "").strip(),
                "position": str(player.get("position") or "").strip().upper(),
                "status": str(player.get("report_status") or "").strip().title(),
                "injury": " / ".join(injuries),
                "news_date": f"Week {requested_week}" + (f" · {practice_status}" if practice_status else ""),
                "role": "Role not checked",
                "role_basis": "Official weekly report via nflverse; role pending snap-count match",
                "role_checked_at": "",
                "production": "",
                "impact": "listed",
                "impact_points": 0.0,
                "source_url": source_url,
                "team_url": "",
                "note": "Official NFL game designation via nflverse.",
            }
        )

    # A hidden coverage row lets the UI distinguish a checked, clean report
    # from a provider failure. Only add it when nflverse actually contains a
    # row for that team in the requested week.
    covered_abbreviations = {
        str(value).strip().upper() for value in weekly["team"].dropna().tolist()
    }
    for team_name in sorted(target_teams or set()):
        abbreviation = nfl_team_abbreviation(team_name)
        if abbreviation and abbreviation in covered_abbreviations:
            rows.append(
                {
                    "updated_at": captured_at.isoformat(),
                    "game_date": "",
                    "team": NFL_TEAM_DISPLAY_NAMES.get(abbreviation, team_name),
                    "opponent": "",
                    "player": "__TEAM_REPORT_CHECKED__",
                    "position": "",
                    "status": "Report checked",
                    "injury": "",
                    "news_date": f"Week {requested_week}",
                    "role": "Coverage marker",
                    "role_basis": "Official weekly report via nflverse",
                    "role_checked_at": captured_at.isoformat(),
                    "production": "",
                    "impact": "listed",
                    "impact_points": 0.0,
                    "source_url": source_url,
                    "team_url": "",
                    "note": "Hidden report-coverage marker.",
                }
            )
    return prepare_ncaaf_injury_report(pd.DataFrame(rows, columns=NCAAF_INJURY_COLUMNS))

def nfl_parse_official_inactives(
    markup: str,
    season: int,
    week: int,
    target_teams: set[str] | None = None,
    updated_at: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Parse NFL.com's official Sunday game-day inactive lists.

    The weekly injury report cannot tell us which questionable players were
    cleared. NFL.com publishes the final inactive lists about 90 minutes before
    kickoff, so a covered team section is also an explicit active-player clear.
    """
    captured_at = updated_at or pd.Timestamp.now(tz="UTC").floor("s")
    source_url = NFL_OFFICIAL_INACTIVES_URL.format(week=int(week), season=int(season))
    target_abbreviations = {
        nfl_team_abbreviation(team) for team in (target_teams or set()) if nfl_team_abbreviation(team)
    }
    sections = re.findall(
        r"<h3[^>]*>(.*?)</h3>\s*<ul[^>]*>(.*?)</ul>",
        str(markup or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows: list[dict] = []
    covered: set[str] = set()
    for team_raw, player_list in sections:
        abbreviation = nfl_team_abbreviation(ncaaf_clean_source_text(team_raw))
        if not abbreviation or (target_abbreviations and abbreviation not in target_abbreviations):
            continue
        players = re.findall(r"<li[^>]*>(.*?)</li>", player_list, flags=re.IGNORECASE | re.DOTALL)
        if not players:
            continue
        covered.add(abbreviation)
        team_name = NFL_TEAM_DISPLAY_NAMES.get(abbreviation, abbreviation)
        for player_raw in players:
            inactive_text = ncaaf_clean_source_text(player_raw)
            match = re.match(
                r"^(QB|RB|FB|WR|TE|C|G|OG|OT|OL|T|LT|RT|LG|RG|DL|DT|DE|EDGE|OLB|ILB|LB|CB|DB|S|SAF|K|P|LS)\s+(.+)$",
                inactive_text,
                flags=re.IGNORECASE,
            )
            if not match:
                continue
            position = match.group(1).upper()
            player = re.sub(r"\s*\([^)]*\)\s*$", "", match.group(2)).strip()
            emergency_qb = "emergency third qb" in inactive_text.lower()
            rows.append(
                {
                    "updated_at": captured_at.isoformat(),
                    "game_date": "",
                    "team": team_name,
                    "opponent": "",
                    "player": player,
                    "position": position,
                    "status": "Out — emergency QB" if emergency_qb else "Out — game-day inactive",
                    "injury": "Official game-day inactive",
                    "news_date": f"Week {int(week)} · final inactive list",
                    "role": "Role not checked",
                    "role_basis": "Official NFL game-day inactive; role pending snap-count match",
                    "role_checked_at": "",
                    "production": "",
                    "impact": "listed",
                    "impact_points": 0.0,
                    "source_url": source_url,
                    "team_url": "",
                    "note": (
                        "Emergency third quarterback; eligible only if the active quarterbacks are unavailable."
                        if emergency_qb
                        else "Official inactive status; the inactive list does not always state whether the reason is injury or coach decision."
                    ),
                }
            )
    for abbreviation in sorted(covered):
        rows.append(
            {
                "updated_at": captured_at.isoformat(),
                "game_date": "",
                "team": NFL_TEAM_DISPLAY_NAMES.get(abbreviation, abbreviation),
                "opponent": "",
                "player": "__TEAM_REPORT_CHECKED__",
                "position": "",
                "status": "Final inactive list checked",
                "injury": "",
                "news_date": f"Week {int(week)} · NFL.com",
                "role": "Coverage marker",
                "role_basis": "Official NFL game-day inactive list",
                "role_checked_at": captured_at.isoformat(),
                "production": "",
                "impact": "listed",
                "impact_points": 0.0,
                "source_url": source_url,
                "team_url": "",
                "note": "Hidden final inactive-list coverage marker.",
            }
        )
    return prepare_ncaaf_injury_report(pd.DataFrame(rows, columns=NCAAF_INJURY_COLUMNS))

@st.cache_data(ttl=300)
def fetch_nfl_official_inactives(
    season: int,
    week: int,
    target_teams: tuple[str, ...],
) -> pd.DataFrame:
    """Refresh the final NFL.com inactive layer every five minutes on game day."""
    if not safe_int(season) or not safe_int(week) or not target_teams:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
    try:
        source_url = NFL_OFFICIAL_INACTIVES_URL.format(week=int(week), season=int(season))
        response = requests.get(
            source_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NFL research dashboard)"},
            timeout=20,
        )
        response.raise_for_status()
        return nfl_parse_official_inactives(
            response.text,
            int(season),
            int(week),
            set(target_teams),
        )
    except Exception:
        return pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)

def nfl_merge_injury_sources(
    covers: pd.DataFrame,
    official: pd.DataFrame,
    gameday: pd.DataFrame | None = None,
) -> pd.DataFrame:
    covers_report = prepare_ncaaf_injury_report(covers)
    official_report = prepare_ncaaf_injury_report(official)
    gameday_report = prepare_ncaaf_injury_report(gameday)
    if official_report.empty and gameday_report.empty:
        return covers_report
    # Covers often uses a short team name and player initials ("Carolina",
    # "D. Lewis") while the official report uses full names. Remove those
    # aliases before concatenating so the official game designation wins.
    for _, official_row in official_report.iterrows():
        if str(official_row.get("player") or "") == "__TEAM_REPORT_CHECKED__":
            continue
        official_team = nfl_team_abbreviation(official_row.get("team"))
        duplicate = covers_report.apply(
            lambda covers_row: (
                nfl_team_abbreviation(covers_row.get("team")) == official_team
                and ncaaf_player_names_match(official_row.get("player"), covers_row.get("player"))
            ),
            axis=1,
        )
        covers_report = covers_report[~duplicate].copy()
    covered_gameday_teams = {
        nfl_team_abbreviation(value)
        for value in gameday_report.loc[
            gameday_report["player"].eq("__TEAM_REPORT_CHECKED__"), "team"
        ].tolist()
        if nfl_team_abbreviation(value)
    }
    gameday_players = {
        (nfl_team_abbreviation(row.get("team")), normalize_name(row.get("player")))
        for _, row in gameday_report.iterrows()
        if str(row.get("player") or "") != "__TEAM_REPORT_CHECKED__"
    }
    base_report = pd.concat([covers_report, official_report], ignore_index=True)
    if covered_gameday_teams and not base_report.empty:
        keep_rows = []
        for _, row in base_report.iterrows():
            team_key = nfl_team_abbreviation(row.get("team"))
            player_key = normalize_name(row.get("player"))
            status = str(row.get("status") or "").strip().lower()
            cleared_on_game_day = (
                team_key in covered_gameday_teams
                and str(row.get("player") or "") != "__TEAM_REPORT_CHECKED__"
                and (team_key, player_key) not in gameday_players
                and not (status.startswith("out") or "suspend" in status or "reserve" in status or "ir" == status)
            )
            keep_rows.append(not cleared_on_game_day)
        base_report = base_report[pd.Series(keep_rows, index=base_report.index)].copy()
    combined = pd.concat([base_report, gameday_report], ignore_index=True)
    combined["_team_key"] = combined["team"].map(lambda value: nfl_team_abbreviation(value) or normalize_name(value))
    combined["_player_key"] = combined["player"].map(normalize_name)
    source = combined["source_url"].fillna("").astype(str)
    combined["_priority"] = 1
    combined.loc[source.str.contains("nflverse", case=False, na=False), "_priority"] = 2
    combined.loc[source.str.contains("nfl.com/news/nfl-week-", case=False, na=False), "_priority"] = 3
    combined = combined.sort_values("_priority", ascending=False)
    combined = combined.drop_duplicates(["_team_key", "_player_key"], keep="first")
    return prepare_ncaaf_injury_report(combined.drop(columns=["_team_key", "_player_key", "_priority"]))

def update_nfl_injury_report(_game_date: Any = None) -> tuple[bool, str]:
    try:
        snap_season = nfl_season_for_date(_game_date or pd.Timestamp.today())
        snap_ok, snap_message = update_nfl_snap_counts(snap_season)
        schedule = fetch_nfl_schedule_for_date(_game_date) if _game_date is not None else []
        target_teams = {
            str(game.get(side) or "")
            for game in schedule
            for side in ["away_team", "home_team"]
            if str(game.get(side) or "")
        }
        target_weeks = [safe_int(game.get("week")) for game in schedule if safe_int(game.get("week"))]
        target_week = max(target_weeks) if target_weeks else None
        try:
            response = requests.get(
                COVERS_NFL_INJURIES_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NFL research dashboard)"},
                timeout=30,
            )
            response.raise_for_status()
            covers_report = nfl_parse_covers_injuries(response.text)
            covers_message = f"{len(covers_report)} Covers news/IR rows"
        except Exception as exc:
            covers_report = pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
            covers_message = f"Covers unavailable ({exc})"
        official_message = "official weekly report unavailable"
        try:
            official_response = requests.get(
                NFLVERSE_INJURIES_URL.format(season=snap_season),
                headers={"User-Agent": "Mozilla/5.0 (compatible; NFL research dashboard)"},
                timeout=45,
            )
            official_response.raise_for_status()
            official = nfl_parse_nflverse_injuries(
                official_response.text,
                snap_season,
                target_week,
                target_teams,
            )
            official_message = f"{len(official[official['player'] != '__TEAM_REPORT_CHECKED__'])} official game designations"
        except Exception as exc:
            official = pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
            official_message = f"official weekly report unavailable ({exc})"
        gameday = fetch_nfl_official_inactives(
            snap_season,
            target_week,
            tuple(sorted(target_teams)),
        ) if target_week and target_teams else pd.DataFrame(columns=NCAAF_INJURY_COLUMNS)
        gameday_count = int((gameday["player"] != "__TEAM_REPORT_CHECKED__").sum()) if not gameday.empty else 0
        gameday_teams = int((gameday["player"] == "__TEAM_REPORT_CHECKED__").sum()) if not gameday.empty else 0
        gameday_message = (
            f"{gameday_count} official game-day inactives across {gameday_teams} confirmed teams"
            if gameday_teams
            else "official game-day inactive lists not posted for this slate yet"
        )
        parsed = nfl_merge_injury_sources(covers_report, official, gameday)
        if parsed.empty:
            return False, "Both NFL injury sources returned no player rows; the saved report was left unchanged."
        existing = load_nfl_injury_report(nfl_injury_signature())
        enriched = ncaaf_enrich_injuries_from_covers(parsed, existing, target_teams)
        saved_snaps = (
            prepare_nfl_snap_counts(pd.read_csv(NFL_SNAP_COUNTS_PATH))
            if NFL_SNAP_COUNTS_PATH.exists()
            else pd.DataFrame(columns=NFL_SNAP_COUNT_COLUMNS)
        )
        enriched = nfl_enrich_injuries_with_snap_counts(enriched, saved_snaps)
        save_df = enriched.copy()
        save_df["updated_at"] = save_df["updated_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        save_df["role_checked_at"] = save_df["role_checked_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        save_df["game_date"] = save_df["game_date"].dt.strftime("%Y-%m-%d").fillna("")
        NFL_INJURY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_df.to_csv(NFL_INJURY_REPORT_PATH, index=False)
        visible_df = save_df[save_df["player"] != "__TEAM_REPORT_CHECKED__"].copy()
        verified = int((visible_df["impact_points"] > 0).sum())
        roles_checked = int(
            (~visible_df["role_basis"].isin(
                {"Covers team page unavailable", "Covers team page not checked", "Covers team page not requested"}
            )).sum()
        )
        snap_matched = int(visible_df["snap_week"].notna().sum())
        return True, (
            f"Saved {len(visible_df)} listed NFL injuries: {covers_message}; {official_message}; {gameday_message}. "
            f"{roles_checked} squad roles were checked "
            f"and {verified} availability entries affect the model. Snap counts matched {snap_matched} players. "
            f"Snap refresh: {snap_message if snap_ok else 'using saved snaps because refresh failed: ' + snap_message}"
        )
    except Exception as exc:
        return False, str(exc)

def ncaaf_parse_number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value or "").strip()
    if not text or text == "-":
        return float("nan")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return float("nan")
    return safe_float(match.group(0))

def ncaaf_parse_efficiency(value: Any) -> tuple[float, float, float]:
    text = str(value or "").strip()
    match = re.search(r"(\d+)\s*[-/]\s*(\d+)", text)
    if not match:
        pct = safe_float(value)
        return float("nan"), float("nan"), pct
    made = safe_float(match.group(1))
    attempts = safe_float(match.group(2))
    pct = made / attempts if attempts else float("nan")
    return made, attempts, pct

def ncaaf_stat_lookup(stats: list[dict]) -> dict:
    return {str(item.get("name", "")).strip(): item for item in stats or []}

def ncaaf_stat_value(stats: dict, name: str) -> float:
    item = stats.get(name, {}) or {}
    value = item.get("value")
    if value in {None, "", "-"}:
        value = item.get("displayValue")
    return ncaaf_parse_number(value)

def ncaaf_stat_display(stats: dict, name: str) -> str:
    item = stats.get(name, {}) or {}
    return str(item.get("displayValue") or item.get("value") or "")

def ncaaf_summary_stats_by_team(summary: dict) -> dict:
    out = {}
    teams = ((summary or {}).get("boxscore", {}) or {}).get("teams", []) or []
    for team_box in teams:
        team_id = safe_int((team_box.get("team", {}) or {}).get("id"))
        if team_id:
            out[team_id] = ncaaf_stat_lookup(team_box.get("statistics", []) or [])
    return out

def ncaaf_defensive_sacks_by_team(summary: dict) -> dict[int, float]:
    """Sum player defensive sacks because ESPN omits sacks from team totals."""
    out: dict[int, float] = {}
    player_groups = ((summary or {}).get("boxscore", {}) or {}).get("players", []) or []
    for team_group in player_groups:
        team_id = safe_int((team_group.get("team", {}) or {}).get("id"))
        if not team_id:
            continue
        sack_total = 0.0
        found = False
        for category in team_group.get("statistics", []) or []:
            if str(category.get("name") or "").lower() != "defensive":
                continue
            labels = [str(label or "").strip().upper() for label in category.get("labels", []) or []]
            if "SACKS" not in labels:
                continue
            sack_index = labels.index("SACKS")
            for athlete in category.get("athletes", []) or []:
                values = athlete.get("stats", []) or []
                if sack_index < len(values):
                    value = safe_float(values[sack_index])
                    if pd.notna(value):
                        sack_total += value
                        found = True
        if found:
            out[team_id] = sack_total
    return out

def ncaaf_competitor_stats(competitor: dict) -> dict:
    return ncaaf_stat_lookup(competitor.get("statistics", []) or [])

def ncaaf_offense_from_stats(stats: dict) -> dict:
    total_yards = ncaaf_stat_value(stats, "totalYards")
    passing_yards = ncaaf_stat_value(stats, "netPassingYards")
    rushing_yards = ncaaf_stat_value(stats, "rushingYards")
    rushing_attempts = ncaaf_stat_value(stats, "rushingAttempts")
    yards_per_rush = ncaaf_stat_value(stats, "yardsPerRushAttempt")
    yards_per_pass = ncaaf_stat_value(stats, "yardsPerPass")
    first_downs = ncaaf_stat_value(stats, "firstDowns")
    third_conv, third_att, third_pct = ncaaf_parse_efficiency(ncaaf_stat_display(stats, "thirdDownEff"))
    fourth_conv, fourth_att, _ = ncaaf_parse_efficiency(ncaaf_stat_display(stats, "fourthDownEff"))
    completion_display = ncaaf_stat_display(stats, "completionAttempts")
    pass_attempts = float("nan")
    completion_match = re.search(r"(\d+)\s*/\s*(\d+)", completion_display)
    if completion_match:
        pass_attempts = safe_float(completion_match.group(2))
    plays = ncaaf_stat_value(stats, "totalOffensivePlays")
    if pd.isna(plays):
        plays = (pass_attempts if pd.notna(pass_attempts) else 0) + (rushing_attempts if pd.notna(rushing_attempts) else 0)
        if not plays:
            plays = float("nan")
    yards_per_play = total_yards / plays if pd.notna(total_yards) and pd.notna(plays) and plays else float("nan")
    run_rate = rushing_attempts / plays if pd.notna(rushing_attempts) and pd.notna(plays) and plays else float("nan")
    pass_rate = pass_attempts / plays if pd.notna(pass_attempts) and pd.notna(plays) and plays else float("nan")
    turnovers = ncaaf_stat_value(stats, "turnovers")
    if pd.isna(turnovers):
        turnovers = ncaaf_stat_value(stats, "fumblesLost") + ncaaf_stat_value(stats, "interceptions")
    possession = ncaaf_stat_value(stats, "possessionTime")
    return {
        "total_yards": total_yards,
        "plays": plays,
        "pass_attempts": pass_attempts,
        "yards_per_play": yards_per_play,
        "run_rate": run_rate,
        "pass_rate": pass_rate,
        "passing_yards": passing_yards,
        "rushing_yards": rushing_yards,
        "rushing_attempts": rushing_attempts,
        "yards_per_rush": yards_per_rush,
        "yards_per_pass": yards_per_pass,
        "first_downs": first_downs,
        "third_down_conv": third_conv,
        "third_down_att": third_att,
        "third_down_pct": third_pct,
        "fourth_down_conv": fourth_conv,
        "fourth_down_att": fourth_att,
        "turnovers": turnovers,
        "possession_seconds": possession,
    }

def ncaaf_team_name(competitor: dict) -> str:
    team = competitor.get("team", {}) or {}
    return str(team.get("displayName") or team.get("name") or team.get("shortDisplayName") or "Team")

def ncaaf_clean_hex_color(value: Any, fallback: str = "#2dd4bf") -> str:
    color = str(value or "").strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", color):
        return f"#{color}"
    return fallback

def ncaaf_team_color(competitor: dict, fallback: str = "#2dd4bf") -> str:
    team = competitor.get("team", {}) or {}
    return ncaaf_clean_hex_color(team.get("color"), fallback)

def ncaaf_team_alt_color(competitor: dict, fallback: str = "#f8fafc") -> str:
    team = competitor.get("team", {}) or {}
    return ncaaf_clean_hex_color(team.get("alternateColor"), fallback)

def ncaaf_team_abbreviation_from_competitor(competitor: dict) -> str:
    team = competitor.get("team", {}) or {}
    abbreviation = str(team.get("abbreviation") or team.get("shortDisplayName") or team.get("name") or "NCAA")
    return abbreviation[:6].upper()

def readable_text_for_hex(hex_color: str) -> str:
    color = ncaaf_clean_hex_color(hex_color, "#111827").lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return "#0f172a" if luminance > 0.63 else "#ffffff"

def football_play_by_play_metrics(summary: dict) -> dict[int, dict]:
    """Derive finishing and line-of-scrimmage rates from ESPN play-by-play.

    A trip is counted once per offensive drive. Short yardage is restricted to
    third/fourth down with two yards or fewer, while rush stuffs exclude kneels.
    Counts are retained beside every rate so small samples stay visible.
    """
    metrics: dict[int, dict] = {}
    drives_block = (summary or {}).get("drives", {}) or {}
    drives = list(drives_block.get("previous", []) or [])
    current = drives_block.get("current")
    if isinstance(current, dict) and current.get("id"):
        drives.append(current)
    unique_drives = []
    seen_drive_ids = set()
    for drive in drives:
        drive_id = str((drive or {}).get("id") or "")
        if drive_id and drive_id in seen_drive_ids:
            continue
        if drive_id:
            seen_drive_ids.add(drive_id)
        unique_drives.append(drive)
    drives = unique_drives

    def team_metrics(team_id: int) -> dict:
        if team_id not in metrics:
            metrics[team_id] = {
                "red_zone_td": 0.0,
                "red_zone_trips": 0.0,
                "goal_to_go_td": 0.0,
                "goal_to_go_trips": 0.0,
                "short_yardage_conv": 0.0,
                "short_yardage_att": 0.0,
                "rush_stuffed": 0.0,
                "rush_attempts_charted": 0.0,
            }
        return metrics[team_id]

    for drive in drives:
        offense_id = safe_int(((drive or {}).get("team", {}) or {}).get("id"))
        if not offense_id:
            continue
        plays = []
        for play in (drive or {}).get("plays", []) or []:
            start = play.get("start", {}) or {}
            start_team_id = safe_int((start.get("team", {}) or {}).get("id"))
            if start_team_id == offense_id:
                plays.append(play)
        if not plays:
            continue

        values = team_metrics(offense_id)
        reached_red_zone = False
        reached_goal_to_go = False
        offensive_td = False
        for play in plays:
            start = play.get("start", {}) or {}
            end = play.get("end", {}) or {}
            end_team_id = safe_int((end.get("team", {}) or {}).get("id"))
            play_type = str(((play.get("type", {}) or {}).get("text")) or "").strip().lower()
            play_text = str(play.get("text") or "").lower()
            scoring_play = bool(play.get("scoringPlay"))
            start_distance_to_goal = safe_float(start.get("yardsToEndzone"))
            end_distance_to_goal = safe_float(end.get("yardsToEndzone"))
            field_distances = [
                value
                for value, belongs_to_offense in [
                    (start_distance_to_goal, True),
                    (end_distance_to_goal, end_team_id == offense_id and not scoring_play),
                ]
                if belongs_to_offense and pd.notna(value) and value > 0
            ]
            reached_red_zone = reached_red_zone or any(value <= 20 for value in field_distances)
            reached_goal_to_go = reached_goal_to_go or any(value <= 10 for value in field_distances)

            if scoring_play and play_type in {"rushing touchdown", "passing touchdown"}:
                offensive_td = True

            is_rush = play_type in {"rush", "rushing touchdown"}
            if is_rush and "kneel" not in play_text:
                values["rush_attempts_charted"] += 1
                yards = safe_float(play.get("statYardage"))
                if pd.notna(yards) and yards <= 0:
                    values["rush_stuffed"] += 1

            down = safe_int(start.get("down"))
            distance = safe_float(start.get("distance"))
            short_yardage_play = (
                down in {3, 4}
                and pd.notna(distance)
                and 0 < distance <= 2
                and play_type not in {"penalty", "timeout", "end period", "end of game"}
            )
            if short_yardage_play:
                values["short_yardage_att"] += 1
                end_down = safe_int(end.get("down"))
                converted = offensive_td or (end_team_id == offense_id and end_down == 1)
                if converted:
                    values["short_yardage_conv"] += 1

        if reached_red_zone:
            values["red_zone_trips"] += 1
            if offensive_td:
                values["red_zone_td"] += 1
        if reached_goal_to_go:
            values["goal_to_go_trips"] += 1
            if offensive_td:
                values["goal_to_go_td"] += 1

    for values in metrics.values():
        for rate_key, made_key, attempt_key in [
            ("red_zone_td_pct", "red_zone_td", "red_zone_trips"),
            ("goal_to_go_td_pct", "goal_to_go_td", "goal_to_go_trips"),
            ("short_yardage_pct", "short_yardage_conv", "short_yardage_att"),
            ("rush_stuffed_rate", "rush_stuffed", "rush_attempts_charted"),
        ]:
            attempts = safe_float(values.get(attempt_key))
            values[rate_key] = (
                safe_float(values.get(made_key)) / attempts
                if pd.notna(attempts) and attempts > 0
                else float("nan")
            )
    return metrics

def ncaaf_build_team_log_rows(event: dict, summary: dict) -> list[dict]:
    competitions = event.get("competitions", []) or []
    if not competitions:
        return []
    competition = competitions[0]
    competitors = competition.get("competitors", []) or []
    if len(competitors) < 2:
        return []
    stats_by_team = ncaaf_summary_stats_by_team(summary)
    defensive_sacks_by_team = ncaaf_defensive_sacks_by_team(summary)
    situational_by_team = football_play_by_play_metrics(summary)
    raw_rows = []
    for competitor in competitors:
        team = competitor.get("team", {}) or {}
        team_id = safe_int(team.get("id"))
        stats = stats_by_team.get(team_id) or ncaaf_competitor_stats(competitor)
        offense = ncaaf_offense_from_stats(stats)
        raw_rows.append(
            {
                "game_id": str(event.get("id") or ""),
                "date": str(event.get("date") or "")[:10],
                "season": safe_int(((event.get("season", {}) or {}).get("year"))),
                "week": safe_int(((event.get("week", {}) or {}).get("number"))),
                "season_type": str(((event.get("season", {}) or {}).get("slug")) or ((event.get("season", {}) or {}).get("type")) or ""),
                "team": ncaaf_team_name(competitor),
                "team_id": team_id,
                "opponent": "",
                "opponent_id": "",
                "home_away": str(competitor.get("homeAway") or ""),
                "neutral_site": bool(competition.get("neutralSite")),
                "points": safe_int(competitor.get("score")),
                "opponent_points": pd.NA,
                "win": bool(competitor.get("winner")),
                "sacks_made": defensive_sacks_by_team.get(team_id, float("nan")),
                **offense,
                **situational_by_team.get(team_id, {}),
            }
        )
        points = safe_float(raw_rows[-1].get("points"))
        plays = safe_float(raw_rows[-1].get("plays"))
        total_yards = safe_float(raw_rows[-1].get("total_yards"))
        raw_rows[-1]["plays_per_point"] = plays / points if points and pd.notna(plays) else float("nan")
        raw_rows[-1]["points_per_play"] = points / plays if pd.notna(points) and pd.notna(plays) and plays else float("nan")
        raw_rows[-1]["yards_per_point"] = total_yards / points if points and pd.notna(total_yards) else float("nan")
    if len(raw_rows) != 2:
        return raw_rows
    a, b = raw_rows
    a.update(
        {
            "opponent": b["team"],
            "opponent_id": b["team_id"],
            "opponent_points": b["points"],
            "yards_allowed": b.get("total_yards"),
            "plays_allowed": b.get("plays"),
            "pass_attempts_allowed": b.get("pass_attempts"),
            "sacks_allowed": b.get("sacks_made"),
            "yards_per_play_allowed": b.get("yards_per_play"),
            "plays_per_point_allowed": b.get("plays_per_point"),
            "points_per_play_allowed": b.get("points_per_play"),
            "yards_per_point_allowed": b.get("yards_per_point"),
            "passing_yards_allowed": b.get("passing_yards"),
            "rushing_yards_allowed": b.get("rushing_yards"),
            "rushing_attempts_allowed": b.get("rushing_attempts"),
            "run_rate_allowed": b.get("run_rate"),
            "pass_rate_allowed": b.get("pass_rate"),
            "third_down_conv_allowed": b.get("third_down_conv"),
            "third_down_att_allowed": b.get("third_down_att"),
            "third_down_pct_allowed": b.get("third_down_pct"),
            "red_zone_td_allowed": b.get("red_zone_td"),
            "red_zone_trips_allowed": b.get("red_zone_trips"),
            "red_zone_td_pct_allowed": b.get("red_zone_td_pct"),
            "goal_to_go_td_allowed": b.get("goal_to_go_td"),
            "goal_to_go_trips_allowed": b.get("goal_to_go_trips"),
            "goal_to_go_td_pct_allowed": b.get("goal_to_go_td_pct"),
            "goal_to_go_stop_pct": (
                1 - safe_float(b.get("goal_to_go_td_pct"))
                if pd.notna(safe_float(b.get("goal_to_go_td_pct")))
                else float("nan")
            ),
            "short_yardage_conv_allowed": b.get("short_yardage_conv"),
            "short_yardage_att_allowed": b.get("short_yardage_att"),
            "short_yardage_pct_allowed": b.get("short_yardage_pct"),
            "short_yardage_stop_pct": (
                1 - safe_float(b.get("short_yardage_pct"))
                if pd.notna(safe_float(b.get("short_yardage_pct")))
                else float("nan")
            ),
            "rush_stuffs": b.get("rush_stuffed"),
            "rush_stuff_opportunities": b.get("rush_attempts_charted"),
            "rush_stuff_rate": b.get("rush_stuffed_rate"),
            "takeaways": b.get("turnovers"),
        }
    )
    b.update(
        {
            "opponent": a["team"],
            "opponent_id": a["team_id"],
            "opponent_points": a["points"],
            "yards_allowed": a.get("total_yards"),
            "plays_allowed": a.get("plays"),
            "pass_attempts_allowed": a.get("pass_attempts"),
            "sacks_allowed": a.get("sacks_made"),
            "yards_per_play_allowed": a.get("yards_per_play"),
            "plays_per_point_allowed": a.get("plays_per_point"),
            "points_per_play_allowed": a.get("points_per_play"),
            "yards_per_point_allowed": a.get("yards_per_point"),
            "passing_yards_allowed": a.get("passing_yards"),
            "rushing_yards_allowed": a.get("rushing_yards"),
            "rushing_attempts_allowed": a.get("rushing_attempts"),
            "run_rate_allowed": a.get("run_rate"),
            "pass_rate_allowed": a.get("pass_rate"),
            "third_down_conv_allowed": a.get("third_down_conv"),
            "third_down_att_allowed": a.get("third_down_att"),
            "third_down_pct_allowed": a.get("third_down_pct"),
            "red_zone_td_allowed": a.get("red_zone_td"),
            "red_zone_trips_allowed": a.get("red_zone_trips"),
            "red_zone_td_pct_allowed": a.get("red_zone_td_pct"),
            "goal_to_go_td_allowed": a.get("goal_to_go_td"),
            "goal_to_go_trips_allowed": a.get("goal_to_go_trips"),
            "goal_to_go_td_pct_allowed": a.get("goal_to_go_td_pct"),
            "goal_to_go_stop_pct": (
                1 - safe_float(a.get("goal_to_go_td_pct"))
                if pd.notna(safe_float(a.get("goal_to_go_td_pct")))
                else float("nan")
            ),
            "short_yardage_conv_allowed": a.get("short_yardage_conv"),
            "short_yardage_att_allowed": a.get("short_yardage_att"),
            "short_yardage_pct_allowed": a.get("short_yardage_pct"),
            "short_yardage_stop_pct": (
                1 - safe_float(a.get("short_yardage_pct"))
                if pd.notna(safe_float(a.get("short_yardage_pct")))
                else float("nan")
            ),
            "rush_stuffs": a.get("rush_stuffed"),
            "rush_stuff_opportunities": a.get("rush_attempts_charted"),
            "rush_stuff_rate": a.get("rush_stuffed_rate"),
            "takeaways": a.get("turnovers"),
        }
    )
    for row in raw_rows:
        pass_attempts = safe_float(row.get("pass_attempts"))
        sacks_allowed = safe_float(row.get("sacks_allowed"))
        opponent_pass_attempts = safe_float(row.get("pass_attempts_allowed"))
        sacks_made = safe_float(row.get("sacks_made"))
        row["sack_rate_allowed"] = (
            sacks_allowed / (pass_attempts + sacks_allowed)
            if pd.notna(pass_attempts) and pd.notna(sacks_allowed) and pass_attempts + sacks_allowed > 0
            else float("nan")
        )
        row["sack_rate_made"] = (
            sacks_made / (opponent_pass_attempts + sacks_made)
            if pd.notna(opponent_pass_attempts) and pd.notna(sacks_made) and opponent_pass_attempts + sacks_made > 0
            else float("nan")
        )
        row["turnover_margin"] = safe_float(row.get("takeaways")) - safe_float(row.get("turnovers"))
    return [{col: row.get(col, pd.NA) for col in NCAAF_TEAM_LOG_COLUMNS} for row in raw_rows]

def update_ncaaf_team_game_logs(season: int) -> tuple[bool, str]:
    try:
        today = pd.Timestamp.today().normalize()
        target_end = min(today - pd.Timedelta(days=1), ncaaf_season_end(season))
        existing = pd.DataFrame()
        if NCAAF_TEAM_LOG_PATH.exists():
            try:
                existing = pd.read_csv(NCAAF_TEAM_LOG_PATH)
                missing_schema_cols = [col for col in NCAAF_TEAM_LOG_COLUMNS if col not in existing.columns]
                if "date" in existing.columns:
                    existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
            except Exception:
                existing = pd.DataFrame()
                missing_schema_cols = []
        else:
            missing_schema_cols = []
        if not existing.empty and "date" in existing.columns and existing["date"].notna().any():
            latest_existing = existing["date"].max().normalize()
            if latest_existing >= target_end and not missing_schema_cols:
                return True, f"NCAAF logs already up to date through {latest_existing.strftime('%Y-%m-%d')}."
            start_ts = (
                ncaaf_season_start(season)
                if missing_schema_cols
                else max(ncaaf_season_start(season), latest_existing - pd.Timedelta(days=3))
            )
        else:
            start_ts = ncaaf_season_start(season)
        if target_end < start_ts:
            return True, f"NCAAF logs already fresh through {target_end.strftime('%Y-%m-%d')}."

        rows = []
        failed = []
        completed_events = []
        for day in pd.date_range(start_ts, target_end):
            try:
                scoreboard = espn_cfb_get({"dates": day.strftime("%Y%m%d"), "groups": 80, "limit": 300}, timeout=20)
            except Exception as exc:
                failed.append(f"{day.strftime('%Y-%m-%d')}: scoreboard {exc}")
                continue
            for event in scoreboard.get("events", []) or []:
                status = (((event.get("status", {}) or {}).get("type", {}) or {}))
                if not status.get("completed"):
                    continue
                event_id = str(event.get("id") or "")
                if not event_id:
                    continue
                completed_events.append(event)

        def fetch_completed_event(event: dict) -> tuple[str, list[dict], str]:
            event_id = str(event.get("id") or "")
            try:
                summary = espn_cfb_summary(event_id, timeout=20)
                return event_id, ncaaf_build_team_log_rows(event, summary), ""
            except Exception as exc:
                return event_id, [], str(exc)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_completed_event, event) for event in completed_events]
            for future in as_completed(futures):
                event_id, event_rows, error = future.result()
                if error:
                    failed.append(f"{event_id}: summary {error}")
                else:
                    rows.extend(event_rows)

        fresh = pd.DataFrame(rows)
        if fresh.empty and existing.empty:
            return False, "No completed NCAAF games were returned from ESPN for this range."
        if not fresh.empty:
            refreshed_ids = set(fresh["game_id"].dropna().astype(str))
            if not existing.empty and "game_id" in existing.columns:
                existing = existing[~existing["game_id"].astype(str).isin(refreshed_ids)]
            combined = pd.concat([existing, fresh], ignore_index=True) if not existing.empty else fresh
        else:
            combined = existing.copy()
        combined = prepare_ncaaf_team_logs(combined)
        combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
        NCAAF_TEAM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(NCAAF_TEAM_LOG_PATH, index=False)
        message = (
            f"Updated {len(rows)} team-game rows from {start_ts.strftime('%Y-%m-%d')} through {target_end.strftime('%Y-%m-%d')}. "
            f"Saved {len(combined)} total rows to {NCAAF_TEAM_LOG_PATH}."
        )
        if failed:
            message += "\nSkipped items:\n" + "\n".join(failed[:12])
        return True, message
    except Exception as exc:
        return False, str(exc)

def fetch_ncaaf_schedule_for_date(game_date: Any) -> list[dict]:
    data = fetch_ncaaf_scoreboard_data(str(game_date))
    games = []
    for event in data.get("events", []) or []:
        competitions = event.get("competitions", []) or []
        if not competitions:
            continue
        competition = competitions[0]
        competitors = competition.get("competitors", []) or []
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[0] if competitors else {})
        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[-1] if competitors else {})
        status = ((event.get("status", {}) or {}).get("type", {}) or {})
        venue = (competition.get("venue", {}) or {}).get("fullName") or (competition.get("venue", {}) or {}).get("name")
        games.append(
            {
                "game_id": str(event.get("id") or ""),
                "label": str(event.get("shortName") or event.get("name") or ""),
                "name": str(event.get("name") or ""),
                "date": str(event.get("date") or ""),
                "season": safe_int(((event.get("season", {}) or {}).get("year"))),
                "week": safe_int(((event.get("week", {}) or {}).get("number"))),
                "status": str(status.get("description") or status.get("detail") or ""),
                "state": str(status.get("state") or ""),
                "completed": bool(status.get("completed")),
                "venue": venue or "",
                "neutral_site": bool(competition.get("neutralSite")),
                "away_team": ncaaf_team_name(away),
                "away_id": safe_int((away.get("team", {}) or {}).get("id")),
                "away_abbrev": ncaaf_team_abbreviation_from_competitor(away),
                "away_color": ncaaf_team_color(away, "#38bdf8"),
                "away_alt_color": ncaaf_team_alt_color(away, "#f8fafc"),
                "away_score": safe_int(away.get("score")),
                "home_team": ncaaf_team_name(home),
                "home_id": safe_int((home.get("team", {}) or {}).get("id")),
                "home_abbrev": ncaaf_team_abbreviation_from_competitor(home),
                "home_color": ncaaf_team_color(home, "#f59e0b"),
                "home_alt_color": ncaaf_team_alt_color(home, "#f8fafc"),
                "home_score": safe_int(home.get("score")),
                "espn_odds": competition.get("odds", []) or [],
            }
        )
    fallback_time = pd.Timestamp("2100-01-01", tz="UTC")
    return sorted(games, key=lambda game: parse_timestamp_utc(game.get("date")) or fallback_time)

def update_nfl_team_game_logs(season: int) -> tuple[bool, str]:
    try:
        today = pd.Timestamp.today().normalize()
        target_end = min(today - pd.Timedelta(days=1), nfl_season_end(season))
        existing = pd.DataFrame()
        if NFL_TEAM_LOG_PATH.exists():
            try:
                existing = pd.read_csv(NFL_TEAM_LOG_PATH)
                missing_schema_cols = [col for col in NCAAF_TEAM_LOG_COLUMNS if col not in existing.columns]
                if "date" in existing.columns:
                    existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
            except Exception:
                existing = pd.DataFrame()
                missing_schema_cols = []
        else:
            missing_schema_cols = []
        if not existing.empty and "date" in existing.columns and existing["date"].notna().any():
            latest_existing = existing["date"].max().normalize()
            if latest_existing >= target_end - pd.Timedelta(days=4) and not missing_schema_cols:
                return True, f"NFL logs already current through {latest_existing.strftime('%Y-%m-%d')}."
            start_ts = (
                nfl_season_start(season)
                if missing_schema_cols
                else max(nfl_season_start(season), latest_existing - pd.Timedelta(days=7))
            )
        else:
            start_ts = nfl_season_start(season)
        if target_end < start_ts:
            return True, f"NFL logs already current through {target_end.strftime('%Y-%m-%d')}."

        rows = []
        failed = []
        completed_events = []
        for day in pd.date_range(start_ts, target_end):
            try:
                scoreboard = espn_nfl_get({"dates": day.strftime("%Y%m%d"), "limit": 100}, timeout=20)
            except Exception as exc:
                failed.append(f"{day.strftime('%Y-%m-%d')}: scoreboard {exc}")
                continue
            for event in scoreboard.get("events", []) or []:
                status = ((event.get("status", {}) or {}).get("type", {}) or {})
                event_id = str(event.get("id") or "")
                if status.get("completed") and event_id:
                    completed_events.append(event)

        def fetch_completed_event(event: dict) -> tuple[str, list[dict], str]:
            event_id = str(event.get("id") or "")
            try:
                summary = espn_nfl_summary(event_id, timeout=20)
                return event_id, ncaaf_build_team_log_rows(event, summary), ""
            except Exception as exc:
                return event_id, [], str(exc)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_completed_event, event) for event in completed_events]
            for future in as_completed(futures):
                event_id, event_rows, error = future.result()
                if error:
                    failed.append(f"{event_id}: summary {error}")
                else:
                    rows.extend(event_rows)

        fresh = pd.DataFrame(rows)
        if fresh.empty and existing.empty:
            return False, "No completed NFL games were returned from ESPN for this range."
        if not fresh.empty:
            refreshed_ids = set(fresh["game_id"].dropna().astype(str))
            if not existing.empty and "game_id" in existing.columns:
                existing = existing[~existing["game_id"].astype(str).isin(refreshed_ids)]
            combined = pd.concat([existing, fresh], ignore_index=True) if not existing.empty else fresh
        else:
            combined = existing.copy()
        combined = prepare_ncaaf_team_logs(combined)
        combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
        NFL_TEAM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(NFL_TEAM_LOG_PATH, index=False)
        message = (
            f"Updated {len(rows)} NFL team-game rows from {start_ts.strftime('%Y-%m-%d')} through "
            f"{target_end.strftime('%Y-%m-%d')}. Saved {len(combined)} total rows to {NFL_TEAM_LOG_PATH}."
        )
        if failed:
            message += "\nSkipped items:\n" + "\n".join(failed[:12])
        return True, message
    except Exception as exc:
        return False, str(exc)

def fetch_nfl_schedule_for_date(game_date: Any) -> list[dict]:
    data = fetch_nfl_scoreboard_data(str(game_date))
    games = []
    for event in data.get("events", []) or []:
        competitions = event.get("competitions", []) or []
        if not competitions:
            continue
        competition = competitions[0]
        competitors = competition.get("competitors", []) or []
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[0] if competitors else {})
        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[-1] if competitors else {})
        status = ((event.get("status", {}) or {}).get("type", {}) or {})
        venue = (competition.get("venue", {}) or {}).get("fullName") or (competition.get("venue", {}) or {}).get("name")
        games.append(
            {
                "game_id": str(event.get("id") or ""),
                "label": str(event.get("shortName") or event.get("name") or ""),
                "name": str(event.get("name") or ""),
                "date": str(event.get("date") or ""),
                "season": safe_int((event.get("season", {}) or {}).get("year")),
                "week": safe_int((event.get("week", {}) or {}).get("number")),
                "status": str(status.get("description") or status.get("detail") or ""),
                "state": str(status.get("state") or ""),
                "completed": bool(status.get("completed")),
                "venue": venue or "",
                "neutral_site": bool(competition.get("neutralSite")),
                "away_team": ncaaf_team_name(away),
                "away_id": safe_int((away.get("team", {}) or {}).get("id")),
                "away_abbrev": ncaaf_team_abbreviation_from_competitor(away),
                "away_color": ncaaf_team_color(away, "#38bdf8"),
                "away_alt_color": ncaaf_team_alt_color(away, "#f8fafc"),
                "away_score": safe_int(away.get("score")),
                "home_team": ncaaf_team_name(home),
                "home_id": safe_int((home.get("team", {}) or {}).get("id")),
                "home_abbrev": ncaaf_team_abbreviation_from_competitor(home),
                "home_color": ncaaf_team_color(home, "#f59e0b"),
                "home_alt_color": ncaaf_team_alt_color(home, "#f8fafc"),
                "home_score": safe_int(home.get("score")),
                "espn_odds": competition.get("odds", []) or [],
            }
        )
    fallback_time = pd.Timestamp("2100-01-01", tz="UTC")
    return sorted(games, key=lambda game: parse_timestamp_utc(game.get("date")) or fallback_time)

def ncaaf_weighted_rate(df: pd.DataFrame, made_col: str, att_col: str) -> float:
    made = df[made_col].sum(skipna=True) if made_col in df.columns else 0
    attempts = df[att_col].sum(skipna=True) if att_col in df.columns else 0
    return float(made / attempts) if attempts else float("nan")

def ncaaf_aggregate_rows(team_df: pd.DataFrame) -> dict:
    if team_df.empty:
        return {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "points": float("nan"),
            "points_allowed": float("nan"),
            "total_yards": float("nan"),
            "yards_allowed": float("nan"),
            "plays": float("nan"),
            "plays_allowed": float("nan"),
            "pass_attempts": float("nan"),
            "pass_attempts_allowed": float("nan"),
            "sacks_allowed": float("nan"),
            "sacks_made": float("nan"),
            "sack_rate_allowed": float("nan"),
            "sack_rate_made": float("nan"),
            "yards_per_play": float("nan"),
            "yards_per_play_allowed": float("nan"),
            "plays_per_point": float("nan"),
            "plays_per_point_allowed": float("nan"),
            "points_per_play": float("nan"),
            "points_per_play_allowed": float("nan"),
            "yards_per_point": float("nan"),
            "yards_per_point_allowed": float("nan"),
            "passing_yards": float("nan"),
            "passing_yards_allowed": float("nan"),
            "rushing_yards": float("nan"),
            "rushing_yards_allowed": float("nan"),
            "rushing_attempts": float("nan"),
            "rushing_attempts_allowed": float("nan"),
            "run_rate": float("nan"),
            "run_rate_allowed": float("nan"),
            "pass_rate": float("nan"),
            "pass_rate_allowed": float("nan"),
            "yards_per_rush": float("nan"),
            "yards_per_pass": float("nan"),
            "third_down_pct": float("nan"),
            "third_down_conv": float("nan"),
            "third_down_att": float("nan"),
            "third_down_conv_allowed": float("nan"),
            "third_down_att_allowed": float("nan"),
            "third_down_pct_allowed": float("nan"),
            "red_zone_td": float("nan"),
            "red_zone_trips": float("nan"),
            "red_zone_td_pct": float("nan"),
            "red_zone_td_allowed": float("nan"),
            "red_zone_trips_allowed": float("nan"),
            "red_zone_td_pct_allowed": float("nan"),
            "goal_to_go_td": float("nan"),
            "goal_to_go_trips": float("nan"),
            "goal_to_go_td_pct": float("nan"),
            "goal_to_go_td_allowed": float("nan"),
            "goal_to_go_trips_allowed": float("nan"),
            "goal_to_go_td_pct_allowed": float("nan"),
            "goal_to_go_stop_pct": float("nan"),
            "short_yardage_conv": float("nan"),
            "short_yardage_att": float("nan"),
            "short_yardage_pct": float("nan"),
            "short_yardage_conv_allowed": float("nan"),
            "short_yardage_att_allowed": float("nan"),
            "short_yardage_pct_allowed": float("nan"),
            "short_yardage_stop_pct": float("nan"),
            "rush_stuffed": float("nan"),
            "rush_attempts_charted": float("nan"),
            "rush_stuffed_rate": float("nan"),
            "rush_stuffs": float("nan"),
            "rush_stuff_opportunities": float("nan"),
            "rush_stuff_rate": float("nan"),
            "turnovers": float("nan"),
            "takeaways": float("nan"),
            "turnover_margin": float("nan"),
        }
    points_sum = team_df["points"].sum(skipna=True)
    points_allowed_sum = team_df["opponent_points"].sum(skipna=True)
    yards_sum = team_df["total_yards"].sum(skipna=True)
    yards_allowed_sum = team_df["yards_allowed"].sum(skipna=True)
    plays_sum = team_df["plays"].sum(skipna=True)
    plays_allowed_sum = team_df["plays_allowed"].sum(skipna=True)
    rush_attempts_sum = team_df["rushing_attempts"].sum(skipna=True)
    rush_attempts_allowed_sum = team_df["rushing_attempts_allowed"].sum(skipna=True)
    pass_attempts_sum = team_df["pass_attempts"].sum(skipna=True)
    pass_attempts_allowed_sum = team_df["pass_attempts_allowed"].sum(skipna=True)
    sacks_allowed_sum = team_df["sacks_allowed"].sum(skipna=True)
    sacks_made_sum = team_df["sacks_made"].sum(skipna=True)
    goal_to_go_stop_pct = 1 - ncaaf_weighted_rate(team_df, "goal_to_go_td_allowed", "goal_to_go_trips_allowed")
    short_yardage_stop_pct = 1 - ncaaf_weighted_rate(
        team_df, "short_yardage_conv_allowed", "short_yardage_att_allowed"
    )
    return {
        "games": int(len(team_df)),
        "wins": int(team_df["win"].sum()),
        "losses": int(len(team_df) - team_df["win"].sum()),
        "points": float(team_df["points"].mean()),
        "points_allowed": float(team_df["opponent_points"].mean()),
        "total_yards": float(team_df["total_yards"].mean()),
        "yards_allowed": float(team_df["yards_allowed"].mean()),
        "plays": float(team_df["plays"].mean()),
        "plays_allowed": float(team_df["plays_allowed"].mean()),
        "pass_attempts": float(team_df["pass_attempts"].mean()),
        "pass_attempts_allowed": float(team_df["pass_attempts_allowed"].mean()),
        "sacks_allowed": float(sacks_allowed_sum),
        "sacks_made": float(sacks_made_sum),
        "sack_rate_allowed": (
            float(sacks_allowed_sum / (pass_attempts_sum + sacks_allowed_sum))
            if pass_attempts_sum + sacks_allowed_sum > 0 and team_df["sacks_allowed"].notna().any()
            else float("nan")
        ),
        "sack_rate_made": (
            float(sacks_made_sum / (pass_attempts_allowed_sum + sacks_made_sum))
            if pass_attempts_allowed_sum + sacks_made_sum > 0 and team_df["sacks_made"].notna().any()
            else float("nan")
        ),
        "yards_per_play": float(yards_sum / plays_sum) if plays_sum else float("nan"),
        "yards_per_play_allowed": float(yards_allowed_sum / plays_allowed_sum) if plays_allowed_sum else float("nan"),
        "plays_per_point": float(plays_sum / points_sum) if points_sum else float("nan"),
        "plays_per_point_allowed": float(plays_allowed_sum / points_allowed_sum) if points_allowed_sum else float("nan"),
        "points_per_play": float(points_sum / plays_sum) if plays_sum else float("nan"),
        "points_per_play_allowed": float(points_allowed_sum / plays_allowed_sum) if plays_allowed_sum else float("nan"),
        "yards_per_point": float(yards_sum / points_sum) if points_sum else float("nan"),
        "yards_per_point_allowed": float(yards_allowed_sum / points_allowed_sum) if points_allowed_sum else float("nan"),
        "passing_yards": float(team_df["passing_yards"].mean()),
        "passing_yards_allowed": float(team_df["passing_yards_allowed"].mean()),
        "rushing_yards": float(team_df["rushing_yards"].mean()),
        "rushing_yards_allowed": float(team_df["rushing_yards_allowed"].mean()),
        "rushing_attempts": float(team_df["rushing_attempts"].mean()),
        "rushing_attempts_allowed": float(team_df["rushing_attempts_allowed"].mean()),
        "run_rate": float(rush_attempts_sum / plays_sum) if plays_sum else float("nan"),
        "run_rate_allowed": float(rush_attempts_allowed_sum / plays_allowed_sum) if plays_allowed_sum else float("nan"),
        "pass_rate": float(pass_attempts_sum / plays_sum) if plays_sum else float("nan"),
        "pass_rate_allowed": float(pass_attempts_allowed_sum / plays_allowed_sum) if plays_allowed_sum else float("nan"),
        "yards_per_rush": float(team_df["yards_per_rush"].mean()),
        "yards_per_pass": float(team_df["yards_per_pass"].mean()),
        "third_down_conv": float(team_df["third_down_conv"].sum(skipna=True)),
        "third_down_att": float(team_df["third_down_att"].sum(skipna=True)),
        "third_down_pct": ncaaf_weighted_rate(team_df, "third_down_conv", "third_down_att"),
        "third_down_conv_allowed": float(team_df["third_down_conv_allowed"].sum(skipna=True)),
        "third_down_att_allowed": float(team_df["third_down_att_allowed"].sum(skipna=True)),
        "third_down_pct_allowed": ncaaf_weighted_rate(
            team_df, "third_down_conv_allowed", "third_down_att_allowed"
        ),
        "red_zone_td": float(team_df["red_zone_td"].sum(skipna=True)),
        "red_zone_trips": float(team_df["red_zone_trips"].sum(skipna=True)),
        "red_zone_td_pct": ncaaf_weighted_rate(team_df, "red_zone_td", "red_zone_trips"),
        "red_zone_td_allowed": float(team_df["red_zone_td_allowed"].sum(skipna=True)),
        "red_zone_trips_allowed": float(team_df["red_zone_trips_allowed"].sum(skipna=True)),
        "red_zone_td_pct_allowed": ncaaf_weighted_rate(
            team_df, "red_zone_td_allowed", "red_zone_trips_allowed"
        ),
        "goal_to_go_td": float(team_df["goal_to_go_td"].sum(skipna=True)),
        "goal_to_go_trips": float(team_df["goal_to_go_trips"].sum(skipna=True)),
        "goal_to_go_td_pct": ncaaf_weighted_rate(team_df, "goal_to_go_td", "goal_to_go_trips"),
        "goal_to_go_td_allowed": float(team_df["goal_to_go_td_allowed"].sum(skipna=True)),
        "goal_to_go_trips_allowed": float(team_df["goal_to_go_trips_allowed"].sum(skipna=True)),
        "goal_to_go_td_pct_allowed": ncaaf_weighted_rate(
            team_df, "goal_to_go_td_allowed", "goal_to_go_trips_allowed"
        ),
        "goal_to_go_stop_pct": goal_to_go_stop_pct,
        "short_yardage_conv": float(team_df["short_yardage_conv"].sum(skipna=True)),
        "short_yardage_att": float(team_df["short_yardage_att"].sum(skipna=True)),
        "short_yardage_pct": ncaaf_weighted_rate(team_df, "short_yardage_conv", "short_yardage_att"),
        "short_yardage_conv_allowed": float(team_df["short_yardage_conv_allowed"].sum(skipna=True)),
        "short_yardage_att_allowed": float(team_df["short_yardage_att_allowed"].sum(skipna=True)),
        "short_yardage_pct_allowed": ncaaf_weighted_rate(
            team_df, "short_yardage_conv_allowed", "short_yardage_att_allowed"
        ),
        "short_yardage_stop_pct": short_yardage_stop_pct,
        "rush_stuffed": float(team_df["rush_stuffed"].sum(skipna=True)),
        "rush_attempts_charted": float(team_df["rush_attempts_charted"].sum(skipna=True)),
        "rush_stuffed_rate": ncaaf_weighted_rate(team_df, "rush_stuffed", "rush_attempts_charted"),
        "rush_stuffs": float(team_df["rush_stuffs"].sum(skipna=True)),
        "rush_stuff_opportunities": float(team_df["rush_stuff_opportunities"].sum(skipna=True)),
        "rush_stuff_rate": ncaaf_weighted_rate(team_df, "rush_stuffs", "rush_stuff_opportunities"),
        "turnovers": float(team_df["turnovers"].mean()),
        "takeaways": float(team_df["takeaways"].mean()),
        "turnover_margin": float(team_df["turnover_margin"].mean()),
    }

def ncaaf_sos_label(score: Any) -> tuple[str, str]:
    numeric = safe_float(score)
    if pd.isna(numeric):
        return "SOS unavailable", "neutral"
    if numeric >= 4.0:
        return "Very tough schedule", "good"
    if numeric >= 1.5:
        return "Tough schedule", "good"
    if numeric <= -4.0:
        return "Very soft schedule", "bad"
    if numeric <= -1.5:
        return "Soft schedule", "warning"
    return "Average schedule", "neutral"

def ordinal_rank(value: Any) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric) or numeric <= 0:
        return "n/a"
    rank = int(numeric)
    suffix = "th" if 10 <= rank % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
    return f"{rank}{suffix}"

def ncaaf_strength_of_schedule_map(logs: pd.DataFrame) -> dict[str, dict]:
    """Rate opponents using only their games against other teams.

    Excluding the head-to-head result prevents a team's own blowout from being
    counted twice: once in its performance and again as proof of a soft schedule.
    """
    if logs is None or logs.empty:
        return {}
    season_logs = logs.copy()
    if "season" in season_logs.columns and season_logs["season"].notna().any():
        season_logs = season_logs[season_logs["season"] == season_logs["season"].max()].copy()
    season_logs["game_id"] = season_logs["game_id"].astype(str)
    out: dict[str, dict] = {}
    for team_name, team_games in season_logs.groupby("team", dropna=True):
        components = []
        opponent_wins = 0
        opponent_losses = 0
        independent_games = 0
        for _, game in team_games.iterrows():
            opponent = str(game.get("opponent") or "").strip()
            if not opponent:
                continue
            opponent_games = season_logs[
                (season_logs["team"] == opponent)
                & (season_logs["game_id"] != str(game.get("game_id") or ""))
            ]
            if opponent_games.empty:
                continue
            opponent_form = ncaaf_aggregate_rows(opponent_games)
            games = safe_int(opponent_form.get("games"))
            if not games:
                continue
            wins = safe_int(opponent_form.get("wins"))
            losses = safe_int(opponent_form.get("losses"))
            win_pct = wins / games
            point_margin = safe_float(opponent_form.get("points")) - safe_float(opponent_form.get("points_allowed"))
            ypp_margin = safe_float(opponent_form.get("yards_per_play")) - safe_float(opponent_form.get("yards_per_play_allowed"))
            point_component = 0.0 if pd.isna(point_margin) else max(-30.0, min(30.0, point_margin)) * 0.12
            ypp_component = 0.0 if pd.isna(ypp_margin) else max(-3.0, min(3.0, ypp_margin))
            components.append(6.0 * (win_pct - 0.5) + point_component + ypp_component)
            opponent_wins += wins
            opponent_losses += losses
            independent_games += games

        played_opponents = int(len(team_games))
        rated_opponents = len(components)
        coverage = rated_opponents / played_opponents if played_opponents else 0.0
        if not components:
            out[str(team_name)] = {
                "available": False,
                "label": "SOS unavailable",
                "tone": "neutral",
                "score": float("nan"),
                "adjustment": 0.0,
                "opponent_wins": 0,
                "opponent_losses": 0,
                "opponent_win_pct": float("nan"),
                "rated_opponents": 0,
                "played_opponents": played_opponents,
                "independent_games": 0,
                "coverage": 0.0,
                "reliability": 0.0,
                "confidence": "Low",
            }
            continue

        score = sum(components) / len(components)
        reliability = min(1.0, independent_games / 8.0) * coverage
        adjustment = max(-4.5, min(4.5, score * reliability))
        label, tone = ncaaf_sos_label(score)
        opponent_total = opponent_wins + opponent_losses
        out[str(team_name)] = {
            "available": True,
            "label": label,
            "tone": tone,
            "score": round(score, 2),
            "adjustment": round(adjustment, 2),
            "opponent_wins": opponent_wins,
            "opponent_losses": opponent_losses,
            "opponent_win_pct": opponent_wins / opponent_total if opponent_total else float("nan"),
            "rated_opponents": rated_opponents,
            "played_opponents": played_opponents,
            "independent_games": independent_games,
            "coverage": coverage,
            "reliability": reliability,
            "confidence": "High" if reliability >= 0.75 else ("Medium" if reliability >= 0.40 else "Low"),
        }
    return out

def nfl_strength_of_schedule_map(logs: pd.DataFrame) -> dict[str, dict]:
    """Apply the NFL definition: aggregate W-L-T percentage of all opponents.

    A repeated divisional opponent is counted once for each scheduled meeting,
    matching the aggregate-opponent-record convention.  The official metric is
    the percentage and rank; its betting-model translation is capped at one
    point per team and reduced until eight games have been played.
    """
    if logs is None or logs.empty:
        return {}
    season_logs = logs.copy()
    if "season" in season_logs.columns and season_logs["season"].notna().any():
        season_logs = season_logs[season_logs["season"] == season_logs["season"].max()].copy()
    if "season_type" in season_logs.columns:
        regular_logs = season_logs[season_logs["season_type"].astype(str).str.lower() != "preseason"].copy()
        if not regular_logs.empty:
            season_logs = regular_logs
    season_logs["game_id"] = season_logs["game_id"].astype(str)
    season_logs = season_logs.drop_duplicates(["team", "game_id"], keep="last")

    raw: dict[str, dict] = {}
    for team_name, team_games in season_logs.groupby("team", dropna=True):
        opponent_wins = 0
        opponent_losses = 0
        opponent_ties = 0
        rated_opponents = 0
        opponent_games_counted = 0
        for _, game in team_games.iterrows():
            opponent = str(game.get("opponent") or "").strip()
            if not opponent:
                continue
            opponent_games = season_logs[season_logs["team"] == opponent]
            if opponent_games.empty:
                continue
            points = pd.to_numeric(opponent_games["points"], errors="coerce")
            points_allowed = pd.to_numeric(opponent_games["opponent_points"], errors="coerce")
            valid = points.notna() & points_allowed.notna()
            wins = int((points[valid] > points_allowed[valid]).sum())
            losses = int((points[valid] < points_allowed[valid]).sum())
            ties = int((points[valid] == points_allowed[valid]).sum())
            games = wins + losses + ties
            if not games:
                continue
            # Deliberately count an opponent's record again when that opponent
            # appears twice on the schedule (normally a divisional opponent).
            opponent_wins += wins
            opponent_losses += losses
            opponent_ties += ties
            opponent_games_counted += games
            rated_opponents += 1

        played_opponents = int(len(team_games))
        coverage = rated_opponents / played_opponents if played_opponents else 0.0
        opponent_win_pct = (
            (opponent_wins + 0.5 * opponent_ties) / opponent_games_counted
            if opponent_games_counted
            else float("nan")
        )
        raw[str(team_name)] = {
            "available": bool(opponent_games_counted),
            "method": "nfl_official",
            "metric_name": "Opponent aggregate W-L-T%",
            "opponent_wins": opponent_wins,
            "opponent_losses": opponent_losses,
            "opponent_ties": opponent_ties,
            "opponent_win_pct": opponent_win_pct,
            "rated_opponents": rated_opponents,
            "played_opponents": played_opponents,
            "independent_games": opponent_games_counted,
            "coverage": coverage,
        }

    available_pcts = [
        safe_float(values.get("opponent_win_pct"))
        for values in raw.values()
        if values.get("available") and pd.notna(safe_float(values.get("opponent_win_pct")))
    ]
    league_average = sum(available_pcts) / len(available_pcts) if available_pcts else float("nan")
    for values in raw.values():
        pct = safe_float(values.get("opponent_win_pct"))
        if not values.get("available") or pd.isna(pct):
            values.update(
                {
                    "label": "SOS unavailable",
                    "tone": "neutral",
                    "score": float("nan"),
                    "adjustment": 0.0,
                    "reliability": 0.0,
                    "confidence": "Low",
                    "official_rank": None,
                    "official_rank_display": "n/a",
                    "official_rank_available": False,
                    "rank_source": "NFL opponent aggregate W-L-T%",
                }
            )
            continue
        rank = 1 + sum(other > pct + 1e-12 for other in available_pcts)
        team_games = safe_int(values.get("played_opponents"))
        reliability = min(1.0, team_games / 8.0) * safe_float(values.get("coverage"))
        centered = pct - league_average if pd.notna(league_average) else 0.0
        adjustment = max(-1.0, min(1.0, centered * 10.0)) * reliability
        field_size = max(1, len(available_pcts))
        percentile = (rank - 1) / max(1, field_size - 1)
        if percentile <= 0.20:
            label, tone = "Very tough schedule", "good"
        elif percentile <= 0.40:
            label, tone = "Tough schedule", "good"
        elif percentile >= 0.80:
            label, tone = "Very soft schedule", "bad"
        elif percentile >= 0.60:
            label, tone = "Soft schedule", "warning"
        else:
            label, tone = "Average schedule", "neutral"
        values.update(
            {
                "label": label,
                "tone": tone,
                "score": round(pct, 4),
                "league_average": round(league_average, 4) if pd.notna(league_average) else float("nan"),
                "adjustment": round(adjustment, 2),
                "reliability": reliability,
                "confidence": "High" if reliability >= 0.75 else ("Medium" if reliability >= 0.40 else "Low"),
                "official_rank": rank,
                "official_rank_display": ordinal_rank(rank),
                "official_rank_available": True,
                "rank_source": "NFL opponent aggregate W-L-T%",
            }
        )
    return raw

def attach_espn_sos_ranks(
    sos_map: dict[str, dict],
    ranking_data: dict,
    league_label: str = "NCAAF",
) -> dict[str, dict]:
    """Attach ESPN's published SOS rank and keep the model consistent with it.

    The NFL keeps its league-defined opponent W-L-T calculation.  For NCAAF,
    ESPN AvgInSOS is both the displayed rank and the source of the capped point
    adjustment.  The local opponent-adjusted calculation is retained only as a
    fallback when ESPN does not publish a rank for a logged team.
    """
    enriched = {team: dict(values or {}) for team, values in (sos_map or {}).items()}
    is_nfl = str(league_label).upper() == "NFL"
    internal_order = sorted(
        (
            (team, safe_float(values.get("score")))
            for team, values in enriched.items()
            if values.get("available") and pd.notna(safe_float(values.get("score")))
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    internal_ranks = {team: rank for rank, (team, _) in enumerate(internal_order, start=1)}
    official_rows = list((ranking_data or {}).get("rows", []) or [])
    official_ranks = [
        safe_int(row.get("rank"))
        for row in official_rows
        if safe_int(row.get("rank")) > 0
    ]
    official_field_size = max(official_ranks, default=0)
    used_rows: set[int] = set()

    for team, values in enriched.items():
        values["internal_rank"] = internal_ranks.get(team)
        values["internal_rank_display"] = ordinal_rank(internal_ranks.get(team))
        match_index = None
        expected = normalize_name(team)
        for index, row in enumerate(official_rows):
            if index in used_rows:
                continue
            candidates = [row.get("team", ""), row.get("short_name", ""), row.get("abbreviation", "")]
            if expected and expected in {normalize_name(candidate) for candidate in candidates if candidate}:
                match_index = index
                break
        if match_index is not None:
            espn_rank = safe_int(official_rows[match_index].get("rank"))
            used_rows.add(match_index)
        else:
            espn_rank = 0
        values["espn_rank"] = espn_rank or None
        values["espn_rank_display"] = ordinal_rank(espn_rank)
        values["espn_rank_available"] = bool(espn_rank)
        values["espn_rank_source"] = str((ranking_data or {}).get("source") or "ESPN FPI AvgInSOS")
        values["espn_rank_updated_at"] = (ranking_data or {}).get("updated_at")
        if not is_nfl:
            values["fallback_score"] = values.get("score")
            values["fallback_adjustment"] = values.get("adjustment")
            values["fallback_label"] = values.get("label")
            fallback_rank = safe_int(values.get("internal_rank"))
            primary_rank = espn_rank or fallback_rank
            values["official_rank"] = primary_rank or None
            values["official_rank_display"] = ordinal_rank(primary_rank)
            values["official_rank_available"] = bool(primary_rank)
            values["rank_source"] = (
                str((ranking_data or {}).get("source") or "ESPN FPI AvgInSOS")
                if espn_rank
                else "NCAAF opponent-adjusted fallback"
            )
            values["rank_updated_at"] = (ranking_data or {}).get("updated_at")
            if espn_rank and official_field_size > 1:
                rank_percentile = (espn_rank - 1) / (official_field_size - 1)
                rank_strength = 1.0 - (2.0 * rank_percentile)
                # One team's official SOS can move its rating by at most 2.25
                # points, so even the strongest-vs-softest matchup is capped at
                # 4.5 points.  ESPN already incorporates the schedule sample in
                # AvgInSOS, so a second local reliability multiplier is avoided.
                values["adjustment"] = round(max(-2.25, min(2.25, rank_strength * 2.25)), 2)
                values["adjustment_source"] = "ESPN FPI AvgInSOS rank"
                values["available"] = True
                if rank_percentile <= 0.20:
                    values["label"], values["tone"] = "Very tough schedule", "good"
                elif rank_percentile <= 0.40:
                    values["label"], values["tone"] = "Tough schedule", "good"
                elif rank_percentile >= 0.80:
                    values["label"], values["tone"] = "Very soft schedule", "bad"
                elif rank_percentile >= 0.60:
                    values["label"], values["tone"] = "Soft schedule", "warning"
                else:
                    values["label"], values["tone"] = "Average schedule", "neutral"
            else:
                values["adjustment_source"] = "NCAAF opponent-adjusted fallback"
    return enriched

def ncaaf_team_snapshot(
    logs: pd.DataFrame,
    team_name: str,
    recent_games: int = 3,
    sos_map: dict[str, dict] | None = None,
) -> dict:
    team_df = logs[logs["team"] == team_name].sort_values(["date", "game_id"]) if not logs.empty else pd.DataFrame()
    season = ncaaf_aggregate_rows(team_df)
    recent = ncaaf_aggregate_rows(team_df.tail(recent_games))
    last3 = ncaaf_aggregate_rows(team_df.tail(3))
    last5 = ncaaf_aggregate_rows(team_df.tail(5))
    return {
        "team": team_name,
        "season": season,
        "recent": recent,
        "last3": last3,
        "last5": last5,
        "games": season.get("games", 0),
        "record": f"{season.get('wins', 0)}-{season.get('losses', 0)}",
        "sos": (sos_map or {}).get(team_name, {}),
    }

def ncaaf_profile_label(snapshot: dict, side: str = "offense") -> tuple[str, str]:
    recent = (snapshot or {}).get("recent", {}) or {}
    points = safe_float(recent.get("points" if side == "offense" else "points_allowed"))
    ypp = safe_float(recent.get("yards_per_play" if side == "offense" else "yards_per_play_allowed"))
    sos_adjustment = safe_float(((snapshot or {}).get("sos", {}) or {}).get("adjustment"))
    sos_adjustment = 0.0 if pd.isna(sos_adjustment) else sos_adjustment
    if side == "offense":
        points = points + sos_adjustment if pd.notna(points) else points
        ypp = ypp + sos_adjustment * 0.06 if pd.notna(ypp) else ypp
    else:
        points = points - sos_adjustment if pd.notna(points) else points
        ypp = ypp - sos_adjustment * 0.06 if pd.notna(ypp) else ypp
    if side == "offense":
        if pd.notna(points) and points >= 34 and pd.notna(ypp) and ypp >= 6.2:
            return "Explosive offense", "good"
        if pd.notna(points) and points >= 28 and pd.notna(ypp) and ypp >= 5.6:
            return "Productive offense", "good"
        if pd.notna(points) and points <= 20:
            return "Low-output offense", "bad"
        return "Neutral offense", "neutral"
    if pd.notna(points) and points <= 18 and pd.notna(ypp) and ypp <= 4.9:
        return "Stop unit", "good"
    if pd.notna(points) and points <= 23:
        return "Solid defense", "good"
    if pd.notna(points) and points >= 31:
        return "Targetable defense", "bad"
    return "Neutral defense", "neutral"

def ncaaf_format_rate(value: Any) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric):
        return "n/a"
    return f"{numeric * 100:.0f}%"

def ncaaf_conversion_display(made: Any, attempts: Any, rate: Any) -> str:
    made_value = safe_float(made)
    attempts_value = safe_float(attempts)
    rate_label = ncaaf_format_rate(rate)
    if pd.notna(made_value) and pd.notna(attempts_value) and attempts_value > 0:
        return f"{made_value:.0f}/{attempts_value:.0f} · {rate_label}"
    return rate_label

def ncaaf_pressure_matchup(team_snap: dict, opp_snap: dict) -> dict:
    team = (team_snap or {}).get("recent", {}) or {}
    opp = (opp_snap or {}).get("recent", {}) or {}

    def average_available(*values: Any) -> float:
        usable = [safe_float(value) for value in values]
        usable = [value for value in usable if pd.notna(value)]
        return sum(usable) / len(usable) if usable else float("nan")

    team_risk = average_available(team.get("sack_rate_allowed"), opp.get("sack_rate_made"))
    opponent_risk = average_available(opp.get("sack_rate_allowed"), team.get("sack_rate_made"))
    sample_games = min(safe_int(team.get("games")), safe_int(opp.get("games")))
    reliability = min(1.0, sample_games / 4.0)
    if pd.isna(team_risk) or pd.isna(opponent_risk):
        adjustment = 0.0
    else:
        adjustment = max(-2.5, min(2.5, (opponent_risk - team_risk) * 28.0)) * reliability
    return {
        "available": pd.notna(team_risk) and pd.notna(opponent_risk),
        "team_risk": team_risk,
        "opponent_risk": opponent_risk,
        "adjustment": adjustment,
        "reliability": reliability,
    }

def football_goal_line_los_matchup(team_snap: dict, opp_snap: dict) -> dict:
    """Compare each offense with the opposing goal-line/LOS defense.

    The adjustment is deliberately capped and attempt-weighted. These events
    are highly predictive in context but can be dangerously noisy early in a
    season, especially goal-to-go possessions.
    """
    team = (team_snap or {}).get("recent", {}) or {}
    opp = (opp_snap or {}).get("recent", {}) or {}

    def average_available(*values: Any) -> float:
        usable = [safe_float(value) for value in values]
        usable = [value for value in usable if pd.notna(value)]
        return sum(usable) / len(usable) if usable else float("nan")

    def reliability(*attempts: Any, full_sample: float) -> float:
        total = sum(max(0.0, safe_float(value)) for value in attempts if pd.notna(safe_float(value)))
        return min(1.0, total / full_sample) if total > 0 else 0.0

    team_goal = average_available(team.get("goal_to_go_td_pct"), opp.get("goal_to_go_td_pct_allowed"))
    opp_goal = average_available(opp.get("goal_to_go_td_pct"), team.get("goal_to_go_td_pct_allowed"))
    goal_reliability = reliability(
        team.get("goal_to_go_trips"),
        opp.get("goal_to_go_trips_allowed"),
        opp.get("goal_to_go_trips"),
        team.get("goal_to_go_trips_allowed"),
        full_sample=16.0,
    )

    team_short = average_available(team.get("short_yardage_pct"), opp.get("short_yardage_pct_allowed"))
    opp_short = average_available(opp.get("short_yardage_pct"), team.get("short_yardage_pct_allowed"))
    short_reliability = reliability(
        team.get("short_yardage_att"),
        opp.get("short_yardage_att_allowed"),
        opp.get("short_yardage_att"),
        team.get("short_yardage_att_allowed"),
        full_sample=28.0,
    )

    team_stuff_risk = average_available(team.get("rush_stuffed_rate"), opp.get("rush_stuff_rate"))
    opp_stuff_risk = average_available(opp.get("rush_stuffed_rate"), team.get("rush_stuff_rate"))
    stuff_reliability = reliability(
        team.get("rush_attempts_charted"),
        opp.get("rush_stuff_opportunities"),
        opp.get("rush_attempts_charted"),
        team.get("rush_stuff_opportunities"),
        full_sample=120.0,
    )

    components = []
    if pd.notna(team_goal) and pd.notna(opp_goal):
        components.append((team_goal - opp_goal) * 2.0 * goal_reliability)
    if pd.notna(team_short) and pd.notna(opp_short):
        components.append((team_short - opp_short) * 1.5 * short_reliability)
    if pd.notna(team_stuff_risk) and pd.notna(opp_stuff_risk):
        components.append((opp_stuff_risk - team_stuff_risk) * 2.0 * stuff_reliability)
    adjustment = max(-1.5, min(1.5, sum(components))) if components else 0.0
    return {
        "available": bool(components),
        "adjustment": adjustment,
        "team_goal_td_expectation": team_goal,
        "opponent_goal_td_expectation": opp_goal,
        "team_short_yardage_expectation": team_short,
        "opponent_short_yardage_expectation": opp_short,
        "team_stuff_risk": team_stuff_risk,
        "opponent_stuff_risk": opp_stuff_risk,
        "goal_reliability": goal_reliability,
        "short_reliability": short_reliability,
        "stuff_reliability": stuff_reliability,
    }

def ncaaf_ol_continuity_context(
    flags: pd.DataFrame | None,
    team_name: Any,
    injury_context: dict | None = None,
) -> dict:
    prepared = prepare_ncaaf_ol_continuity_flags(flags)
    rows = prepared.iloc[0:0].copy()
    if not prepared.empty:
        mask = prepared["team"].map(
            lambda value: ncaaf_team_names_match(str(team_name or ""), [str(value)])
        )
        rows = prepared[mask].sort_values("updated_at", ascending=False).head(1)

    manual_penalty = 0.0
    status = "No continuity flag"
    note = ""
    source_url = ""
    line_combinations = float("nan")
    if not rows.empty:
        row = rows.iloc[0]
        age_days = max(0.0, (pd.Timestamp.now(tz="UTC") - row.get("updated_at")).total_seconds() / 86400)
        freshness_scale = 1.0 if age_days <= 21 else (0.5 if age_days <= 42 else 0.0)
        manual_penalty = min(2.0, max(0.0, safe_float(row.get("penalty_points")))) * freshness_scale
        status = str(row.get("status") or "Continuity concern")
        note = str(row.get("note") or "")
        source_url = str(row.get("source_url") or "")
        line_combinations = safe_float(row.get("line_combinations"))

    ol_rows = (injury_context or {}).get("rows")
    injury_penalty = 0.0
    active_ol = 0
    if isinstance(ol_rows, pd.DataFrame) and not ol_rows.empty:
        ol_positions = {"OL", "OT", "OG", "C", "T", "G", "LT", "RT", "LG", "RG"}
        for _, row in ol_rows.iterrows():
            if str(row.get("position") or "").upper() not in ol_positions:
                continue
            status_factor = ncaaf_injury_status_factor(row.get("status"))
            if status_factor <= 0:
                continue
            active_ol += 1
            snap_share = safe_float(row.get("recent_offense_pct"))
            if pd.isna(snap_share):
                snap_share = safe_float(row.get("offense_pct"))
            usage_weight = 0.75 if pd.isna(snap_share) else max(0.25, min(1.0, snap_share))
            injury_penalty += usage_weight * status_factor
    injury_penalty = min(2.0, injury_penalty)
    penalty = max(manual_penalty, injury_penalty)
    if active_ol and manual_penalty <= 0:
        status = f"{active_ol} OL availability concern{'s' if active_ol != 1 else ''}"
        note = "Active offensive-line listings increase pass-protection uncertainty."
    return {
        "available": not rows.empty or active_ol > 0,
        "status": status,
        "line_combinations": line_combinations,
        "active_ol_injuries": active_ol,
        "model_penalty": round(penalty, 2),
        "source_url": source_url,
        "note": note,
    }

def ncaaf_run_pass_profile(snapshot: dict) -> dict:
    recent = (snapshot or {}).get("recent", {}) or {}
    run_rate = safe_float(recent.get("run_rate"))
    pass_rate = safe_float(recent.get("pass_rate"))
    rush_yards = safe_float(recent.get("rushing_yards"))
    pass_yards = safe_float(recent.get("passing_yards"))
    ypr = safe_float(recent.get("yards_per_rush"))
    ypa = safe_float(recent.get("yards_per_pass"))
    notes = []

    if pd.notna(run_rate):
        notes.append(f"{ncaaf_format_rate(run_rate)} run rate")
    if pd.notna(pass_rate):
        notes.append(f"{ncaaf_format_rate(pass_rate)} pass rate")

    if pd.notna(run_rate) and run_rate >= 0.56:
        label, tone = "Run-first offense", "control"
    elif pd.notna(pass_rate) and pass_rate >= 0.56:
        label, tone = "Pass-heavy offense", "volatile"
    elif pd.notna(rush_yards) and pd.notna(pass_yards) and rush_yards >= 165 and pass_yards >= 230:
        label, tone = "Balanced production", "good"
    elif pd.notna(ypa) and ypa >= 8.4 and pd.notna(pass_yards) and pass_yards >= 260:
        label, tone = "Explosive pass profile", "power"
    elif pd.notna(ypr) and ypr >= 5.2 and pd.notna(rush_yards) and rush_yards >= 185:
        label, tone = "Ground efficiency", "control"
    else:
        label, tone = "Neutral play-calling", "neutral"

    if pd.notna(ypr):
        notes.append(f"{ncaaf_metric(ypr, 2)} yards/rush")
    if pd.notna(ypa):
        notes.append(f"{ncaaf_metric(ypa, 2)} yards/pass")
    return {"label": label, "tone": tone, "notes": notes[:4]}

def ncaaf_truth_profile(snapshot: dict, opponent_snapshot: dict | None = None) -> dict:
    recent = (snapshot or {}).get("recent", {}) or {}
    opponent_recent = ((opponent_snapshot or {}).get("recent", {}) or {})
    points = safe_float(recent.get("points"))
    ypp = safe_float(recent.get("yards_per_play"))
    yards = safe_float(recent.get("total_yards"))
    plays_per_point = safe_float(recent.get("plays_per_point"))
    yards_per_point = safe_float(recent.get("yards_per_point"))
    third_down = safe_float(recent.get("third_down_pct"))
    goal_to_go_td_pct = safe_float(recent.get("goal_to_go_td_pct"))
    short_yardage_pct = safe_float(recent.get("short_yardage_pct"))
    turnovers = safe_float(recent.get("turnovers"))
    opponent_allowed = safe_float(opponent_recent.get("points_allowed"))
    opponent_ypp_allowed = safe_float(opponent_recent.get("yards_per_play_allowed"))
    notes = []

    if pd.notna(plays_per_point):
        notes.append(f"{ncaaf_metric(plays_per_point, 2)} plays/point")
    if pd.notna(ypp):
        notes.append(f"{ncaaf_metric(ypp, 2)} YPP")
    if pd.notna(turnovers):
        notes.append(f"{ncaaf_metric(turnovers, 1)} turnovers/game")
    if pd.notna(goal_to_go_td_pct):
        notes.append(f"{ncaaf_format_rate(goal_to_go_td_pct)} goal-to-go TD")
    if pd.notna(short_yardage_pct):
        notes.append(f"{ncaaf_format_rate(short_yardage_pct)} short-yard conversion")

    opponent_wall = (
        pd.notna(opponent_allowed)
        and pd.notna(opponent_ypp_allowed)
        and opponent_allowed <= 21
        and opponent_ypp_allowed <= 5.1
    )
    if pd.notna(ypp) and ypp >= 5.6 and pd.notna(points) and points <= 24 and pd.notna(turnovers) and turnovers >= 2:
        return {
            "label": "Turnover drag",
            "tone": "warning",
            "note": "Yards/efficiency were playable, but giveaways likely dragged the scoreboard.",
            "details": notes,
        }
    finishing_warning = (
        (pd.notna(goal_to_go_td_pct) and goal_to_go_td_pct <= 0.55)
        or (pd.notna(short_yardage_pct) and short_yardage_pct <= 0.45)
    )
    if (
        pd.notna(ypp)
        and ypp >= 5.6
        and pd.notna(yards)
        and yards >= 360
        and ((pd.notna(plays_per_point) and plays_per_point >= 3.2) or finishing_warning)
    ):
        return {
            "label": "Finishing problem",
            "tone": "warning",
            "note": "Moved the ball better than the score suggests, but drives were not turning into points.",
            "details": notes,
        }
    if pd.notna(points) and points <= 20 and pd.notna(ypp) and ypp <= 4.8 and pd.notna(third_down) and third_down <= 0.34:
        if opponent_wall:
            return {
                "label": "Opponent wall",
                "tone": "neutral",
                "note": "Bad offensive line, but the opponent defensive context was strong enough to soften the downgrade.",
                "details": notes,
            }
        return {
            "label": "Real offensive issue",
            "tone": "bad",
            "note": "Low scoring matched weak efficiency and chain-moving numbers.",
            "details": notes,
        }
    if pd.notna(points) and points >= 30 and pd.notna(ypp) and ypp < 5.2 and pd.notna(plays_per_point) and plays_per_point <= 2.25:
        return {
            "label": "Short-field scoring",
            "tone": "volatile",
            "note": "Points were high, but efficiency was not. Watch for turnover/special-teams help inflating the result.",
            "details": notes,
        }
    if pd.notna(points) and points >= 28 and pd.notna(ypp) and ypp >= 5.9 and pd.notna(plays_per_point) and plays_per_point <= 2.7:
        return {
            "label": "Sustainable scoring",
            "tone": "good",
            "note": "Points, yards/play and scoring efficiency are all aligned.",
            "details": notes,
        }
    if pd.notna(yards_per_point) and yards_per_point >= 18 and pd.notna(yards) and yards >= 360:
        return {
            "label": "Hidden yards",
            "tone": "warning",
            "note": "Yardage was there, but it took too many yards to create each point.",
            "details": notes + [f"{ncaaf_metric(yards_per_point, 1)} yards/point"],
        }
    return {
        "label": "Boxscore aligned",
        "tone": "neutral",
        "note": "The scoring result mostly matches the efficiency profile.",
        "details": notes,
    }

def ncaaf_matchup_fit_note(team_snap: dict, opp_snap: dict) -> str:
    team = (team_snap or {}).get("recent", {}) or {}
    opp = (opp_snap or {}).get("recent", {}) or {}
    notes = []
    team_goal_td = safe_float(team.get("goal_to_go_td_pct"))
    opp_goal_stop = safe_float(opp.get("goal_to_go_stop_pct"))
    team_short = safe_float(team.get("short_yardage_pct"))
    opp_short_stop = safe_float(opp.get("short_yardage_stop_pct"))
    team_stuffed = safe_float(team.get("rush_stuffed_rate"))
    opp_stuff_rate = safe_float(opp.get("rush_stuff_rate"))
    if pd.notna(team_goal_td) and pd.notna(opp_goal_stop):
        if team_goal_td <= 0.55 and opp_goal_stop >= 0.45:
            notes.append("goal-line finishing weakness meets a defense that has produced stops")
        elif team_goal_td >= 0.70 and opp_goal_stop <= 0.30:
            notes.append("goal-to-go offense can attack weak goal-line resistance")
    if pd.notna(team_short) and pd.notna(opp_short_stop):
        if team_short <= 0.45 and opp_short_stop >= 0.55:
            notes.append("short-yardage offense faces a line-of-scrimmage disadvantage")
        elif team_short >= 0.65 and opp_short_stop <= 0.35:
            notes.append("short-yardage offense owns a line-of-scrimmage edge")
    if pd.notna(team_stuffed) and pd.notna(opp_stuff_rate) and team_stuffed >= 0.22 and opp_stuff_rate >= 0.22:
        notes.append("run game is vulnerable to an opponent that creates stuffs")
    if safe_float(team.get("rushing_yards")) >= 165 and safe_float(opp.get("rushing_yards_allowed")) >= 175:
        notes.append("run game can attack rush-defense leakage")
    if safe_float(team.get("passing_yards")) >= 245 and safe_float(opp.get("passing_yards_allowed")) >= 250:
        notes.append("pass game can attack secondary leakage")
    if safe_float(team.get("run_rate")) >= 0.56 and safe_float(opp.get("yards_per_play_allowed")) <= 5.0:
        notes.append("run-first style may need sustained drives against a stable defense")
    if safe_float(team.get("plays_per_point")) <= 2.6 and safe_float(opp.get("plays_per_point_allowed")) <= 2.6:
        notes.append("scoring efficiency meets a defense allowing efficient scoring")
    return "; ".join(notes[:2]) or "no clear run/pass or line-of-scrimmage mismatch yet"

def ncaaf_normalize_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())

def ncaaf_game_date_candidates(game: dict) -> set[pd.Timestamp]:
    game_time = parse_timestamp_utc(game.get("date"))
    if game_time is None:
        return set()
    candidates = {
        game_time.normalize().tz_localize(None),
        game_time.tz_convert("Europe/Stockholm").normalize().tz_localize(None),
    }
    return {pd.Timestamp(candidate).normalize() for candidate in candidates if pd.notna(candidate)}

def ncaaf_familiarity_for_game(flags: pd.DataFrame, game: dict) -> pd.DataFrame:
    flags = prepare_ncaaf_familiarity_flags(flags)
    if flags.empty:
        return flags
    away = ncaaf_normalize_name(game.get("away_team"))
    home = ncaaf_normalize_name(game.get("home_team"))
    matchup_mask = (
        (flags["team"].map(ncaaf_normalize_name).isin({away, home}))
        & (flags["opponent"].map(ncaaf_normalize_name).isin({away, home}))
    )
    out = flags[matchup_mask].copy()
    if out.empty:
        return out

    date_candidates = ncaaf_game_date_candidates(game)
    if date_candidates:
        flag_dates = out["game_date"].dt.normalize()
        out = out[flag_dates.isna() | flag_dates.isin(date_candidates)]
    season = safe_int(game.get("season"))
    if season:
        out = out[out["season"].isna() | (out["season"] == season)]
    week = safe_int(game.get("week"))
    if week:
        out = out[out["week"].isna() | (out["week"] == week)]
    return out.reset_index(drop=True)

def ncaaf_familiarity_for_team(flags: pd.DataFrame, team_name: Any) -> pd.DataFrame:
    flags = prepare_ncaaf_familiarity_flags(flags)
    if flags.empty:
        return flags
    team = ncaaf_normalize_name(team_name)
    return flags[flags["team"].map(ncaaf_normalize_name) == team].reset_index(drop=True)

def ncaaf_injury_context(injuries: pd.DataFrame, team_name: Any) -> dict:
    report = prepare_ncaaf_injury_report(injuries)
    if report.empty or report["updated_at"].dropna().empty:
        return {
            "available": False,
            "rows": report.iloc[0:0].copy(),
            "label": "Availability unverified",
            "freshness": "No report",
            "model_penalty": 0.0,
            "raw_penalty": 0.0,
            "critical_qb": False,
            "stale": True,
            "updated_at": None,
        }
    def freshness_for(latest_value: pd.Timestamp) -> tuple[float, str, float]:
        hours = max(0.0, (pd.Timestamp.now(tz="UTC") - latest_value).total_seconds() / 3600)
        if hours <= 12:
            return hours, "Fresh", 1.0
        if hours <= 36:
            return hours, "Current", 1.0
        if hours <= 72:
            return hours, "Aging", 0.5
        return hours, "Stale — verify", 0.0

    latest = report["updated_at"].dropna().max()
    age_hours, freshness, freshness_scale = freshness_for(latest)
    if str(team_name or "") == "__report_status__":
        return {
            "available": True,
            "rows": report.iloc[0:0].copy(),
            "label": "Report available",
            "freshness": freshness,
            "age_hours": age_hours,
            "model_penalty": 0.0,
            "raw_penalty": 0.0,
            "critical_qb": False,
            "stale": freshness_scale == 0.0,
            "updated_at": latest,
        }
    mask = report["team"].map(lambda value: ncaaf_team_names_match(str(team_name or ""), [str(value)]))
    team_report = report[mask].copy()
    team_updates = team_report["updated_at"].dropna()
    if not team_updates.empty:
        latest = team_updates.max()
        age_hours, freshness, freshness_scale = freshness_for(latest)
    coverage_checked = bool((team_report["player"] == "__TEAM_REPORT_CHECKED__").any())
    rows = team_report[team_report["player"] != "__TEAM_REPORT_CHECKED__"].copy()
    if rows.empty and not coverage_checked:
        return {
            "available": False,
            "rows": rows,
            "label": "Availability unverified",
            "freshness": freshness,
            "age_hours": age_hours,
            "model_penalty": 0.0,
            "raw_penalty": 0.0,
            "critical_qb": False,
            "stale": True,
            "updated_at": latest,
        }
    stale_status_mask = (
        rows.apply(ncaaf_injury_game_status_is_stale, axis=1)
        if not rows.empty
        else pd.Series(dtype=bool)
    )
    stale_status_rows = rows[stale_status_mask].copy() if not rows.empty else rows.copy()
    if not rows.empty:
        rows = rows[~stale_status_mask].copy()
    if not rows.empty:
        status_text = rows["status"].fillna("").astype(str).str.lower()
        decision_status = status_text.str.contains(r"questionable|doubtful|game[ -]time", regex=True)
        qb_status = rows["position"].fillna("").astype(str).str.upper().eq("QB")
        quantified = pd.to_numeric(rows["impact_points"], errors="coerce").fillna(0).gt(0)
        rows["_display_priority"] = (
            qb_status.astype(int) * 20
            + decision_status.astype(int) * 10
            + quantified.astype(int) * 5
            + rows["status"].map(ncaaf_injury_status_factor)
        )
        rows = rows.sort_values(
            ["_display_priority", "impact_points", "position", "player"],
            ascending=[False, False, True, True],
        ).drop(columns=["_display_priority"])
    raw_penalty = min(7.5, float(rows["impact_points"].clip(lower=0).sum())) if not rows.empty else 0.0
    model_penalty = raw_penalty * freshness_scale
    critical_qb = False
    if not rows.empty:
        critical_qb = bool(
            rows.apply(
                lambda row: str(row.get("role") or "").startswith("QB1")
                and ncaaf_injury_status_factor(row.get("status")) >= 0.70,
                axis=1,
            ).any()
        )
    if rows.empty and not stale_status_rows.empty:
        label = f"{len(stale_status_rows)} old game statuses ignored"
    elif rows.empty:
        label = "Report checked — no current designation"
    elif critical_qb:
        label = "Primary QB OUT / doubtful"
    elif (rows["impact_points"] >= 1.0).any():
        label = "Key production affected"
    elif (rows["impact_points"] > 0).any():
        label = "Key availability question"
    else:
        label = f"{len(rows)} listed — roles unverified"
    return {
        "available": True,
        "rows": rows.reset_index(drop=True),
        "stale_status_rows": stale_status_rows.reset_index(drop=True),
        "stale_status_count": int(len(stale_status_rows)),
        "label": label,
        "freshness": freshness,
        "age_hours": age_hours,
        "model_penalty": round(model_penalty, 2),
        "raw_penalty": round(raw_penalty, 2),
        "critical_qb": critical_qb,
        "stale": freshness_scale == 0.0,
        "updated_at": latest,
    }

def ncaaf_metric(value: Any, digits: int = 1) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric):
        return "n/a"
    if digits == 0:
        return f"{numeric:.0f}"
    return f"{numeric:.{digits}f}"

def ncaaf_injury_spread_summary(context: dict, limit: int = 3) -> str:
    """Summarize the verified player values behind an availability adjustment."""
    rows = prepare_ncaaf_injury_report((context or {}).get("rows"))
    if rows.empty:
        return ""
    rows = rows[rows["impact_points"] > 0].sort_values("impact_points", ascending=False).head(limit)
    return ", ".join(
        f"{row.get('player')} −{ncaaf_spread_value_text(row.get('impact_points'))}"
        for _, row in rows.iterrows()
    )

def ncaaf_spread_value_text(value: Any) -> str:
    numeric = safe_float(value)
    if pd.isna(numeric):
        return "n/a"
    return f"{numeric:.2f}" if 0 < abs(numeric) < 0.1 else f"{numeric:.1f}"

def ncaaf_ol_player_spread_value(row: pd.Series) -> float:
    """Return a listed OL player's share of the separate protection adjustment."""
    ol_positions = {"OL", "OT", "OG", "C", "T", "G", "LT", "RT", "LG", "RG"}
    if str(row.get("position") or "").upper() not in ol_positions:
        return 0.0
    status_factor = ncaaf_injury_status_factor(row.get("status"))
    if status_factor <= 0:
        return 0.0
    snap_share = safe_float(row.get("recent_offense_pct"))
    if pd.isna(snap_share):
        snap_share = safe_float(row.get("offense_pct"))
    usage_weight = 0.75 if pd.isna(snap_share) else max(0.25, min(1.0, snap_share))
    return round(usage_weight * status_factor, 2)

def ncaaf_best_market_quote(odd: dict, field: str, use_closing: bool = False) -> dict:
    """Return the bettor-friendly best available line/price across books."""
    quotes = []
    for book, book_odds in ((odd or {}).get("byBookmaker", {}) or {}).items():
        if not isinstance(book_odds, dict) or (not use_closing and book_odds.get("available") is False):
            continue
        price = safe_float(book_odds.get("closeOdds" if use_closing else "odds"))
        if pd.isna(price) and use_closing:
            price = safe_float(book_odds.get("odds"))
        if pd.isna(price):
            continue
        line_key = "closeSpread" if use_closing and field == "spread" else field
        line = safe_float(book_odds.get(line_key)) if field else float("nan")
        if field and pd.isna(line) and use_closing:
            line = safe_float(book_odds.get(field))
        if field and pd.isna(line):
            continue
        quotes.append(
            {
                "book": str(book),
                "price": price,
                "line": line,
                "open_line": safe_float(book_odds.get("openSpread")) if field == "spread" else float("nan"),
                "open_price": safe_float(book_odds.get("openOdds")),
            }
        )
    if not quotes:
        return {}
    if field:
        standard_juice = [quote for quote in quotes if -125 <= quote["price"] <= 115]
        priced_quotes = standard_juice or quotes
        best_line = max(quote["line"] for quote in priced_quotes)
        same_line = [quote for quote in priced_quotes if abs(quote["line"] - best_line) < 0.01]
        return max(same_line, key=lambda quote: quote["price"])
    return max(quotes, key=lambda quote: quote["price"])

def ncaaf_sgo_market_for_game(game: dict, events: list[dict], use_closing: bool = False) -> dict:
    phase = "closing" if use_closing else "pregame"
    event = find_sgo_event(
        events,
        game.get("away_team", ""),
        game.get("home_team", ""),
        game,
        name_matcher=ncaaf_team_names_match,
    )
    if not event:
        return {"phase": phase, "availability": "no_event"}
    odds = event.get("odds", {}) if isinstance(event, dict) else {}

    def odd_by_id(odd_id: str) -> dict:
        direct = odds.get(odd_id, {}) if isinstance(odds, dict) else {}
        if direct:
            return direct
        return next((odd for odd in odds.values() if isinstance(odd, dict) and odd.get("oddID") == odd_id), {})

    market = {
        "event_id": event.get("eventID"),
        "phase": phase,
        "source": "SportsGameOdds",
        "away": {
            "spread": ncaaf_best_market_quote(odd_by_id("points-away-game-sp-away"), "spread", use_closing),
            "moneyline": ncaaf_best_market_quote(odd_by_id("points-away-game-ml-away"), "", use_closing),
        },
        "home": {
            "spread": ncaaf_best_market_quote(odd_by_id("points-home-game-sp-home"), "spread", use_closing),
            "moneyline": ncaaf_best_market_quote(odd_by_id("points-home-game-ml-home"), "", use_closing),
        },
    }
    market["availability"] = (
        "priced"
        if any(
            (market.get(side, {}) or {}).get(market_type)
            for side in ["away", "home"]
            for market_type in ["spread", "moneyline"]
        )
        else "no_quote"
    )
    return market

def espn_football_market_for_game(game: dict, use_closing: bool = False) -> dict:
    """Translate ESPN scoreboard odds into the shared football market shape.

    ESPN exposes the live pregame quote under ``close`` and the opener under
    ``open``.  Keeping this parser local to the already-fetched scoreboard
    gives the football pages a zero-request fallback when the primary odds
    service is rate limited or temporarily unavailable.
    """
    phase = "closing" if use_closing else "pregame"
    entries = game.get("espn_odds", []) or []
    if isinstance(entries, dict):
        entries = [entries]
    odd = next(
        (
            entry
            for entry in entries
            if isinstance(entry, dict) and (entry.get("pointSpread") or entry.get("moneyline"))
        ),
        {},
    )
    if not odd:
        return {"phase": phase, "availability": "no_event", "source": "ESPN"}

    provider = (odd.get("provider") or {}) if isinstance(odd.get("provider"), dict) else {}
    provider_name = str(provider.get("displayName") or provider.get("name") or "ESPN").strip()
    source = f"ESPN / {provider_name}" if provider_name and provider_name.lower() != "espn" else "ESPN"

    def quote(market_name: str, side: str, field: str = "") -> dict:
        market_block = odd.get(market_name, {}) or {}
        side_block = market_block.get(side, {}) if isinstance(market_block, dict) else {}
        if not isinstance(side_block, dict):
            return {}
        current = side_block.get("close", {}) or {}
        opener = side_block.get("open", {}) or {}
        if not isinstance(current, dict):
            current = {}
        if not isinstance(opener, dict):
            opener = {}
        price = safe_float(current.get("odds"))
        if pd.isna(price):
            price = safe_float(opener.get("odds"))
        line = safe_float(current.get("line")) if field else float("nan")
        if field and pd.isna(line):
            line = safe_float(opener.get("line"))
        if pd.isna(price) or (field and pd.isna(line)):
            return {}
        return {
            "book": provider_name or "ESPN",
            "price": price,
            "line": line,
            "open_line": safe_float(opener.get("line")) if field else float("nan"),
            "open_price": safe_float(opener.get("odds")),
        }

    market = {
        "event_id": str(game.get("game_id") or ""),
        "phase": phase,
        "source": source,
        "away": {
            "spread": quote("pointSpread", "away", "line"),
            "moneyline": quote("moneyline", "away"),
        },
        "home": {
            "spread": quote("pointSpread", "home", "line"),
            "moneyline": quote("moneyline", "home"),
        },
    }
    market["availability"] = (
        "priced"
        if any(
            (market.get(side, {}) or {}).get(market_type)
            for side in ["away", "home"]
            for market_type in ["spread", "moneyline"]
        )
        else "no_quote"
    )
    return market

def merge_football_markets(primary: dict, fallback: dict) -> dict:
    """Fill missing primary quotes from a secondary market without hiding provenance."""
    primary = dict(primary or {})
    fallback = dict(fallback or {})
    merged = {
        "event_id": primary.get("event_id") or fallback.get("event_id"),
        "phase": primary.get("phase") or fallback.get("phase") or "pregame",
        "away": {},
        "home": {},
    }
    used_sources = []
    for side in ["away", "home"]:
        for market_type in ["spread", "moneyline"]:
            primary_quote = ((primary.get(side, {}) or {}).get(market_type) or {})
            fallback_quote = ((fallback.get(side, {}) or {}).get(market_type) or {})
            quote = primary_quote or fallback_quote
            merged[side][market_type] = quote
            if quote:
                source = primary.get("source") if primary_quote else fallback.get("source")
                if source and source not in used_sources:
                    used_sources.append(str(source))
    has_quote = any(
        (merged.get(side, {}) or {}).get(market_type)
        for side in ["away", "home"]
        for market_type in ["spread", "moneyline"]
    )
    merged["availability"] = "priced" if has_quote else (
        primary.get("availability") or fallback.get("availability") or "no_event"
    )
    merged["source"] = " + ".join(used_sources) if used_sources else (
        primary.get("source") or fallback.get("source") or ""
    )
    return merged

def ncaaf_american_price(value: Any) -> str:
    price = safe_float(value)
    if pd.isna(price):
        return ""
    return f"{price:+.0f}" if price > 0 else f"{price:.0f}"

def ncaaf_signed_line(value: Any) -> str:
    line = safe_float(value)
    if pd.isna(line):
        return ""
    return f"{line:+.1f}".replace(".0", "")

def football_final_recommendation_profile(team_snap: dict, opp_snap: dict) -> dict:
    """Build the five-pillar supporting team-trait profile.

    Third-down offense/defense and red-zone offense/defense are compared as
    like-for-like team traits.  SOS is the fifth confirmation pillar.  SOS is
    intentionally not added to the numeric adjustment here because the main
    margin model already applies its value.  This is supporting context, not a
    standalone spread or moneyline recommendation.
    """
    team = (team_snap or {}).get("recent", {}) or {}
    opp = (opp_snap or {}).get("recent", {}) or {}
    categories: list[dict] = []
    weighted_signal = 0.0

    def add_rate_category(
        label: str,
        team_field: str,
        opp_field: str,
        higher_is_better: bool,
        scale: float,
        weight: float,
        team_sample_field: str,
        opp_sample_field: str,
        minimum_sample: int,
        tie_band: float,
    ) -> None:
        nonlocal weighted_signal
        team_value = safe_float(team.get(team_field))
        opp_value = safe_float(opp.get(opp_field))
        team_sample = safe_int(team.get(team_sample_field))
        opp_sample = safe_int(opp.get(opp_sample_field))
        available = (
            pd.notna(team_value)
            and pd.notna(opp_value)
            and team_sample >= minimum_sample
            and opp_sample >= minimum_sample
        )
        if not available:
            categories.append(
                {
                    "label": label,
                    "state": "unavailable",
                    "detail": f"{label} sample unavailable",
                    "available": False,
                }
            )
            return
        delta = team_value - opp_value if higher_is_better else opp_value - team_value
        if delta > tie_band:
            state = "edge"
        elif delta < -tie_band:
            state = "risk"
        else:
            state = "even"
        weighted_signal += max(-1.0, min(1.0, delta / scale)) * weight
        categories.append(
            {
                "label": label,
                "state": state,
                "detail": f"{label} {team_value * 100:.1f}% vs {opp_value * 100:.1f}%",
                "available": True,
                "delta": delta,
            }
        )

    add_rate_category(
        "3D offense", "third_down_pct", "third_down_pct", True,
        0.08, 0.65, "third_down_att", "third_down_att", 8, 0.01,
    )
    add_rate_category(
        "3D defense", "third_down_pct_allowed", "third_down_pct_allowed", False,
        0.08, 0.65, "third_down_att_allowed", "third_down_att_allowed", 8, 0.01,
    )
    add_rate_category(
        "Red zone offense", "red_zone_td_pct", "red_zone_td_pct", True,
        0.15, 0.45, "red_zone_trips", "red_zone_trips", 2, 0.02,
    )
    add_rate_category(
        "Red zone defense", "red_zone_td_pct_allowed", "red_zone_td_pct_allowed", False,
        0.15, 0.45, "red_zone_trips_allowed", "red_zone_trips_allowed", 2, 0.02,
    )

    team_sos = (team_snap or {}).get("sos", {}) or {}
    opp_sos = (opp_snap or {}).get("sos", {}) or {}
    team_rank = safe_int(team_sos.get("official_rank"))
    opp_rank = safe_int(opp_sos.get("official_rank"))
    if team_rank and opp_rank:
        rank_delta = opp_rank - team_rank
        sos_state = "edge" if rank_delta > 2 else ("risk" if rank_delta < -2 else "even")
        categories.append(
            {
                "label": "SOS",
                "state": sos_state,
                "detail": f"SOS {ordinal_rank(team_rank)} vs {ordinal_rank(opp_rank)}",
                "available": True,
                "delta": rank_delta,
            }
        )
    else:
        team_espn_rank = safe_int(team_sos.get("espn_rank"))
        opp_espn_rank = safe_int(opp_sos.get("espn_rank"))
        team_sos_adjustment = safe_float(team_sos.get("adjustment"))
        opp_sos_adjustment = safe_float(opp_sos.get("adjustment"))
        if team_espn_rank and opp_espn_rank:
            rank_delta = opp_espn_rank - team_espn_rank
            sos_state = "edge" if rank_delta > 2 else ("risk" if rank_delta < -2 else "even")
            categories.append(
                {
                    "label": "SOS (ESPN)",
                    "state": sos_state,
                    "detail": f"ESPN SOS {ordinal_rank(team_espn_rank)} vs {ordinal_rank(opp_espn_rank)}",
                    "available": True,
                    "delta": rank_delta,
                }
            )
        elif team_sos.get("available") and opp_sos.get("available") and pd.notna(team_sos_adjustment) and pd.notna(opp_sos_adjustment):
            sos_delta = team_sos_adjustment - opp_sos_adjustment
            sos_state = "edge" if sos_delta > 0.25 else ("risk" if sos_delta < -0.25 else "even")
            categories.append(
                {
                    "label": "SOS",
                    "state": sos_state,
                    "detail": f"SOS model {team_sos_adjustment:+.1f} vs {opp_sos_adjustment:+.1f}",
                    "available": True,
                    "delta": sos_delta,
                }
            )
        else:
            categories.append(
                {
                    "label": "SOS",
                    "state": "unavailable",
                    "detail": "SOS comparison unavailable",
                    "available": False,
                }
            )

    field_categories = [category for category in categories[:4] if category.get("available")]
    field_wins = sum(category.get("state") == "edge" for category in field_categories)
    field_losses = sum(category.get("state") == "risk" for category in field_categories)
    if field_wins >= 3:
        weighted_signal += 0.35
    elif field_losses >= 3:
        weighted_signal -= 0.35

    sample_games = min(safe_int(team.get("games")), safe_int(opp.get("games")))
    reliability = min(1.0, sample_games / 5.0) if sample_games else 0.0
    adjustment = max(-2.5, min(2.5, weighted_signal * reliability))
    available_categories = [category for category in categories if category.get("available")]
    wins = sum(category.get("state") == "edge" for category in available_categories)
    losses = sum(category.get("state") == "risk" for category in available_categories)
    evens = sum(category.get("state") == "even" for category in available_categories)
    available = len(available_categories)

    if available < 3:
        label, tone = "Limited team-trait evidence", "neutral"
    elif wins >= 4 and losses <= 1:
        label, tone = "Strong team-trait edge", "good"
    elif wins >= 3 and wins > losses:
        label, tone = "Team-trait edge", "good"
    elif losses >= 4 and wins <= 1:
        label, tone = "Strong team-trait concern", "bad"
    elif losses >= 3 and losses > wins:
        label, tone = "Team-trait concern", "bad"
    else:
        label, tone = "Split team-trait profile", "warning"

    team_name = str((team_snap or {}).get("team") or "Team")
    summary = (
        f"{wins}/{available} available team-trait pillars favor {team_name}; "
        f"{losses} oppose and {evens} are even."
        if available
        else "Third-down, red-zone and SOS evidence is not available yet."
    )
    return {
        "label": label,
        "tone": tone,
        "adjustment": round(adjustment, 2),
        "reliability": reliability,
        "wins": wins,
        "losses": losses,
        "evens": evens,
        "available": available,
        "categories": categories,
        "summary": summary,
    }

def ncaaf_market_adjusted_margin(
    team_snap: dict,
    opp_snap: dict,
    is_home: bool,
    neutral_site: bool,
    spread_line: float,
) -> tuple[float, list[str], list[str]]:
    """Blend recent scoring/YPP dominance with the market, then apply blowout risks."""
    team = (team_snap or {}).get("recent", {}) or {}
    opp = (opp_snap or {}).get("recent", {}) or {}
    team_games = safe_int(team.get("games"))
    opp_games = safe_int(opp.get("games"))
    reasons = []
    risks = []
    if not team_games or not opp_games:
        return float("nan"), reasons, ["no completed-game comparison yet"]

    team_net = safe_float(team.get("points")) - safe_float(team.get("points_allowed"))
    opp_net = safe_float(opp.get("points")) - safe_float(opp.get("points_allowed"))
    scoring_margin = (team_net - opp_net) / 2
    team_ypp_net = safe_float(team.get("yards_per_play")) - safe_float(team.get("yards_per_play_allowed"))
    opp_ypp_net = safe_float(opp.get("yards_per_play")) - safe_float(opp.get("yards_per_play_allowed"))
    ypp_margin = (team_ypp_net - opp_ypp_net) * 6
    components = [value for value in [scoring_margin, ypp_margin] if pd.notna(value)]
    if not components:
        return float("nan"), reasons, ["insufficient efficiency data"]
    raw_margin = scoring_margin if pd.isna(ypp_margin) else (scoring_margin * 0.68 + ypp_margin * 0.32)

    team_sos = (team_snap or {}).get("sos", {}) or {}
    opp_sos = (opp_snap or {}).get("sos", {}) or {}
    if team_sos.get("available") and opp_sos.get("available"):
        team_sos_adjustment = safe_float(team_sos.get("adjustment"))
        opp_sos_adjustment = safe_float(opp_sos.get("adjustment"))
        sos_delta = team_sos_adjustment - opp_sos_adjustment
        if pd.notna(sos_delta):
            raw_margin += sos_delta
            team_sos_context = (
                f"{team_sos.get('official_rank_display')} {team_sos.get('rank_source', 'SOS')}"
                if team_sos.get("official_rank_available")
                else team_sos.get("label", "n/a")
            )
            opp_sos_context = (
                f"{opp_sos.get('official_rank_display')} {opp_sos.get('rank_source', 'SOS')}"
                if opp_sos.get("official_rank_available")
                else opp_sos.get("label", "n/a")
            )
            reasons.append(
                f"SOS adjustment {sos_delta:+.1f} points "
                f"({team_sos_context} vs {opp_sos_context})"
            )
        if min(safe_float(team_sos.get("reliability")), safe_float(opp_sos.get("reliability"))) < 0.40:
            risks.append("strength-of-schedule evidence is still low confidence")
    else:
        risks.append("strength of schedule unavailable for one side")

    if not neutral_site:
        raw_margin += 1.5 if is_home else -1.5

    market_margin = -spread_line if pd.notna(spread_line) else float("nan")
    if pd.notna(market_margin):
        sample_weight = min(0.78, 0.40 + 0.10 * min(team_games, opp_games))
        margin = raw_margin * sample_weight + market_margin * (1 - sample_weight)
    else:
        margin = raw_margin

    pressure = ncaaf_pressure_matchup(team_snap, opp_snap)
    if pressure.get("available"):
        pressure_adjustment = safe_float(pressure.get("adjustment"))
        margin += pressure_adjustment
        if abs(pressure_adjustment) >= 0.35:
            reasons.append(f"pass-protection matchup {pressure_adjustment:+.1f} points")
        team_pressure_risk = safe_float(pressure.get("team_risk"))
        if pd.notna(team_pressure_risk) and team_pressure_risk >= 0.10:
            risks.append(f"high projected pressure rate ({team_pressure_risk * 100:.1f}%)")
            if pd.notna(spread_line) and spread_line <= -7:
                margin -= 0.75
                risks.append("pass-protection volatility is dangerous when laying a touchdown or more")
    else:
        risks.append("sack-rate matchup unavailable until logs are refreshed")

    goal_line_los = football_goal_line_los_matchup(team_snap, opp_snap)
    if goal_line_los.get("available"):
        goal_line_los_adjustment = safe_float(goal_line_los.get("adjustment"))
        margin += goal_line_los_adjustment
        if abs(goal_line_los_adjustment) >= 0.25:
            reasons.append(f"goal-line / line-of-scrimmage matchup {goal_line_los_adjustment:+.1f} points")
        if safe_float(goal_line_los.get("goal_reliability")) < 0.50:
            risks.append("goal-to-go sample is still small; finishing adjustment is reduced")
    else:
        risks.append("goal-line and short-yardage data unavailable until logs are refreshed")

    final_profile = football_final_recommendation_profile(team_snap, opp_snap)
    final_profile_adjustment = safe_float(final_profile.get("adjustment"))
    if pd.notna(final_profile_adjustment):
        margin += final_profile_adjustment
    if safe_int(final_profile.get("available")) >= 3:
        reasons.append(
            f"supporting team-trait profile {final_profile_adjustment:+.1f} points "
            f"({safe_int(final_profile.get('wins'))}/{safe_int(final_profile.get('available'))} pillars)"
        )
        if str(final_profile.get("tone")) == "bad":
            risks.append("the supporting team-trait profile points against this side")

    reasons.append(f"recent scoring-margin read {scoring_margin:+.1f}")
    if pd.notna(ypp_margin):
        reasons.append(f"YPP dominance read {ypp_margin:+.1f}")

    team_run_rate = safe_float(team.get("run_rate"))
    opp_run_rate = safe_float(opp.get("run_rate"))
    if pd.notna(spread_line) and spread_line <= -28:
        if team_run_rate >= 0.56:
            margin -= 2.0
            risks.append("run-heavy favorite can drain its own cover clock")
        if spread_line <= -35:
            margin -= 1.5
            risks.append("late backup/backdoor exposure")
        if safe_float(opp.get("points")) <= 10 and safe_float(team.get("points_allowed")) <= 14:
            margin += 1.0
            reasons.append("credible shutout profile")
    elif pd.notna(spread_line) and spread_line >= 28:
        if opp_run_rate >= 0.56:
            margin += 2.0
            reasons.append("favorite's run rate can shorten the game")
        if spread_line >= 35:
            margin += 1.5
            reasons.append("large cushion benefits from backup minutes")
        if safe_float(team.get("points")) <= 10 and safe_float(opp.get("points_allowed")) <= 14:
            margin -= 1.0
            risks.append("offense faces a credible shutout risk")
    return max(-70.0, min(70.0, margin)), reasons, risks

def ncaaf_side_signal(
    team_snap: dict,
    opp_snap: dict,
    is_home: bool,
    market: dict | None = None,
    neutral_site: bool = False,
    team_injuries: dict | None = None,
    opponent_injuries: dict | None = None,
    team_ol_context: dict | None = None,
    opponent_ol_context: dict | None = None,
) -> dict:
    team_recent = (team_snap or {}).get("recent", {}) or {}
    opp_recent = (opp_snap or {}).get("recent", {}) or {}
    reasons = []
    risks = []
    market_phase = str((market or {}).get("phase") or "pregame")
    market_availability = str((market or {}).get("availability") or "")
    side_key = "home" if is_home else "away"
    side_market = (market or {}).get(side_key, {}) or {}
    spread_quote = side_market.get("spread", {}) or {}
    ml_quote = side_market.get("moneyline", {}) or {}
    spread_line = safe_float(spread_quote.get("line"))
    spread_price = safe_float(spread_quote.get("price"))
    ml_price = safe_float(ml_quote.get("price"))
    sample_games = min(safe_int(team_recent.get("games")), safe_int(opp_recent.get("games")))
    volatility = "High" if sample_games < 3 else ("Medium" if sample_games < 5 else "Normal")
    if sample_games < 2:
        risks.append("one-game/small-sample volatility")

    margin, margin_reasons, margin_risks = ncaaf_market_adjusted_margin(
        team_snap,
        opp_snap,
        is_home,
        neutral_site,
        spread_line,
    )
    reasons.extend(margin_reasons)
    risks.extend(margin_risks)
    team_availability = team_injuries or {"available": False, "model_penalty": 0.0, "label": "Availability unverified"}
    opponent_availability = opponent_injuries or {"available": False, "model_penalty": 0.0, "label": "Availability unverified"}
    team_injury_penalty = safe_float(team_availability.get("model_penalty"))
    opponent_injury_penalty = safe_float(opponent_availability.get("model_penalty"))
    team_injury_penalty = 0.0 if pd.isna(team_injury_penalty) else team_injury_penalty
    opponent_injury_penalty = 0.0 if pd.isna(opponent_injury_penalty) else opponent_injury_penalty
    availability_adjustment = opponent_injury_penalty - team_injury_penalty
    team_ol = team_ol_context or {"available": False, "model_penalty": 0.0, "status": "No continuity flag"}
    opponent_ol = opponent_ol_context or {"available": False, "model_penalty": 0.0, "status": "No continuity flag"}
    team_ol_penalty = safe_float(team_ol.get("model_penalty"))
    opponent_ol_penalty = safe_float(opponent_ol.get("model_penalty"))
    team_ol_penalty = 0.0 if pd.isna(team_ol_penalty) else team_ol_penalty
    opponent_ol_penalty = 0.0 if pd.isna(opponent_ol_penalty) else opponent_ol_penalty
    ol_adjustment = opponent_ol_penalty - team_ol_penalty
    if pd.notna(margin):
        margin = max(-70.0, min(70.0, margin + availability_adjustment + ol_adjustment))
    team_injury_summary = ncaaf_injury_spread_summary(team_availability)
    opponent_injury_summary = ncaaf_injury_spread_summary(opponent_availability)
    if team_injury_penalty > 0:
        player_detail = f" ({team_injury_summary})" if team_injury_summary else ""
        risks.insert(0, f"availability costs {team_snap.get('team')} {team_injury_penalty:.1f} projected points{player_detail}")
    if opponent_injury_penalty > 0:
        player_detail = f" ({opponent_injury_summary})" if opponent_injury_summary else ""
        reasons.insert(0, f"opponent availability adds {opponent_injury_penalty:.1f} projected points{player_detail}")
    if not team_availability.get("available") or not opponent_availability.get("available"):
        risks.insert(0, "injury availability is not verified for both teams")
    elif team_availability.get("stale") or opponent_availability.get("stale"):
        risks.insert(0, "injury report is stale; no stale adjustment is applied")
    if team_ol_penalty > 0:
        risks.insert(0, f"offensive-line continuity costs {team_snap.get('team')} {team_ol_penalty:.1f} projected points ({team_ol.get('status')})")
    if opponent_ol_penalty > 0:
        reasons.insert(0, f"opponent OL instability adds {opponent_ol_penalty:.1f} projected points ({opponent_ol.get('status')})")
    cover_edge = margin + spread_line if pd.notna(margin) and pd.notna(spread_line) else float("nan")

    if pd.isna(spread_line):
        if market_availability == "provider_error":
            label = "Market feed unavailable"
            reasons.append("odds providers could not be refreshed and no fallback quote was available")
        elif market_availability == "no_event":
            label = "No posted market"
            reasons.append("odds feeds returned no market for this matchup")
        else:
            label = "Spread unavailable"
            reasons.append("event matched, but no usable spread quote was posted")
    elif pd.isna(margin) or pd.isna(cover_edge):
        label = "Insufficient data"
    elif cover_edge >= 5:
        label = "Lay spread" if spread_line < 0 else "Take points"
    elif cover_edge >= 2:
        label = "Cover lean" if spread_line < 0 else "Points lean"
    elif cover_edge > -2:
        label = "Line looks fair"
    elif cover_edge > -5:
        label = "Spread pass"
    else:
        label = "Do not lay" if spread_line < 0 else "Do not take points"

    if (
        bool(team_availability.get("critical_qb"))
        and pd.notna(spread_line)
        and spread_line < 0
        and label in {"Lay spread", "Cover lean"}
        and (pd.isna(cover_edge) or cover_edge < 7.5)
    ):
        label = "Spread pass — QB1"
        risks.insert(0, "QB1 is out/doubtful; favorite needs a larger post-injury cushion")

    if pd.notna(spread_line):
        reasons.append(f"market asks {team_snap.get('team')} to cover {ncaaf_signed_line(spread_line)}")
    if pd.notna(cover_edge):
        reasons.append(f"adjusted cover edge {cover_edge:+.1f} points")

    win_prob = 0.5 * (1 + math.erf(margin / (17.0 * math.sqrt(2)))) if pd.notna(margin) else float("nan")
    if pd.isna(margin):
        ml_call = "ML model unavailable"
    elif pd.isna(ml_price):
        ml_call = "ML unavailable / off board"
    elif pd.notna(spread_line) and abs(spread_line) >= 28:
        ml_call = "ML unplayable at this mismatch" if ml_price < 0 else "Lottery ML — spread only"
    else:
        implied = american_implied_probability(ml_price)
        ml_edge = win_prob - implied if pd.notna(win_prob) and pd.notna(implied) else float("nan")
        if pd.notna(ml_edge) and ml_edge >= 0.05:
            ml_call = f"ML value ({ml_edge * 100:+.1f}% model edge)"
        elif pd.notna(ml_edge) and ml_edge >= 0.02:
            ml_call = f"ML lean ({ml_edge * 100:+.1f}% model edge)"
        else:
            ml_call = "ML pass"

    spread_display = "No spread" if pd.isna(spread_line) else f"{ncaaf_signed_line(spread_line)} {ncaaf_american_price(spread_price)}".strip()
    ml_display = "OFF" if pd.isna(ml_price) else ncaaf_american_price(ml_price)
    final_profile = football_final_recommendation_profile(team_snap, opp_snap)
    return {
        "team": team_snap.get("team"),
        "opponent": opp_snap.get("team"),
        "label": label,
        "spread": spread_line,
        "spread_display": spread_display,
        "moneyline": ml_price,
        "ml_display": ml_display,
        "ml_call": ml_call,
        "model_margin": round(margin, 1) if pd.notna(margin) else float("nan"),
        "cover_edge": round(cover_edge, 1) if pd.notna(cover_edge) else float("nan"),
        "win_prob": win_prob,
        "volatility": volatility,
        "market_phase": market_phase,
        "market_availability": market_availability,
        "market_source": str((market or {}).get("source") or ""),
        "team_sos": (team_snap or {}).get("sos", {}) or {},
        "opponent_sos": (opp_snap or {}).get("sos", {}) or {},
        "availability_adjustment": round(availability_adjustment, 2),
        "ol_adjustment": round(ol_adjustment, 2),
        "pressure_matchup": ncaaf_pressure_matchup(team_snap, opp_snap),
        "goal_line_los_matchup": football_goal_line_los_matchup(team_snap, opp_snap),
        "final_profile": final_profile,
        "team_availability": team_availability,
        "opponent_availability": opponent_availability,
        "team_ol_context": team_ol,
        "opponent_ol_context": opponent_ol,
        "reasons": reasons[:6],
        "risks": list(dict.fromkeys(risks))[:5],
    }

def football_window_stability(
    signal: dict | None,
    alternate_signal: dict | None,
    current_window: int,
    alternate_window: int,
) -> dict:
    """Compare Last-3 and Last-5 cover edges before presenting a side lean."""
    current_edge = safe_float((signal or {}).get("cover_edge"))
    alternate_edge = safe_float((alternate_signal or {}).get("cover_edge"))
    if pd.isna(current_edge) or pd.isna(alternate_edge):
        return {
            "state": "unavailable",
            "label": "Window check unavailable",
            "tone": "neutral",
            "detail": "Both Last 3 and Last 5 need a posted spread and sufficient saved games.",
            "override_label": "",
        }

    def edge_state(value: float) -> str:
        if value >= 2.0:
            return "support"
        if value <= -2.0:
            return "oppose"
        return "neutral"

    current_state = edge_state(current_edge)
    alternate_state = edge_state(alternate_edge)
    detail = (
        f"Last {current_window} cover edge {current_edge:+.1f}; "
        f"Last {alternate_window} {alternate_edge:+.1f}."
    )
    if {current_state, alternate_state} == {"support", "oppose"}:
        return {
            "state": "conflict",
            "label": "Window conflict — pass",
            "tone": "bad",
            "detail": detail + " The form windows point to opposite sides.",
            "override_label": "Window conflict — pass",
        }
    if current_state == alternate_state == "support":
        return {
            "state": "stable_support",
            "label": "Stable across Last 3 / Last 5",
            "tone": "good",
            "detail": detail,
            "override_label": "",
        }
    if current_state == alternate_state == "oppose":
        return {
            "state": "stable_opposition",
            "label": "Stable opposition across windows",
            "tone": "bad",
            "detail": detail,
            "override_label": "",
        }
    return {
        "state": "sensitive",
        "label": "Window-sensitive read",
        "tone": "warning",
        "detail": detail + " One window does not clear the two-point lean threshold.",
        "override_label": "",
    }

def ncaaf_total_signal(away_snap: dict, home_snap: dict) -> dict:
    away = away_snap.get("recent", {}) or {}
    home = home_snap.get("recent", {}) or {}
    over = 0.0
    under = 0.0
    reasons = []
    if safe_float(away.get("points")) >= 28 and safe_float(home.get("points")) >= 28:
        over += 2.0
        reasons.append("both offenses are scoring recently")
    if safe_float(away.get("yards_per_play")) >= 5.8 and safe_float(home.get("yards_per_play")) >= 5.8:
        over += 1.4
        reasons.append("both offenses show YPP efficiency")
    if safe_float(away.get("plays_per_point")) <= 2.7 and safe_float(home.get("plays_per_point")) <= 2.7:
        over += 1.0
        reasons.append("both offenses are turning plays into points")
    if safe_float(away.get("points_allowed")) >= 27 or safe_float(home.get("points_allowed")) >= 27:
        over += 1.0
        reasons.append("at least one defense is allowing points")
    if safe_float(away.get("points")) <= 21 or safe_float(home.get("points")) <= 21:
        under += 1.2
        reasons.append("one offense is low-output")
    if safe_float(away.get("points_allowed")) <= 20 and safe_float(home.get("points_allowed")) <= 20:
        under += 1.4
        reasons.append("both defenses have recent stop profile")
    if safe_float(away.get("plays_per_point")) >= 3.5 or safe_float(home.get("plays_per_point")) >= 3.5:
        under += 0.8
        reasons.append("one offense needs too many plays per point")
    label = "Over lean" if over > under + 0.6 else ("Under lean" if under > over + 0.6 else "Mixed total")
    return {"label": label, "over_score": round(over, 2), "under_score": round(under, 2), "reasons": reasons[:4]}

def render_ncaaf_snapshot_card(
    snapshot: dict,
    team_color: str = "#2dd4bf",
    team_alt_color: str = "#f8fafc",
    abbreviation: str = "",
) -> str:
    offense_label, offense_tone = ncaaf_profile_label(snapshot, "offense")
    defense_label, defense_tone = ncaaf_profile_label(snapshot, "defense")
    play_profile = ncaaf_run_pass_profile(snapshot)
    truth = ncaaf_truth_profile(snapshot)
    recent = (snapshot or {}).get("recent", {}) or {}
    season = (snapshot or {}).get("season", {}) or {}
    sos = (snapshot or {}).get("sos", {}) or {}
    team_color = ncaaf_clean_hex_color(team_color, "#2dd4bf")
    team_alt_color = ncaaf_clean_hex_color(team_alt_color, "#f8fafc")
    team_glow = hex_to_rgba(team_color, 0.26)
    team_wash = hex_to_rgba(team_color, 0.14)
    team_abbrev = abbreviation or team_abbreviation(snapshot.get("team", "Team"))
    badge_text = readable_text_for_hex(team_color)
    tone_color = {"good": "#2dd4bf", "bad": "#fb7185", "neutral": "#f8fafc", "warning": "#fbbf24", "volatile": "#fb923c", "control": "#38bdf8", "power": "#a78bfa"}
    truth_details = " | ".join(truth.get("details", []) or [])
    play_notes = " | ".join(play_profile.get("notes", []) or [])
    sos_available = bool(sos.get("available"))
    is_nfl_sos = str(sos.get("method") or "") == "nfl_official"
    official_sos_rank = str(sos.get("official_rank_display") or "n/a")
    sos_tone = tone_color.get(str(sos.get("tone") or "neutral"), "#f8fafc")
    sos_adjustment_value = safe_float(sos.get("adjustment"))
    sos_adjustment = f"{sos_adjustment_value:+.1f} pts" if sos_available and pd.notna(sos_adjustment_value) else "n/a"
    if is_nfl_sos:
        sos_rank_label = "NFL SOS rank"
        sos_pct = safe_float(sos.get("opponent_win_pct"))
        sos_score_label = "NFL SOS %"
        sos_score = f"{sos_pct:.3f}" if sos_available and pd.notna(sos_pct) else "n/a"
        opponent_record = (
            f"{safe_int(sos.get('opponent_wins'))}-{safe_int(sos.get('opponent_losses'))}-{safe_int(sos.get('opponent_ties'))}"
            if sos_available
            else "n/a"
        )
        opponent_record_label = "Opponent W-L-T"
        espn_sos_rank = str(sos.get("espn_rank_display") or "n/a")
        secondary_label = "ESPN FPI SOS"
        secondary_value = espn_sos_rank
        sos_evidence = (
            f"{safe_int(sos.get('rated_opponents'))}/{safe_int(sos.get('played_opponents'))} scheduled opponents · "
            f"{safe_int(sos.get('independent_games'))} opponent games counted"
            if sos_available
            else "not enough opponent records"
        )
        sos_source_note = (
            "NFL formula: opponents' aggregate W-L-T percentage; repeated opponents are weighted by each meeting. "
            f"Capped model adjustment: {sos_adjustment}. ESPN FPI is shown separately and does not move it."
        )
    else:
        espn_rank_available = bool(sos.get("espn_rank_available"))
        sos_rank_label = "ESPN SOS rank" if espn_rank_available else "Fallback SOS rank"
        sos_score_label = "Fallback SOS score"
        fallback_score = sos.get("fallback_score") if espn_rank_available else sos.get("score")
        sos_score = ncaaf_metric(fallback_score, 1) if sos_available else "n/a"
        opponent_record = (
            f"{safe_int(sos.get('opponent_wins'))}-{safe_int(sos.get('opponent_losses'))}"
            if sos_available
            else "n/a"
        )
        opponent_record_label = "Opponent W-L"
        secondary_label = "Official rank adj." if espn_rank_available else "Fallback adj."
        secondary_value = sos_adjustment
        sos_evidence = (
            f"{safe_int(sos.get('rated_opponents'))}/{safe_int(sos.get('played_opponents'))} opp · "
            f"{safe_int(sos.get('independent_games'))} games"
            if sos_available
            else "not enough independent games"
        )
        sos_source_note = (
            "ESPN FPI AvgInSOS supplies both the primary rank and the capped margin adjustment; the local score is context only."
            if espn_rank_available
            else "ESPN FPI is unavailable; the displayed rank and adjustment use the NCAAF opponent-adjusted fallback, excluding the head-to-head result."
        )
    return compact_html(f"""
    <div class="game-card" style="min-height:238px; border-color:{html.escape(team_glow)}; background:linear-gradient(135deg, {html.escape(team_wash)} 0%, rgba(15,23,42,0.94) 48%, rgba(2,6,23,0.98) 100%); box-shadow:0 16px 36px rgba(0,0,0,0.34), inset 5px 0 0 {html.escape(team_color)};">
      <div style="display:flex; align-items:center; gap:0.75rem; min-width:0;">
        <div style="width:3.1rem; height:3.1rem; border-radius:8px; display:grid; place-items:center; background:{html.escape(team_color)}; color:{html.escape(badge_text)}; border:1px solid {html.escape(hex_to_rgba(team_alt_color, 0.55))}; box-shadow:0 12px 28px rgba(0,0,0,0.30); font-size:0.92rem; font-weight:950; letter-spacing:0.02em;">{html.escape(str(team_abbrev))}</div>
        <div style="min-width:0;">
          <div class="game-card__label">{html.escape(snapshot.get("record", "0-0"))}</div>
          <div class="game-card__team" style="font-size:1.34rem; white-space:normal;">{html.escape(str(snapshot.get("team") or "Team"))}</div>
        </div>
      </div>
      <div class="game-card__meta" style="margin-top:0.35rem;">
        <span style="color:{tone_color.get(offense_tone, '#f8fafc')}; font-weight:900;">{html.escape(offense_label)}</span>
        <span style="color:#94a3b8;"> / </span>
        <span style="color:{tone_color.get(defense_tone, '#f8fafc')}; font-weight:900;">{html.escape(defense_label)}</span>
      </div>
      <div style="margin-top:0.55rem; display:flex; gap:0.35rem; flex-wrap:wrap;">
        <span style="display:inline-block; padding:0.16rem 0.5rem; border-radius:999px; background:rgba(56,189,248,0.13); color:{tone_color.get(play_profile.get("tone"), '#38bdf8')}; font-weight:900; font-size:0.78rem;">{html.escape(play_profile.get("label", "Profile n/a"))}</span>
        <span style="display:inline-block; padding:0.16rem 0.5rem; border-radius:999px; background:rgba(251,191,36,0.13); color:{tone_color.get(truth.get("tone"), '#fbbf24')}; font-weight:900; font-size:0.78rem;">{html.escape(truth.get("label", "Truth n/a"))}</span>
      </div>
      <div style="color:#cbd5e1; font-size:0.78rem; line-height:1.35; margin-top:0.42rem;">{html.escape(play_notes)}</div>
      <div style="color:#94a3b8; font-size:0.76rem; line-height:1.35; margin-top:0.18rem;">{html.escape(truth_details or truth.get("note", ""))}</div>
      <div style="color:#94a3b8; font-size:0.7rem; font-weight:950; letter-spacing:0.09em; text-transform:uppercase; margin-top:0.75rem;">Schedule strength</div>
      <div class="quick-grid" style="display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:0.45rem; margin-top:0.35rem;">
        <div class="quick-tile"><div class="quick-tile__label">{html.escape(sos_rank_label)}</div><div class="quick-tile__value" style="color:{html.escape(sos_tone)};">{html.escape(official_sos_rank)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">{html.escape(sos_score_label)}</div><div class="quick-tile__value">{html.escape(sos_score)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">{html.escape(opponent_record_label)}</div><div class="quick-tile__value">{html.escape(opponent_record)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">{html.escape(secondary_label)}</div><div class="quick-tile__value">{html.escape(secondary_value)}</div></div>
      </div>
      <div style="color:#64748b; font-size:0.7rem; line-height:1.3; margin-top:0.3rem;">{html.escape(sos_source_note)} Evidence: {html.escape(sos_evidence)} · {html.escape(str(sos.get('confidence') or 'Low'))} confidence.</div>
      <div style="color:#94a3b8; font-size:0.7rem; font-weight:950; letter-spacing:0.09em; text-transform:uppercase; margin-top:0.75rem;">Recent offense · per game</div>
      <div class="quick-grid" style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:0.45rem; margin-top:0.35rem;">
        <div class="quick-tile"><div class="quick-tile__label">Recent PPG</div><div class="quick-tile__value">{ncaaf_metric(recent.get("points"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Total yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("total_yards"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Pass yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("passing_yards"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Rush yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("rushing_yards"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Recent YPP</div><div class="quick-tile__value">{ncaaf_metric(recent.get("yards_per_play"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Plays/point</div><div class="quick-tile__value">{ncaaf_metric(recent.get("plays_per_point"), 2)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">3rd down</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("third_down_conv"), recent.get("third_down_att"), recent.get("third_down_pct"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Goal-to-go TD</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("goal_to_go_td"), recent.get("goal_to_go_trips"), recent.get("goal_to_go_td_pct"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Short-yard conversion</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("short_yardage_conv"), recent.get("short_yardage_att"), recent.get("short_yardage_pct"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Runs stuffed</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("rush_stuffed"), recent.get("rush_attempts_charted"), recent.get("rush_stuffed_rate"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Sacks allowed</div><div class="quick-tile__value">{ncaaf_metric(recent.get("sacks_allowed"), 0)} · {ncaaf_format_rate(recent.get("sack_rate_allowed"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Run/pass</div><div class="quick-tile__value">{ncaaf_format_rate(recent.get("run_rate"))}/{ncaaf_format_rate(recent.get("pass_rate"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Season PPG</div><div class="quick-tile__value">{ncaaf_metric(season.get("points"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Games logged</div><div class="quick-tile__value">{safe_int(recent.get("games"))}</div></div>
      </div>
      <div style="color:#94a3b8; font-size:0.7rem; font-weight:950; letter-spacing:0.09em; text-transform:uppercase; margin-top:0.7rem;">Recent defense · allowed per game</div>
      <div class="quick-grid" style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:0.45rem; margin-top:0.35rem;">
        <div class="quick-tile"><div class="quick-tile__label">Points</div><div class="quick-tile__value">{ncaaf_metric(recent.get("points_allowed"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Total yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("yards_allowed"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Def YPP</div><div class="quick-tile__value">{ncaaf_metric(recent.get("yards_per_play_allowed"), 2)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Pass yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("passing_yards_allowed"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Rush yards</div><div class="quick-tile__value">{ncaaf_metric(recent.get("rushing_yards_allowed"), 0)}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">3rd down allowed</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("third_down_conv_allowed"), recent.get("third_down_att_allowed"), recent.get("third_down_pct_allowed"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Goal-line stops</div><div class="quick-tile__value">{ncaaf_conversion_display(safe_float(recent.get("goal_to_go_trips_allowed")) - safe_float(recent.get("goal_to_go_td_allowed")), recent.get("goal_to_go_trips_allowed"), recent.get("goal_to_go_stop_pct"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Short-yard stops</div><div class="quick-tile__value">{ncaaf_conversion_display(safe_float(recent.get("short_yardage_att_allowed")) - safe_float(recent.get("short_yardage_conv_allowed")), recent.get("short_yardage_att_allowed"), recent.get("short_yardage_stop_pct"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Rush stuff rate</div><div class="quick-tile__value">{ncaaf_conversion_display(recent.get("rush_stuffs"), recent.get("rush_stuff_opportunities"), recent.get("rush_stuff_rate"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Defensive sacks</div><div class="quick-tile__value">{ncaaf_metric(recent.get("sacks_made"), 0)} · {ncaaf_format_rate(recent.get("sack_rate_made"))}</div></div>
        <div class="quick-tile"><div class="quick-tile__label">Takeaways</div><div class="quick-tile__value">{ncaaf_metric(recent.get("takeaways"))}</div></div>
      </div>
    </div>
    """)

def render_ncaaf_matchup_header(game: dict, logs: pd.DataFrame, recent_games: int) -> str:
    game_time = parse_timestamp_utc(game.get("date"))
    time_label = game_time.tz_convert("Europe/Stockholm").strftime("%a %d %b %H:%M") if game_time is not None else ""
    away_color = ncaaf_clean_hex_color(game.get("away_color"), "#38bdf8")
    home_color = ncaaf_clean_hex_color(game.get("home_color"), "#f59e0b")
    away_alt = ncaaf_clean_hex_color(game.get("away_alt_color"), "#f8fafc")
    home_alt = ncaaf_clean_hex_color(game.get("home_alt_color"), "#f8fafc")
    away_glow = hex_to_rgba(away_color, 0.24)
    home_glow = hex_to_rgba(home_color, 0.24)
    away_text = readable_text_for_hex(away_color)
    home_text = readable_text_for_hex(home_color)
    away_abbrev = str(game.get("away_abbrev") or team_abbreviation(game.get("away_team", "Away")))
    home_abbrev = str(game.get("home_abbrev") or team_abbreviation(game.get("home_team", "Home")))

    def team_panel(team_name: Any, abbrev: str, side_label: str, color: str, alt_color: str, text_color: str, glow: str, is_home: bool) -> str:
        direction = "row-reverse" if is_home else "row"
        align = "right" if is_home else "left"
        gradient_direction = "270deg" if is_home else "90deg"
        inset = f"inset {'-4px' if is_home else '4px'} 0 0 {html.escape(color)}"
        return f"""
        <div style="min-width:0; padding:0.72rem 0.78rem; border-radius:8px; border:1px solid {html.escape(glow)}; background:linear-gradient({gradient_direction}, {html.escape(hex_to_rgba(color, 0.18))}, rgba(15,23,42,0.76)); box-shadow:{inset}; text-align:{align};">
          <div style="display:flex; flex-direction:{direction}; align-items:center; gap:0.65rem; min-width:0;">
            <div style="width:2.8rem; height:2.8rem; border-radius:8px; display:grid; place-items:center; background:{html.escape(color)}; color:{html.escape(text_color)}; border:1px solid {html.escape(hex_to_rgba(alt_color, 0.58))}; font-weight:950; font-size:0.78rem; flex:0 0 auto;">{html.escape(abbrev)}</div>
            <div style="min-width:0;">
              <div style="color:#f8fafc; font-size:1.22rem; line-height:1.1; font-weight:950; white-space:normal;">{html.escape(str(team_name or "Team"))}</div>
              <div style="color:#94a3b8; font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">{html.escape(side_label)}</div>
            </div>
          </div>
        </div>
        """

    return compact_html(f"""
    <div class="dashboard-card" style="padding:1rem; margin-bottom:0.85rem; border-color:{html.escape(hex_to_rgba(away_color, 0.30))}; background:linear-gradient(90deg, {html.escape(hex_to_rgba(away_color, 0.10))} 0%, rgba(15,23,42,0.96) 43%, rgba(15,23,42,0.96) 57%, {html.escape(hex_to_rgba(home_color, 0.10))} 100%);">
      <div style="display:grid; grid-template-columns:minmax(0,1fr) 3.2rem minmax(0,1fr); gap:0.7rem; align-items:center; margin-bottom:0.72rem;">
        {team_panel(game.get("away_team", "Away"), away_abbrev, "Away", away_color, away_alt, away_text, away_glow, False)}
        <div style="height:2.4rem; border-radius:999px; display:grid; place-items:center; background:rgba(15,23,42,0.92); color:#e2e8f0; border:1px solid rgba(148,163,184,0.28); font-weight:950; font-size:0.78rem;">VS</div>
        {team_panel(game.get("home_team", "Home"), home_abbrev, "Home", home_color, home_alt, home_text, home_glow, True)}
      </div>
      <div style="display:flex; justify-content:space-between; gap:0.75rem; color:#cbd5e1; font-size:0.88rem; flex-wrap:wrap;">
        <span>{html.escape(time_label)} | {html.escape(str(game.get("status", "")))}</span>
        <span>{html.escape(str(game.get("venue", "")))}</span>
      </div>
    </div>
    """)

def football_metric_profile(value: Any, benchmark: dict | None, higher_is_better: bool) -> str:
    """Classify one metric against its own league distribution."""
    numeric = safe_float(value)
    lower = safe_float((benchmark or {}).get("lower"))
    upper = safe_float((benchmark or {}).get("upper"))
    sample = safe_int((benchmark or {}).get("sample"))
    if pd.isna(numeric) or pd.isna(lower) or pd.isna(upper) or sample < 6 or upper <= lower:
        return "neutral"
    if higher_is_better:
        if numeric >= upper:
            return "good"
        if numeric <= lower:
            return "bad"
    else:
        if numeric <= lower:
            return "good"
        if numeric >= upper:
            return "bad"
    return "neutral"

def football_matchup_cell_states(
    offense_value: Any,
    defense_value: Any,
    offense_benchmark: dict | None,
    defense_benchmark: dict | None,
    *,
    offense_higher_is_better: bool = True,
    defense_higher_is_better: bool = False,
) -> tuple[str, str]:
    """Highlight only a league-relative strength that meets an opposing weakness."""
    offense_profile = football_metric_profile(offense_value, offense_benchmark, offense_higher_is_better)
    defense_profile = football_metric_profile(defense_value, defense_benchmark, defense_higher_is_better)
    if offense_profile == "good" and defense_profile == "bad":
        return "good", "bad"
    if offense_profile == "bad" and defense_profile == "good":
        return "bad", "good"
    return "neutral", "neutral"

def football_matchup_benchmarks(logs: pd.DataFrame, recent_games: int = 3) -> dict[str, dict]:
    """Build league-specific top/bottom-third cutoffs for matchup-board metrics."""
    if logs is None or logs.empty or "team" not in logs.columns:
        return {}
    fields = {
        "third_down_pct",
        "third_down_pct_allowed",
        "goal_to_go_td_pct",
        "goal_to_go_stop_pct",
        "short_yardage_pct",
        "short_yardage_stop_pct",
        "rush_stuffed_rate",
        "rush_stuff_rate",
        "total_yards",
        "yards_allowed",
        "passing_yards",
        "passing_yards_allowed",
        "rushing_yards",
        "rushing_yards_allowed",
        "yards_per_play",
        "yards_per_play_allowed",
        "points",
        "points_allowed",
        "sack_rate_allowed",
        "sack_rate_made",
        "turnovers",
        "takeaways",
    }
    values_by_field = {field: [] for field in fields}
    for team_name in sorted(logs["team"].dropna().astype(str).unique()):
        recent = ncaaf_team_snapshot(logs, team_name, recent_games).get("recent", {}) or {}
        for field in fields:
            value = safe_float(recent.get(field))
            if pd.notna(value):
                values_by_field[field].append(value)
    benchmarks = {}
    for field, values in values_by_field.items():
        if len(values) < 6:
            continue
        series = pd.Series(values, dtype="float64")
        benchmarks[field] = {
            "lower": float(series.quantile(1 / 3)),
            "upper": float(series.quantile(2 / 3)),
            "median": float(series.median()),
            "sample": len(values),
        }
    return benchmarks

def render_football_matchup_edge_board(
    away_snap: dict,
    home_snap: dict,
    away_color: str = "#38bdf8",
    home_color: str = "#f59e0b",
    recent_games: int = 3,
    benchmarks: dict[str, dict] | None = None,
) -> str:
    """Render a mirrored offense-vs-defense board with matchup-relative outlines."""
    away_recent = (away_snap or {}).get("recent", {}) or {}
    home_recent = (home_snap or {}).get("recent", {}) or {}
    away_color = ncaaf_clean_hex_color(away_color, "#38bdf8")
    home_color = ncaaf_clean_hex_color(home_color, "#f59e0b")

    def value_label(value: Any, kind: str) -> str:
        numeric = safe_float(value)
        if pd.isna(numeric):
            return "n/a"
        if kind == "rate":
            return f"{numeric * 100:.1f}%"
        if kind == "yards":
            return f"{numeric:.0f}"
        return f"{numeric:.1f}"

    def stat_cell(value: Any, kind: str, state: str, detail: str) -> str:
        palette = {
            "good": ("#22c55e", "rgba(34,197,94,0.12)", "Matchup edge"),
            "bad": ("#ef4444", "rgba(239,68,68,0.12)", "Opponent can exploit this"),
            "neutral": ("#475569", "rgba(51,65,85,0.22)", "Insufficient data"),
        }
        border, background, title = palette.get(state, palette["neutral"])
        return f"""
        <div style="display:flex; justify-content:center; min-width:0;">
          <div title="{html.escape(title)}" style="min-width:4.75rem; padding:0.38rem 0.5rem; border:2px solid {border}; border-radius:5px; background:{background}; box-shadow:0 0 0 1px rgba(2,6,23,0.85), 0 0 14px {background}; text-align:center;">
            <div style="color:#f8fafc; font-size:1rem; line-height:1.05; font-weight:950; font-variant-numeric:tabular-nums;">{html.escape(value_label(value, kind))}</div>
            <div style="color:#94a3b8; font-size:0.58rem; line-height:1.15; font-weight:850; letter-spacing:0.04em; text-transform:uppercase; margin-top:0.18rem; white-space:nowrap;">{html.escape(detail)}</div>
          </div>
        </div>
        """

    def attempt_detail(label: str, made: Any, attempts: Any, invert: bool = False) -> str:
        made_value = safe_float(made)
        attempt_value = safe_float(attempts)
        if pd.isna(made_value) or pd.isna(attempt_value) or attempt_value <= 0:
            return label
        display_made = max(0.0, attempt_value - made_value) if invert else made_value
        return f"{label} {display_made:.0f}/{attempt_value:.0f}"

    benchmarks = benchmarks or {}
    rows = [
        {
            "label": "3rd down",
            "kind": "rate",
            "off_field": "third_down_pct",
            "def_field": "third_down_pct_allowed",
            "away_off": away_recent.get("third_down_pct"),
            "home_def": home_recent.get("third_down_pct_allowed"),
            "away_def": away_recent.get("third_down_pct_allowed"),
            "home_off": home_recent.get("third_down_pct"),
            "off_detail": "converted",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Goal-to-go TD",
            "kind": "rate",
            "off_field": "goal_to_go_td_pct",
            "def_field": "goal_to_go_stop_pct",
            "away_off": away_recent.get("goal_to_go_td_pct"),
            "home_def": home_recent.get("goal_to_go_stop_pct"),
            "away_def": away_recent.get("goal_to_go_stop_pct"),
            "home_off": home_recent.get("goal_to_go_td_pct"),
            "off_detail": attempt_detail(
                "TD", away_recent.get("goal_to_go_td"), away_recent.get("goal_to_go_trips")
            ),
            "def_detail": attempt_detail(
                "stopped",
                home_recent.get("goal_to_go_td_allowed"),
                home_recent.get("goal_to_go_trips_allowed"),
                invert=True,
            ),
            "away_def_detail": attempt_detail(
                "stopped",
                away_recent.get("goal_to_go_td_allowed"),
                away_recent.get("goal_to_go_trips_allowed"),
                invert=True,
            ),
            "home_off_detail": attempt_detail(
                "TD", home_recent.get("goal_to_go_td"), home_recent.get("goal_to_go_trips")
            ),
            "offense_higher": True,
            "defense_higher": True,
        },
        {
            "label": "3rd/4th & 1-2",
            "kind": "rate",
            "off_field": "short_yardage_pct",
            "def_field": "short_yardage_stop_pct",
            "away_off": away_recent.get("short_yardage_pct"),
            "home_def": home_recent.get("short_yardage_stop_pct"),
            "away_def": away_recent.get("short_yardage_stop_pct"),
            "home_off": home_recent.get("short_yardage_pct"),
            "off_detail": attempt_detail(
                "converted", away_recent.get("short_yardage_conv"), away_recent.get("short_yardage_att")
            ),
            "def_detail": attempt_detail(
                "stopped",
                home_recent.get("short_yardage_conv_allowed"),
                home_recent.get("short_yardage_att_allowed"),
                invert=True,
            ),
            "away_def_detail": attempt_detail(
                "stopped",
                away_recent.get("short_yardage_conv_allowed"),
                away_recent.get("short_yardage_att_allowed"),
                invert=True,
            ),
            "home_off_detail": attempt_detail(
                "converted", home_recent.get("short_yardage_conv"), home_recent.get("short_yardage_att")
            ),
            "offense_higher": True,
            "defense_higher": True,
        },
        {
            "label": "Rush stuff rate",
            "kind": "rate",
            "off_field": "rush_stuffed_rate",
            "def_field": "rush_stuff_rate",
            "away_off": away_recent.get("rush_stuffed_rate"),
            "home_def": home_recent.get("rush_stuff_rate"),
            "away_def": away_recent.get("rush_stuff_rate"),
            "home_off": home_recent.get("rush_stuffed_rate"),
            "off_detail": attempt_detail(
                "stuffed", away_recent.get("rush_stuffed"), away_recent.get("rush_attempts_charted")
            ),
            "def_detail": attempt_detail(
                "stuffs", home_recent.get("rush_stuffs"), home_recent.get("rush_stuff_opportunities")
            ),
            "away_def_detail": attempt_detail(
                "stuffs", away_recent.get("rush_stuffs"), away_recent.get("rush_stuff_opportunities")
            ),
            "home_off_detail": attempt_detail(
                "stuffed", home_recent.get("rush_stuffed"), home_recent.get("rush_attempts_charted")
            ),
            "offense_higher": False,
            "defense_higher": True,
        },
        {
            "label": "Total YPG",
            "kind": "yards",
            "off_field": "total_yards",
            "def_field": "yards_allowed",
            "away_off": away_recent.get("total_yards"),
            "home_def": home_recent.get("yards_allowed"),
            "away_def": away_recent.get("yards_allowed"),
            "home_off": home_recent.get("total_yards"),
            "off_detail": "offense",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Pass YPG",
            "kind": "yards",
            "off_field": "passing_yards",
            "def_field": "passing_yards_allowed",
            "away_off": away_recent.get("passing_yards"),
            "home_def": home_recent.get("passing_yards_allowed"),
            "away_def": away_recent.get("passing_yards_allowed"),
            "home_off": home_recent.get("passing_yards"),
            "off_detail": "offense",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Rush YPG",
            "kind": "yards",
            "off_field": "rushing_yards",
            "def_field": "rushing_yards_allowed",
            "away_off": away_recent.get("rushing_yards"),
            "home_def": home_recent.get("rushing_yards_allowed"),
            "away_def": away_recent.get("rushing_yards_allowed"),
            "home_off": home_recent.get("rushing_yards"),
            "off_detail": "offense",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Yards / play",
            "kind": "number",
            "off_field": "yards_per_play",
            "def_field": "yards_per_play_allowed",
            "away_off": away_recent.get("yards_per_play"),
            "home_def": home_recent.get("yards_per_play_allowed"),
            "away_def": away_recent.get("yards_per_play_allowed"),
            "home_off": home_recent.get("yards_per_play"),
            "off_detail": "offense",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Points / game",
            "kind": "number",
            "off_field": "points",
            "def_field": "points_allowed",
            "away_off": away_recent.get("points"),
            "home_def": home_recent.get("points_allowed"),
            "away_def": away_recent.get("points_allowed"),
            "home_off": home_recent.get("points"),
            "off_detail": "scored",
            "def_detail": "allowed",
            "offense_higher": True,
            "defense_higher": False,
        },
        {
            "label": "Pressure rate",
            "kind": "rate",
            "off_field": "sack_rate_allowed",
            "def_field": "sack_rate_made",
            "away_off": away_recent.get("sack_rate_allowed"),
            "home_def": home_recent.get("sack_rate_made"),
            "away_def": away_recent.get("sack_rate_made"),
            "home_off": home_recent.get("sack_rate_allowed"),
            "off_detail": "sacks allowed",
            "def_detail": "sacks made",
            "offense_higher": False,
            "defense_higher": True,
        },
        {
            "label": "Turnovers",
            "kind": "number",
            "off_field": "turnovers",
            "def_field": "takeaways",
            "away_off": away_recent.get("turnovers"),
            "home_def": home_recent.get("takeaways"),
            "away_def": away_recent.get("takeaways"),
            "home_off": home_recent.get("turnovers"),
            "off_detail": "given away",
            "def_detail": "takeaways",
            "offense_higher": False,
            "defense_higher": True,
        },
    ]

    row_html = []
    for row in rows:
        away_off_state, home_def_state = football_matchup_cell_states(
            row["away_off"],
            row["home_def"],
            benchmarks.get(row["off_field"]),
            benchmarks.get(row["def_field"]),
            offense_higher_is_better=bool(row["offense_higher"]),
            defense_higher_is_better=bool(row["defense_higher"]),
        )
        home_off_state, away_def_state = football_matchup_cell_states(
            row["home_off"],
            row["away_def"],
            benchmarks.get(row["off_field"]),
            benchmarks.get(row["def_field"]),
            offense_higher_is_better=bool(row["offense_higher"]),
            defense_higher_is_better=bool(row["defense_higher"]),
        )
        row_html.append(
            f"""
            <div style="display:grid; grid-template-columns:minmax(5rem,1fr) minmax(5rem,1fr) minmax(7.5rem,0.82fr) minmax(5rem,1fr) minmax(5rem,1fr); gap:0.45rem; align-items:center; padding:0.55rem 0.45rem; border-top:1px solid rgba(148,163,184,0.13);">
              {stat_cell(row['away_off'], row['kind'], away_off_state, row['off_detail'])}
              {stat_cell(row['home_def'], row['kind'], home_def_state, row['def_detail'])}
              <div style="color:#e2e8f0; font-size:0.78rem; font-weight:950; text-align:center; text-transform:uppercase; letter-spacing:0.045em;">{html.escape(row['label'])}</div>
              {stat_cell(row['away_def'], row['kind'], away_def_state, row.get('away_def_detail', row['def_detail']))}
              {stat_cell(row['home_off'], row['kind'], home_off_state, row.get('home_off_detail', row['off_detail']))}
            </div>
            """
        )

    away_team = str((away_snap or {}).get("team") or "Away")
    home_team = str((home_snap or {}).get("team") or "Home")
    away_record = str((away_snap or {}).get("record") or "0-0")
    home_record = str((home_snap or {}).get("record") or "0-0")
    return compact_html(f"""
    <div class="dashboard-card" style="padding:0; margin:-0.15rem 0 0.9rem; overflow:hidden; border-color:rgba(148,163,184,0.22); background:linear-gradient(90deg, {html.escape(hex_to_rgba(away_color, 0.08))} 0%, rgba(2,6,23,0.97) 45%, rgba(2,6,23,0.97) 55%, {html.escape(hex_to_rgba(home_color, 0.08))} 100%);">
      <div style="padding:0.72rem 0.85rem 0.62rem; display:flex; align-items:center; justify-content:space-between; gap:0.75rem; flex-wrap:wrap;">
        <div>
          <div style="color:#f8fafc; font-size:0.95rem; font-weight:950;">Strength vs weakness board</div>
          <div style="color:#94a3b8; font-size:0.7rem; margin-top:0.1rem;">Last {safe_int(recent_games)} games · outlines appear only when a league top-third strength meets a bottom-third weakness</div>
        </div>
        <div style="display:flex; gap:0.7rem; align-items:center; color:#cbd5e1; font-size:0.7rem; font-weight:850;">
          <span><span style="display:inline-block; width:0.68rem; height:0.68rem; border:2px solid #22c55e; border-radius:2px; vertical-align:-0.08rem; margin-right:0.25rem;"></span>edge</span>
          <span><span style="display:inline-block; width:0.68rem; height:0.68rem; border:2px solid #ef4444; border-radius:2px; vertical-align:-0.08rem; margin-right:0.25rem;"></span>exposed</span>
          <span><span style="display:inline-block; width:0.68rem; height:0.68rem; border:2px solid #475569; border-radius:2px; vertical-align:-0.08rem; margin-right:0.25rem;"></span>n/a</span>
        </div>
      </div>
      <div style="overflow-x:auto; padding:0 0.35rem 0.45rem;">
        <div style="min-width:690px;">
          <div style="display:grid; grid-template-columns:minmax(5rem,1fr) minmax(5rem,1fr) minmax(7.5rem,0.82fr) minmax(5rem,1fr) minmax(5rem,1fr); gap:0.45rem; align-items:end; padding:0.54rem 0.45rem; background:rgba(15,23,42,0.72); border-top:1px solid rgba(148,163,184,0.13);">
            <div style="text-align:center;"><div style="color:{html.escape(away_color)}; font-size:0.72rem; font-weight:950;">{html.escape(away_team)}</div><div style="color:#94a3b8; font-size:0.6rem; text-transform:uppercase;">Offense · {html.escape(away_record)}</div></div>
            <div style="text-align:center;"><div style="color:{html.escape(home_color)}; font-size:0.72rem; font-weight:950;">{html.escape(home_team)}</div><div style="color:#94a3b8; font-size:0.6rem; text-transform:uppercase;">Defense</div></div>
            <div style="color:#64748b; font-size:0.62rem; font-weight:950; text-align:center; text-transform:uppercase; letter-spacing:0.08em;">Matchup</div>
            <div style="text-align:center;"><div style="color:{html.escape(away_color)}; font-size:0.72rem; font-weight:950;">{html.escape(away_team)}</div><div style="color:#94a3b8; font-size:0.6rem; text-transform:uppercase;">Defense</div></div>
            <div style="text-align:center;"><div style="color:{html.escape(home_color)}; font-size:0.72rem; font-weight:950;">{html.escape(home_team)}</div><div style="color:#94a3b8; font-size:0.6rem; text-transform:uppercase;">Offense · {html.escape(home_record)}</div></div>
          </div>
          {''.join(row_html)}
        </div>
      </div>
    </div>
    """)

def render_ncaaf_familiarity_items(flags: pd.DataFrame, team_color: str) -> str:
    flags = prepare_ncaaf_familiarity_flags(flags)
    if flags.empty:
        return '<div style="color:#64748b; font-size:0.76rem; margin-top:0.42rem;">No personnel context flags saved.</div>'
    items = []
    for _, row in flags.head(4).iterrows():
        person = str(row.get("person") or "Context")
        role = str(row.get("role") or "").strip()
        connection = str(row.get("connection_type") or "familiarity").strip()
        impact = str(row.get("impact") or "watch").strip()
        confidence = str(row.get("confidence") or "").strip()
        note = str(row.get("note") or "").strip()
        source_url = str(row.get("source_url") or "").strip()
        label_bits = [person]
        if role:
            label_bits.append(role)
        source_html = f' <a href="{html.escape(source_url)}" target="_blank" style="color:#93c5fd; text-decoration:none;">source</a>' if source_url else ""
        items.append(
            f"""
            <div style="margin-top:0.42rem; padding:0.46rem 0.5rem; border-radius:8px; border:1px solid {html.escape(hex_to_rgba(team_color, 0.22))}; background:rgba(2,6,23,0.34);">
              <div style="display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start;">
                <div style="color:#f8fafc; font-size:0.82rem; font-weight:950;">{html.escape(' | '.join(label_bits))}</div>
                <div style="color:#a7f3d0; font-size:0.68rem; font-weight:950; text-transform:uppercase; letter-spacing:0.08em;">{html.escape(impact)}</div>
              </div>
              <div style="color:#cbd5e1; font-size:0.74rem; line-height:1.32; margin-top:0.12rem;">{html.escape(connection)}{f' | {html.escape(confidence)}' if confidence else ''}{source_html}</div>
              <div style="color:#94a3b8; font-size:0.74rem; line-height:1.32; margin-top:0.12rem;">{html.escape(note)}</div>
            </div>
            """
        )
    extra_count = max(0, len(flags) - 4)
    if extra_count:
        items.append(f'<div style="color:#94a3b8; font-size:0.72rem; margin-top:0.34rem;">+{extra_count} more context flags saved.</div>')
    return "".join(items)

def render_ncaaf_injury_items(context: dict, team_color: str) -> str:
    if not context.get("available"):
        return (
            '<div style="margin-top:0.42rem; padding:0.52rem; border-radius:8px; '
            'border:1px solid rgba(251,191,36,0.30); background:rgba(120,53,15,0.12); '
            'color:#fbbf24; font-size:0.76rem; line-height:1.35;">'
            'Availability unverified. Do not read this as a healthy roster; update the injury report before betting.</div>'
        )
    rows = prepare_ncaaf_injury_report(context.get("rows"))
    freshness = str(context.get("freshness") or "Unknown")
    updated_at = context.get("updated_at")
    if updated_at is not None and pd.notna(updated_at):
        updated_label = pd.Timestamp(updated_at).tz_convert("Europe/Stockholm").strftime("%d %b %H:%M")
    else:
        updated_label = "unknown"
    penalty = safe_float(context.get("model_penalty"))
    penalty_text = f"Model −{ncaaf_spread_value_text(penalty)} pts" if pd.notna(penalty) and penalty > 0 else "No automatic adjustment"
    stale_status_count = safe_int(context.get("stale_status_count"))
    stale_note = (
        " Report is stale, so its point adjustment is disabled."
        if context.get("stale")
        else " Only verified roles and production move the model."
    )
    old_status_note = (
        f" {stale_status_count} old game-specific status{'es' if stale_status_count != 1 else ''} "
        "were ignored and do not move the model."
        if stale_status_count
        else ""
    )
    header = f"""
    <div style="margin-top:0.42rem; padding:0.5rem; border-radius:8px; border:1px solid {html.escape(hex_to_rgba(team_color, 0.24))}; background:rgba(2,6,23,0.34);">
      <div style="display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start;">
        <div style="color:#f8fafc; font-size:0.82rem; font-weight:950;">{html.escape(str(context.get('label') or 'Availability'))}</div>
        <div style="color:{'#fb7185' if context.get('critical_qb') else '#fbbf24' if len(rows) else '#a7f3d0'}; font-size:0.68rem; font-weight:950; text-transform:uppercase; letter-spacing:0.06em;">{html.escape(penalty_text)}</div>
      </div>
      <div style="color:#94a3b8; font-size:0.71rem; line-height:1.32; margin-top:0.12rem;">{html.escape(freshness)} · refreshed {html.escape(updated_label)}.{html.escape(stale_note)}{html.escape(old_status_note)}</div>
    </div>
    """
    if rows.empty:
        if stale_status_count:
            return header + (
                '<div style="color:#fbbf24; font-size:0.75rem; margin-top:0.34rem;">'
                'No current game designation is confirmed. Old opponent-specific statuses were ignored; re-check the final availability report.</div>'
            )
        return header + (
            '<div style="color:#a7f3d0; font-size:0.75rem; margin-top:0.34rem;">'
            'No injuries are listed for this team in the current source report. Re-check late scratches.</div>'
        )
    items = [header]
    visible_limit = 6
    for _, row in rows.head(visible_limit).iterrows():
        status = str(row.get("status") or "Listed")
        status_factor = ncaaf_injury_status_factor(status)
        status_color = "#fb7185" if status_factor >= 0.70 else ("#fbbf24" if status_factor > 0 else "#cbd5e1")
        role = str(row.get("role") or "Role unavailable")
        role_basis = str(row.get("role_basis") or "")
        production = str(row.get("production") or "")
        detail = " · ".join(filter(None, [str(row.get("injury") or ""), str(row.get("news_date") or "")]))
        source_url = str(row.get("source_url") or "")
        team_url = str(row.get("team_url") or "")
        source_html = f' <a href="{html.escape(source_url)}" target="_blank" style="color:#93c5fd; text-decoration:none;">injury source</a>' if source_url else ""
        role_source_html = f' · <a href="{html.escape(team_url)}" target="_blank" style="color:#93c5fd; text-decoration:none;">role source</a>' if team_url else ""
        impact_points = safe_float(row.get("impact_points"))
        ol_spread_value = ncaaf_ol_player_spread_value(row)
        if pd.notna(impact_points) and impact_points > 0:
            verified_badge = f"Spread −{ncaaf_spread_value_text(impact_points)} pts"
        elif ol_spread_value > 0:
            verified_badge = f"Protection −{ncaaf_spread_value_text(ol_spread_value)} pts"
        else:
            verified_badge = "No quantified spread value"
        snap_week = safe_int(row.get("snap_week"))
        snap_games = safe_int(row.get("snap_games"))
        snap_parts = []
        for unit_label, unit_key in [("OFF", "offense"), ("DEF", "defense"), ("ST", "st")]:
            snaps = safe_float(row.get(f"{unit_key}_snaps"))
            pct = safe_float(row.get(f"{unit_key}_pct"))
            recent_pct = safe_float(row.get(f"recent_{unit_key}_pct"))
            if (pd.notna(snaps) and snaps > 0) or (pd.notna(pct) and pct > 0):
                latest_usage = f"{safe_int(snaps)} / {pct:.0%}" if pd.notna(pct) else f"{safe_int(snaps)}"
                recent_usage = f" · L{snap_games} {recent_pct:.0%}" if snap_games and pd.notna(recent_pct) else ""
                snap_parts.append(f"{unit_label} {latest_usage}{recent_usage}")
        snap_source = str(row.get("snap_source_url") or "")
        snap_source_html = (
            f' · <a href="{html.escape(snap_source)}" target="_blank" style="color:#93c5fd; text-decoration:none;">snap source</a>'
            if snap_source
            else ""
        )
        snap_html = (
            f'<div style="color:#a7f3d0; font-size:0.71rem; line-height:1.3; margin-top:0.1rem;">'
            f'Last active Week {snap_week}: {html.escape(" · ".join(snap_parts))}{snap_source_html}</div>'
            if snap_week and snap_parts
            else ""
        )
        items.append(
            f"""
            <div style="margin-top:0.36rem; padding:0.46rem 0.5rem; border-radius:8px; border:1px solid {html.escape(hex_to_rgba(team_color, 0.18))}; background:rgba(2,6,23,0.25);">
              <div style="display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start;">
                <div style="color:#f8fafc; font-size:0.8rem; font-weight:950;">{html.escape(str(row.get('player') or 'Player'))} · {html.escape(str(row.get('position') or ''))}</div>
                <div style="color:{status_color}; font-size:0.68rem; font-weight:950; text-transform:uppercase;">{html.escape(status)} · {html.escape(verified_badge)}</div>
              </div>
              <div style="color:#cbd5e1; font-size:0.73rem; line-height:1.3; margin-top:0.12rem;">{html.escape(role)}{f' · {html.escape(production)}' if production else ''}</div>
              <div style="color:#64748b; font-size:0.69rem; line-height:1.3; margin-top:0.08rem;">{html.escape(role_basis)}</div>
              {snap_html}
              <div style="color:#94a3b8; font-size:0.71rem; line-height:1.3; margin-top:0.1rem;">{html.escape(detail)}{source_html}{role_source_html}</div>
            </div>
            """
        )
    extra_rows = rows.iloc[visible_limit:]
    extra_count = len(extra_rows)
    if extra_count:
        extra_names = ", ".join(str(value) for value in extra_rows["player"].tolist())
        items.append(
            f'<div style="color:#94a3b8; font-size:0.72rem; line-height:1.35; margin-top:0.3rem;">'
            f'+{extra_count} more: {html.escape(extra_names)}.</div>'
        )
    return "".join(items)

def render_ncaaf_team_signal_card(
    team_snap: dict,
    opp_snap: dict,
    team_color: str,
    is_home: bool,
    market: dict | None = None,
    neutral_site: bool = False,
    familiarity_flags: pd.DataFrame | None = None,
    injury_context: dict | None = None,
    opponent_injury_context: dict | None = None,
    ol_context: dict | None = None,
    opponent_ol_context: dict | None = None,
    alternate_team_snap: dict | None = None,
    alternate_opp_snap: dict | None = None,
    current_window: int = 0,
    alternate_window: int = 0,
) -> str:
    signal = ncaaf_side_signal(
        team_snap,
        opp_snap,
        is_home,
        market,
        neutral_site,
        injury_context,
        opponent_injury_context,
        ol_context,
        opponent_ol_context,
    )
    alternate_signal = None
    if alternate_team_snap and alternate_opp_snap and current_window and alternate_window:
        alternate_signal = ncaaf_side_signal(
            alternate_team_snap,
            alternate_opp_snap,
            is_home,
            market,
            neutral_site,
            injury_context,
            opponent_injury_context,
            ol_context,
            opponent_ol_context,
        )
    window_stability = football_window_stability(
        signal,
        alternate_signal,
        current_window,
        alternate_window,
    )
    displayed_label = str(window_stability.get("override_label") or signal["label"])
    team_color = ncaaf_clean_hex_color(team_color, "#2dd4bf")
    color = (
        "#2dd4bf"
        if displayed_label in {"Lay spread", "Take points", "Cover lean", "Points lean"}
        else ("#fbbf24" if displayed_label in {"Line looks fair", "Spread pass", "Window conflict — pass"} else "#fb7185")
    )
    why = "; ".join(signal.get("reasons", []) or ["needs more support"])
    risk = "; ".join(signal.get("risks", []) or [])
    risk_html = f'<div style="color:#fb7185; margin-top:0.18rem;">Risk: {html.escape(risk)}</div>' if risk else ""
    context_html = render_ncaaf_familiarity_items(familiarity_flags, team_color)
    injury_html = render_ncaaf_injury_items(injury_context or {}, team_color)
    pressure = signal.get("pressure_matchup") or {}
    team_pressure_rate = safe_float(pressure.get("team_risk"))
    opponent_pressure_rate = safe_float(pressure.get("opponent_risk"))
    pressure_text = (
        f"Projected sack exposure {ncaaf_format_rate(team_pressure_rate)} vs opponent {ncaaf_format_rate(opponent_pressure_rate)}"
        if pressure.get("available")
        else "Sack-rate matchup unavailable until football logs are refreshed"
    )
    ol_status = str((ol_context or {}).get("status") or "No OL continuity flag")
    ol_note = str((ol_context or {}).get("note") or "")
    ol_model_penalty = safe_float((ol_context or {}).get("model_penalty"))
    ol_value_text = f" · spread −{ncaaf_spread_value_text(ol_model_penalty)} pts" if pd.notna(ol_model_penalty) and ol_model_penalty > 0 else ""
    ol_source = str((ol_context or {}).get("source_url") or "")
    ol_source_html = (
        f' · <a href="{html.escape(ol_source)}" target="_blank" style="color:#93c5fd; text-decoration:none;">source</a>'
        if ol_source
        else ""
    )
    margin = safe_float(signal.get("model_margin"))
    if pd.isna(margin):
        margin_text = "Adjusted margin unavailable"
    elif margin >= 0:
        margin_text = f"Adjusted margin: {team_snap.get('team')} by {abs(margin):.1f}"
    else:
        margin_text = f"Adjusted margin: {opp_snap.get('team')} by {abs(margin):.1f}"
    edge = safe_float(signal.get("cover_edge"))
    edge_text = "" if pd.isna(edge) else f" | Cover cushion {edge:+.1f}"
    win_prob = safe_float(signal.get("win_prob"))
    win_prob_text = "n/a" if pd.isna(win_prob) else f"{win_prob * 100:.0f}%"
    closing_review = signal.get("market_phase") == "closing"
    decision_label = "Closing-line review" if closing_review else "Side market decision"
    spread_label = "Closing spread" if closing_review else "Spread"
    market_source = str(signal.get("market_source") or "Market source unavailable")
    final_profile = signal.get("final_profile") or {}
    profile_tone = str(final_profile.get("tone") or "neutral")
    profile_color = {
        "good": "#22c55e",
        "bad": "#ef4444",
        "warning": "#fbbf24",
        "neutral": "#94a3b8",
    }.get(profile_tone, "#94a3b8")
    profile_adjustment = safe_float(final_profile.get("adjustment"))
    profile_adjustment_text = (
        f"{profile_adjustment:+.1f} pts"
        if pd.notna(profile_adjustment)
        else "no adjustment"
    )
    profile_pills = []
    for category in final_profile.get("categories", []) or []:
        state = str(category.get("state") or "unavailable")
        state_color = {
            "edge": "#22c55e",
            "risk": "#ef4444",
            "even": "#fbbf24",
            "unavailable": "#64748b",
        }.get(state, "#64748b")
        profile_pills.append(
            f'<span style="padding:0.22rem 0.42rem; border-radius:6px; '
            f'border:1px solid {state_color}; color:{state_color}; background:rgba(2,6,23,0.38); '
            f'font-size:0.69rem; font-weight:900;">{html.escape(str(category.get("detail") or category.get("label") or "n/a"))}</span>'
        )
    profile_pills_html = "".join(profile_pills)
    window_tone = str(window_stability.get("tone") or "neutral")
    window_color = {
        "good": "#22c55e",
        "bad": "#ef4444",
        "warning": "#fbbf24",
        "neutral": "#94a3b8",
    }.get(window_tone, "#94a3b8")
    window_check_html = (
        f'<div style="margin:0.42rem 0 0.2rem; padding:0.42rem 0.5rem; border-radius:8px; '
        f'background:rgba(2,6,23,0.28); border:1px solid {window_color};">'
        f'<div style="color:{window_color}; font-size:0.73rem; font-weight:950;">'
        f'{html.escape(str(window_stability.get("label") or "Window check unavailable"))}</div>'
        f'<div style="color:#cbd5e1; font-size:0.7rem; line-height:1.3; margin-top:0.1rem;">'
        f'{html.escape(str(window_stability.get("detail") or ""))}</div></div>'
    )
    return compact_html(f"""
    <div class="quick-tile" style="margin-top:0.62rem; margin-bottom:0.9rem; border-color:{html.escape(hex_to_rgba(team_color, 0.32))}; box-shadow:inset 4px 0 0 {html.escape(team_color)};">
      <div class="quick-tile__label">{html.escape(decision_label)}</div>
      <div class="quick-tile__value" style="color:{color};">{html.escape(displayed_label)}</div>
      <div style="display:flex; gap:0.38rem; flex-wrap:wrap; margin:0.34rem 0 0.42rem;">
        <span style="padding:0.22rem 0.48rem; border-radius:999px; background:rgba(15,23,42,0.78); border:1px solid rgba(148,163,184,0.25); color:#f8fafc; font-size:0.74rem; font-weight:900;">{html.escape(spread_label)} {html.escape(signal['spread_display'])}</span>
        <span style="padding:0.22rem 0.48rem; border-radius:999px; background:rgba(15,23,42,0.78); border:1px solid rgba(148,163,184,0.25); color:#f8fafc; font-size:0.74rem; font-weight:900;">ML {html.escape(signal['ml_display'])}</span>
        <span style="padding:0.22rem 0.48rem; border-radius:999px; background:rgba(15,23,42,0.78); border:1px solid rgba(148,163,184,0.25); color:#cbd5e1; font-size:0.74rem; font-weight:900;">Win {html.escape(win_prob_text)}</span>
        <span style="padding:0.22rem 0.48rem; border-radius:999px; background:rgba(15,23,42,0.78); border:1px solid rgba(148,163,184,0.25); color:#93c5fd; font-size:0.74rem; font-weight:900;">{html.escape(market_source)}</span>
      </div>
      {window_check_html}
      <div style="font-size:0.78rem; color:#a7f3d0; line-height:1.35; margin-bottom:0.18rem;">{html.escape(margin_text + edge_text)}</div>
      <div style="font-size:0.78rem; color:#93c5fd; line-height:1.35; margin-bottom:0.18rem;">{html.escape(signal['ml_call'])} | {html.escape(signal['volatility'])} volatility</div>
      <div style="font-size:0.82rem; color:#cbd5e1; line-height:1.35;">{html.escape(why)}{risk_html}</div>
      <div style="margin-top:0.58rem; color:#94a3b8; font-size:0.72rem; font-weight:950; letter-spacing:0.08em; text-transform:uppercase;">Pass protection</div>
      <div style="margin-top:0.24rem; padding:0.44rem 0.5rem; border-radius:8px; background:rgba(2,6,23,0.25); border:1px solid {html.escape(hex_to_rgba(team_color, 0.18))};">
        <div style="color:#f8fafc; font-size:0.76rem; font-weight:900;">{html.escape(pressure_text)}</div>
        <div style="color:#cbd5e1; font-size:0.72rem; line-height:1.3; margin-top:0.12rem;">{html.escape(ol_status + ol_value_text)}{f' · {html.escape(ol_note)}' if ol_note else ''}{ol_source_html}</div>
      </div>
      <div style="margin-top:0.58rem; color:#94a3b8; font-size:0.72rem; font-weight:950; letter-spacing:0.08em; text-transform:uppercase;">Injuries &amp; availability</div>
      {injury_html}
      <div style="margin-top:0.58rem; color:#94a3b8; font-size:0.72rem; font-weight:950; letter-spacing:0.08em; text-transform:uppercase;">Personnel context</div>
      {context_html}
      <div style="margin-top:0.72rem; padding-top:0.65rem; border-top:1px solid rgba(148,163,184,0.18);">
        <div style="display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start; flex-wrap:wrap;">
          <div>
            <div style="color:#94a3b8; font-size:0.7rem; font-weight:950; letter-spacing:0.08em; text-transform:uppercase;">Supporting team-trait profile</div>
            <div style="color:{profile_color}; font-size:0.94rem; font-weight:950; margin-top:0.16rem;">{html.escape(str(final_profile.get('label') or 'Profile unavailable'))}</div>
          </div>
          <div style="padding:0.22rem 0.46rem; border-radius:999px; border:1px solid {profile_color}; color:{profile_color}; font-size:0.7rem; font-weight:950;">{html.escape(profile_adjustment_text)}</div>
        </div>
        <div style="color:#cbd5e1; font-size:0.76rem; line-height:1.35; margin-top:0.24rem;">{html.escape(str(final_profile.get('summary') or 'No team-trait evidence.'))}</div>
        <div style="display:flex; gap:0.34rem; flex-wrap:wrap; margin-top:0.42rem;">{profile_pills_html}</div>
        <div style="color:#64748b; font-size:0.68rem; line-height:1.3; margin-top:0.34rem;">Supporting context only—not the bet recommendation. The side-market decision above also includes the line, efficiency, location, injuries and pass protection. Order: 3rd-down offense/defense → red-zone offense/defense → SOS.</div>
      </div>
    </div>
    """)

def render_ncaaf_matchup_card(
    game: dict,
    logs: pd.DataFrame,
    recent_games: int,
    sos_map: dict[str, dict] | None = None,
    league_label: str = "NCAAF",
) -> str:
    away_snap = ncaaf_team_snapshot(logs, game.get("away_team", ""), recent_games, sos_map)
    home_snap = ncaaf_team_snapshot(logs, game.get("home_team", ""), recent_games, sos_map)
    away_truth = ncaaf_truth_profile(away_snap, home_snap)
    home_truth = ncaaf_truth_profile(home_snap, away_snap)
    away_fit = ncaaf_matchup_fit_note(away_snap, home_snap)
    home_fit = ncaaf_matchup_fit_note(home_snap, away_snap)
    total = ncaaf_total_signal(away_snap, home_snap)
    away_color = ncaaf_clean_hex_color(game.get("away_color"), "#38bdf8")
    home_color = ncaaf_clean_hex_color(game.get("home_color"), "#f59e0b")

    def truth_html(truth: dict, fit: str, team_color: str, side_label: str) -> str:
        truth_details = " | ".join(truth.get("details", []) or [])
        truth_note = truth_details or truth.get("note", "")
        return f"""
        <div class="quick-tile" style="border-color:{html.escape(hex_to_rgba(team_color, 0.30))}; box-shadow:inset 4px 0 0 {html.escape(team_color)};">
          <div class="quick-tile__label">{html.escape(side_label)}</div>
          <div class="quick-tile__value">{html.escape(str(truth.get("label", "n/a")))}</div>
          <div style="font-size:0.78rem; color:#cbd5e1; line-height:1.35;">{html.escape(str(truth_note))}</div>
          <div style="font-size:0.76rem; color:#a7f3d0; line-height:1.35; margin-top:0.22rem;">Fit: {html.escape(str(fit))}</div>
        </div>
        """

    return compact_html(f"""
    <div class="dashboard-card" style="padding:1rem; margin-bottom:1rem; border-color:rgba(148,163,184,0.18);">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; margin-bottom:0.72rem; flex-wrap:wrap;">
        <div style="color:#f8fafc; font-size:1.02rem; font-weight:950;">Box score truth</div>
        <div style="color:#94a3b8; font-size:0.78rem; font-weight:900; text-transform:uppercase; letter-spacing:0.08em;">{html.escape(league_label)}</div>
      </div>
      <div class="quick-grid">
        {truth_html(away_truth, away_fit, away_color, "Away")}
        {truth_html(home_truth, home_fit, home_color, "Home")}
        <div class="quick-tile">
          <div class="quick-tile__label">Total read</div>
          <div class="quick-tile__value">{html.escape(total["label"])}</div>
          <div style="font-size:0.78rem; color:#cbd5e1; line-height:1.35;">{html.escape("; ".join(total.get("reasons", []) or ["mixed pace/efficiency"]))}</div>
        </div>
      </div>
    </div>
    """)

def ncaaf_shortlist_rows(
    games: list[dict],
    logs: pd.DataFrame,
    recent_games: int,
    sos_map: dict[str, dict] | None = None,
    injuries: pd.DataFrame | None = None,
    ol_flags: pd.DataFrame | None = None,
) -> list[dict]:
    rows = []
    for game in games:
        if str(game.get("state") or "").lower() != "pre":
            continue
        away_snap = ncaaf_team_snapshot(logs, game.get("away_team", ""), recent_games, sos_map)
        home_snap = ncaaf_team_snapshot(logs, game.get("home_team", ""), recent_games, sos_map)
        alternate_recent_games = 3 if recent_games == 5 else 5
        away_alternate_snap = ncaaf_team_snapshot(logs, game.get("away_team", ""), alternate_recent_games, sos_map)
        home_alternate_snap = ncaaf_team_snapshot(logs, game.get("home_team", ""), alternate_recent_games, sos_map)
        away_injuries = ncaaf_injury_context(injuries, game.get("away_team"))
        home_injuries = ncaaf_injury_context(injuries, game.get("home_team"))
        away_ol = ncaaf_ol_continuity_context(ol_flags, game.get("away_team"), away_injuries)
        home_ol = ncaaf_ol_continuity_context(ol_flags, game.get("home_team"), home_injuries)
        signal_pairs = [
            (
                ncaaf_side_signal(
                    away_snap,
                    home_snap,
                    False,
                    game.get("market"),
                    bool(game.get("neutral_site")),
                    away_injuries,
                    home_injuries,
                    away_ol,
                    home_ol,
                ),
                ncaaf_side_signal(
                    away_alternate_snap,
                    home_alternate_snap,
                    False,
                    game.get("market"),
                    bool(game.get("neutral_site")),
                    away_injuries,
                    home_injuries,
                    away_ol,
                    home_ol,
                ),
            ),
            (
                ncaaf_side_signal(
                    home_snap,
                    away_snap,
                    True,
                    game.get("market"),
                    bool(game.get("neutral_site")),
                    home_injuries,
                    away_injuries,
                    home_ol,
                    away_ol,
                ),
                ncaaf_side_signal(
                    home_alternate_snap,
                    away_alternate_snap,
                    True,
                    game.get("market"),
                    bool(game.get("neutral_site")),
                    home_injuries,
                    away_injuries,
                    home_ol,
                    away_ol,
                ),
            ),
        ]
        for signal, alternate_signal in signal_pairs:
            stability = football_window_stability(
                signal,
                alternate_signal,
                recent_games,
                alternate_recent_games,
            )
            if stability.get("state") == "conflict":
                continue
            if signal["label"] not in {"Lay spread", "Take points", "Cover lean", "Points lean"}:
                continue
            rows.append(
                {
                    "Game": f"{game.get('away_team')} @ {game.get('home_team')}",
                    "Bet": f"{signal['team']} {signal['spread_display']}",
                    "Call": signal["label"],
                    "Window Check": str(stability.get("label") or "n/a"),
                    "Alternate Edge": alternate_signal.get("cover_edge"),
                    "Adjusted Margin": signal["model_margin"],
                    "Cover Edge": signal["cover_edge"],
                    "Moneyline": f"{signal['ml_display']} | {signal['ml_call']}",
                    "SOS Rank": str((signal.get("team_sos") or {}).get("official_rank_display") or "n/a"),
                    "Availability": str((signal.get("team_availability") or {}).get("label") or "unverified"),
                    "Injury Adj": f"{safe_float(signal.get('availability_adjustment')):+.1f}",
                    "Protection Adj": f"{safe_float(signal.get('ol_adjustment')) + safe_float((signal.get('pressure_matchup') or {}).get('adjustment')):+.1f}",
                    "Trait Profile": str((signal.get("final_profile") or {}).get("label") or "n/a"),
                    "Trait Pillars": f"{safe_int((signal.get('final_profile') or {}).get('wins'))}/{safe_int((signal.get('final_profile') or {}).get('available'))}",
                    "Volatility": signal["volatility"],
                    "Why": "; ".join(signal.get("reasons", [])),
                    "Risk": "; ".join(signal.get("risks", [])),
                }
            )
    return sorted(rows, key=lambda row: safe_float(row.get("Cover Edge")), reverse=True)

def ncaaf_team_ranking_rows(
    logs: pd.DataFrame,
    recent_games: int,
    sos_map: dict[str, dict] | None = None,
) -> pd.DataFrame:
    if logs.empty:
        return pd.DataFrame()
    rows = []
    for team in sorted(logs["team"].dropna().unique()):
        snap = ncaaf_team_snapshot(logs, team, recent_games, sos_map)
        recent = snap["recent"]
        sos = snap.get("sos", {}) or {}
        offense_label, _ = ncaaf_profile_label(snap, "offense")
        defense_label, _ = ncaaf_profile_label(snap, "defense")
        play_profile = ncaaf_run_pass_profile(snap)
        truth = ncaaf_truth_profile(snap)
        power_score = (
            safe_float(recent.get("points")) * 0.16
            + safe_float(recent.get("yards_per_play")) * 1.45
            - safe_float(recent.get("points_allowed")) * 0.11
            - safe_float(recent.get("yards_per_play_allowed")) * 1.00
            - safe_float(recent.get("plays_per_point")) * 0.22
            + safe_float(recent.get("turnover_margin")) * 0.8
        )
        sos_adjustment = safe_float(sos.get("adjustment"))
        is_nfl_sos = str(sos.get("method") or "") == "nfl_official"
        sos_value = (
            f"{safe_float(sos.get('opponent_win_pct')):.3f}"
            if is_nfl_sos and pd.notna(safe_float(sos.get("opponent_win_pct")))
            else ncaaf_metric(sos.get("score"), 1)
        )
        opponent_record = (
            f"{safe_int(sos.get('opponent_wins'))}-{safe_int(sos.get('opponent_losses'))}-{safe_int(sos.get('opponent_ties'))}"
            if is_nfl_sos and sos.get("available")
            else (
                f"{safe_int(sos.get('opponent_wins'))}-{safe_int(sos.get('opponent_losses'))}"
                if sos.get("available")
                else "n/a"
            )
        )
        if pd.notna(power_score) and pd.notna(sos_adjustment):
            power_score += sos_adjustment * 0.55
        rows.append(
            {
                "Team": team,
                "Record": snap["record"],
                "Games": snap["games"],
                "Score": round(power_score, 2) if pd.notna(power_score) else float("nan"),
                "SOS Rank": sos.get("official_rank_display", "n/a"),
                "SOS Source": str(sos.get("rank_source") or "Unavailable"),
                "SOS Profile": sos.get("label", "SOS unavailable"),
                "SOS Value": sos_value,
                "ESPN FPI SOS": str(sos.get("espn_rank_display") or "n/a"),
                "SOS Adj": f"{sos_adjustment:+.1f}" if pd.notna(sos_adjustment) else "n/a",
                "Opponent Record": opponent_record,
                "SOS Conf": sos.get("confidence", "Low"),
                "Offense": offense_label,
                "Run/pass": play_profile.get("label"),
                "Truth": truth.get("label"),
                "Defense": defense_label,
                "PPG": ncaaf_metric(recent.get("points")),
                "Total Off Yds": ncaaf_metric(recent.get("total_yards"), 0),
                "Pass Yds": ncaaf_metric(recent.get("passing_yards"), 0),
                "Rush Yds": ncaaf_metric(recent.get("rushing_yards"), 0),
                "3rd Down": ncaaf_conversion_display(
                    recent.get("third_down_conv"), recent.get("third_down_att"), recent.get("third_down_pct")
                ),
                "Goal-to-go TD": ncaaf_conversion_display(
                    recent.get("goal_to_go_td"), recent.get("goal_to_go_trips"), recent.get("goal_to_go_td_pct")
                ),
                "Short-yard Conv": ncaaf_conversion_display(
                    recent.get("short_yardage_conv"), recent.get("short_yardage_att"), recent.get("short_yardage_pct")
                ),
                "Runs Stuffed": ncaaf_conversion_display(
                    recent.get("rush_stuffed"), recent.get("rush_attempts_charted"), recent.get("rush_stuffed_rate")
                ),
                "Sacks Allowed": ncaaf_metric(recent.get("sacks_allowed"), 0),
                "Sack Rate Allowed": ncaaf_format_rate(recent.get("sack_rate_allowed")),
                "Plays/Point": ncaaf_metric(recent.get("plays_per_point"), 2),
                "Pts Allowed": ncaaf_metric(recent.get("points_allowed")),
                "YPP": ncaaf_metric(recent.get("yards_per_play")),
                "Run Rate": ncaaf_format_rate(recent.get("run_rate")),
                "Pass Rate": ncaaf_format_rate(recent.get("pass_rate")),
                "Total Yds Allowed": ncaaf_metric(recent.get("yards_allowed"), 0),
                "Pass Yds Allowed": ncaaf_metric(recent.get("passing_yards_allowed"), 0),
                "Rush Yds Allowed": ncaaf_metric(recent.get("rushing_yards_allowed"), 0),
                "3rd Down Allowed": ncaaf_conversion_display(
                    recent.get("third_down_conv_allowed"),
                    recent.get("third_down_att_allowed"),
                    recent.get("third_down_pct_allowed"),
                ),
                "Goal-line Stops": ncaaf_conversion_display(
                    safe_float(recent.get("goal_to_go_trips_allowed")) - safe_float(recent.get("goal_to_go_td_allowed")),
                    recent.get("goal_to_go_trips_allowed"),
                    recent.get("goal_to_go_stop_pct"),
                ),
                "Short-yard Stops": ncaaf_conversion_display(
                    safe_float(recent.get("short_yardage_att_allowed")) - safe_float(recent.get("short_yardage_conv_allowed")),
                    recent.get("short_yardage_att_allowed"),
                    recent.get("short_yardage_stop_pct"),
                ),
                "Rush Stuff Rate": ncaaf_conversion_display(
                    recent.get("rush_stuffs"), recent.get("rush_stuff_opportunities"), recent.get("rush_stuff_rate")
                ),
                "Def Sacks": ncaaf_metric(recent.get("sacks_made"), 0),
                "Def Sack Rate": ncaaf_format_rate(recent.get("sack_rate_made")),
                "Def YPP": ncaaf_metric(recent.get("yards_per_play_allowed"), 2),
                "TO Margin": ncaaf_metric(recent.get("turnover_margin")),
            }
        )
    return pd.DataFrame(rows).sort_values("Score", ascending=False)

def football_game_display_label(game: dict) -> str:
    game_time = parse_timestamp_utc(game.get("date"))
    time_label = (
        game_time.tz_convert("Europe/Stockholm").strftime("%a %H:%M")
        if game_time is not None
        else "Time n/a"
    )
    return f"{game.get('away_team', 'Away')} @ {game.get('home_team', 'Home')} · {time_label}"

def render_nfl_decision_strip(
    away_signal: dict,
    home_signal: dict,
    away_stability: dict,
    home_stability: dict,
    total_signal: dict,
    away_color: str,
    home_color: str,
) -> str:
    def decision_card(signal: dict, stability: dict, team_color: str, side_label: str) -> str:
        team_color = ncaaf_clean_hex_color(team_color, "#38bdf8")
        signal_label = str(stability.get("override_label") or signal.get("label") or "Market unavailable")
        label_tone = (
            "#22c55e"
            if signal_label in {"Lay spread", "Take points", "Cover lean", "Points lean"}
            else ("#ef4444" if "conflict" in signal_label.lower() else "#fbbf24")
        )
        win_prob = safe_float(signal.get("win_prob"))
        win_text = f"{win_prob * 100:.0f}%" if pd.notna(win_prob) else "n/a"
        cover_edge = safe_float(signal.get("cover_edge"))
        edge_text = f"{cover_edge:+.1f}" if pd.notna(cover_edge) else "n/a"
        injury_context = signal.get("team_availability") or {}
        injury_label = str(injury_context.get("label") or "Availability unverified")
        return f"""
        <div class="quick-tile" style="border-color:{html.escape(hex_to_rgba(team_color, 0.34))}; box-shadow:inset 4px 0 0 {html.escape(team_color)}; min-height:154px;">
          <div style="display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start;">
            <div>
              <div class="quick-tile__label">{html.escape(side_label)}</div>
              <div class="quick-tile__value" style="font-size:1.02rem;">{html.escape(str(signal.get('team') or 'Team'))}</div>
            </div>
            <span style="padding:0.2rem 0.46rem; border-radius:999px; border:1px solid {label_tone}; color:{label_tone}; font-size:0.7rem; font-weight:950; white-space:nowrap;">{html.escape(signal_label)}</span>
          </div>
          <div style="display:flex; gap:0.34rem; flex-wrap:wrap; margin-top:0.52rem;">
            <span style="padding:0.2rem 0.42rem; border-radius:999px; background:rgba(15,23,42,0.72); border:1px solid rgba(148,163,184,0.22); color:#e2e8f0; font-size:0.69rem; font-weight:900;">{html.escape(str(signal.get('spread_display') or 'Spread n/a'))}</span>
            <span style="padding:0.2rem 0.42rem; border-radius:999px; background:rgba(15,23,42,0.72); border:1px solid rgba(148,163,184,0.22); color:#e2e8f0; font-size:0.69rem; font-weight:900;">ML {html.escape(str(signal.get('ml_display') or 'n/a'))}</span>
            <span style="padding:0.2rem 0.42rem; border-radius:999px; background:rgba(15,23,42,0.72); border:1px solid rgba(148,163,184,0.22); color:#e2e8f0; font-size:0.69rem; font-weight:900;">Win {html.escape(win_text)}</span>
            <span style="padding:0.2rem 0.42rem; border-radius:999px; background:rgba(15,23,42,0.72); border:1px solid rgba(148,163,184,0.22); color:#e2e8f0; font-size:0.69rem; font-weight:900;">Edge {html.escape(edge_text)}</span>
          </div>
          <div style="color:#cbd5e1; font-size:0.73rem; line-height:1.35; margin-top:0.46rem;">{html.escape(str(stability.get('label') or 'Window check unavailable'))}</div>
          <div style="color:#64748b; font-size:0.69rem; line-height:1.3; margin-top:0.2rem;">{html.escape(injury_label)}</div>
        </div>
        """

    total_label = str(total_signal.get("label") or "Mixed total")
    total_color = "#38bdf8" if total_label == "Over lean" else ("#a78bfa" if total_label == "Under lean" else "#fbbf24")
    total_reasons = "; ".join(total_signal.get("reasons", []) or ["mixed pace and efficiency signals"])
    total_card = f"""
    <div class="quick-tile" style="border-color:{total_color}; box-shadow:inset 4px 0 0 {total_color}; min-height:154px;">
      <div class="quick-tile__label">Game script</div>
      <div class="quick-tile__value" style="color:{total_color}; font-size:1.02rem;">{html.escape(total_label)}</div>
      <div style="color:#cbd5e1; font-size:0.75rem; line-height:1.4; margin-top:0.52rem;">{html.escape(total_reasons)}</div>
      <div style="color:#64748b; font-size:0.69rem; line-height:1.3; margin-top:0.42rem;">Compare the two team columns below for injuries, pass protection, SOS and the full model explanation.</div>
    </div>
    """
    return compact_html(f"""
    <div class="dashboard-card" style="padding:0.85rem; margin-bottom:0.85rem; border-color:rgba(56,189,248,0.24);">
      <div style="display:flex; justify-content:space-between; gap:0.75rem; align-items:center; flex-wrap:wrap; margin-bottom:0.62rem;">
        <div>
          <div style="color:#f8fafc; font-size:1rem; font-weight:950;">Market verdict first</div>
          <div style="color:#94a3b8; font-size:0.74rem;">Spread, moneyline and window stability before the deeper matchup evidence.</div>
        </div>
        <div style="color:#64748b; font-size:0.68rem; font-weight:900; text-transform:uppercase; letter-spacing:0.08em;">Verdict → matchup → detail</div>
      </div>
      <div class="quick-grid" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:0.55rem;">
        {decision_card(away_signal, away_stability, away_color, "Away side")}
        {decision_card(home_signal, home_stability, home_color, "Home side")}
        {total_card}
      </div>
    </div>
    """)

def render_football_game_section(
    game: dict,
    logs: pd.DataFrame,
    recent_games: int,
    sos_map: dict[str, dict],
    familiarity_flags: pd.DataFrame,
    injury_report: pd.DataFrame,
    ol_continuity_flags: pd.DataFrame,
    matchup_benchmarks: dict,
    show_details: bool,
    league_label: str,
) -> None:
    is_nfl = str(league_label).upper() == "NFL"
    away_snap = ncaaf_team_snapshot(logs, game.get("away_team", ""), recent_games, sos_map)
    home_snap = ncaaf_team_snapshot(logs, game.get("home_team", ""), recent_games, sos_map)
    alternate_recent_games = 3 if recent_games == 5 else 5
    away_alternate_snap = ncaaf_team_snapshot(logs, game.get("away_team", ""), alternate_recent_games, sos_map)
    home_alternate_snap = ncaaf_team_snapshot(logs, game.get("home_team", ""), alternate_recent_games, sos_map)
    game_familiarity = ncaaf_familiarity_for_game(familiarity_flags, game)
    away_familiarity = ncaaf_familiarity_for_team(game_familiarity, game.get("away_team"))
    home_familiarity = ncaaf_familiarity_for_team(game_familiarity, game.get("home_team"))
    away_injuries = ncaaf_injury_context(injury_report, game.get("away_team"))
    home_injuries = ncaaf_injury_context(injury_report, game.get("home_team"))
    away_ol = ncaaf_ol_continuity_context(ol_continuity_flags, game.get("away_team"), away_injuries)
    home_ol = ncaaf_ol_continuity_context(ol_continuity_flags, game.get("home_team"), home_injuries)

    st.markdown(render_ncaaf_matchup_header(game, logs, recent_games), unsafe_allow_html=True)

    if is_nfl:
        away_signal = ncaaf_side_signal(
            away_snap, home_snap, False, game.get("market"), bool(game.get("neutral_site")),
            away_injuries, home_injuries, away_ol, home_ol,
        )
        home_signal = ncaaf_side_signal(
            home_snap, away_snap, True, game.get("market"), bool(game.get("neutral_site")),
            home_injuries, away_injuries, home_ol, away_ol,
        )
        away_alternate_signal = ncaaf_side_signal(
            away_alternate_snap, home_alternate_snap, False, game.get("market"), bool(game.get("neutral_site")),
            away_injuries, home_injuries, away_ol, home_ol,
        )
        home_alternate_signal = ncaaf_side_signal(
            home_alternate_snap, away_alternate_snap, True, game.get("market"), bool(game.get("neutral_site")),
            home_injuries, away_injuries, home_ol, away_ol,
        )
        st.markdown(
            render_nfl_decision_strip(
                away_signal,
                home_signal,
                football_window_stability(away_signal, away_alternate_signal, recent_games, alternate_recent_games),
                football_window_stability(home_signal, home_alternate_signal, recent_games, alternate_recent_games),
                ncaaf_total_signal(away_snap, home_snap),
                game.get("away_color", "#38bdf8"),
                game.get("home_color", "#f59e0b"),
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        render_football_matchup_edge_board(
            away_snap,
            home_snap,
            game.get("away_color", "#38bdf8"),
            game.get("home_color", "#f59e0b"),
            recent_games,
            matchup_benchmarks,
        ),
        unsafe_allow_html=True,
    )

    def render_team_detail(
        team_snap: dict,
        opponent_snap: dict,
        team_color: str,
        alt_color: str,
        abbreviation: str,
        is_home: bool,
        team_familiarity: dict,
        team_injuries: dict,
        opponent_injuries: dict,
        team_ol: dict,
        opponent_ol: dict,
        alternate_team_snap: dict,
        alternate_opp_snap: dict,
    ) -> None:
        st.markdown(
            render_ncaaf_snapshot_card(team_snap, team_color, alt_color, abbreviation),
            unsafe_allow_html=True,
        )
        st.markdown(
            render_ncaaf_team_signal_card(
                team_snap,
                opponent_snap,
                team_color,
                is_home,
                market=game.get("market"),
                neutral_site=bool(game.get("neutral_site")),
                familiarity_flags=team_familiarity,
                injury_context=team_injuries,
                opponent_injury_context=opponent_injuries,
                ol_context=team_ol,
                opponent_ol_context=opponent_ol,
                alternate_team_snap=alternate_team_snap,
                alternate_opp_snap=alternate_opp_snap,
                current_window=recent_games,
                alternate_window=alternate_recent_games,
            ),
            unsafe_allow_html=True,
        )

    recent_rows = logs[logs["team"].isin([game.get("away_team"), game.get("home_team")])].sort_values(["date", "team"]).tail(recent_games * 2)

    def render_game_log() -> None:
        if not show_details or recent_rows.empty:
            return
        st.dataframe(
            recent_rows[
                [
                    "date", "team", "opponent", "home_away", "points", "opponent_points",
                    "total_yards", "passing_yards", "rushing_yards", "third_down_conv",
                    "third_down_att", "third_down_pct", "sacks_allowed", "sack_rate_allowed",
                    "plays", "yards_per_play", "plays_per_point", "run_rate", "pass_rate",
                    "yards_allowed", "passing_yards_allowed", "rushing_yards_allowed",
                    "third_down_conv_allowed", "third_down_att_allowed", "third_down_pct_allowed",
                    "sacks_made", "sack_rate_made", "yards_per_play_allowed",
                    "plays_per_point_allowed", "turnover_margin",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    snap_cols = st.columns(2)
    with snap_cols[0]:
        render_team_detail(
            away_snap, home_snap, game.get("away_color", "#38bdf8"),
            game.get("away_alt_color", "#f8fafc"), game.get("away_abbrev", ""), False,
            away_familiarity, away_injuries, home_injuries, away_ol, home_ol,
            away_alternate_snap, home_alternate_snap,
        )
    with snap_cols[1]:
        render_team_detail(
            home_snap, away_snap, game.get("home_color", "#f59e0b"),
            game.get("home_alt_color", "#f8fafc"), game.get("home_abbrev", ""), True,
            home_familiarity, home_injuries, away_injuries, home_ol, away_ol,
            home_alternate_snap, away_alternate_snap,
        )
    st.markdown(render_ncaaf_matchup_card(game, logs, recent_games, sos_map, league_label), unsafe_allow_html=True)
    render_game_log()

def render_ncaaf_workspace(
    selected_date: Any,
    season: int,
    page_mode: str,
    recent_games: int,
    show_details: bool,
    hide_started_games: bool = False,
    league_label: str = "NCAAF",
) -> None:
    league_label = "NFL" if str(league_label).upper() == "NFL" else "NCAAF"
    is_nfl = league_label == "NFL"
    board_title = "NFL Research Board" if is_nfl else "College Football Research Board"
    sos_method_label = (
        "NFL-defined opponent aggregate W-L-T percentage"
        if is_nfl
        else "opponent-adjusted schedule strength with ESPN FPI rank"
    )
    st.markdown(
        f"""
        <div class="dashboard-card" style="padding:1rem 1.1rem; margin-bottom:1rem; border-color:rgba(45,212,191,0.45);">
          <div class="dashboard-hero__eyebrow">{league_label} template</div>
          <div class="dashboard-hero__title" style="font-size:1.8rem;">{board_title}</div>
          <div class="dashboard-hero__subtitle">Team form, matchup weaknesses and market-aware spread / moneyline decisions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    logs = prepare_ncaaf_team_logs(
        load_nfl_team_logs(nfl_data_signature()) if is_nfl else load_ncaaf_team_logs(ncaaf_data_signature())
    )
    if is_nfl and not logs.empty:
        competitive_logs = logs[logs["season_type"].str.lower() != "preseason"].copy()
        if not competitive_logs.empty:
            logs = competitive_logs.reset_index(drop=True)
    sos_ranking_data = fetch_espn_football_sos_ranks(season, league_label)
    base_sos_map = nfl_strength_of_schedule_map(logs) if is_nfl else ncaaf_strength_of_schedule_map(logs)
    sos_map = attach_espn_sos_ranks(base_sos_map, sos_ranking_data, league_label)
    familiarity_flags = prepare_ncaaf_familiarity_flags(
        load_nfl_familiarity_flags(nfl_familiarity_signature())
        if is_nfl
        else load_ncaaf_familiarity_flags(ncaaf_familiarity_signature())
    )
    injury_report = prepare_ncaaf_injury_report(
        load_nfl_injury_report(nfl_injury_signature())
        if is_nfl
        else load_ncaaf_injury_report(ncaaf_injury_signature())
    )
    ol_continuity_flags = prepare_ncaaf_ol_continuity_flags(
        load_nfl_ol_continuity_flags(nfl_ol_continuity_signature())
        if is_nfl
        else load_ncaaf_ol_continuity_flags(ncaaf_ol_continuity_signature())
    )
    latest = latest_nfl_log_date() if is_nfl else latest_ncaaf_log_date()
    full_schedule = fetch_nfl_schedule_for_date(selected_date) if is_nfl else fetch_ncaaf_schedule_for_date(selected_date)
    gameday_inactive_count = 0
    gameday_confirmed_teams = 0
    if is_nfl and full_schedule:
        slate_weeks = [safe_int(game.get("week")) for game in full_schedule if safe_int(game.get("week"))]
        slate_week = max(slate_weeks) if slate_weeks else 0
        slate_teams = tuple(sorted({
            str(game.get(side) or "")
            for game in full_schedule
            for side in ["away_team", "home_team"]
            if str(game.get(side) or "")
        }))
        gameday_report = fetch_nfl_official_inactives(season, slate_week, slate_teams)
        if not gameday_report.empty:
            gameday_inactive_count = int((gameday_report["player"] != "__TEAM_REPORT_CHECKED__").sum())
            gameday_confirmed_teams = int((gameday_report["player"] == "__TEAM_REPORT_CHECKED__").sum())
            injury_report = nfl_merge_injury_sources(
                injury_report,
                pd.DataFrame(columns=NCAAF_INJURY_COLUMNS),
                gameday_report,
            )
            injury_report = nfl_enrich_injuries_with_snap_counts(
                injury_report,
                load_nfl_snap_counts(nfl_snap_counts_signature()),
            )
    schedule = (
        [game for game in full_schedule if str(game.get("state") or "").lower() not in {"in", "post"}]
        if hide_started_games
        else full_schedule
    )
    hidden_game_count = len(full_schedule) - len(schedule)
    football_odds_key = get_sportsgameodds_api_key()
    football_odds_events = []
    football_odds_error = ""
    if football_odds_key and schedule:
        if is_nfl:
            football_odds_events, football_odds_error = fetch_sgo_nfl_events_for_date(football_odds_key, str(selected_date))
        else:
            football_odds_events, football_odds_error = fetch_sgo_ncaaf_events_for_date(football_odds_key, str(selected_date))
    for game in schedule:
        game_state = str(game.get("state") or "").lower()
        use_closing = game_state in {"in", "post"}
        primary_market = ncaaf_sgo_market_for_game(
            game,
            football_odds_events,
            use_closing=use_closing,
        )
        fallback_market = espn_football_market_for_game(game, use_closing=use_closing)
        game["market"] = merge_football_markets(primary_market, fallback_market)
        if football_odds_error and game["market"].get("availability") != "priced":
            game["market"]["availability"] = "provider_error"
            game["market"]["error"] = football_odds_error
    status_cols = st.columns(4)
    status_cols[0].metric("Saved games", str(int(logs["game_id"].nunique()) if not logs.empty else 0))
    status_cols[1].metric("Teams", str(int(logs["team"].nunique()) if not logs.empty else 0))
    status_cols[2].metric("Latest log", latest.strftime("%Y-%m-%d") if latest is not None else "none")
    status_cols[3].metric("Slate games", str(len(schedule)))
    status_notes: list[str] = []

    if is_nfl and gameday_confirmed_teams:
        status_notes.append(
            f"Official NFL game-day layer: {gameday_inactive_count} inactives confirmed across "
            f"{gameday_confirmed_teams} teams. Auto-refreshes every five minutes; cleared questionable players are removed."
        )

    if hide_started_games:
        hide_note = f"Hide started games is on: {hidden_game_count} live/completed games hidden, {len(schedule)} upcoming games shown."
        if is_nfl:
            status_notes.append(hide_note)
        else:
            st.caption(hide_note)

    cfbd_key = get_cfbd_api_key() if not is_nfl else ""
    espn_sos_count = len(sos_ranking_data.get("rows", []) or [])
    nfl_sos_count = sum(bool(values.get("available")) for values in sos_map.values()) if is_nfl else 0
    if is_nfl and nfl_sos_count:
        espn_context = f" ESPN FPI comparison is available for {espn_sos_count} teams." if espn_sos_count else " ESPN FPI comparison is temporarily unavailable."
        status_notes.append(
            f"NFL SOS uses aggregate opponent W-L-T percentage ({ordinal_rank(1)} = toughest schedule played) "
            f"for {nfl_sos_count} teams. Its model adjustment is capped at ±1.0 point and reduced before eight games."
            + espn_context
        )
    elif not is_nfl and espn_sos_count:
        st.caption(
            f"Published SOS rank: ESPN FPI AvgInSOS ({ordinal_rank(1)} = toughest schedule played), "
            f"with {espn_sos_count} teams available. The displayed official rank now supplies the capped "
            "NCAAF margin adjustment; the saved-results calculation is fallback context only."
        )
    elif is_nfl:
        status_notes.append("NFL SOS is temporarily unavailable because opponent records could not be built. ESPN FPI is also unavailable, so SOS does not move the NFL recommendation.")
    elif cfbd_key:
        st.success("Published ESPN FPI SOS rank is temporarily unavailable. The opponent-adjusted NCAAF fallback remains active from saved ESPN results. CFBD_API_KEY is also configured for future advanced metrics.")
    else:
        st.caption("Published ESPN FPI SOS rank is temporarily unavailable. The opponent-adjusted NCAAF fallback remains active from saved ESPN results and shrinks the adjustment while evidence is limited. CollegeFootballData can still add drives, success rate, PPA and SP+/CORE later.")

    priced_by_phase = {"pregame": 0, "closing": 0}
    for game in schedule:
        market = game.get("market") or {}
        has_price = any(
            (market.get(side, {}) or {}).get(market_type)
            for side in ["away", "home"]
            for market_type in ["spread", "moneyline"]
        )
        if has_price:
            phase = "closing" if market.get("phase") == "closing" else "pregame"
            priced_by_phase[phase] += 1
    priced_games = sum(priced_by_phase.values())
    fallback_priced = sum(
        1
        for game in schedule
        if "ESPN" in str((game.get("market") or {}).get("source") or "")
        and (game.get("market") or {}).get("availability") == "priced"
    )
    if not football_odds_key and fallback_priced:
        st.info(
            f"SportsGameOdds is not configured. ESPN scoreboard markets are active for "
            f"{fallback_priced} of {len(schedule)} slate games."
        )
    elif not football_odds_key:
        st.warning(f"{league_label} side prices are unavailable because no configured or ESPN fallback market was found.")
    elif football_odds_error and fallback_priced:
        st.warning(
            f"SportsGameOdds refresh failed ({football_odds_error}). ESPN scoreboard fallback is active for "
            f"{fallback_priced} of {len(schedule)} slate games."
        )
    elif football_odds_error:
        st.warning(f"{league_label} side prices could not be refreshed: {football_odds_error}")
    else:
        unpriced_games = max(0, len(schedule) - priced_games)
        unavailable_note = (
            f" {unpriced_games} game{'s' if unpriced_games != 1 else ''} currently "
            f"{'has' if unpriced_games == 1 else 'have'} no usable provider market."
            if unpriced_games
            else ""
        )
        market_note = (
            f"Spread / moneyline match: {priced_games} of {len(schedule)} slate games "
            f"({priced_by_phase['pregame']} pregame, {priced_by_phase['closing']} closing). "
            "Pregame prices are current; started and completed games use frozen closing prices, never live odds. "
            f"Markets marked OFF are judged on the spread only.{unavailable_note}"
        )
        if is_nfl:
            status_notes.append(market_note)
        else:
            st.caption(market_note)

    if not logs.empty:
        data_path = NFL_TEAM_LOG_PATH if is_nfl else NCAAF_TEAM_LOG_PATH
        data_file_note = f"{league_label} data file: {data_path.name}"
        defense_note = "Defensive pass, rush and total-yard figures are opponent box-score averages per completed saved game. Teams without a completed saved game show n/a."
        if is_nfl:
            status_notes.extend([data_file_note, defense_note])
        else:
            st.caption(data_file_note)
            st.caption(defense_note)
    else:
        st.info(f"{league_label} logs are empty. Press Update {league_label} logs in the sidebar to build the database from ESPN.")
    if not familiarity_flags.empty:
        familiarity_path = NFL_FAMILIARITY_FLAGS_PATH if is_nfl else NCAAF_FAMILIARITY_FLAGS_PATH
        familiarity_note = f"Personnel context flags: {len(familiarity_flags)} saved in {familiarity_path.name}"
        if is_nfl:
            status_notes.append(familiarity_note)
        else:
            st.caption(familiarity_note)
    report_context = ncaaf_injury_context(injury_report, "__report_status__")
    if not report_context.get("available"):
        update_label = "Update NFL injury report" if is_nfl else "Update NCAAF injury report"
        st.warning(f"{league_label} injuries are unverified. Use ‘{update_label}’ in the sidebar before trusting a side signal.")
    else:
        report_time = report_context.get("updated_at")
        report_label = (
            pd.Timestamp(report_time).tz_convert("Europe/Stockholm").strftime("%Y-%m-%d %H:%M")
            if report_time is not None and pd.notna(report_time)
            else "unknown"
        )
        listed_count = int((injury_report["player"] != "__TEAM_REPORT_CHECKED__").sum())
        report_source = (
            "NFL.com final game-day inactives, official weekly designations via nflverse and Covers news/IR rows"
            if is_nfl else "official ACC game-day availability reports plus Covers injury news"
        )
        report_message = (
            f"Injury report: {listed_count} listed players · refreshed {report_label} Swedish time · "
            f"sourced from {report_source}."
        )
        if report_context.get("stale"):
            st.warning(report_message + " The report is stale, so injury point adjustments are disabled until refreshed.")
        else:
            if is_nfl:
                status_notes.append(report_message)
            else:
                st.caption(report_message)

    if is_nfl and status_notes:
        with st.expander("Data freshness, sources & methodology", expanded=False):
            for note in status_notes:
                st.caption(note)

    if page_mode == "Team rankings":
        render_section_intro(f"{league_label} team rankings", f"Teams ranked from the latest saved games using a last {recent_games} game window. SOS uses {sos_method_label}.")
        ranking_df = ncaaf_team_ranking_rows(logs, recent_games, sos_map)
        if ranking_df.empty:
            st.info(f"No {league_label} team logs available yet.")
        else:
            st.dataframe(ranking_df, use_container_width=True, hide_index=True)
        return

    if not schedule:
        if hide_started_games and full_schedule:
            st.info("All games on this slate have already started or finished. Turn off ‘Hide games that have started’ to review them.")
            return
        error_data = fetch_nfl_scoreboard_data(str(selected_date)) if is_nfl else fetch_ncaaf_scoreboard_data(str(selected_date))
        error = error_data.get("_error")
        st.warning(f"No {league_label} games found for this date." + (f" ESPN error: {error}" if error else ""))
        return

    if page_mode == "Shortlist":
        render_section_intro(f"{league_label} shortlist", f"Market-aware sides only: the actual spread is compared with recent form, {sos_method_label} and the market baseline; moneylines are filtered for price and availability.")
        rows = ncaaf_shortlist_rows(schedule, logs, recent_games, sos_map, injury_report, ol_continuity_flags)
        if not rows:
            st.info(f"No {league_label} sides passed the first shortlist rules for this slate.")
        else:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    render_section_intro(
        f"{league_label} matchups",
        f"Each matchup uses saved season context, a last {recent_games} game read and {sos_method_label}.",
    )
    display_schedule = schedule
    slate_display = "Full slate"
    if is_nfl:
        view_col, game_col = st.columns([0.9, 2.1])
        with view_col:
            slate_display = st.radio(
                "Slate display",
                ["Focus one game", "Full slate"],
                horizontal=True,
                key="nfl_slate_display",
            )
        if slate_display == "Focus one game":
            game_labels = [football_game_display_label(game) for game in schedule]
            with game_col:
                selected_game_label = st.selectbox(
                    "Choose matchup",
                    game_labels,
                    key="nfl_focused_game",
                )
            selected_index = game_labels.index(selected_game_label)
            display_schedule = [schedule[selected_index]]
        else:
            with game_col:
                st.caption("Every matchup remains available below in a collapsed game card.")

    matchup_benchmarks = football_matchup_benchmarks(logs, recent_games)
    for game in display_schedule:
        if is_nfl and slate_display == "Full slate":
            with st.expander(football_game_display_label(game), expanded=False):
                render_football_game_section(
                    game, logs, recent_games, sos_map, familiarity_flags, injury_report,
                    ol_continuity_flags, matchup_benchmarks, show_details, league_label,
                )
        else:
            render_football_game_section(
                game, logs, recent_games, sos_map, familiarity_flags, injury_report,
                ol_continuity_flags, matchup_benchmarks, show_details, league_label,
            )

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

def render_line_movement_section(
    game: dict,
    selected_date: Any,
    current_game_key: str,
    current_game_label: str,
    odds_markets: list[str],
    odds_books_text: str,
    save_odds_snapshot: bool,
    away_snapshot: dict,
    home_snapshot: dict,
    away_pitcher: dict,
    home_pitcher: dict,
    away_bullpen: dict,
    home_bullpen: dict,
    away_home_away: dict,
    home_home_away: dict,
    weather_context: dict,
) -> None:
    render_section_intro("Odds / line movement", "Fetch selected SportsGameOdds markets and save snapshots to track movement over time.")
    sgo_api_key = get_sportsgameodds_api_key()
    odd_ids = sgo_selected_odd_ids(odds_markets)
    selected_books = [book.strip() for book in odds_books_text.split(",") if book.strip()]
    odds_rows = []
    if not sgo_api_key:
        st.info("Add SPORTSGAMEODDS_API_KEY to Streamlit secrets or your environment to enable odds.")
    else:
        if st.button("Fetch latest odds", use_container_width=True, key="fetch_latest_odds_line_movement"):
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


def render_pitcher_er_lines_section(
    game: dict,
    selected_date: Any,
    current_game_key: str,
    odds_books_text: str,
) -> None:
    render_section_intro("Pitcher ER lines", "Fetch pitcher earned-run lines and prices. This section does not suggest plays or grade results.")
    sgo_api_key = get_sportsgameodds_api_key()
    selected_books = [book.strip() for book in odds_books_text.split(",") if book.strip()]
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
        if st.button("Fetch ER lines", use_container_width=True, key="fetch_pitcher_er_lines"):
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
    sport_mode = st.radio("Sport", ["MLB", "NCAAF", "NFL", "NCAAB"], index=0)
    selected_date = st.date_input("Date", value=default_slate_date())

    if sport_mode == "NCAAB":
        st.caption("College Basketball • ESPN schedule + optional adjusted ratings")
    elif sport_mode in {"NCAAF", "NFL"}:
        football_label = sport_mode
        football_is_nfl = sport_mode == "NFL"
        football_log_path = NFL_TEAM_LOG_PATH if football_is_nfl else NCAAF_TEAM_LOG_PATH
        season = nfl_season_for_date(selected_date) if football_is_nfl else ncaaf_season_for_date(selected_date)
        stale_ncaaf_logs, latest_ncaaf_log_ts, expected_ncaaf_log_date = (
            nfl_logs_are_stale(pd.Timestamp(selected_date))
            if football_is_nfl
            else ncaaf_logs_are_stale(pd.Timestamp(selected_date))
        )
        missing_football_schema = []
        if football_log_path.exists():
            try:
                saved_football_columns = set(pd.read_csv(football_log_path, nrows=0).columns)
                missing_football_schema = [
                    column for column in NCAAF_TEAM_LOG_COLUMNS if column not in saved_football_columns
                ]
            except Exception:
                missing_football_schema = list(NCAAF_TEAM_LOG_COLUMNS)
        football_logs_need_refresh = stale_ncaaf_logs or bool(missing_football_schema)
        if football_log_path.exists():
            st.caption(f"Data file: {football_log_path.name}")
            st.caption(f"File saved: {pd.Timestamp(football_log_path.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.caption(f"{football_label} data file will be created on first update.")

        latest_ncaaf_label = latest_ncaaf_log_ts.strftime("%Y-%m-%d") if latest_ncaaf_log_ts is not None else "none"
        expected_ncaaf_label = expected_ncaaf_log_date.strftime("%Y-%m-%d")
        if missing_football_schema:
            st.warning(
                f"{football_label} logs need a one-time rebuild for goal-line and line-of-scrimmage data."
            )
        elif stale_ncaaf_logs:
            st.warning(f"{football_label} logs outdated. Latest saved result: {latest_ncaaf_label}. Needed through: {expected_ncaaf_label}.")
        else:
            st.success(f"{football_label} logs fresh through {latest_ncaaf_label}.")

        if st.button(f"Update {football_label} logs", use_container_width=True):
            if not football_logs_need_refresh:
                ok = True
                message = f"{football_label} logs already up to date through {latest_ncaaf_label}."
            else:
                with st.spinner(f"Downloading {football_label} team logs..."):
                    ok, message = (
                        update_nfl_team_game_logs(season)
                        if football_is_nfl
                        else update_ncaaf_team_game_logs(season)
                    )
            st.session_state[f"{football_label.lower()}_update_message"] = ("success" if ok else "error", message)
            st.cache_data.clear()
            st.rerun()

        football_update_key = f"{football_label.lower()}_update_message"
        if football_update_key in st.session_state:
            kind, msg = st.session_state[football_update_key]
            if kind == "success":
                st.success(f"{football_label} logs updated.")
            else:
                st.error(f"{football_label} update failed.")
            with st.expander(f"{football_label} update log"):
                st.text(msg)

        sidebar_injuries = prepare_ncaaf_injury_report(
            load_nfl_injury_report(nfl_injury_signature())
            if football_is_nfl
            else load_ncaaf_injury_report(ncaaf_injury_signature())
        )
        sidebar_gameday_teams = 0
        if football_is_nfl:
            sidebar_schedule = fetch_nfl_schedule_for_date(selected_date)
            sidebar_weeks = [safe_int(game.get("week")) for game in sidebar_schedule if safe_int(game.get("week"))]
            sidebar_week = max(sidebar_weeks) if sidebar_weeks else 0
            sidebar_teams = tuple(sorted({
                str(game.get(side) or "")
                for game in sidebar_schedule
                for side in ["away_team", "home_team"]
                if str(game.get(side) or "")
            }))
            sidebar_gameday = fetch_nfl_official_inactives(season, sidebar_week, sidebar_teams)
            if not sidebar_gameday.empty:
                sidebar_gameday_teams = int(
                    (sidebar_gameday["player"] == "__TEAM_REPORT_CHECKED__").sum()
                )
                sidebar_injuries = nfl_merge_injury_sources(
                    sidebar_injuries,
                    pd.DataFrame(columns=NCAAF_INJURY_COLUMNS),
                    sidebar_gameday,
                )
        sidebar_injury_status = ncaaf_injury_context(sidebar_injuries, "__report_status__")
        if sidebar_injury_status.get("available"):
            injury_time = sidebar_injury_status.get("updated_at")
            injury_time_label = (
                pd.Timestamp(injury_time).tz_convert("Europe/Stockholm").strftime("%Y-%m-%d %H:%M")
                if injury_time is not None and pd.notna(injury_time)
                else "unknown"
            )
            if sidebar_injury_status.get("stale"):
                st.warning(f"Injury report stale: {injury_time_label}")
            else:
                game_day_note = f" · final lists for {sidebar_gameday_teams} teams" if sidebar_gameday_teams else ""
                st.success(f"Injury report: {injury_time_label}{game_day_note}")
        else:
            st.warning("Injury report not downloaded yet.")

        if football_is_nfl:
            sidebar_snaps = prepare_nfl_snap_counts(load_nfl_snap_counts(nfl_snap_counts_signature()))
            if sidebar_snaps.empty:
                st.warning("NFL snap counts not downloaded yet.")
            else:
                st.caption(
                    f"NFL snap counts: {len(sidebar_snaps)} player-game rows through "
                    f"Week {safe_int(sidebar_snaps['week'].max())}."
                )

        injury_button_label = "Update NFL injury report (game-day + weekly + Covers)" if football_is_nfl else "Update NCAAF injuries (official ACC + Covers)"
        if st.button(injury_button_label, use_container_width=True):
            spinner_message = (
                "Downloading final NFL game-day inactives, official weekly designations, Covers news/IR rows, snap counts and squad roles..."
                if football_is_nfl
                else "Downloading official ACC availability, Covers injuries and checking squad roles..."
            )
            with st.spinner(spinner_message):
                injury_ok, injury_message = (
                    update_nfl_injury_report(selected_date)
                    if football_is_nfl
                    else update_ncaaf_injury_report(selected_date)
                )
            st.session_state[f"{football_label.lower()}_injury_update_message"] = (
                "success" if injury_ok else "error",
                injury_message,
            )
            st.cache_data.clear()
            st.rerun()

        football_injury_key = f"{football_label.lower()}_injury_update_message"
        if football_injury_key in st.session_state:
            injury_kind, injury_msg = st.session_state[football_injury_key]
            if injury_kind == "success":
                st.success("Injury report updated.")
            else:
                st.error("Injury update failed; the previous report was kept.")
            with st.expander("Injury update log"):
                st.text(injury_msg)

        st.subheader("View")
        page_mode = st.radio("Page", ["Matchups", "Shortlist", "Team rankings"], index=0)
        ncaaf_window_choice = st.radio("Recent window", ["Last 3", "Last 5"], index=1)
        ncaaf_recent_games = 3 if ncaaf_window_choice == "Last 3" else 5
        hide_started_ncaaf_games = st.toggle("Hide games that have started", value=False)
        show_ncaaf_detail_tables = st.toggle("Game log detail", value=False)
        with st.expander(f"{football_label} signal guide"):
            st.markdown(
                f"""
                **{football_label} update** uses ESPN scoreboard and game summaries to save completed team-game logs.

                **Side market decisions** evaluate the actual spread (run line) rather than simply rating the stronger team. The adjusted margin blends recent scoring margin, yards-per-play dominance, opponent-adjusted strength of schedule, home field and the market baseline.

                **Injuries & availability** {"use NFL.com's final game-day inactive lists above official weekly Out/Doubtful/Questionable designations from nflverse and Covers news/IR rows. Game-day lists auto-refresh every five minutes and clear active questionable players" if football_is_nfl else "use official ACC game-day availability as the primary status source for ACC teams, supplemented by Covers injury news for the national slate"}. Squad roles are checked against recent snap counts and Covers team pages: QB order uses passing attempts, backs use rushing workload, receivers use receiving production, and defenders use defensive stats/team-leader listings. Unverified offensive-line roles are never guessed. An out/doubtful QB1 can force a favorite to pass unless the post-injury cover cushion remains large. A missing team report means unverified, never healthy; freshness is evaluated separately for each team and stale reports do not move the model.

                **Strength of schedule (SOS)** {"uses opponents' aggregate W-L-T percentage and rank under the NFL definition. Repeated divisional opponents are weighted by each meeting; the margin adjustment is capped at ±1.0 point and reduced before eight games. ESPN FPI AvgInSOS is displayed only as a separate external comparison." if football_is_nfl else "uses ESPN FPI AvgInSOS for both the displayed rank and the capped margin adjustment. The NCAAF saved-results model excludes the direct head-to-head result and is used only when ESPN has no published rank."}

                **Large-favorite checks** explicitly penalize run-heavy clock drain and late backup/backdoor exposure. A credible shutout profile can offset part of that penalty.

                **Moneyline** is evaluated only when the price is meaningful. Huge mismatches with an unavailable or prohibitively expensive ML are marked spread-only instead of receiving automatic confidence points.

                **Volatility** replaces false precision: one-game and small samples are clearly marked even when the spread edge looks large.

                **Third down** shows combined conversions/attempts and the weighted conversion rate for the selected recent window. **Third down allowed** uses opponents' conversions against that defense over the same games.

                **Supporting team-trait profile** closes every team analysis with five ordered context pillars: third-down offense, third-down defense, red-zone offense, red-zone defense and strength of schedule. It is not the betting recommendation. A team that wins at least four available pillars receives a strong trait edge; a team that loses at least four receives a strong trait concern. Third-down and red-zone agreement can move the projected margin by at most 2.5 points and is reduced in small samples. SOS is not added twice because its official-rank value already influences the main margin.

                **Form-window check** always compares the selected Last 3/Last 5 projection with the other window. If one produces a cover edge of at least two points and the other opposes the same side by at least two, the card becomes **Window conflict — pass** and is removed from the shortlist.

                **Goal line & line of scrimmage** separates finishing strength from open-field yardage. Goal-to-go TD/stops use drives that reach the opponent's 10, short-yardage uses third/fourth down with two yards or fewer, and rush stuff rate counts non-kneel runs held to zero or negative yards. Raw attempts are shown beside every rate. The combined margin adjustment is sample-weighted and capped at 1.5 points.

                **Pass protection** combines sacks allowed per dropback with the opponent's defensive sack rate. Its model influence is capped, reduced in small samples, and receives an extra favorite-risk warning when a team with fragile protection is laying at least a touchdown. Verified offensive-line instability and active OL injury listings add a separate continuity adjustment.

                **Defense allowed** shows per-game opponent production: points, total yards, pass yards, rush yards and defensive yards per play. A team displays n/a until it has a completed game in the saved log.

                **Plays per point** tells us how many offensive plays a team needs to create one point. Lower is more efficient; very low scoring without YPP support can be fake, and high plays/point with good YPP can point to finishing or turnover problems.

                **Team truth profile** flags sustainable scoring, short-field scoring, turnover drag, finishing problems, real offensive issues, hidden yards, and opponent-wall games.

                **Run/pass profile** labels teams as run-first, pass-heavy, balanced production, explosive pass profile, or ground efficiency.

                **Totals** look for both-team offensive efficiency, points allowed, and low-output/defensive drag.

                ESPN covers the boxscore logs and opponent-adjusted SOS used by this section.
                """
            )
    else:
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
            st.error(f"Slate stats outdated. Latest saved result: {latest_label}. Needed through: {expected_label}.")
        else:
            st.success(f"Slate stats fresh through {latest_label}.")

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
        page_mode = st.radio("Page", ["Matchups", "Line movement", "ER lines", "Bullpens", "Pitchers", "Hitters"], index=0)
        view_mode = st.radio("Detail level", ["Simple", "Detailed"], index=0)
        show_detail_tables = view_mode == "Detailed"
        bullpen_recent_games = 5
        show_best_bet_shortlist = False
        show_pitcher_detail_cards = True
        show_hitter_detail_cards = True
        odds_markets = ["Moneyline", "Run line", "Game total"]
        odds_books_text = DEFAULT_ODDS_BOOKS
        save_odds_snapshot = True

        if page_mode == "Matchups":
            show_best_bet_shortlist = st.toggle("Best-bet shortlist", value=True)
            with st.expander("Chart settings"):
                metric = st.selectbox("Metric", ["ops", "obp"], index=0)
                window = st.slider("Rolling window", min_value=3, max_value=14, value=7)
                chart_mode = st.radio("Chart style", ["Rolling trend only", "Rolling + daily"], index=0)
                smooth_lines = st.toggle("Smooth lines", value=False)
        elif page_mode == "Line movement":
            st.subheader("Line movement")
            odds_markets = st.multiselect(
                "Markets",
                ["Moneyline", "Run line", "Game total"],
                default=["Moneyline", "Run line", "Game total"],
            )
            odds_books_text = st.text_input("Books", value=DEFAULT_ODDS_BOOKS)
            save_odds_snapshot = st.toggle("Save odds snapshots", value=True)
        elif page_mode == "ER lines":
            st.subheader("ER lines")
            odds_books_text = st.text_input("Books", value=DEFAULT_ODDS_BOOKS)
        elif page_mode == "Bullpens":
            bullpen_recent_games = st.slider("Recent bullpen games", min_value=3, max_value=10, value=5)
        elif page_mode == "Pitchers":
            show_pitcher_detail_cards = st.toggle("Pitcher detail cards", value=True)
        elif page_mode == "Hitters":
            show_hitter_detail_cards = st.toggle("Hitter detail cards", value=True)

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

# NCAAB is intentionally isolated from the existing MLB/NCAAF/NFL workspaces.
ESPN_NCAAB_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
NCAAB_RATINGS_PATH = APP_DIR / "data" / "ncaab_adjusted_ratings.csv"
NCAAB_TORVIK_URL = "https://barttorvik.com/{season}_team_results.csv"
NCAAB_RATINGS_MAX_AGE_HOURS = 12


@st.cache_data(ttl=600)
def fetch_ncaab_scoreboard(date_str: str) -> dict:
    response = requests.get(
        ESPN_NCAAB_SCOREBOARD_URL,
        params={"dates": date_str.replace("-", ""), "groups": 50, "limit": 500},
        timeout=25,
    )
    response.raise_for_status()
    return response.json()


def ncaab_match_rows(payload: dict) -> pd.DataFrame:
    rows = []
    for event in payload.get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        def name(c):
            team = c.get("team") or {}
            return team.get("displayName") or team.get("shortDisplayName") or "Unknown"
        status = (event.get("status") or {}).get("type") or {}
        start = pd.to_datetime(event.get("date"), utc=True, errors="coerce")
        start_local = start.tz_convert("Europe/Stockholm").strftime("%Y-%m-%d %H:%M") if pd.notna(start) else "—"
        rows.append({
            "Event ID": str(event.get("id", "")),
            "Start (Sweden)": start_local,
            "Away": name(away),
            "Home": name(home),
            "Away location": (away.get("team") or {}).get("location", ""),
            "Home location": (home.get("team") or {}).get("location", ""),
            "Status": status.get("shortDetail") or status.get("description") or "Scheduled",
            "Away score": away.get("score", ""),
            "Home score": home.get("score", ""),
        })
    return pd.DataFrame(rows)


def ncaab_season_for_date(date_value) -> int:
    # The 2026-27 season uses Bart Torvik's 2027 season identifier.
    day = pd.Timestamp(date_value)
    return int(day.year + (day.month >= 7))


def parse_ncaab_torvik_ratings(content: bytes, season: int) -> pd.DataFrame:
    # Torvik publishes a season-specific team_results CSV. Never accept a
    # different season or an HTML error page as adjusted ratings.
    if len(content) < 100 or content.lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise ValueError("The ratings source did not return a valid CSV file.")
    source = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig", low_memory=False)
    normalized = {str(c).strip().lower().replace(" ", "").replace("_", ""): c for c in source.columns}
    required = {"team": "Team", "adjoe": "AdjO", "adjde": "AdjD", "adjt": "AdjT"}
    missing = [key for key in required if key not in normalized]
    if missing:
        raise ValueError(f"Torvik CSV is missing fields: {', '.join(missing)}")
    result = source[[normalized[key] for key in required]].copy()
    result.columns = list(required.values())
    result["Team"] = result["Team"].astype(str).str.strip()
    for field in ("AdjO", "AdjD", "AdjT"):
        result[field] = pd.to_numeric(result[field], errors="coerce")
    result = result.dropna(subset=["Team", "AdjO", "AdjD", "AdjT"])
    result = result[result["Team"].ne("") & result["Team"].ne("nan")]
    result = result.drop_duplicates(subset=["Team"])
    if len(result) < 100:
        raise ValueError(f"Only {len(result)} valid teams were returned; keeping the existing snapshot.")
    now = pd.Timestamp.now(tz="UTC").isoformat()
    result["Source"] = "Bart Torvik"
    result["AsOf"] = now
    result["Season"] = int(season)
    return result.reset_index(drop=True)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ncaab_torvik_ratings(season: int) -> pd.DataFrame:
    url = NCAAB_TORVIK_URL.format(season=season)
    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (compatible; PersonalNCAABResearch/1.0)"})
    response.raise_for_status()
    return parse_ncaab_torvik_ratings(response.content, season)


def load_ncaab_adjusted_ratings(season: int | None = None) -> pd.DataFrame:
    if not NCAAB_RATINGS_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(NCAAB_RATINGS_PATH)
        if not {"Team", "AdjO", "AdjD", "AdjT"}.issubset(df.columns):
            return pd.DataFrame()
        if season is not None and "Season" in df.columns:
            df = df[pd.to_numeric(df["Season"], errors="coerce") == int(season)]
        elif season is not None:
            # Unlabelled imports are not safe to use as current-season ratings.
            return pd.DataFrame()
        for column in ("AdjO", "AdjD", "AdjT"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        return df.dropna(subset=["Team", "AdjO", "AdjD", "AdjT"])
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()


def ncaab_ratings_stale(season: int) -> bool:
    if not NCAAB_RATINGS_PATH.exists():
        return True
    age_seconds = pd.Timestamp.now().timestamp() - NCAAB_RATINGS_PATH.stat().st_mtime
    return load_ncaab_adjusted_ratings(season).empty or age_seconds >= NCAAB_RATINGS_MAX_AGE_HOURS * 3600


def refresh_ncaab_ratings(season: int, force: bool = False) -> tuple[bool, str]:
    if not force and not ncaab_ratings_stale(season):
        return True, "Existing snapshot is fresh."
    try:
        ratings = fetch_ncaab_torvik_ratings(season)
        NCAAB_RATINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Atomic replacement prevents a failed/partial download overwriting good data.
        temp_path = NCAAB_RATINGS_PATH.with_suffix(".tmp")
        ratings.to_csv(temp_path, index=False)
        os.replace(temp_path, NCAAB_RATINGS_PATH)
        return True, f"Updated {len(ratings)} teams from Bart Torvik, season {season}."
    except (requests.RequestException, ValueError, OSError, pd.errors.ParserError) as exc:
        return False, f"Unable to update Bart Torvik ratings: {exc}"


def ncaab_team_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower().replace("&", "and"))


NCAAB_TEAM_ALIASES = {
    "connecticut": "uconn",
    "universityofconnecticut": "uconn",
    "mississippi": "olemiss",
    "miamifl": "miamifl",
    "miamiflorida": "miamifl",
    "saintmarys": "stmarys",
    "saintjohns": "stjohns",
    "saintjosephs": "stjosephs",
}


def find_ncaab_rating(ratings: pd.DataFrame, team: str, location: str = "") -> pd.DataFrame:
    lookup = ratings.copy()
    lookup["_key"] = lookup["Team"].map(ncaab_team_key)
    candidates = [ncaab_team_key(location), ncaab_team_key(team)]
    candidates.extend(NCAAB_TEAM_ALIASES.get(key, key) for key in list(candidates))
    for candidate in dict.fromkeys(candidates):
        matches = lookup[lookup["_key"] == candidate]
        if len(matches) == 1:
            return matches
    return lookup.iloc[0:0]


# These projections are deliberately NOT labelled as the historical full OG model.
# Historical OG additionally required recent-three splits and the Four Factors.
# Its exact coefficients are not present in this dashboard's source files.
NCAAB_PROJECTION_LOG_PATH = APP_DIR / "data" / "ncaab_projection_snapshots.csv"
NCAAB_PROJECTION_COLUMNS = [
    "saved_at_utc", "game_id", "game_start_sweden", "season", "away", "home",
    "ratings_source", "ratings_as_of", "model", "away_projected", "home_projected",
    "total_projected", "home_margin_projected", "market_home_spread",
    "market_total", "ats_side", "ats_edge", "actual_away", "actual_home",
    "actual_total", "actual_home_margin", "winner_correct", "ats_result",
    "margin_abs_error", "total_abs_error",
]


def ncaab_rating_core_projection(away: pd.Series, home: pd.Series) -> dict:
    """Transparent preliminary rating-only core; NOT the complete historical OG."""
    tempo = (float(away["AdjT"]) + float(home["AdjT"])) / 2.0
    # OG's documented matchup core takes the mean of offense and opposing defense.
    away_eff = (float(away["AdjO"]) + float(home["AdjD"])) / 2.0
    home_eff = (float(home["AdjO"]) + float(away["AdjD"])) / 2.0
    return {
        "away_projected": round(tempo * away_eff / 100.0, 2),
        "home_projected": round(tempo * home_eff / 100.0, 2),
        "tempo": round(tempo, 2),
    }


def ncaab_ats_sandbox_projection(core: dict, home_advantage: float, margin_scale: float) -> dict:
    """Separate, user-adjustable experiment; never modifies OG/core output."""
    baseline_total = core["away_projected"] + core["home_projected"]
    baseline_home_margin = core["home_projected"] - core["away_projected"]
    adjusted_margin = baseline_home_margin * margin_scale + home_advantage
    return {
        "home_projected": round((baseline_total + adjusted_margin) / 2, 2),
        "away_projected": round((baseline_total - adjusted_margin) / 2, 2),
        "tempo": core["tempo"],
    }


def ncaab_saved_projections() -> pd.DataFrame:
    if not NCAAB_PROJECTION_LOG_PATH.exists():
        return pd.DataFrame(columns=NCAAB_PROJECTION_COLUMNS)
    try:
        frame = pd.read_csv(NCAAB_PROJECTION_LOG_PATH, dtype={"game_id": str})
        for col in NCAAB_PROJECTION_COLUMNS:
            if col not in frame.columns:
                frame[col] = pd.NA
        return frame[NCAAB_PROJECTION_COLUMNS]
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame(columns=NCAAB_PROJECTION_COLUMNS)


def ncaab_save_projection_snapshot(rows: list[dict]) -> None:
    NCAAB_PROJECTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    previous = ncaab_saved_projections()
    incoming = pd.DataFrame(rows).reindex(columns=NCAAB_PROJECTION_COLUMNS)
    combined = pd.concat([previous, incoming], ignore_index=True)
    # Keep every timestamped prediction, including subsequent model refinements.
    temp_file = NCAAB_PROJECTION_LOG_PATH.with_suffix(".tmp")
    combined.to_csv(temp_file, index=False)
    os.replace(temp_file, NCAAB_PROJECTION_LOG_PATH)


def ncaab_grade_saved_projections(log: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    if log.empty or games.empty:
        return log
    result = log.copy()
    games_by_id = games.set_index("Event ID")
    for idx, row in result.iterrows():
        game_id = str(row["game_id"])
        if game_id not in games_by_id.index:
            continue
        game = games_by_id.loc[game_id]
        if isinstance(game, pd.DataFrame):
            continue
        if not ("final" in str(game["Status"]).lower()):
            continue
        a = pd.to_numeric(game["Away score"], errors="coerce")
        h = pd.to_numeric(game["Home score"], errors="coerce")
        if pd.isna(a) or pd.isna(h):
            continue
        pred_h = pd.to_numeric(row["home_projected"], errors="coerce")
        pred_a = pd.to_numeric(row["away_projected"], errors="coerce")
        result.at[idx, "actual_away"] = a
        result.at[idx, "actual_home"] = h
        result.at[idx, "actual_total"] = a + h
        result.at[idx, "actual_home_margin"] = h - a
        if pd.notna(pred_h) and pd.notna(pred_a):
            result.at[idx, "winner_correct"] = ((pred_h > pred_a) == (h > a)) if h != a else pd.NA
            result.at[idx, "margin_abs_error"] = abs((pred_h - pred_a) - (h - a))
            result.at[idx, "total_abs_error"] = abs((pred_h + pred_a) - (h + a))
        spread = pd.to_numeric(row["market_home_spread"], errors="coerce")
        side = str(row["ats_side"])
        if pd.notna(spread) and side in ("Home", "Away"):
            cover_margin = h - a + spread
            result.at[idx, "ats_result"] = ("Push" if cover_margin == 0 else
                "Win" if ((cover_margin > 0) == (side == "Home")) else "Loss")
    return result


def render_ncaab_projections(matches: pd.DataFrame, ratings: pd.DataFrame, season: int) -> None:
    st.subheader("Match projections · research preview")
    st.warning(
        "The full historical OG model is NOT reproduced here: its recent-3/Four-Factors "
        "inputs and exact weights are missing. The rating-only core below uses the documented "
        "OG efficiency equation. ATS sandbox is a NEW, separate adjustable test, not the "
        "previously backtested ATS model. Do not compare these previews against old OG/ATS records."
    )
    if matches.empty or ratings.empty:
        st.info("Match list and valid adjusted ratings are both required to calculate previews.")
        return
    with st.expander("ATS sandbox assumptions (research only)", expanded=False):
        home_advantage = st.number_input("Experimental home advantage (points)", min_value=-10.0, max_value=10.0, value=2.5, step=0.5, key="ncaab_ats_hca")
        margin_scale = st.slider("Experimental margin multiplier", min_value=0.5, max_value=1.2, value=0.85, step=0.05, key="ncaab_ats_multiplier")
        st.caption("These are adjustable experimental assumptions, not calibrated coefficients or original OG settings. Neutral sites are not automatically corrected.")
    rows = []
    missing = []
    for _, game in matches.iterrows():
        away = find_ncaab_rating(ratings, game["Away"], game["Away location"])
        home = find_ncaab_rating(ratings, game["Home"], game["Home location"])
        if away.empty or home.empty:
            missing.append(f"{game['Away']} @ {game['Home']}")
            continue
        core = ncaab_rating_core_projection(away.iloc[0], home.iloc[0])
        ats = ncaab_ats_sandbox_projection(core, home_advantage, margin_scale)
        for model, projection in (("OG rating core · incomplete", core), ("ATS sandbox · experimental", ats)):
            a = projection["away_projected"]
            h = projection["home_projected"]
            rows.append({
                "Event ID": game["Event ID"], "Start (Sweden)": game["Start (Sweden)"],
                "Away": game["Away"], "Home": game["Home"], "Model": model,
                "Away projected": round(a, 1), "Home projected": round(h, 1),
                "Total": round(a + h, 1), "Home margin": round(h - a, 1),
                "Winner": game["Home"] if h > a else game["Away"] if a > h else "Even",
                "Tempo": projection["tempo"],
            })
    if missing:
        with st.expander(f"Unmatched teams · {len(missing)} games"):
            st.write("These games were skipped, not assigned estimated ratings:")
            st.write(missing)
    if not rows:
        st.info("No games have both teams matched to valid ratings.")
        return
    projections = pd.DataFrame(rows)
    selected_game = st.selectbox(
        "Select game to compare models", sorted(projections["Event ID"].unique()),
        format_func=lambda gid: f"{matches[matches['Event ID'] == gid].iloc[0]['Away']} @ {matches[matches['Event ID'] == gid].iloc[0]['Home']}",
        key="ncaab_prediction_game",
    )
    selected_predictions = projections[projections["Event ID"] == selected_game]
    st.dataframe(selected_predictions.drop(columns=["Event ID"]), hide_index=True, use_container_width=True)
    st.caption("A lower AdjD is better. All outputs use same-snapshot ratings; they are not historical backtests.")
    with st.expander("Market comparison & timestamped tracking", expanded=False):
        spread = st.number_input("Market HOME spread (e.g. -6.5 for home favorite)", value=0.0, step=0.5, key="ncaab_market_home_spread")
        include_spread = st.checkbox("Market spread entered / verified", value=False, key="ncaab_market_spread_valid")
        total_line = st.number_input("Market game total", value=140.0, step=0.5, key="ncaab_market_total")
        include_total = st.checkbox("Market total entered / verified", value=False, key="ncaab_market_total_valid")
        snapshot_records = []
        for _, pred in selected_predictions.iterrows():
            margin = float(pred["Home margin"])
            edge = margin + spread if include_spread else float("nan")
            ats_side = "Home" if edge > 0 else "Away" if edge < 0 else "Push/Even"
            if not include_spread:
                ats_side = "Not set"
            if include_spread:
                st.write(f"**{pred['Model']}** · {ats_side} ATS · projected cushion {abs(edge):.1f} pts")
            snapshot_records.append({
                "saved_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "game_id": str(pred["Event ID"]), "game_start_sweden": pred["Start (Sweden)"],
                "season": season, "away": pred["Away"], "home": pred["Home"],
                "ratings_source": str(ratings["Source"].iloc[0]) if "Source" in ratings else "Unspecified",
                "ratings_as_of": str(ratings["AsOf"].iloc[0]) if "AsOf" in ratings else "Unspecified",
                "model": pred["Model"], "away_projected": pred["Away projected"],
                "home_projected": pred["Home projected"], "total_projected": pred["Total"],
                "home_margin_projected": pred["Home margin"],
                "market_home_spread": spread if include_spread else float("nan"),
                "market_total": total_line if include_total else float("nan"),
                "ats_side": ats_side, "ats_edge": edge,
            })
        if st.button("Save timestamped projections", key="ncaab_save_projection"):
            start = pd.to_datetime(selected_predictions.iloc[0]["Start (Sweden)"], errors="coerce")
            current = pd.Timestamp.now(tz="Europe/Stockholm").tz_localize(None)
            if pd.isna(start) or start <= current:
                st.error("Cannot save as a pregame prediction: this game's scheduled start has passed.")
            else:
                ncaab_save_projection_snapshot(snapshot_records)
                st.success("Saved both experimental preview outputs with timestamp; historical OG and ATS remain untouched.")
    log = ncaab_saved_projections()
    if not log.empty:
        st.subheader("Saved prediction history")
        graded = ncaab_grade_saved_projections(log, matches)
        st.dataframe(graded.tail(100), hide_index=True, use_container_width=True)
        if st.button("Save final scores for displayed games", key="ncaab_grade_save"):
            temp = NCAAB_PROJECTION_LOG_PATH.with_suffix(".tmp")
            graded.to_csv(temp, index=False)
            os.replace(temp, NCAAB_PROJECTION_LOG_PATH)
            st.success("Final results updated for games loaded on the selected scoreboard date.")



def ncaab_category_regions(fig, data, x_key, y_key, mode):
    """Descriptive chart zones, derived solely from the displayed sample."""
    x = pd.to_numeric(data[x_key], errors="coerce").dropna()
    y = pd.to_numeric(data[y_key], errors="coerce").dropna()
    if len(x) < 2 or len(y) < 2:
        return ""
    def bounds(values):
        lo, hi = float(values.min()), float(values.max())
        pad = max((hi - lo) * .08, .02)
        return lo - pad, hi + pad
    x0, x1 = bounds(x)
    y0, y1 = bounds(y)
    if mode == "net":
        cuts = [float(y.quantile(q)) for q in (.2, .4, .6, .8)]
        edges = [y0] + cuts + [y1]
        names = ["Below Average", "Developing", "Average", "Great", "Elite"]
        colors = ["rgba(239,68,68,.085)", "rgba(249,115,22,.07)",
                  "rgba(148,163,184,.06)", "rgba(34,197,94,.065)", "rgba(45,212,191,.10)"]
        for i, name in enumerate(names):
            if edges[i+1] <= edges[i]:
                continue
            fig.add_hrect(y0=edges[i], y1=edges[i+1], fillcolor=colors[i], line_width=0, layer="below")
            fig.add_annotation(x=.99, y=(edges[i]+edges[i+1])/2, xref="paper", yref="y",
                               text=name, showarrow=False, xanchor="right",
                               font=dict(color="#cbd5e1", size=11),
                               bgcolor="rgba(7,13,24,.58)")
        return "Net-rating categories are sample quintiles (20% each), not fixed NCAA benchmarks."
    xmid, ymid = float(x.median()), float(y.median())
    # Quadrants are descriptive; dependence and volatility are not quality scores.
    if mode == "volatility":
        cells = [
            (x0,xmid,y0,ymid,"Consistent / Lower Rated","rgba(148,163,184,.075)"),
            (xmid,x1,y0,ymid,"Consistently Strong","rgba(34,197,94,.09)"),
            (x0,xmid,ymid,y1,"Volatile / Lower Rated","rgba(249,115,22,.09)"),
            (xmid,x1,ymid,y1,"Strong but Volatile","rgba(239,68,68,.08)"),
        ]
    elif mode == "shooting":
        cells = [
            (x0,xmid,y0,ymid,"Low Volume / Low Accuracy","rgba(239,68,68,.08)"),
            (xmid,x1,y0,ymid,"High Volume / Low Accuracy","rgba(249,115,22,.10)"),
            (x0,xmid,ymid,y1,"Selective & Accurate","rgba(34,197,94,.08)"),
            (xmid,x1,ymid,y1,"High Volume & Accurate","rgba(45,212,191,.09)"),
        ]
    elif mode == "threes":
        cells = [
            (x0,xmid,y0,ymid,"Low 3P Share / Negative Edge","rgba(148,163,184,.07)"),
            (xmid,x1,y0,ymid,"Low 3P Share / Positive Edge","rgba(34,197,94,.08)"),
            (x0,xmid,ymid,y1,"High 3P Share / Negative Edge","rgba(239,68,68,.09)"),
            (xmid,x1,ymid,y1,"High 3P Share / Positive Edge","rgba(45,212,191,.08)"),
        ]
    elif mode == "paint":
        cells = [
            (x0,xmid,y0,ymid,"Low Paint Production","rgba(239,68,68,.075)"),
            (xmid,x1,y0,ymid,"Productive / Mixed Scoring","rgba(34,197,94,.08)"),
            (x0,xmid,ymid,y1,"Paint Reliant / Low Output","rgba(249,115,22,.09)"),
            (xmid,x1,ymid,y1,"Paint-Focused & Productive","rgba(45,212,191,.09)"),
        ]
    else:
        return ""
    for xa, xb, ya, yb, label, color in cells:
        fig.add_shape(type="rect", x0=xa, x1=xb, y0=ya, y1=yb,
                      xref="x", yref="y", fillcolor=color, line_width=0, layer="below")
        fig.add_annotation(x=(xa+xb)/2, y=(ya+yb)/2, xref="x", yref="y",
                           text=label, showarrow=False, font=dict(size=10,color="#cbd5e1"),
                           bgcolor="rgba(7,13,24,.66)")
    return "Areas are defined by the displayed sample medians, not fixed NCAA-wide ratings or betting recommendations."


def render_ncaab_pace_net_chart(ratings: pd.DataFrame, season: int) -> None:
    """Interactive team-level adjusted tempo vs adjusted net rating."""
    st.subheader("Pace vs Net Rating • opponent-adjusted")
    st.caption("X = AdjT (adjusted possessions / 40 min) · Y = AdjO − AdjD (points / 100 possessions). All values come from the selected ratings snapshot.")

    chart_data = ratings.copy()
    for field in ("AdjO", "AdjD", "AdjT"):
        chart_data[field] = pd.to_numeric(chart_data[field], errors="coerce")
    chart_data = chart_data.dropna(subset=["Team", "AdjO", "AdjD", "AdjT"]).copy()
    chart_data["Net Rating"] = chart_data["AdjO"] - chart_data["AdjD"]
    if len(chart_data) < 2:
        st.info("At least two valid team ratings are required to draw this chart.")
        return

    team_list = sorted(chart_data["Team"].astype(str).unique().tolist())
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        highlighted = st.multiselect("Highlight teams", team_list, default=[], key="ncaab_pace_highlight")
    with c2:
        label_mode = st.selectbox("Team labels", ["Highlighted only", "Top net rating", "All teams", "None"], key="ncaab_pace_labels")
    with c3:
        elite_zone = st.checkbox("Show category regions", value=True, key="ncaab_pace_elite")

    pace_mid = float(chart_data["AdjT"].median())
    net_mid = float(chart_data["Net Rating"].median())
    pace_min, pace_max = float(chart_data["AdjT"].min()), float(chart_data["AdjT"].max())
    net_min, net_max = float(chart_data["Net Rating"].min()), float(chart_data["Net Rating"].max())
    pad_x = max(0.8, (pace_max - pace_min) * 0.07)
    pad_y = max(1.5, (net_max - net_min) * 0.07)
    x_low, x_high = pace_min - pad_x, pace_max + pad_x
    y_low, y_high = net_min - pad_y, net_max + pad_y

    fig = go.Figure()
    if elite_zone:
        zone_note = ncaab_category_regions(fig, chart_data, "AdjT", "Net Rating", "net")
    else:
        zone_note = "Category shading hidden."

    fig.add_vline(x=pace_mid, line_color="rgba(148,163,184,0.6)", line_width=1)
    fig.add_hline(y=net_mid, line_color="rgba(148,163,184,0.6)", line_width=1)
    ordinary = chart_data[~chart_data["Team"].isin(highlighted)].copy()
    special = chart_data[chart_data["Team"].isin(highlighted)].copy()

    def add_points(df: pd.DataFrame, selected: bool) -> None:
        if df.empty:
            return
        if label_mode == "All teams":
            labels = df["Team"].tolist()
        elif label_mode == "Top net rating":
            top_teams = set(chart_data.nlargest(15, "Net Rating")["Team"])
            labels = [name if name in top_teams else "" for name in df["Team"]]
        elif label_mode == "Highlighted only":
            labels = df["Team"].tolist() if selected else [""] * len(df)
        else:
            labels = [""] * len(df)
        fig.add_trace(go.Scatter(
            x=df["AdjT"], y=df["Net Rating"], mode="markers+text",
            text=labels, textposition="top center",
            textfont=dict(size=10 if not selected else 12, color="#e2e8f0"),
            marker=dict(size=16 if selected else 9, color="#fbbf24" if selected else "#38bdf8",
                        opacity=1 if selected else 0.70, line=dict(color="#ffffff" if selected else "#1e293b", width=2 if selected else 0.5)),
            customdata=df[["Team", "AdjO", "AdjD"]].to_numpy(),
            hovertemplate=("<b>%{customdata[0]}</b><br>AdjT: %{x:.1f}<br>Adj Net: %{y:+.1f}"
                           "<br>AdjO: %{customdata[1]:.1f}<br>AdjD: %{customdata[2]:.1f}<extra></extra>"),
            name="Highlighted" if selected else "Division I", showlegend=True,
        ))

    add_points(ordinary, False)
    add_points(special, True)
    fig.update_layout(
        template="plotly_dark", height=650, margin=dict(l=25, r=25, t=40, b=30),
        title=dict(text=f"{season - 1}–{str(season)[-2:]} Men's Division I | {len(chart_data)} teams", font=dict(size=16)),
        xaxis=dict(title="Adjusted Pace (AdjT)", range=[x_low, x_high], gridcolor="rgba(148,163,184,0.17)", zeroline=False),
        yaxis=dict(title="Adjusted Net Rating (AdjO − AdjD)", range=[y_low, y_high], gridcolor="rgba(148,163,184,0.17)", zeroline=False),
        legend=dict(orientation="h", y=1.04, x=0),
        paper_bgcolor="#070d18", plot_bgcolor="#0b1220",
    )
    st.plotly_chart(fig, use_container_width=True, key="ncaab_pace_net_chart")
    st.caption(f"Reference lines: AdjT median {pace_mid:.1f}, net median {net_mid:+.1f}. {zone_note}")



# Descriptive consistency research; NOT EvanMiya's proprietary Volatility Score.
# The adjusted snapshot is CURRENT and must never be treated as pregame ratings.
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_ncaab_completed_games(start_day: str, end_day: str) -> pd.DataFrame:
    """Fetch completed NCAA D-I games day-by-day; ESPN may reject ranged dates."""
    start = pd.Timestamp(start_day).normalize()
    end = pd.Timestamp(end_day).normalize()
    if end < start:
        return pd.DataFrame()
    rows = []
    current_day = start
    while current_day <= end:
        # The ESPN v2 scoreboard commonly accepts a single YYYYMMDD date;
        # YYYYMMDD-YYYYMMDD date ranges can return HTTP 400.
        period = f"{current_day:%Y%m%d}"
        limit = 500
        response = requests.get(
            ESPN_NCAAB_SCOREBOARD_URL,
            params={"dates": period, "groups": 50, "limit": limit},
            timeout=35,
        )
        response.raise_for_status()
        events = response.json().get("events", [])
        if not isinstance(events, list):
            raise ValueError(f"Unexpected ESPN events payload for {period}")
        if len(events) >= limit:
            raise ValueError(f"ESPN returned {limit} events for {period}; refusing potentially incomplete sample")
        for event in events:
            competition = (event.get("competitions") or [{}])[0]
            status = (event.get("status") or {}).get("type") or {}
            if not status.get("completed"):
                continue
            opponents = competition.get("competitors") or []
            home = next((x for x in opponents if x.get("homeAway") == "home"), None)
            away = next((x for x in opponents if x.get("homeAway") == "away"), None)
            if home is None or away is None:
                continue
            try:
                home_pts = float(home["score"])
                away_pts = float(away["score"])
            except (KeyError, TypeError, ValueError):
                continue
            rows.append({
                "game_id": str(event.get("id", "")),
                "date": str(event.get("date", "")),
                "home": (home.get("team") or {}).get("displayName", ""),
                "away": (away.get("team") or {}).get("displayName", ""),
                "home_location": (home.get("team") or {}).get("location", ""),
                "away_location": (away.get("team") or {}).get("location", ""),
                "home_pts": home_pts,
                "away_pts": away_pts,
                "neutral_site": bool(competition.get("neutralSite", False)),
            })
        current_day += pd.Timedelta(days=1)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["game_id"], keep="last")


def ncaab_volatility_results(games: pd.DataFrame, ratings: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a reproducible, descriptive per-team residual SD in points/100 estimated possessions."""
    if games.empty or ratings.empty:
        return pd.DataFrame(), pd.DataFrame()
    current = ratings.copy()
    for col in ("AdjO", "AdjD", "AdjT"):
        current[col] = pd.to_numeric(current[col], errors="coerce")
    current = current.dropna(subset=["Team", "AdjO", "AdjD", "AdjT"])
    current = current[current["AdjT"] > 0].copy()
    current["net"] = current["AdjO"] - current["AdjD"]
    # Both full ESPN names and city/location aliases are checked with the same
    # strict lookup used elsewhere. Do not fuzzy-assign ambiguous team names.
    lookup = {}
    for _, rating in current.iterrows():
        key = ncaab_team_key(rating["Team"])
        lookup.setdefault(key, []).append(rating)
    def find(team, location):
        candidates = [ncaab_team_key(location), ncaab_team_key(team)]
        candidates += [NCAAB_TEAM_ALIASES.get(k, k) for k in candidates]
        for key in dict.fromkeys(candidates):
            found = lookup.get(key, [])
            if len(found) == 1:
                return found[0]
        return None

    observations = []
    matched_games = 0
    for _, game in games.iterrows():
        home = find(game["home"], game["home_location"])
        away = find(game["away"], game["away_location"])
        if home is None or away is None or home["Team"] == away["Team"]:
            continue
        possessions = (float(home["AdjT"]) + float(away["AdjT"])) / 2.0
        if possessions <= 0:
            continue
        # No fabricated matchup injury or home adjustment. We compare the
        # observed point margin to the difference between CURRENT adjusted nets.
        actual_margin_per_100 = (game["home_pts"] - game["away_pts"]) * 100.0 / possessions
        expected_margin_per_100 = float(home["net"]) - float(away["net"])
        residual = actual_margin_per_100 - expected_margin_per_100
        matched_games += 1
        for team, opponent, deviation, margin in (
            (home, away, residual, float(game["home_pts"] - game["away_pts"])),
            (away, home, -residual, float(game["away_pts"] - game["home_pts"])),
        ):
            observations.append({
                "Team": str(team["Team"]), "Opponent": str(opponent["Team"]),
                "Game": game["game_id"], "Date": game["date"],
                "Residual / 100": deviation, "Margin": margin,
                "Adj Net": float(team["net"]), "AdjT": float(team["AdjT"]),
            })
    if not observations:
        return pd.DataFrame(), pd.DataFrame()
    detail = pd.DataFrame(observations)
    summary = (detail.groupby("Team", as_index=False)
               .agg(Games=("Game", "nunique"),
                    Volatility=("Residual / 100", "std"),
                    **{"Avg abs deviation": ("Residual / 100", lambda x: x.abs().mean()),
                       "Mean deviation": ("Residual / 100", "mean"),
                       "Adj Net": ("Adj Net", "first")}))
    summary["Coverage"] = f"{matched_games} matched games / {len(games)} completed"
    return summary, detail


def render_ncaab_volatility_chart(ratings: pd.DataFrame, season: int, date_value) -> None:
    st.subheader("Consistency vs Volatility • independent research")
    st.caption("X = current AdjO − AdjD. Y = sample standard deviation of game-by-game adjusted-margin residuals (points / 100 **estimated** possessions). Lower means more consistent.")
    controls = st.columns([1, 1, 2])
    with controls[0]:
        window_days = st.selectbox("History window", [14, 30, 60], index=1, key="ncaab_vol_window")
    with controls[1]:
        min_games = st.selectbox("Minimum games", [3, 5, 8], index=1, key="ncaab_vol_games")
    with controls[2]:
        reload_history = st.button("↻ Refresh completed games", key="ncaab_vol_refresh")
    if reload_history:
        fetch_ncaab_completed_games.clear()
    # Historical season starts in autumn; don't request last season's games or
    # use match results from dates later than the selected scoreboard date.
    requested = pd.Timestamp(date_value).normalize()
    today = pd.Timestamp.now(tz="Europe/Stockholm").tz_localize(None).normalize()
    cutoff = min(requested, today)
    season_start = pd.Timestamp(year=season - 1, month=11, day=1)
    start = max(season_start, cutoff - pd.Timedelta(days=window_days - 1))
    if cutoff < start:
        st.info("No completed current-season games are available before this date.")
        return
    try:
        with st.spinner("Loading completed NCAA games from ESPN..."):
            games = fetch_ncaab_completed_games(str(start.date()), str(cutoff.date()))
    except (requests.RequestException, ValueError, KeyError) as exc:
        st.warning(f"Completed-game history unavailable: {exc}. No substitute volatility scores are generated.")
        return
    if games.empty:
        st.info("No completed games returned for this period.")
        return
    summary, detail = ncaab_volatility_results(games, ratings)
    if summary.empty:
        st.info("No games could be matched to both teams' adjusted ratings. No scores are inferred.")
        return
    enough = summary[(summary["Games"] >= min_games) & summary["Volatility"].notna()].copy()
    a, b, c = st.columns(3)
    a.metric("Completed games fetched", len(games))
    b.metric("Games matched to both teams", len(detail) // 2)
    c.metric(f"Teams with ≥{min_games} games", len(enough))
    if enough.empty:
        st.info(f"No teams have {min_games} matched games yet. Lower the minimum or select a longer window.")
        return
    selected = st.multiselect("Highlight teams", sorted(enough["Team"].tolist()), key="ncaab_vol_highlight")
    cutoff_strength = float(enough["Adj Net"].quantile(0.75))
    cutoff_vol = float(enough["Volatility"].median())
    fig = go.Figure()
    zone_note = ncaab_category_regions(fig, enough, "Adj Net", "Volatility", "volatility")
    def plot_points(df, highlighted):
        if df.empty:
            return
        fig.add_trace(go.Scatter(
            x=df["Adj Net"], y=df["Volatility"], mode="markers+text",
            text=df["Team"].tolist() if highlighted else [""] * len(df),
            textposition="top center",
            marker=dict(size=16 if highlighted else 9,
                        color="#fbbf24" if highlighted else "#38bdf8",
                        opacity=1 if highlighted else 0.72,
                        line=dict(color="#fff" if highlighted else "#1e293b", width=2 if highlighted else 0.5)),
            customdata=df[["Team", "Games", "Avg abs deviation", "Mean deviation"]].to_numpy(),
            hovertemplate=("<b>%{customdata[0]}</b><br>Adj net: %{x:+.1f}"
                           "<br>Residual SD: %{y:.1f}<br>Games: %{customdata[1]}"
                           "<br>Mean absolute residual: %{customdata[2]:.1f}"
                           "<br>Mean signed residual: %{customdata[3]:+.1f}<extra></extra>"),
            name="Highlighted" if highlighted else "Teams", showlegend=True,
        ))
    plot_points(enough[~enough["Team"].isin(selected)], False)
    plot_points(enough[enough["Team"].isin(selected)], True)
    fig.add_vline(x=cutoff_strength, line_dash="dash", line_color="rgba(148,163,184,0.6)")
    fig.add_hline(y=cutoff_vol, line_dash="dash", line_color="rgba(148,163,184,0.6)")
    fig.update_layout(
        template="plotly_dark", height=630, margin=dict(l=20, r=20, t=45, b=25),
        title=dict(text=f"{season-1}–{str(season)[-2:]} • {start:%b %d} to {cutoff:%b %d} • {len(enough)} teams", font=dict(size=16)),
        xaxis=dict(title="Adjusted net rating (AdjO − AdjD)", gridcolor="rgba(148,163,184,0.17)"),
        yaxis=dict(title="Game-to-game residual volatility (SD / 100 estimated possessions)", gridcolor="rgba(148,163,184,0.17)", rangemode="tozero"),
        paper_bgcolor="#070d18", plot_bgcolor="#0b1220",
    )
    st.plotly_chart(fig, use_container_width=True, key="ncaab_volatility_chart")
    st.caption(f"Guides: Adj Net and volatility medians define the four quadrants. {zone_note} This is not EvanMiya\u2019s proprietary score.")
    with st.expander("Method, limitations & team-by-team game deviations", expanded=False):
        st.markdown(
            "**Method:** For each completed game, observed margin × 100 / average current AdjT "
            "minus (team current Adj Net − opponent current Adj Net). Volatility is the sample "
            "standard deviation of these residuals across the selected games. "
            "This is an **approximation** because actual possessions are not available from ESPN scoreboards. "
            "Ratings are a **current snapshot**, not historical pregame ratings. "
            "Game dates, opponents, injuries, home advantage and overtime are not controlled; "
            "small samples can be unstable. It must not be used as a pregame backtest or OG/ATS input. "
            "The pictured EvanMiya volatility metric uses a different, unverified proprietary calculation."
        )
        st.dataframe(enough.sort_values(["Adj Net", "Volatility"], ascending=[False, True]),
                     use_container_width=True, hide_index=True)
        if selected:
            st.dataframe(detail[detail["Team"].isin(selected)].sort_values("Date", ascending=False),
                         use_container_width=True, hide_index=True)

# Independent descriptive shooting and paint analysis. These metrics require
# verified box-score totals and must not be inferred from adjusted efficiencies.
NCAAB_STYLE_STATS_PATH = APP_DIR / "data" / "ncaab_style_stats.csv"
NCAAB_STYLE_REQUIRED = [
    "Team", "FGA", "3PA", "3PM", "Opponent3PM", "Points", "PaintPoints", "Possessions"
]


def clean_ncaab_style_stats(raw: pd.DataFrame, season: int) -> pd.DataFrame:
    """Validate season-level aggregates without inventing missing box-score stats."""
    missing = [c for c in NCAAB_STYLE_REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))
    frame = raw.copy()
    if "Season" not in frame.columns:
        raise ValueError("Season column is required to prevent cross-season mixing.")
    frame["Season"] = pd.to_numeric(frame["Season"], errors="coerce")
    frame = frame[frame["Season"] == int(season)].copy()
    if frame.empty:
        raise ValueError(f"No rows for the selected {season} season.")
    frame["Team"] = frame["Team"].astype(str).str.strip()
    for c in NCAAB_STYLE_REQUIRED[1:]:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    frame = frame.dropna(subset=NCAAB_STYLE_REQUIRED).copy()
    frame = frame[(frame["Team"] != "") & (frame["Team"].str.lower() != "nan")]
    if frame["Team"].duplicated().any():
        raise ValueError("Duplicate team names in season totals; aggregate them before importing.")
    if frame.empty:
        raise ValueError("No complete valid rows in the imported stats.")
    for col in NCAAB_STYLE_REQUIRED[1:]:
        if (frame[col] < 0).any():
            raise ValueError(f"Negative values in {col} are not valid season totals.")
    invalid = (frame["FGA"] <= 0) | (frame["3PA"] > frame["FGA"]) | (frame["3PM"] > frame["3PA"]) | (frame["Points"] <= 0) | (frame["Possessions"] <= 0)
    if invalid.any():
        raise ValueError("Invalid totals: require FGA/Points/Possessions > 0, 3PM ≤ 3PA ≤ FGA.")
    frame["3PA Rate"] = 100 * frame["3PA"] / frame["FGA"]
    frame["3P %"] = (100 * frame["3PM"] / frame["3PA"].replace(0, float("nan")))
    frame["3P Made Differential"] = frame["3PM"] - frame["Opponent3PM"]
    frame["Points from 3P %"] = 100 * (3 * frame["3PM"]) / frame["Points"]
    frame["Paint / 100 Poss"] = 100 * frame["PaintPoints"] / frame["Possessions"]
    frame["Paint Points %"] = 100 * frame["PaintPoints"] / frame["Points"]
    if ((frame["Points from 3P %"] > 100.01) | (frame["Paint Points %"] > 100.01)).any():
        raise ValueError("Some rows have more points from threes/paint than total points. Check units and totals.")
    return frame.reset_index(drop=True)


def load_ncaab_style_stats(season: int) -> pd.DataFrame:
    if not NCAAB_STYLE_STATS_PATH.exists():
        return pd.DataFrame()
    try:
        return clean_ncaab_style_stats(pd.read_csv(NCAAB_STYLE_STATS_PATH), season)
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()


def render_ncaab_style_scatter(
    data: pd.DataFrame, x_key: str, y_key: str, heading: str,
    x_title: str, y_title: str, highlighted: list[str], season: int,
    percent_x: bool = False, percent_y: bool = False,
) -> None:
    st.markdown(f"#### {heading}")
    subset = data.dropna(subset=[x_key, y_key]).copy()
    if len(subset) < 2:
        st.info("At least two teams with complete figures are needed for this chart.")
        return
    fig = go.Figure()
    mid_x, mid_y = float(subset[x_key].median()), float(subset[y_key].median())
    mode = ("shooting" if x_key == "3PA Rate" else
            "threes" if "3P Made Differential" in x_key else
            "paint" if "Paint" in x_key else "")
    zone_note = ncaab_category_regions(fig, subset, x_key, y_key, mode)
    fig.add_vline(x=mid_x, line=dict(color="rgba(148,163,184,0.55)", dash="dash", width=1))
    fig.add_hline(y=mid_y, line=dict(color="rgba(148,163,184,0.55)", dash="dash", width=1))
    for selected, group_label, color, size in [
        (False, "Other teams", "#38bdf8", 9),
        (True, "Highlighted", "#fbbf24", 17),
    ]:
        part = subset[subset["Team"].isin(highlighted) == selected]
        if part.empty:
            continue
        fig.add_trace(go.Scatter(
            x=part[x_key], y=part[y_key], mode="markers+text",
            text=part["Team"] if selected else None,
            textposition="top center", textfont=dict(color="#f8fafc", size=11),
            customdata=part[["Team"]].to_numpy(),
            marker=dict(size=size, color=color, opacity=1 if selected else .68,
                        line=dict(width=1 if selected else 0, color="#ffffff")),
            name=group_label,
            hovertemplate=("<b>%{customdata[0]}</b><br>" + x_title + ": %{x:.1f}" + ("%" if percent_x else "") +
                           "<br>" + y_title + ": %{y:.1f}" + ("%" if percent_y else "") + "<extra></extra>"),
        ))
    fig.update_layout(
        template="plotly_dark", height=530,
        margin=dict(l=35, r=25, t=35, b=40),
        title=f"{season-1}–{str(season)[-2:]} | {len(subset)} teams",
        xaxis=dict(title=x_title, gridcolor="rgba(148,163,184,.15)", ticksuffix="%" if percent_x else ""),
        yaxis=dict(title=y_title, gridcolor="rgba(148,163,184,.15)", ticksuffix="%" if percent_y else ""),
        paper_bgcolor="#070d18", plot_bgcolor="#0b1220",
        legend=dict(orientation="h", y=1.06, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Dashed lines indicate medians for the {len(subset)} displayed teams. {zone_note}")


# TeamRankings publishes per-game shooting stats on team-stat pages. Its terms
# do not authorize bulk automated ingestion, so users can enter/export authorized
# summaries. This is deliberately NOT used as an OG/ATS input.
NCAAB_TR_STYLE_PATH = APP_DIR / "data" / "ncaab_teamrankings_per_game.csv"
NCAAB_TR_REQUIRED = [
    "Season", "Team", "Games", "FGA_per_game", "3PA_per_game",
    "3PM_per_game", "Opponent3PM_per_game", "Points_per_game",
]
NCAAB_TR_TEMPLATE = (
    "Season,Team,Games,FGA_per_game,3PA_per_game,3PM_per_game,"
    "Opponent3PM_per_game,Points_per_game,PaintPoints_per_game,Possessions_per_game\n"
)


def clean_ncaab_tr_per_game(source: pd.DataFrame, season: int) -> pd.DataFrame:
    missing = [c for c in NCAAB_TR_REQUIRED if c not in source.columns]
    if missing:
        raise ValueError("Missing TeamRankings per-game columns: " + ", ".join(missing))
    frame = source.copy()
    for col in [c for c in NCAAB_TR_REQUIRED if c not in ("Season", "Team")]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in ("PaintPoints_per_game", "Possessions_per_game"):
        if col not in frame:
            frame[col] = float("nan")
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["Season"] = pd.to_numeric(frame["Season"], errors="coerce")
    frame = frame.loc[frame["Season"] == season].copy()
    frame["Team"] = frame["Team"].astype(str).str.strip()
    frame = frame.dropna(subset=NCAAB_TR_REQUIRED)
    if frame.empty:
        raise ValueError(f"No complete rows for season {season}.")
    if frame["Team"].eq("").any() or frame["Team"].duplicated().any():
        raise ValueError("Team names must be populated and unique.")
    if ((frame["Games"] < 1) | (frame["Games"] % 1 != 0)).any():
        raise ValueError("Games must be a positive whole number for every team.")
    if (frame[["FGA_per_game", "3PA_per_game", "3PM_per_game", "Opponent3PM_per_game", "Points_per_game"]] < 0).any().any():
        raise ValueError("Per-game stats cannot be negative.")
    if ((frame["FGA_per_game"] <= 0) |
        (frame["3PA_per_game"] > frame["FGA_per_game"]) |
        (frame["3PM_per_game"] > frame["3PA_per_game"]) |
        (frame["Points_per_game"] <= 0) |
        (3 * frame["3PM_per_game"] > frame["Points_per_game"] + .05)).any():
        raise ValueError("Impossible FGA, 3PA, 3PM or scoring values.")
    frame["3PA Rate"] = 100 * frame["3PA_per_game"] / frame["FGA_per_game"]
    frame["3P %"] = 100 * frame["3PM_per_game"] / frame["3PA_per_game"].replace(0, float("nan"))
    frame["3P Made Differential"] = frame["Games"] * (frame["3PM_per_game"] - frame["Opponent3PM_per_game"])
    frame["3P Made Differential / Game"] = frame["3PM_per_game"] - frame["Opponent3PM_per_game"]
    frame["Points from 3P %"] = 300 * frame["3PM_per_game"] / frame["Points_per_game"]
    # Paint is genuinely missing from TeamRankings team stats: never use two-point
    # points as a substitute for points in the paint.
    usable_paint = ((frame["PaintPoints_per_game"] >= 0) &
                    (frame["Possessions_per_game"] > 0) &
                    (frame["PaintPoints_per_game"] <= frame["Points_per_game"] + .05))
    frame["Paint / 100 Poss"] = (100 * frame["PaintPoints_per_game"] /
                                  frame["Possessions_per_game"]).where(usable_paint)
    frame["Paint Points %"] = (100 * frame["PaintPoints_per_game"] /
                                 frame["Points_per_game"]).where(usable_paint)
    frame["Source"] = "TeamRankings-style per-game values (user supplied)"
    return frame.reset_index(drop=True)


def render_ncaab_teamrankings_import(season: int) -> None:
    st.subheader("TeamRankings shooting profiles")
    st.caption("3P data can be entered using TeamRankings' per-game field names. Automated bulk scraping is not enabled. These charts do not affect OG or ATS.")
    st.markdown("[TeamRankings NCAAB team statistics](https://www.teamrankings.com/ncaa-basketball/team/maryland-terrapins/stats) · [TeamRankings terms](https://www.teamrankings.com/terms-of-service/)")
    with st.expander("Import per-game shooting values from an authorized CSV", expanded=False):
        st.write("Include **Games** and use the same season and snapshot date for every team. Values shown on TeamRankings team pages include FGA/Game, 3PA/Game, 3PM/Game, Opp 3PM/Game and Points/Game. Add paint points and possessions only if sourced separately.")
        st.download_button("Download TeamRankings-format CSV template", NCAAB_TR_TEMPLATE.encode("utf-8"),
                           "ncaab_teamrankings_per_game_template.csv", "text/csv", key="ncaab_tr_template")
        upload = st.file_uploader("TeamRankings-format shooting CSV", type="csv", key="ncaab_tr_upload")
        if upload is not None:
            try:
                parsed = clean_ncaab_tr_per_game(pd.read_csv(upload), season)
                st.success(f"Validated {len(parsed)} teams")
                st.dataframe(parsed[["Team", "Games", "3PA Rate", "3P %", "3P Made Differential / Game", "Points from 3P %"]].head(15),
                             use_container_width=True, hide_index=True)
                if st.button("Save per-game shooting statistics", key="ncaab_tr_save"):
                    NCAAB_TR_STYLE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    tmp = NCAAB_TR_STYLE_PATH.with_suffix(".tmp")
                    parsed[NCAAB_TR_REQUIRED + ["PaintPoints_per_game", "Possessions_per_game"]].to_csv(tmp, index=False)
                    os.replace(tmp, NCAAB_TR_STYLE_PATH)
                    st.rerun()
            except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
                st.error(f"Cannot import per-game values: {exc}")
    if not NCAAB_TR_STYLE_PATH.exists():
        st.info("TeamRankings fields are mapped, but no verified per-game CSV has been imported. The existing season-total CSV below remains available.")
        return
    try:
        data = clean_ncaab_tr_per_game(pd.read_csv(NCAAB_TR_STYLE_PATH), season)
    except (ValueError, OSError, pd.errors.ParserError) as exc:
        st.warning(f"Saved TeamRankings-style data unavailable for this season: {exc}")
        return
    highlights = st.multiselect("Highlight teams • per-game data", sorted(data["Team"].unique()), key="ncaab_tr_highlights")
    a,b,c = st.tabs(["3PA rate / accuracy", "3P made differential", "Paint (optional)"])
    with a:
        render_ncaab_style_scatter(data, "3PA Rate", "3P %", "Three-Point Rate vs Accuracy",
                                   "Three-point attempt rate", "3-point percentage", highlights, season, True, True)
    with b:
        render_ncaab_style_scatter(data, "3P Made Differential / Game", "Points from 3P %",
                                   "3P Differential / Game vs Share of Points from Three",
                                   "3PM − Opp 3PM per game", "Share of points from threes", highlights, season, False, True)
        st.caption("Per-game 3P differential is used to compare teams fairly even when game counts differ. Rounded per-game inputs can introduce small errors.")
    with c:
        if data["Paint / 100 Poss"].notna().sum() < 2:
            st.info("TeamRankings team statistics do not supply verified points in the paint. Add PaintPoints_per_game and Possessions_per_game from another source to unlock this graph.")
        else:
            render_ncaab_style_scatter(data, "Paint / 100 Poss", "Paint Points %",
                                       "Paint Scoring per 100 Possessions vs Scoring Share",
                                       "Paint points / 100 possessions", "Paint points share", highlights, season, False, True)
    with st.expander("Imported per-game source values"):
        st.dataframe(data, use_container_width=True, hide_index=True)




# ESPN provides public game box scores, not an official bulk-stats contract.
# Cache valid completed-game rows locally to reduce repeated requests.
ESPN_NCAAB_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
NCAAB_ESPN_BOXSCORE_PATH = APP_DIR / "data" / "ncaab_espn_boxscores.csv"
NCAAB_ESPN_BOX_COLUMNS = ["Season", "GameID", "GameDate", "TeamID", "Team", "OpponentID", "Points", "FGA", "3PA", "3PM", "FTA", "OREB", "TO", "PaintPoints"]


def _ncaab_espn_stat_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _ncaab_espn_shooting_pair(value):
    match = re.fullmatch(r"\s*(\d+)\s*[-/]\s*(\d+)\s*", str(value))
    if not match:
        return None
    made, attempted = map(int, match.groups())
    return (made, attempted) if made <= attempted else None


def _ncaab_espn_team_stat_map(team_row):
    stats = {}
    for item in team_row.get("statistics") or []:
        if not isinstance(item, dict):
            continue
        for key in (item.get("name"), item.get("label"), item.get("displayName"), item.get("abbreviation")):
            if key:
                stats[_ncaab_espn_stat_key(key)] = item.get("displayValue", item.get("value"))
    return stats


def _ncaab_espn_get_stat(stats, *aliases):
    for alias in aliases:
        key = _ncaab_espn_stat_key(alias)
        if key in stats and stats[key] is not None:
            return stats[key]
    return None


def _ncaab_espn_number(value):
    try:
        number = float(str(value).replace(",", "").strip())
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def parse_ncaab_espn_boxscore(payload, season, game_id, game_date):
    """Strictly parse the two team totals from a completed ESPN game summary."""
    boxscore = payload.get("boxscore") or {}
    entries = boxscore.get("teams") or []
    if len(entries) != 2:
        return []
    parsed = []
    for entry in entries:
        team_info = entry.get("team") or {}
        team_id = str(team_info.get("id") or "").strip()
        team_name = str(team_info.get("displayName") or "").strip()
        stats = _ncaab_espn_team_stat_map(entry)
        fg_pair = _ncaab_espn_shooting_pair(_ncaab_espn_get_stat(stats, "fieldGoalsMade-fieldGoalsAttempted", "fieldGoalsMadeAttempted", "fieldGoals", "FG"))
        three_pair = _ncaab_espn_shooting_pair(_ncaab_espn_get_stat(stats, "threePointFieldGoalsMade-threePointFieldGoalsAttempted", "threePointFieldGoalsMadeAttempted", "threePointFieldGoals", "3PT"))
        ft_pair = _ncaab_espn_shooting_pair(_ncaab_espn_get_stat(stats, "freeThrowsMade-freeThrowsAttempted", "freeThrowsMadeAttempted", "freeThrows", "FT"))
        if fg_pair is None:
            fg_m = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "fieldGoalsMade"))
            fg_a = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "fieldGoalsAttempted"))
            if fg_m is not None and fg_a is not None:
                fg_pair = (fg_m, fg_a)
        if three_pair is None:
            th_m = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "threePointFieldGoalsMade"))
            th_a = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "threePointFieldGoalsAttempted"))
            if th_m is not None and th_a is not None:
                three_pair = (th_m, th_a)
        if ft_pair is None:
            ft_m = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "freeThrowsMade"))
            ft_a = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "freeThrowsAttempted"))
            if ft_m is not None and ft_a is not None:
                ft_pair = (ft_m, ft_a)
        oreb = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "offensiveRebounds", "offRebounds", "OREB"))
        to = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "totalTurnovers", "turnovers", "TO"))
        # Paint points are not guaranteed in ESPN's college basketball box score.
        paint = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "pointsInPaint", "paintPoints"))
        if not team_id or not team_name or not fg_pair or not three_pair:
            return []
        if not (0 <= three_pair[0] <= three_pair[1] <= fg_pair[1] and 0 <= fg_pair[0] <= fg_pair[1]):
            return []
        points = _ncaab_espn_number(_ncaab_espn_get_stat(stats, "points"))
        # Boxscore team points might instead be top-level.
        if points is None:
            points = _ncaab_espn_number(entry.get("score"))
        if points is None:
            # Fall back to the completed game's header, if present.
            for comp in (payload.get("header") or {}).get("competitions") or []:
                for competitor in comp.get("competitors") or []:
                    if str((competitor.get("team") or {}).get("id")) == team_id:
                        points = _ncaab_espn_number(competitor.get("score"))
        if points is None or points < 3 * three_pair[0]:
            return []
        parsed.append({"Season": season, "GameID": str(game_id), "GameDate": str(game_date),
                       "TeamID": team_id, "Team": team_name, "OpponentID": "", "Points": points,
                       "FGA": fg_pair[1], "3PA": three_pair[1], "3PM": three_pair[0],
                       "FTA": ft_pair[1] if ft_pair else float("nan"),
                       "OREB": oreb if oreb is not None else float("nan"),
                       "TO": to if to is not None else float("nan"),
                       "PaintPoints": paint if paint is not None and 0 <= paint <= points else float("nan")})
    if parsed[0]["TeamID"] == parsed[1]["TeamID"]:
        return []
    parsed[0]["OpponentID"] = parsed[1]["TeamID"]
    parsed[1]["OpponentID"] = parsed[0]["TeamID"]
    return parsed


def load_ncaab_espn_boxes(season):
    if not NCAAB_ESPN_BOXSCORE_PATH.exists():
        return pd.DataFrame(columns=NCAAB_ESPN_BOX_COLUMNS)
    try:
        df = pd.read_csv(NCAAB_ESPN_BOXSCORE_PATH, dtype={"GameID": str, "TeamID": str, "OpponentID": str})
        if not set(NCAAB_ESPN_BOX_COLUMNS).issubset(df.columns):
            raise ValueError("Invalid ESPN boxscore cache columns")
        df = df.loc[pd.to_numeric(df["Season"], errors="coerce") == season].copy()
        return df.drop_duplicates(["GameID", "TeamID"], keep="last")
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.warning(f"ESPN cache could not be read: {exc}")
        return pd.DataFrame(columns=NCAAB_ESPN_BOX_COLUMNS)


def update_ncaab_espn_boxes(season, completed_games, limit=250):
    """Update only missing games; return (new games, skipped games, errors)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    existing = load_ncaab_espn_boxes(season)
    seen = set(existing["GameID"].astype(str))
    pending = completed_games.loc[~completed_games["game_id"].astype(str).isin(seen)].copy()
    pending = pending.drop_duplicates("game_id").sort_values("date", ascending=False).head(limit)
    skipped = max(0, len(completed_games.drop_duplicates("game_id")) - len(pending) - len(seen.intersection(set(completed_games["game_id"].astype(str)))))
    def fetch_one(game):
        game_id = str(game["game_id"])
        response = requests.get(ESPN_NCAAB_SUMMARY_URL, params={"event": game_id}, timeout=20)
        response.raise_for_status()
        return parse_ncaab_espn_boxscore(response.json(), season, game_id, game["date"])
    added = []
    errors = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_one, game) for _, game in pending.iterrows()]
        for task in as_completed(futures):
            try:
                batch = task.result()
                if len(batch) == 2:
                    added.extend(batch)
                else:
                    errors += 1
            except (requests.RequestException, ValueError, KeyError, TypeError):
                errors += 1
    if added:
        combined = pd.concat([existing, pd.DataFrame(added)], ignore_index=True)
        # Preserve other seasons from disk, if present.
        if NCAAB_ESPN_BOXSCORE_PATH.exists():
            try:
                other = pd.read_csv(NCAAB_ESPN_BOXSCORE_PATH, dtype={"GameID": str, "TeamID": str, "OpponentID": str})
                other = other.loc[pd.to_numeric(other["Season"], errors="coerce") != season]
                combined = pd.concat([other, combined], ignore_index=True)
            except (OSError, ValueError, pd.errors.ParserError):
                pass
        combined = combined.drop_duplicates(["Season", "GameID", "TeamID"], keep="last")
        NCAAB_ESPN_BOXSCORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp = NCAAB_ESPN_BOXSCORE_PATH.with_suffix(".tmp")
        combined[NCAAB_ESPN_BOX_COLUMNS].to_csv(temp, index=False)
        os.replace(temp, NCAAB_ESPN_BOXSCORE_PATH)
    return len(added) // 2, skipped, errors


def ncaab_espn_shooting_summary(boxes, season):
    if boxes.empty:
        return pd.DataFrame()
    raw = boxes.copy()
    for col in ("Points", "FGA", "3PA", "3PM", "FTA", "OREB", "TO", "PaintPoints"):
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw["poss"] = raw["FGA"] - raw["OREB"] + raw["TO"] + 0.475 * raw["FTA"]
    # Only award paint possession stats where paint + all needed possession inputs exist.
    raw.loc[(raw["poss"] <= 0) | (raw["PaintPoints"] > raw["Points"]), "PaintPoints"] = float("nan")
    opponents = raw[["GameID", "TeamID", "3PM"]].rename(columns={"TeamID": "OpponentID", "3PM": "Opponent3PM"})
    raw = raw.merge(opponents, on=["GameID", "OpponentID"], how="inner", validate="many_to_one")
    if raw.empty:
        return pd.DataFrame()
    rows = []
    for (team_id, team), g in raw.groupby(["TeamID", "Team"]):
        games = len(g)
        total_fga, total_3pa = g["FGA"].sum(), g["3PA"].sum()
        points = g["Points"].sum()
        if not games or total_fga <= 0 or total_3pa <= 0 or points <= 0:
            continue
        # Paint metrics use a paint-complete subset; do not divide partial
        # paint totals by the full season's points or possessions.
        paint_games = g.loc[g["PaintPoints"].notna() & g["poss"].notna() & (g["poss"] > 0)]
        paint_value = paint_games["PaintPoints"].sum() if len(paint_games) == games else float("nan")
        poss_value = paint_games["poss"].sum() if len(paint_games) == games else float("nan")
        rows.append({"Season": season, "Team": team, "Games": games,
                     "FGA_per_game": total_fga / games, "3PA_per_game": total_3pa / games,
                     "3PM_per_game": g["3PM"].sum() / games,
                     "Opponent3PM_per_game": g["Opponent3PM"].sum() / games,
                     "Points_per_game": points / games,
                     "PaintPoints_per_game": paint_value / games,
                     "Possessions_per_game": poss_value / games})
    if not rows:
        return pd.DataFrame()
    return clean_ncaab_tr_per_game(pd.DataFrame(rows), season).assign(Source="ESPN completed-game boxscores (automatic)")


NCAAB_ESPN_SYNC_MARKER = APP_DIR / "data" / "ncaab_espn_last_sync.txt"
NCAAB_ESPN_AUTO_SYNC_HOURS = 6


def ncaab_espn_auto_sync_due(season):
    """Only auto-fetch current-season data periodically, not on every Streamlit rerun."""
    now = pd.Timestamp.now(tz="Europe/Stockholm")
    if season != ncaab_season_for_date(now.date()):
        return False
    try:
        timestamp = pd.Timestamp(NCAAB_ESPN_SYNC_MARKER.read_text(encoding="utf-8").strip())
        if timestamp.tzinfo is None:
            return True
        return (now - timestamp).total_seconds() >= NCAAB_ESPN_AUTO_SYNC_HOURS * 3600
    except (OSError, ValueError, TypeError):
        return True


def ncaab_espn_mark_sync_attempt():
    """Throttle automatic attempts even when ESPN has no completed games yet."""
    try:
        NCAAB_ESPN_SYNC_MARKER.parent.mkdir(parents=True, exist_ok=True)
        NCAAB_ESPN_SYNC_MARKER.write_text(pd.Timestamp.now(tz="Europe/Stockholm").isoformat(), encoding="utf-8")
    except OSError:
        pass


def render_ncaab_espn_shooting(season, selected_chart="3PA Rate vs 3P%"):
    st.subheader("ESPN • automatically collected shooting statistics")
    st.caption("Pulls completed-game boxscores, not TeamRankings pages. Independent exploratory charts only; does not change OG or ATS.")
    a, b, c = st.columns([1, 1, 2])
    with a:
        days = st.selectbox("History window (days)", [7, 14, 30], index=0, key="ncaab_espn_shooting_days")
    with b:
        fetch = st.button("↻ Sync ESPN games", key="ncaab_espn_shooting_sync")
        auto_enabled = st.checkbox("Auto-sync every 6 hours", value=True, key="ncaab_espn_auto_sync")
    with c:
        st.caption("ESPN boxscores are cached locally. Auto-sync checks the latest 14 days and only runs when due; manual sync uses the selected history window.")
    auto_fetch = auto_enabled and ncaab_espn_auto_sync_due(season)
    if fetch or auto_fetch:
        if auto_fetch:
            ncaab_espn_mark_sync_attempt()
        sync_days = days if fetch else 14
        cutoff = min(pd.Timestamp.now(tz="Europe/Stockholm").tz_localize(None).normalize(), pd.Timestamp(st.session_state.get("ncaab_selected_date", pd.Timestamp.today())).normalize())
        start = max(pd.Timestamp(season - 1, 11, 1), cutoff - pd.Timedelta(days=sync_days - 1))
        try:
            with st.spinner("Fetching completed games and ESPN box scores..."):
                games = fetch_ncaab_completed_games(str(start.date()), str(cutoff.date()))
                if games.empty:
                    st.info("ESPN returned no completed games for the selected period.")
                else:
                    added, skipped, errors = update_ncaab_espn_boxes(season, games)
                    st.success(f"Stored {added} new games. {errors} missing/failed boxscores. {skipped} beyond sync limit.")
                    if fetch:
                        ncaab_espn_mark_sync_attempt()
        except (requests.RequestException, ValueError, KeyError, OSError) as exc:
            st.error(f"ESPN sync failed: {exc}")
    boxes = load_ncaab_espn_boxes(season)
    if boxes.empty:
        st.info("No cached ESPN games yet. Automatic sync checks periodically, or click 'Sync ESPN games' to retry.")
        return
    # Filter to complete two-team game pairs; the dataframe is historical
    # and never presented as a full-season rating when collection is partial.
    completed_ids = boxes.groupby("GameID")["TeamID"].nunique()
    boxes = boxes.loc[boxes["GameID"].isin(completed_ids[completed_ids == 2].index)]
    st.caption(f"ESPN sample: {boxes['GameID'].nunique()} completed games across {boxes['TeamID'].nunique()} teams; {boxes['GameDate'].min()[:10]} to {boxes['GameDate'].max()[:10]}. This is NOT necessarily the entire season.")
    summary = ncaab_espn_shooting_summary(boxes, season)
    if summary.empty:
        st.info("ESPN did not supply enough complete shooting data to draw the charts.")
        return
    min_games = st.selectbox("Minimum games in synced sample", [1, 2, 3, 5], index=1, key="ncaab_espn_shoot_min")
    shown = summary[summary["Games"] >= min_games].copy()
    if len(shown) < 2:
        st.info("Not enough teams meet the minimum number of games yet.")
        return
    selected = st.multiselect("Highlight teams • ESPN", sorted(shown["Team"].tolist()), key="ncaab_espn_shoot_highlight")
    if selected_chart == "3PA Rate vs 3P%":
        render_ncaab_style_scatter(shown, "3PA Rate", "3P %", "3PA Rate vs Shooting Accuracy (ESPN)", "3PA / FGA", "3PM / 3PA", selected, season, True, True)
    elif selected_chart == "3P Differential":
        render_ncaab_style_scatter(shown, "3P Made Differential / Game", "Points from 3P %", "3P Made Differential vs Scoring Share (ESPN)", "3PM − Opp 3PM / game", "% points from threes", selected, season, False, True)
    elif selected_chart == "Points in the Paint":
        verified_paint_games = boxes.loc[boxes["PaintPoints"].notna(), "GameID"].nunique()
        total_games = boxes["GameID"].nunique()
        st.caption(f"Verified ESPN paint coverage: {verified_paint_games} of {total_games} cached games have at least one paint value. Missing values are never inferred.")
        if shown["Paint / 100 Poss"].notna().sum() < 2:
            st.info("ESPN has not supplied complete verified points-in-paint values for enough teams. Use the CSV source below if available.")
        else:
            render_ncaab_style_scatter(shown, "Paint / 100 Poss", "Paint Points %", "Paint Scoring (ESPN)", "Paint points / 100 estimated possessions", "Paint scoring share", selected, season, False, True)
    with st.expander("Raw ESPN aggregates and source coverage"):
        st.dataframe(shown, hide_index=True, use_container_width=True)


def render_ncaab_shooting_paint_charts(season: int, selected_chart="3PA Rate vs 3P%") -> None:
    render_ncaab_espn_shooting(season, selected_chart)
    render_ncaab_teamrankings_import(season)
    # The legacy season-total CSV remains available below for historical imports.
    st.subheader("Shooting & Paint Profiles • season totals (CSV fallback)")
    st.caption("Independent research views based on actual team totals, not inferred from AdjO/AdjD/AdjT. No changes to OG or ATS formulas.")
    template = "Season,Team,FGA,3PA,3PM,Opponent3PM,Points,PaintPoints,Possessions\n"
    with st.expander("Import shooting and paint statistics (CSV)", expanded=False):
        st.write("Upload season-to-date **cumulative team totals**. Use the same season and cutoff date for every team. Do not mix per-game averages with totals.")
        st.download_button("Download CSV column template", template.encode("utf-8"),
                           "ncaab_style_stats_template.csv", "text/csv", key="ncaab_style_template")
        st.caption("FGA = field-goal attempts; 3PA/3PM = 3-point attempts/makes; Opponent3PM = opponent 3-point makes; Points = total points scored; PaintPoints = points scored in the paint; Possessions = estimated or recorded total team possessions. Season = ending year (e.g., 2027).")
        uploaded = st.file_uploader("Shooting & paint team totals CSV", type=["csv"], key="ncaab_style_upload")
        if uploaded is not None:
            try:
                incoming = clean_ncaab_style_stats(pd.read_csv(uploaded), season)
                st.success(f"Validated {len(incoming)} teams for season {season}.")
                st.dataframe(incoming[["Team", "3PA Rate", "3P %", "3P Made Differential", "Paint / 100 Poss", "Paint Points %"]].head(12),
                             use_container_width=True, hide_index=True)
                if st.button("Save shooting & paint statistics", type="primary", key="ncaab_style_save"):
                    NCAAB_STYLE_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
                    temp = NCAAB_STYLE_STATS_PATH.with_suffix(".tmp")
                    incoming.to_csv(temp, index=False)
                    os.replace(temp, NCAAB_STYLE_STATS_PATH)
                    st.success("Statistics saved. The charts below can now use these totals.")
                    st.rerun()
            except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
                st.error(f"CSV validation failed: {exc}")
    style = load_ncaab_style_stats(season)
    if style.empty:
        st.info("The three charts are installed. Import verified season totals above to populate them. Adjusted ratings alone cannot provide these statistics.")
        return
    st.caption(f"Loaded {len(style)} teams for season {season}. Data file: {NCAAB_STYLE_STATS_PATH.name}. Upload a fresh snapshot when the season advances.")
    highlights = st.multiselect("Highlight teams in all three charts", sorted(style["Team"].unique().tolist()),
                                key="ncaab_style_highlight")
    if selected_chart == "3PA Rate vs 3P%":
        render_ncaab_style_scatter(style, "3PA Rate", "3P %",
            "Three Point Attempt Rate vs 3-Point Percentage", "3-point attempt rate", "3-point percentage", highlights, season, True, True)
        st.caption("3PA rate = 3PA / FGA; 3P% = 3PM / 3PA. Higher reliance does not automatically imply high game-to-game volatility.")
    elif selected_chart == "3P Differential":
        render_ncaab_style_scatter(style, "3P Made Differential", "Points from 3P %",
            "3P Made Differential vs % of Total Points from 3-Pointers", "3PM − opponent 3PM (season total)",
            "Share of total points from threes", highlights, season, False, True)
        st.caption("3P differential is the cumulative makes differential, not a per-game statistic. Teams with different game counts are not directly comparable without normalization.")
    elif selected_chart == "Points in the Paint":
        render_ncaab_style_scatter(style, "Paint / 100 Poss", "Paint Points %",
            "Points in the Paint / 100 Possessions vs Paint Scoring Share", "Paint points per 100 possessions",
            "Share of total points in the paint", highlights, season, False, True)
        st.caption("Paint / 100 = 100 × paint points / total possessions. Paint share = paint points / total points.")
    with st.expander("Source figures and calculated metrics", expanded=False):
        st.dataframe(style, use_container_width=True, hide_index=True)


def render_ncaab_workspace(date_value) -> None:
    st.session_state["ncaab_selected_date"] = str(date_value)
    st.title("🏀 NCAAB Research Board")
    st.caption("Men's NCAA Division I • Game times in Sweden • Adjusted ratings kept separate from OG/ATS calculations")
    try:
        payload = fetch_ncaab_scoreboard(str(date_value))
        matches = ncaab_match_rows(payload)
    except (requests.RequestException, ValueError, KeyError) as exc:
        st.error(f"Could not fetch ESPN NCAAB fixtures: {exc}")
        matches = pd.DataFrame()
    if matches.empty:
        st.info("No games were returned for the selected US scoreboard date. Try the day before/after for overnight games.")
    else:
        st.metric("Games on selected scoreboard date", len(matches))
        st.dataframe(matches.drop(columns=["Event ID", "Away location", "Home location"]), use_container_width=True, hide_index=True)
    st.subheader("Opponent-adjusted team ratings")
    season = ncaab_season_for_date(date_value)
    st.caption(f"Season {season - 1}–{str(season)[-2:]} • AdjO/AdjD = points per 100 possessions; AdjT = adjusted possessions per 40 minutes.")
    c_refresh, c_source = st.columns([1, 3])
    with c_refresh:
        force_refresh = st.button("↻ Refresh adjusted ratings", key="ncaab_torvik_refresh")
    with c_source:
        st.caption(f"Source: Bart Torvik team results CSV • automatic refresh after {NCAAB_RATINGS_MAX_AGE_HOURS} hours • no simulated values")
    # Auto-refresh only if the cached snapshot is missing, stale or from a different season.
    # Cache failed attempts for an hour to avoid repeatedly requesting an unavailable endpoint.
    failure_key = f"ncaab_ratings_failed_{season}"
    can_retry = (pd.Timestamp.now().timestamp() - st.session_state.get(failure_key, 0)) >= 3600
    if force_refresh:
        st.session_state.pop(failure_key, None)
        fetch_ncaab_torvik_ratings.clear()
    if force_refresh or (ncaab_ratings_stale(season) and can_retry):
        with st.spinner("Fetching Bart Torvik adjusted ratings..."):
            ratings_ok, ratings_msg = refresh_ncaab_ratings(season, force=force_refresh)
        if ratings_ok:
            st.session_state.pop(failure_key, None)
            st.success(ratings_msg)
        else:
            st.session_state[failure_key] = pd.Timestamp.now().timestamp()
            st.warning(ratings_msg + " You can try again or import a CSV.")
    with st.expander("Import adjusted ratings CSV (fallback)", expanded=False):
        st.markdown("Import a CSV with **Team, AdjO, AdjD, AdjT** columns. Optional: **Source, AsOf**. The app saves the imported snapshot locally. Ratings are not automatically fetched from Bart Torvik.")
        uploaded = st.file_uploader("Ratings CSV", type=["csv"], key="ncaab_ratings_upload")
        if uploaded is not None:
            try:
                ratings_input = pd.read_csv(uploaded)
                required = {"Team", "AdjO", "AdjD", "AdjT"}
                if not required.issubset(ratings_input.columns):
                    st.error("Missing required columns: " + ", ".join(sorted(required - set(ratings_input.columns))))
                elif st.button("Save NCAAB ratings snapshot", type="primary"):
                    for column in ("AdjO", "AdjD", "AdjT"):
                        ratings_input[column] = pd.to_numeric(ratings_input[column], errors="coerce")
                    ratings_input = ratings_input.dropna(subset=["Team", "AdjO", "AdjD", "AdjT"])
                    ratings_input["Season"] = season
                    ratings_input["Source"] = ratings_input.get("Source", "Manual CSV import")
                    ratings_input["AsOf"] = ratings_input.get("AsOf", pd.Timestamp.now(tz="UTC").isoformat())
                    NCAAB_RATINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
                    ratings_input.to_csv(NCAAB_RATINGS_PATH, index=False)
                    st.success(f"Saved {len(ratings_input)} teams to {NCAAB_RATINGS_PATH.name}.")
            except (ValueError, pd.errors.ParserError) as exc:
                st.error(f"Unable to parse CSV: {exc}")
    st.subheader("Analysis charts")
    chart_choice = st.selectbox("Choose graph", [
        "None – hide graphs",
        "Pace vs Net Rating",
        "Consistency vs Volatility",
        "3PA Rate vs 3P%",
        "3P Differential",
        "Points in the Paint",
    ], key="ncaab_chart_choice")
    st.caption("Only the selected graph is expanded. Shooting and paint data imports are available within their selected graph.")
    ratings = load_ncaab_adjusted_ratings(season)
    if ratings.empty:
        st.warning(f"No verified adjusted ratings for season {season}. Schedule data still works; ratings cannot be compared until a valid source is available.")
        if chart_choice in ("3PA Rate vs 3P%", "3P Differential", "Points in the Paint"):
            render_ncaab_shooting_paint_charts(season, chart_choice)
    else:
        source_name = str(ratings["Source"].iloc[0]) if "Source" in ratings else "Unknown source"
        as_of = str(ratings["AsOf"].iloc[0]) if "AsOf" in ratings else "Unknown snapshot date"
        st.success(f"Loaded {len(ratings)} adjusted team ratings • {source_name} • snapshot {as_of}")
        if chart_choice == "Pace vs Net Rating":
            render_ncaab_pace_net_chart(ratings, season)
        elif chart_choice == "Consistency vs Volatility":
            render_ncaab_volatility_chart(ratings, season, date_value)
        elif chart_choice in ("3PA Rate vs 3P%", "3P Differential", "Points in the Paint"):
            render_ncaab_shooting_paint_charts(season, chart_choice)
        with st.expander("Full adjusted ratings table", expanded=False):
            st.dataframe(ratings, use_container_width=True, hide_index=True)
        if not matches.empty:
            st.subheader("Selected matchup • adjusted profile")
            choices = [f"{row['Away']} @ {row['Home']} ({row['Start (Sweden)']})" for _, row in matches.iterrows()]
            selected = st.selectbox("Match", list(range(len(choices))), format_func=lambda i: choices[i])
            match = matches.iloc[selected]
            for label in ("Away", "Home"):
                team = match[label]
                found = find_ncaab_rating(ratings, team, match.get(f"{label} location", ""))
                if found.empty:
                    st.info(f"No verified team-name match for {team}. The app skips unmatched teams rather than assigning another team's ratings.")
                else:
                    entry = found.iloc[0]
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{team} AdjO", f"{entry['AdjO']:.1f}")
                    c2.metric(f"{team} AdjD", f"{entry['AdjD']:.1f}")
                    c3.metric(f"{team} AdjT", f"{entry['AdjT']:.1f}")
    st.divider()
    render_ncaab_projections(matches, ratings, season)


if sport_mode == "NCAAB":
    render_ncaab_workspace(selected_date)
    st.stop()

if sport_mode in {"NCAAF", "NFL"}:
    render_ncaaf_workspace(
        selected_date,
        season,
        page_mode,
        ncaaf_recent_games,
        show_ncaaf_detail_tables,
        hide_started_ncaaf_games,
        sport_mode,
    )
    st.stop()

data_signature = get_data_signature()
team_logs = prepare_team_logs(load_team_logs(data_signature))

if stale_logs:
    latest_label = latest_log_date.strftime("%Y-%m-%d") if latest_log_date is not None else "none"
    expected_label = expected_log_date.strftime("%Y-%m-%d")
    st.warning(
        f"Slate stats are outdated. Last saved result is {latest_label}, but this view needs pregame results through {expected_label}. "
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

if page_mode == "Line movement":
    render_line_movement_section(
        game,
        selected_date,
        current_game_key,
        current_game_label,
        odds_markets,
        odds_books_text,
        save_odds_snapshot,
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
    st.stop()

if page_mode == "ER lines":
    render_pitcher_er_lines_section(
        game,
        selected_date,
        current_game_key,
        odds_books_text,
    )
    st.stop()

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
