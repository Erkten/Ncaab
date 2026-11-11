
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import statsapi

OUTPUT_PATH = Path(__file__).parent / "data" / "team_game_logs_real.csv"

def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

def _team_row(game_id: int, game_date: str, team_name: str, opponent_name: str, home_away: str, team_box: dict) -> dict:
    batting = team_box.get("teamStats", {}).get("batting", {}) or {}

    ab = _safe_int(batting.get("atBats"))
    h = _safe_int(batting.get("hits"))
    bb = _safe_int(batting.get("baseOnBalls"))
    hbp = _safe_int(batting.get("hitByPitch"))
    sf = _safe_int(batting.get("sacFlies"))
    pa = _safe_int(batting.get("plateAppearances"))
    doubles = _safe_int(batting.get("doubles"))
    triples = _safe_int(batting.get("triples"))
    hr = _safe_int(batting.get("homeRuns"))
    runs = _safe_int(batting.get("runs"))
    so = _safe_int(batting.get("strikeOuts"))
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

def build_team_game_log(season: int = 2026) -> pd.DataFrame:
    games = statsapi.schedule(start_date=f"{season}-01-01", end_date=f"{season}-12-31", sportId=1)

    finished_regular_season_games = [
        g for g in games
        if str(g.get("status", "")).lower() == "final"
        and str(g.get("game_type", "")) == "R"
    ]

    rows = []
    seen_game_ids = set()

    for game in finished_regular_season_games:
        game_id = _safe_int(game.get("game_id"))
        if not game_id or game_id in seen_game_ids:
            continue
        seen_game_ids.add(game_id)

        box = statsapi.boxscore_data(game_id)
        away_box = box.get("away", {}) or {}
        home_box = box.get("home", {}) or {}

        game_date = str(game.get("game_date"))
        away_name = game.get("away_name") or "Away"
        home_name = game.get("home_name") or "Home"

        rows.append(_team_row(game_id, game_date, away_name, home_name, "away", away_box))
        rows.append(_team_row(game_id, game_date, home_name, away_name, "home", home_box))

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No finished regular-season games were returned.")

    return df.sort_values(["team", "date", "game_id"]).reset_index(drop=True)

def main() -> None:
    season_input = input("Season to download (press Enter for 2026): ").strip()
    season = int(season_input) if season_input else 2026

    print(f"Downloading season {season} game logs...")
    df = build_team_game_log(season=season)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df)} team-game rows to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
