# Payer Policy Intelligence — Interactive Dashboard

A Streamlit dashboard for exploring the extracted PA policy data and Access Scores. Built to satisfy the hackathon's optional "Dashboard or visual assets" deliverable.

## What it shows

Four tabs:

1. **📊 Overview** — KPI cards (total policies, avg score, brand count), Access Score distribution histogram with FDA-parity reference lines, score-by-brand box plot, restrictiveness heatmap per brand, most/least restrictive policy rankings.
2. **🔍 Policy Detail** — Pick a single (Filename, Brand) row to see a full breakdown: gauge chart for Access Score, comparison vs brand & overall averages, percentile ranking, badges for Yes/No fields, all 12 extracted parameters, and verbatim policy language for the long-text fields.
3. **⚖️ Compare** — Pick 2–3 policies, see a side-by-side parameter table with disagreements highlighted in yellow, plus a radar chart comparing their restrictiveness profiles.
4. **📋 Raw Data** — Searchable, filterable view of the full `result.csv` with one-click CSV download of the filtered subset.

Sidebar has brand multi-select and Access Score range slider that filter all tabs simultaneously.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit application (single file) |
| `requirements.txt` | Pinned minimum versions of Streamlit, Pandas, Plotly, NumPy |
| `result.csv` | Sample data — replace with your real pipeline output |

## Deployment

### Option 1 — Streamlit Community Cloud (recommended; one hosted link, free)

1. Create a public GitHub repo containing `app.py`, `requirements.txt`, and `result.csv`.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **"New app"**.
3. Select your repo, branch `main`, main file path `app.py`.
4. Click **Deploy**. After ~2 minutes you get a URL like `yourname-pa-dashboard.streamlit.app` — that's the URL to put in your hackathon submission.

To update the dashboard after re-running the extraction pipeline, just push a new `result.csv` to the repo; Streamlit Cloud auto-redeploys.

### Option 2 — Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at [http://localhost:8501](http://localhost:8501). Screenshot it for your submission if you don't want to deploy.

### Option 3 — Google Colab (no deployment)

```python
# In a Colab cell
!pip install -q streamlit plotly pyngrok
!wget -qO- https://your-gist-url/app.py > app.py        # or upload via the file browser

from pyngrok import ngrok
import subprocess, threading
def run():
    subprocess.run(["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"])
threading.Thread(target=run, daemon=True).start()
import time; time.sleep(5)
public_url = ngrok.connect(8501)
print(public_url)
```

Note: ngrok URLs expire when the Colab runtime disconnects; use Streamlit Cloud for a stable submission link.

## Data contract

The dashboard reads `result.csv` with these 15 columns (exact submission format):

```
Filename, Brand, Age, Step Therapy Requirements Documented in Policy,
Number of Steps through Brands, Number of Steps through Generic,
Step through-Phototherapy, TB Test required, Quantity Limits, Specialist Types,
Initial Authorization Duration(in-months), Reauthorization Duration(in-months),
Reauthorization Required, Reauthorization Requirements Documented in Policy,
Access Score
```

Either place `result.csv` alongside `app.py`, or upload one via the sidebar file picker at runtime.

The dashboard reads `"NA"` as a literal string value (matching the gold-standard convention from the few-shot tab), not as null.

## Tech notes

- Charts use Plotly for interactivity (hover, zoom, click-to-filter legend)
- `@st.cache_data` on the CSV loader — re-renders are instant once data is loaded
- Sidebar filters reactively re-compute all charts and tables
- Gauge chart shows the Access Score against its 4 colored anchor bands (0–25 red, 25–50 orange, 50–75 yellow, 75–100 green)
- Restrictiveness radar normalises step counts to 0-1 (divide by 5) so all axes are comparable
