"""
B2B SaaS Feedback Triage Engine — app.py
=================================
Uses the Groq API with llama-3.1-8b-instant.
HOW TO RUN:
  1. pip install -r requirements.txt
  2. Set your GROQ_API_KEY as an environment variable
  3. streamlit run app.py
"""

import os, json, re, time, textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
import plotly.express as px
from groq import Groq
# ─────────────────────────────────────────────
# 0.  CONFIGURATION
# ─────────────────────────────────────────────
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

MODEL_NAME    = "llama-3.1-8b-instant"
MAX_ROWS      = 50        # ← This is what's missing!
RETRY_DELAY   = 2
MAX_WORKERS   = 3
REQUEST_DELAY = 1

VALID_CATEGORIES = {"Bug", "Feature Request", "UX Friction", "Praise"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}

CAT_COLORS = {
    "Bug":             "#FF6B6B",
    "Feature Request": "#4ECDC4",
    "UX Friction":     "#FFD93D",
    "Praise":          "#6BCB77",
}
SENT_COLORS = {
    "Positive": "#6BCB77",
    "Neutral":  "#ADB5BD",
    "Negative": "#FF6B6B",
}

# ─────────────────────────────────────────────
# 1.  SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
You are a senior product analyst. Your job is to analyse a single user review
and return a structured JSON object — nothing else.

You MUST classify the review into EXACTLY ONE of these four categories:
  - "Bug"              → The user encountered a technical error, crash, or broken feature.
  - "Feature Request"  → The user is asking for a new capability or improvement.
  - "UX Friction"      → The user finds something confusing, slow, or frustrating (not a bug).
  - "Praise"           → The user is happy or complimentary about the product.

You MUST also assign EXACTLY ONE sentiment:
  - "Positive"  → Overall tone is happy, satisfied, or enthusiastic.
  - "Neutral"   → Tone is matter-of-fact, mixed, or indifferent.
  - "Negative"  → Tone is frustrated, angry, or disappointed.

Return ONLY valid JSON in this exact schema — no markdown fences, no prose:
{
  "category":  "<Bug | Feature Request | UX Friction | Praise>",
  "sentiment": "<Positive | Neutral | Negative>",
  "reason":    "<One concise sentence explaining your classification>"
}
""").strip()

# ─────────────────────────────────────────────
# 2.  GROQ HELPERS
# ─────────────────────────────────────────────
def configure_groq() -> bool:
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        return False
    return True


def _clean_json(raw: str) -> str:
    raw = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
    raw = raw.replace("```", "").strip()
    match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
    return match.group(0) if match else raw

def analyse_review(client: Groq, review_text: str) -> dict:
    last_error = "unknown error"

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Review:\n{review_text.strip()}"}
                ],
                temperature=0.0,
                max_tokens=256,
            )
            raw     = response.choices[0].message.content.strip()
            cleaned = _clean_json(raw)
            parsed  = json.loads(cleaned)

            cat  = str(parsed.get("category",  "")).strip()
            sent = str(parsed.get("sentiment", "")).strip()
            cat  = next((v for v in VALID_CATEGORIES if v.lower() == cat.lower()),  "Unknown")
            sent = next((v for v in VALID_SENTIMENTS if v.lower() == sent.lower()), "Unknown")

            return {"category": cat, "sentiment": sent, "reason": parsed.get("reason", "")}

        except json.JSONDecodeError as exc:
            last_error = f"JSONDecodeError: {exc}"
            time.sleep(RETRY_DELAY)
        except Exception as exc:
            last_error = str(exc)
            if "429" in str(exc) or "rate_limit" in str(exc).lower():
                time.sleep(REQUEST_DELAY * (attempt + 2))
            else:
                time.sleep(RETRY_DELAY * (attempt + 1))

    return {"category": "Unknown", "sentiment": "Unknown",
            "reason": f"Error: {last_error}"}

# ─────────────────────────────────────────────
# 3.  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="B2B SaaS Feedback Triage Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 4.  CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0f1117; color: #e8eaf0; }
[data-testid="stSidebar"] { background: #161b27; border-right: 1px solid #2a2f3d; }
[data-testid="stSidebar"] * { color: #d0d6e8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #ffffff !important; font-weight: 700 !important; }
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] p  { color: #c8d0e0 !important; font-size: 0.9rem !important; line-height: 1.6 !important; }
[data-testid="stSidebar"] .stInfo { background: #1e2a40 !important; border: 1px solid #3a4a6b !important; }
[data-testid="stMetric"] { background: #1a2035; border: 1px solid #2a3150; border-radius: 12px; padding: 16px 20px; }
[data-testid="stMetricLabel"] { font-size: 0.78rem; color: #8892a4; }
[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; color: #e8eaf0; }
.stButton > button { background: linear-gradient(135deg,#4ecdc4,#45b7aa); color:#0f1117; font-weight:700; border:none; border-radius:8px; padding:0.6rem 1.6rem; }
hr { border-color: #2a3150; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 5.  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 B2B SaaS Feedback Triage Engine")
    st.caption("B2B Feedback Triage · MVP v1.0")
    st.divider()
    st.markdown("### How to use")
    st.markdown("1. Upload a **CSV file** with a column named `Review`.\n2. Click **Analyse Reviews**.\n3. Explore the dashboard and download results.")
    st.divider()
    st.markdown("### Limits")
    st.info(f"Max **{MAX_ROWS} rows** per upload.")
    st.divider()
    st.markdown("### Category guide")
    for cat, color in CAT_COLORS.items():
        st.markdown(f'<span style="color:{color}; font-weight:600;">■</span> {cat}', unsafe_allow_html=True)
    st.divider()
    st.caption("Built with Streamlit · Groq (Llama 3.1)")

# ─────────────────────────────────────────────
# 6.  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<h1 style="font-size:2.2rem;font-weight:700;margin-bottom:0;">🔍 B2B SaaS Feedback Triage Engine</h1>
<p style="color:#8892a4;margin-top:4px;">Upload app reviews → get AI-powered categorisation & sentiment in seconds.</p>
""", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────
# 7.  API KEY CHECK
# ─────────────────────────────────────────────
api_ready = configure_groq()
if not api_ready:
    st.error("⚠️ **Groq API key not found.** Set the `GROQ_API_KEY` environment variable and restart the app.", icon="🔑")
    st.stop()

