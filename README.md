# B2B Saas Feedback Triage Engine

> Automatically categorise and sentiment-tag hundreds of app reviews in seconds — not hours.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 The Problem

Product Managers and developers spend hours manually reading App Store reviews, support tickets, and survey responses to identify bugs or feature requests. It is a **slow, biased, and unscalable process**.

This tool eliminates that entirely.

---

## ✨ What It Does

Upload a CSV of raw product reviews → the app sends each review to an LLM via the **Groq API** → every review gets tagged with a **Category** and **Sentiment** → results appear in an interactive dashboard instantly.

| Category | Description |
|---|---|
| 🐛 **Bug** | User encountered a crash, error, or broken feature |
| ✨ **Feature Request** | User asking for a new capability or improvement |
| 😤 **UX Friction** | User finds something confusing, slow, or frustrating |
| 🎉 **Praise** | User is happy or complimentary about the product |

| Sentiment | Description |
|---|---|
| ✅ Positive | Happy, satisfied, or enthusiastic tone |
| ➖ Neutral | Matter-of-fact, mixed, or indifferent tone |
| ❌ Negative | Frustrated, angry, or disappointed tone |

---

## 🚀 Demo

1. Upload a `.csv` file with a column named `Review`
2. Click **Analyse Reviews**
3. Explore the dashboard — pie chart, sentiment bar chart, heatmap
4. Download the tagged CSV

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM Backend | Groq API (LLaMA 3.1 8B Instant) |
| Data | Pandas |
| Charts | Plotly Express |
| Language | Python 3.9+ |

---

## ⚙️ Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/voc-analyser.git
cd voc-analyser
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your Groq API key**

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_actual_groq_key_here
```
Get your free key at [console.groq.com](https://console.groq.com)

**4. Run the app**
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
voc-analyser/
│
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .env                 # Your API key (never committed)
├── .gitignore           # Excludes .env and cache files
└── README.md
```

---

## 📊 Success Metrics

- **Efficiency:** Reduces time to analyse 50 reviews from ~30 minutes (manual) to under 10 seconds
- **Quality:** Targets 85%+ categorisation accuracy vs. human tagging
- **Reliability:** Strict JSON-schema prompting prevents hallucinated categories

---

## 🧠 Technical Decisions & Trade-offs

### Why Groq over Gemini?
During initial prototyping with the Gemini API, processing just 8 rows took over 100 seconds and immediately hit rate limits. The pivot to **Groq's ultra-low-latency inference** turned a slow script into a snappy, production-ready dashboard — making speed-to-insight the core value proposition it needed to be.

### Handling LLM Hallucinations
Early testing showed 100% of reviews being categorised as "Unknown" — the LLM was wrapping JSON responses in Markdown code blocks, breaking the parser silently. The fix was two-pronged:
- **Strict JSON-schema prompting** — the system prompt forces the model to return only valid JSON with predefined category values
- **String-cleansing pipeline** — strips Markdown formatting before parsing to prevent silent failures

---

## 🔬 Edge Case Testing

The model is validated against an `edge_cases.csv` designed to stress-test real-world inputs:

| Test | Input | Expected |
|---|---|---|
| **Sarcasm** | *"Love how the app crashes every time."* | Negative / Bug |
| **Mixed Sentiment** | *"Dashboard looks great but loads slowly."* | Neutral / UX Friction |
| **Garbage Input** | `asdfghjkl` or `🔥🔥👍` | Graceful fallback, no crash |

---

## 📋 CSV Format

Your input CSV must have a column named exactly `Review`:

```csv
Review
"The app crashes every time I try to upload a photo."
"Would love a dark mode option!"
"Super smooth experience, very happy with the update."
```

---

## 🌐 Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub
3. Click **New App** → select this repo → set `app.py` as main file
4. Under **Advanced Settings → Secrets**, add:
```toml
GROQ_API_KEY = "your_actual_groq_key_here"
```
5. Click **Deploy** ✅

---

## 👤 Author

**Stuti Gupta** — Product Manager  
Built as an MVP to automate VoC analysis and demonstrate AI product thinking.

---

## 📄 License

MIT License — free to use, modify, and distribute.
