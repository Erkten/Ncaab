# MLB Betting Dashboard - stats fix

This version keeps the layout you liked, but switches hitter and pitcher stats to a simpler direct stats path:
- `/people/{id}/stats?stats=season`
- `/people/{id}/stats?stats=gameLog`

That should make the hitter tables and pitcher cards populate more reliably.

## Install
Replace your current `app.py` with this bundle's `app.py`, then run:

```bash
cd ~/Downloads/mlb_obp_streamlit_clean_app
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## SportsGameOdds
Set your API key before using the odds section:

```bash
export SPORTSGAMEODDS_API_KEY="your-key-here"
```

Or add it to `.streamlit/secrets.toml`:

```toml
SPORTSGAMEODDS_API_KEY = "your-key-here"
```

This version adds:
- OPS momentum (Season / Last 7 / Last 3)
- Runs momentum (Season / Last 7 / Last 3)
- stronger offense signal labels
- betting notes tied to your momentum logic

If your current CSV was created before runs were added, click **Update team logs** once so the runs momentum section can populate.
