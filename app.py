import json
import os
import streamlit as st
import streamlit.components.v1 as components

# Get the directory where this script lives (the 'pages' folder)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Point directly to the files in the same 'pages' folder
db_path = os.path.join(CURRENT_DIR, "hltb.jsonlines")
html_path = os.path.join(CURRENT_DIR, "hltb-higher-lower-redesign.html")

# 1. Read dataset & html template
try:
  with open(db_path, "r", encoding="utf-8") as f:
    raw_jsonlines = f.read()
except FileNotFoundError:
  st.error(f"❌ File missing at: `{db_path}`")
  st.stop()

try:
  with open(html_path, "r", encoding="utf-8") as f:
    html_code = f.read()
except FileNotFoundError:
  st.error(f"❌ HTML template missing at: `{html_path}`")
  st.stop()

# 2. Safely encode the dataset into JSON string
safe_dataset = json.dumps(raw_jsonlines)

# 3. Inject into HTML page
injection_script = f"""
<script>
  window.addEventListener('DOMContentLoaded', () => {{
    const dataset = {safe_dataset};
    if (typeof init === 'function') {{
      init(dataset);
    }}
  }});
</script>
</body>
"""

if "</body>" in html_code:
  html_code = html_code.replace("</body>", injection_script)
else:
  html_code += injection_script

# 4. Render inside Streamlit iframe
components.html(html_code, height=820, scrolling=True)