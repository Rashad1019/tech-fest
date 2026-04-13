# Property Management AI Dashboard — Tech Fest Demo

## Project Overview
A synthetic-data-driven property management dashboard with an AI engine. Built in 3 phases.
No real data — everything is generated from `generate_data.py`.

## Stack
- **Data generation:** Python (stdlib only)
- **AI engine:** Python + `google-genai` SDK (model: `gemini-3.1-flash-lite-preview`)
- **Dashboard:** Streamlit

## Project Structure
```
tech-fest/
├── generate_data.py        # Phase 1 — generates all synthetic CSVs
├── ai_engine.py            # Phase 2 — AI classifier, churn scorer, vendor router
├── dashboard.py            # Phase 3 — Streamlit dashboard (TO BUILD)
├── requirements.txt        # google-genai>=1.0.0
└── data/
    ├── properties.csv              # 50 buildings, 3 markets (Atlanta, Dallas, Charlotte)
    ├── vendors.csv                 # 30 vendors with specialty, SLA, quality rating
    ├── tenants.csv                 # 500 tenants with lease dates, rent, satisfaction score
    ├── work_orders.csv             # 2200 maintenance requests with free-text descriptions
    ├── payments.csv                # 12 months of rent payment history per tenant
    ├── invoices.csv                # One per resolved work order (labor + parts cost)
    ├── financial_ledger.csv        # Monthly NOI per property (revenue - expenses)
    ├── work_orders_classified.csv  # Phase 2 output — AI-predicted trade + urgency + accuracy
    ├── tenants_scored.csv          # Phase 2 output — churn score + risk level per tenant
    └── vendor_recommendations.csv  # Phase 2 output — top vendor match per open work order
```

## How to Run

### Phase 1 — Regenerate data
```bash
python3 generate_data.py
```

### Phase 2 — Run AI engine
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:GEMINI_API_KEY="your_key"
python ai_engine.py
```

### Phase 3 — Launch dashboard
```powershell
venv\Scripts\Activate.ps1
pip install streamlit plotly pandas
streamlit run dashboard.py
```

## Phase 3: Dashboard — COMPLETE

`dashboard.py` is built and running. Launch with:
```powershell
venv\Scripts\Activate.ps1
streamlit run dashboard.py
```
Opens at http://localhost:8501

---

## Demo Talking Points (for Joel Roberts / Lumicity VP of Ops interview)

**Target role:** VP of Operations — Proptech & Energy | Up to $230K base | 100% Remote
**Recruiter:** Joel Roberts, Lumicity (joel.roberts@lumicity.io / +1 857 267 8717)

### How this project maps to the job requirements

| Job Requirement | What to Point To |
|----------------|-----------------|
| AI-enabled workflows to improve operational efficiency | Gemini classifier auto-triages work orders by trade + urgency — no manual triage |
| Dashboards and reporting for data-heavy environments | 5-panel Streamlit dashboard built for executive decision-making |
| Implementing/revamping BI systems | Built entire data model, AI engine, and BI layer from scratch |
| Proptech experience | This IS a proptech system — properties, tenants, work orders, vendors, NOI |

### Walkthrough Script (2.5 min)

**Opening (15 sec)**
"This is PropIQ — a property management intelligence platform I built end to end. It covers a 50-property portfolio across Atlanta, Dallas, and Charlotte. Let me walk you through it."

**Panel 1 — Portfolio Overview**
"Starting at the top — total units, portfolio value, monthly revenue, and average property age at a glance. Below that, a market-by-market breakdown so leadership can see performance by geography, not just in aggregate. This is the view a VP needs first thing every morning."

**Panel 2 — Financial Summary**
"Here's the financial layer — revenue versus expenses trending over 12 months, and NOI ranked by property. You can immediately see which properties are carrying the portfolio and which are bleeding money. Filterable by market so you can slice it for a regional conversation."

**Panel 3 — Maintenance Operations**
"This is where AI comes in. Every work order comes in as free text — things like 'AC making grinding noise, unit is 85 degrees.' Gemini reads that description and classifies it by trade and urgency automatically. No manual triage. The dashboard shows classifier accuracy, resolution times by urgency level, and open work orders already matched to the best available vendor."

**Panel 4 — Tenant Health & Churn**
"This panel is about retention. The churn model scores every tenant based on payment history, lease expiration, satisfaction, and complaint volume. You can see the risk distribution across the portfolio and drill into the top 20 tenants most likely to leave — before they give notice. In proptech, catching churn early is direct NOI protection."

**Panel 5 — Vendor Scorecard**
"Finally, vendor performance. Every vendor ranked by a composite score — SLA compliance, quality rating, and response time. Filter by specialty. You know at a glance who your top plumber is, who's underperforming, and who to cut."

**Close (15 sec)**
"The entire system — data model, AI engine, and dashboard — I built from the ground up. This is how I think about operations: connected data, AI where it reduces friction, and visibility that drives decisions at every level."

---

## Phase 3: Dashboard Panels

Build `dashboard.py` as a Streamlit app with 5 panels. Use `plotly` for charts, `pandas` for data.
Read all CSVs from the `data/` directory. Prefer `work_orders_classified.csv`, `tenants_scored.csv`,
and `vendor_recommendations.csv` (Phase 2 outputs) when available, fall back to base CSVs if not.

### Panel 1 — Portfolio Overview
- KPI cards: total units, occupancy rate, portfolio market value, monthly revenue
- Market comparison: Atlanta vs Dallas vs Charlotte (property count, avg NOI, avg occupancy)
- Property type breakdown (multifamily / commercial / mixed-use)

### Panel 2 — Financial Summary
- Bar chart: NOI by property (top 10 and bottom 10)
- Line chart: portfolio revenue vs expenses trend over 12 months
- Filterable by market

### Panel 3 — Maintenance Operations
- Work order status breakdown (open / in-progress / resolved)
- Trade volume chart (plumbing / HVAC / electrical / general)
- AI classifier accuracy (trade match % and urgency match %) — from `work_orders_classified.csv`
- Avg resolution hours by urgency level
- Table: open work orders with AI-recommended vendor

### Panel 4 — Tenant Health & Churn
- Churn risk distribution (critical / high / medium / low) — from `tenants_scored.csv`
- Table: top 20 at-risk tenants (churn score, days remaining, late payment rate, satisfaction)
- Payment outcome breakdown: on_time / late / missed across portfolio

### Panel 5 — Vendor Scorecard
- Ranked table of all 30 vendors (SLA compliance, quality rating, avg response time, match score)
- Filter by specialty
- Highlight top vendor per specialty

## Key Data Relationships
- `tenants.property_id` → `properties.property_id`
- `work_orders.tenant_id` → `tenants.tenant_id`
- `work_orders.assigned_vendor` → `vendors.vendor_id`
- `payments.tenant_id` → `tenants.tenant_id`
- `invoices.work_order_id` → `work_orders.work_order_id`
- `financial_ledger.property_id` → `properties.property_id`

## Important Notes
- At-risk tenants (~12%) have higher late/missed payment rates — the churn model detects this signal
- Work order descriptions are raw free text — the Gemini classifier infers trade and urgency from prose
- NOI can go negative for high-maintenance or older properties — this is intentional
- `random.seed(42)` is set in `generate_data.py` — data is fully reproducible