# ─────────────────────────────────────────────
# 8.  FILE UPLOAD
# ─────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"],
    help="The CSV must contain a column named **Review**.")

if uploaded_file is None:
    st.markdown("""
    <div style="background:#1a2035;border:1.5px dashed #2a3150;border-radius:14px;
    padding:40px;text-align:center;color:#8892a4;margin-top:20px;">
    <div style="font-size:2.5rem;margin-bottom:12px;">📂</div>
    <div style="font-size:1.05rem;font-weight:500;color:#c8d0e0;">Drop a CSV to get started</div>
    <div style="font-size:0.85rem;margin-top:6px;">Required column: <code>Review</code> · Max 50 rows</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# 9.  LOAD & VALIDATE CSV
# ─────────────────────────────────────────────
try:
    df_raw = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not parse the CSV file: {exc}")
    st.stop()

if "Review" not in df_raw.columns:
    st.error(f"No **`Review`** column found. Columns in your file: `{list(df_raw.columns)}`")
    st.stop()

df = df_raw[["Review"]].dropna(subset=["Review"]).head(MAX_ROWS).reset_index(drop=True)
total_reviews = len(df)

if total_reviews == 0:
    st.warning("The CSV has no non-empty reviews.")
    st.stop()

with st.expander(f"📄 Preview uploaded data ({total_reviews} reviews)", expanded=False):
    st.dataframe(df, use_container_width=True)

# ─────────────────────────────────────────────
# 10.  ANALYSE BUTTON
# ─────────────────────────────────────────────
st.markdown("---")
col_btn, col_hint = st.columns([1, 4])
with col_btn:
    run_analysis = st.button("⚡ Analyse Reviews", use_container_width=True)
with col_hint:
   st.caption(f"Will send **{total_reviews} reviews** to Groq ({MODEL_NAME}) for analysis.")
if not run_analysis:
    st.stop()

# ─────────────────────────────────────────────
# 11.  RUN ANALYSIS
# ─────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

reviews_list  = df["Review"].astype(str).tolist()
results       = [None] * total_reviews
start_time    = time.time()
progress_bar  = st.progress(0, text="Starting analysis…")
status_holder = st.empty()
completed     = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_idx = {}
    for idx, review in enumerate(reviews_list):
        future = executor.submit(analyse_review, client, review)
        future_to_idx[future] = idx
        if idx < len(reviews_list) - 1:
            time.sleep(REQUEST_DELAY)

    for future in as_completed(future_to_idx):
        idx          = future_to_idx[future]
        res          = future.result()
        results[idx] = res
        if res["category"] == "Unknown":
            st.warning(f"⚠️ Row {idx+1} — {res['reason'][:120]}")
        completed += 1
        progress_bar.progress(completed / total_reviews,
                               text=f"{completed} / {total_reviews} reviews processed")
        status_holder.caption(f"✅ {completed} / {total_reviews} analysed…")

elapsed = time.time() - start_time
progress_bar.empty()
status_holder.empty()

df_results = df.copy()
df_results["Category"]  = [r["category"]  for r in results]
df_results["Sentiment"] = [r["sentiment"] for r in results]
df_results["Reason"]    = [r["reason"]    for r in results]

# ─────────────────────────────────────────────
# 12.  DASHBOARD
# ─────────────────────────────────────────────
st.success(f"✅ Analysis complete — {total_reviews} reviews processed in **{elapsed:.1f}s**")
st.markdown("---")
st.markdown("### 📊 Dashboard")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Reviews",   total_reviews)
m2.metric("🐛 Bugs",         int((df_results["Category"] == "Bug").sum()))
m3.metric("✨ Feature Reqs", int((df_results["Category"] == "Feature Request").sum()))
m4.metric("😤 UX Friction",  int((df_results["Category"] == "UX Friction").sum()))
m5.metric("🎉 Praise",       int((df_results["Category"] == "Praise").sum()))
st.markdown("---")

# ─── Charts ───────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Category Breakdown")
    cat_counts = df_results["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_pie = px.pie(cat_counts, names="Category", values="Count",
                     color="Category", color_discrete_map=CAT_COLORS, hole=0.42)
    fig_pie.update_traces(textposition="outside", textinfo="percent+label",
                          pull=[0.04]*len(cat_counts))
    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#c8d0e0", margin=dict(t=10,b=10,l=10,r=10),
                          legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
    st.markdown("#### Sentiment Distribution")
    sent_counts = df_results["Sentiment"].value_counts().reset_index()
    sent_counts.columns = ["Sentiment", "Count"]
    fig_bar = px.bar(sent_counts, x="Sentiment", y="Count",
                     color="Sentiment", color_discrete_map=SENT_COLORS, text="Count")
    fig_bar.update_traces(textposition="outside", marker_line_width=0)
    fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#c8d0e0", showlegend=False,
                          xaxis=dict(showgrid=False, color="#8892a4"),
                          yaxis=dict(showgrid=True, gridcolor="#2a3150", color="#8892a4"),
                          margin=dict(t=10,b=10,l=10,r=10))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("#### Category × Sentiment Heatmap")
heatmap_df = df_results.groupby(["Category","Sentiment"]).size().reset_index(name="Count")
fig_heat = px.density_heatmap(heatmap_df, x="Category", y="Sentiment", z="Count",
                               color_continuous_scale=["#1a2035","#4ecdc4"], text_auto=True)
fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c8d0e0", coloraxis_showscale=False, height=280,
                        xaxis=dict(showgrid=False,color="#8892a4"),
                        yaxis=dict(showgrid=False,color="#8892a4"),
                        margin=dict(t=10,b=10,l=10,r=10))
st.plotly_chart(fig_heat, use_container_width=True)

# ─────────────────────────────────────────────
# 13.  DETAILED RESULTS TABLE
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Detailed Results")

f1, f2 = st.columns(2)
with f1:
    filter_cat = st.multiselect("Filter by Category",
                                options=sorted(VALID_CATEGORIES),
                                default=sorted(VALID_CATEGORIES))
with f2:
    filter_sent = st.multiselect("Filter by Sentiment",
                                 options=sorted(VALID_SENTIMENTS),
                                 default=sorted(VALID_SENTIMENTS))

df_filtered = df_results[
    df_results["Category"].isin(filter_cat) &
    df_results["Sentiment"].isin(filter_sent)
]

st.dataframe(
    df_filtered[["Review","Category","Sentiment","Reason"]],
    use_container_width=True, height=400,
    column_config={
        "Review":    st.column_config.TextColumn("Review",    width="large"),
        "Category":  st.column_config.TextColumn("Category",  width="medium"),
        "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
        "Reason":    st.column_config.TextColumn("AI Reason", width="large"),
    },
)

# ─────────────────────────────────────────────
# 14.  DOWNLOAD
# ─────────────────────────────────────────────
st.markdown("---")
csv_export = df_results.to_csv(index=False).encode("utf-8")
st.download_button(label="⬇️  Download Tagged CSV", data=csv_export,
                    file_name="triaged_feedback.csv", mime="text/csv",
                    use_container_width=True)
