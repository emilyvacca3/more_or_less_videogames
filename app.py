import json
import os
import re
import streamlit as st
import streamlit.components.v1 as components

# Page config optimized for mobile & desktop
st.set_page_config(
    page_title="Longer or Shorter? — Game Length",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(CURRENT_DIR, "hltb.jsonlines")
html_path = os.path.join(CURRENT_DIR, "longer_or_shorter_game_length.html")

# Helper functions to pre-parse data efficiently in Python


def parse_mins(s):
  if not s:
    return None
  h = re.search(r"(\d+)\s*h", str(s))
  m = re.search(r"(\d+)\s*m", str(s))
  if not h and not m:
    return None
  return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


def parse_polled(s):
  if not s:
    return 0
  s = str(s).strip().upper().replace(",", "")
  if s.endswith("K"):
    try:
      return int(float(s[:-1]) * 1000)
    except ValueError:
      return 0
  try:
    return int(float(s))
  except ValueError:
    return 0


# Cache dataset processing so it only runs ONCE when the server starts
@st.cache_data
def load_and_preprocess_dataset(file_path):
  parsed_games = []
  if not os.path.exists(file_path):
    return None

  with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      try:
        d = json.loads(line)
        main = (
            d.get("Stats", {})
            .get("Single-Player", {})
            .get("Main Story", {})
        )
        if not main:
          continue

        mins = parse_mins(main.get("Average"))
        if not mins or mins <= 0:
          continue

        polled = parse_polled(main.get("Polled"))
        # Filter out games with zero votes to keep file tiny
        if polled < 1:
          continue

        parsed_games.append({
            "name": d.get("Name", ""),
            "mins": mins,
            "polled": polled,
            "steam": d.get("steam_app_id") or None,
            "year": (d.get("Release_date") or "")[:4],
        })
      except Exception:
        continue

  return parsed_games


# 1. Load and process lightweight dataset
parsed_games = load_and_preprocess_dataset(db_path)

if parsed_games is None:
  st.error(
      "❌ **'hltb.jsonlines' not found!** Make sure it is in the same directory"
      " as app.py."
  )
  st.stop()

# 2. Read HTML template
try:
  with open(html_path, "r", encoding="utf-8") as f:
    html_code = f.read()
except FileNotFoundError:
  st.error(
      "❌ **'longer_or_shorter_game_length.html' not found!** Make sure it's in"
      " the same directory as app.py."
  )
  st.stop()

# 3. Inject lightweight JSON directly into browser JavaScript
# Using json.dumps on the already-processed list makes it instantly ready for JS
json_data_str = json.dumps(parsed_games)

injection_script = f"""
<script>
  window.addEventListener('DOMContentLoaded', () => {{
    const preParsedGames = {json_data_str};
    if (typeof initParsedGames === 'function') {{
      initParsedGames(preParsedGames);
    }} else if (typeof init === 'function') {{
      // Fallback
      init(JSON.stringify(preParsedGames));
    }}
  }});
</script>
</body>
"""

if "</body>" in html_code:
  html_code = html_code.replace("</body>", injection_script)
else:
  html_code += injection_script

# 4. Render component
components.html(html_code, height=820, scrolling=True)