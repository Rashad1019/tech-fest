# PropIQ — Property Management AI Dashboard

A synthetic-data-driven property management intelligence platform built end to end.
Covers a 50-property portfolio across Atlanta, Dallas, and Charlotte with an AI-powered
maintenance triage engine, tenant churn prediction, and vendor routing — all visualized
in a 5-panel Streamlit dashboard.

No real data — everything is generated from `generate_data.py`.

---

## Stack

| Layer | Tech |
|-------|------|
| Data generation | Python (stdlib only) |
| AI engine | Python + `google-genai` SDK — `gemini-2.0-flash-lite` |
| Dashboard | Streamlit + Plotly |

---

## Project Structure

```
tech-fest/
├── generate_data.py        # Phase 1 — generates all synthetic CSVs
├── ai_engine.py            # Phase 2 — AI classifier, churn scorer, vendor router
├── dashboard.py            # Phase 3 — Streamlit dashboard
├── requirements.txt
└── data/
    ├── properties.csv              # 50 buildings, 3 markets
    ├── vendors.csv                 # 30 vendors with specialty, SLA, quality rating
    ├── tenants.csv                 # 500 tenants with lease dates, rent, satisfaction
    ├── work_orders.csv             # 2200 maintenance requests (free-text descriptions)
    ├── payments.csv                # 12 months of rent payment history per tenant
    ├── invoices.csv                # One per resolved work order (labor + parts cost)
    ├── financial_ledger.csv        # Monthly NOI per property
    ├── work_orders_classified.csv  # Phase 2 output — AI trade + urgency + accuracy
    ├── tenants_scored.csv          # Phase 2 output — churn score + risk level
    └── vendor_recommendations.csv  # Phase 2 output — top vendor match per open order
```

---

## Setup

### Prerequisites

- Python 3.9+
- A Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com)

### Install

```bash
python -m venv venv

# Windows
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
pip install streamlit plotly pandas
```

---

## How to Run

### Phase 1 — Generate synthetic data

```bash
python generate_data.py
```

Outputs all CSVs into `data/`. Data is fully reproducible (`random.seed(42)`).

### Phase 2 — Run the AI engine

Set your Gemini API key, then run:

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your_key_here"

# macOS / Linux
export GEMINI_API_KEY="your_key_here"

python ai_engine.py
```

This produces three AI-enriched CSVs:
- `work_orders_classified.csv` — trade and urgency predicted from free-text descriptions
- `tenants_scored.csv` — churn risk scored per tenant
- `vendor_recommendations.csv` — best vendor matched to each open work order

### Phase 3 — Launch the dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

---

## Dashboard Panels

| Panel | What it shows |
|-------|--------------|
| Portfolio Overview | KPI cards, market comparison (Atlanta / Dallas / Charlotte), property type breakdown |
| Financial Summary | NOI by property, revenue vs expenses trend, filterable by market |
| Maintenance Operations | Work order status, trade volume, AI classifier accuracy, resolution times, vendor matches |
| Tenant Health & Churn | Risk distribution, top 20 at-risk tenants, payment outcome breakdown |
| Vendor Scorecard | All 30 vendors ranked by SLA, quality, response time — filterable by specialty |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (Phase 2 only) | Your Google Gemini API key |

The dashboard (Phase 3) reads pre-generated CSVs and requires no API key.
