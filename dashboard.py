"""
Phase 3: Property Management AI Dashboard
Run: streamlit run dashboard.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PropIQ — Portfolio Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")

# ─── Global CSS — fix text contrast ──────────────────────────────────────────
st.markdown("""
<style>
    /* Main text */
    html, body, [class*="css"], .stMarkdown, .stCaption, p, span, label, div {
        color: #E2E8F0 !important;
    }
    /* Metric values and labels */
    [data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    [data-testid="stMetricDelta"] { color: #94A3B8 !important; }
    /* Headings */
    h1, h2, h3, h4 { color: #F8FAFC !important; }
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #0F172A !important; }
    section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
    /* Dataframe */
    [data-testid="stDataFrame"] { color: #E2E8F0 !important; }
    /* Selectbox / multiselect labels */
    .stSelectbox label, .stMultiSelect label, .stRadio label { color: #CBD5E1 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Theme colors ─────────────────────────────────────────────────────────────

COLORS = {
    "primary":   "#2563EB",
    "success":   "#16A34A",
    "warning":   "#D97706",
    "danger":    "#DC2626",
    "neutral":   "#6B7280",
    "bg_card":   "#F8FAFC",
}

RISK_COLORS = {
    "critical": COLORS["danger"],
    "high":     COLORS["warning"],
    "medium":   "#F59E0B",
    "low":      COLORS["success"],
}

MARKET_COLORS = {
    "Atlanta":   "#2563EB",
    "Dallas":    "#7C3AED",
    "Charlotte": "#0891B2",
}

# ─── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    def read(name, fallback=None):
        path = DATA_DIR / f"{name}.csv"
        if path.exists():
            return pd.read_csv(path)
        if fallback:
            return pd.read_csv(DATA_DIR / f"{fallback}.csv")
        return pd.DataFrame()

    properties  = read("properties")
    vendors     = read("vendors")
    tenants     = read("tenants_scored", "tenants")
    work_orders = read("work_orders_classified", "work_orders")
    payments    = read("payments")
    invoices    = read("invoices")
    ledger      = read("financial_ledger")
    vendor_recs = read("vendor_recommendations")

    # Type coercions
    ledger["year_month"] = pd.to_datetime(ledger["year_month"])
    work_orders["created_at"] = pd.to_datetime(work_orders["created_at"])
    if "resolution_hours" in work_orders.columns:
        work_orders["resolution_hours"] = pd.to_numeric(work_orders["resolution_hours"], errors="coerce")
    if "churn_score" in tenants.columns:
        tenants["churn_score"] = pd.to_numeric(tenants["churn_score"], errors="coerce")

    return properties, vendors, tenants, work_orders, payments, invoices, ledger, vendor_recs

properties, vendors, tenants, work_orders, payments, invoices, ledger, vendor_recs = load_data()

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏢 PropIQ")
    st.markdown("*AI-Powered Portfolio Intelligence*")
    st.divider()

    panel = st.radio(
        "Navigation",
        ["Portfolio Overview", "Financial Summary", "Maintenance Operations",
         "Tenant Health & Churn", "Vendor Scorecard"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"**Properties:** {len(properties)}")
    st.caption(f"**Tenants:** {len(tenants)}")
    st.caption(f"**Work Orders:** {len(work_orders)}")
    st.caption(f"**Vendors:** {len(vendors)}")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def kpi(label, value, delta=None, delta_color="normal"):
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)

def section(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 1 — Portfolio Overview
# ═══════════════════════════════════════════════════════════════════════════════

if panel == "Portfolio Overview":
    st.title("Portfolio Overview")
    st.caption("All 50 properties across Atlanta, Dallas, and Charlotte")
    st.divider()

    # ── KPI row ──
    total_units    = properties["unit_count"].sum()
    portfolio_val  = properties["market_value"].sum()
    total_revenue  = payments[payments["payment_status"] != "missed"]["amount_paid"].sum()
    monthly_rev    = total_revenue / 12
    avg_age        = properties["age_years"].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi("Total Units", f"{total_units:,}")
    with col2:
        kpi("Portfolio Value", f"${portfolio_val/1_000_000:.1f}M")
    with col3:
        kpi("Avg Monthly Revenue", f"${monthly_rev:,.0f}")
    with col4:
        kpi("Avg Property Age", f"{avg_age:.0f} yrs")

    st.divider()

    # ── Market comparison ──
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        section("Market Breakdown")
        market_stats = properties.groupby("market").agg(
            Properties=("property_id", "count"),
            Total_Units=("unit_count", "sum"),
            Avg_Value=("market_value", "mean"),
            Total_Sqft=("total_sqft", "sum"),
        ).reset_index()

        ledger_market = ledger.merge(
            properties[["property_id","market"]], on="property_id"
        ).groupby("market").agg(Avg_NOI=("noi", "mean")).reset_index()
        market_stats = market_stats.merge(ledger_market, on="market")

        fig = go.Figure()
        for mkt in market_stats["market"]:
            row = market_stats[market_stats["market"] == mkt].iloc[0]
            fig.add_trace(go.Bar(
                name=mkt,
                x=["Properties", "Total Units (÷10)", "Avg NOI ($K)"],
                y=[row["Properties"], row["Total_Units"] / 10, row["Avg_NOI"] / 1000],
                marker_color=MARKET_COLORS[mkt],
            ))
        fig.update_layout(
            barmode="group", height=320,
            margin=dict(t=20, b=20, l=0, r=0),
            legend=dict(orientation="h", y=-0.15),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        section("Property Types")
        ptype_counts = properties["property_type"].value_counts().reset_index()
        ptype_counts.columns = ["type", "count"]
        fig2 = px.pie(
            ptype_counts, names="type", values="count",
            color_discrete_sequence=[COLORS["primary"], "#7C3AED", "#0891B2"],
            hole=0.45,
        )
        fig2.update_layout(
            height=320, margin=dict(t=20, b=20, l=0, r=0),
            showlegend=True, legend=dict(orientation="h", y=-0.1),
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Property table ──
    section("All Properties")
    market_filter = st.multiselect(
        "Filter by market", options=properties["market"].unique().tolist(),
        default=properties["market"].unique().tolist()
    )
    filtered = properties[properties["market"].isin(market_filter)]

    # Merge NOI
    prop_noi = ledger.groupby("property_id").agg(
        Avg_Monthly_NOI=("noi", "mean"),
        Total_NOI=("noi", "sum"),
    ).reset_index()
    filtered = filtered.merge(prop_noi, on="property_id", how="left")

    display = filtered[[
        "property_id","name","market","neighborhood","property_type",
        "unit_count","market_value","Avg_Monthly_NOI"
    ]].copy()
    display["market_value"]     = display["market_value"].apply(lambda x: f"${x:,.0f}")
    display["Avg_Monthly_NOI"]  = display["Avg_Monthly_NOI"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
    display.columns = ["ID","Name","Market","Neighborhood","Type","Units","Market Value","Avg Monthly NOI"]
    st.dataframe(display, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 2 — Financial Summary
# ═══════════════════════════════════════════════════════════════════════════════

elif panel == "Financial Summary":
    st.title("Financial Summary")
    st.caption("Revenue, expenses, and net operating income across the portfolio")
    st.divider()

    # Market filter
    mkt_filter = st.selectbox("Market", ["All Markets"] + sorted(properties["market"].unique().tolist()))

    if mkt_filter != "All Markets":
        prop_ids = properties[properties["market"] == mkt_filter]["property_id"].tolist()
        ledger_f = ledger[ledger["property_id"].isin(prop_ids)]
    else:
        ledger_f = ledger

    # ── KPI row ──
    total_rev  = ledger_f["revenue"].sum()
    total_exp  = ledger_f["expenses"].sum()
    total_noi  = ledger_f["noi"].sum()
    noi_margin = total_noi / total_rev * 100 if total_rev else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi("Total Revenue", f"${total_rev:,.0f}")
    with col2:
        kpi("Total Expenses", f"${total_exp:,.0f}")
    with col3:
        kpi("Net Operating Income", f"${total_noi:,.0f}")
    with col4:
        kpi("NOI Margin", f"{noi_margin:.1f}%")

    st.divider()

    # ── Revenue vs Expenses trend ──
    section("Monthly Portfolio Trend")
    monthly = ledger_f.groupby("year_month").agg(
        Revenue=("revenue", "sum"),
        Expenses=("expenses", "sum"),
        NOI=("noi", "sum"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["Revenue"],
        name="Revenue", line=dict(color=COLORS["success"], width=2.5), fill="tozeroy",
        fillcolor="rgba(22,163,74,0.08)"
    ))
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["Expenses"],
        name="Expenses", line=dict(color=COLORS["danger"], width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["NOI"],
        name="NOI", line=dict(color=COLORS["primary"], width=2.5, dash="dot")
    ))
    fig.update_layout(
        height=320, margin=dict(t=10, b=20, l=0, r=0),
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"),
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(tickprefix="$", tickformat=",", color="#E2E8F0"),
        xaxis=dict(color="#E2E8F0"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Top / Bottom properties by NOI ──
    col_l, col_r = st.columns(2)

    prop_noi = ledger_f.groupby("property_id").agg(Total_NOI=("noi", "sum")).reset_index()
    prop_noi = prop_noi.merge(properties[["property_id","name","market"]], on="property_id")
    prop_noi = prop_noi.sort_values("Total_NOI", ascending=False)

    with col_l:
        section("Top 10 Properties by NOI")
        top10 = prop_noi.head(10)
        fig_top = px.bar(
            top10, x="Total_NOI", y="name", orientation="h",
            color="market", color_discrete_map=MARKET_COLORS,
            labels={"Total_NOI": "Total NOI ($)", "name": ""},
        )
        fig_top.update_layout(
            height=350, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"),
            showlegend=False,
            xaxis=dict(tickprefix="$", tickformat=","),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col_r:
        section("Bottom 10 Properties by NOI")
        bot10 = prop_noi.tail(10).sort_values("Total_NOI")
        fig_bot = px.bar(
            bot10, x="Total_NOI", y="name", orientation="h",
            color="market", color_discrete_map=MARKET_COLORS,
            labels={"Total_NOI": "Total NOI ($)", "name": ""},
        )
        fig_bot.update_layout(
            height=350, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"),
            showlegend=False,
            xaxis=dict(tickprefix="$", tickformat=","),
        )
        st.plotly_chart(fig_bot, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 3 — Maintenance Operations
# ═══════════════════════════════════════════════════════════════════════════════

elif panel == "Maintenance Operations":
    st.title("Maintenance Operations")
    st.caption("Work order pipeline, AI classifier performance, and vendor routing")
    st.divider()

    # ── KPI row ──
    total_wo   = len(work_orders)
    open_wo    = len(work_orders[work_orders["status"] == "open"])
    in_prog    = len(work_orders[work_orders["status"] == "in-progress"])
    resolved   = len(work_orders[work_orders["status"] == "resolved"])
    avg_res    = work_orders[work_orders["status"] == "resolved"]["resolution_hours"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: kpi("Total Work Orders", f"{total_wo:,}")
    with col2: kpi("Open", f"{open_wo:,}", delta_color="inverse")
    with col3: kpi("In Progress", f"{in_prog:,}")
    with col4: kpi("Resolved", f"{resolved:,}")
    with col5: kpi("Avg Resolution", f"{avg_res:.1f} hrs")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        section("Work Orders by Trade")
        trade_counts = work_orders["trade"].value_counts().reset_index()
        trade_counts.columns = ["trade", "count"]
        fig = px.bar(
            trade_counts, x="trade", y="count",
            color="trade",
            color_discrete_sequence=[COLORS["primary"], "#7C3AED", "#0891B2", COLORS["warning"]],
            labels={"trade": "", "count": "Work Orders"},
        )
        fig.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"), showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        section("Work Orders by Urgency")
        urgency_counts = work_orders["urgency"].value_counts().reset_index()
        urgency_counts.columns = ["urgency", "count"]
        urgency_order = ["emergency", "high", "medium", "low"]
        urgency_colors = [COLORS["danger"], COLORS["warning"], "#F59E0B", COLORS["success"]]
        urgency_counts["urgency"] = pd.Categorical(urgency_counts["urgency"], categories=urgency_order, ordered=True)
        urgency_counts = urgency_counts.sort_values("urgency")
        fig2 = px.bar(
            urgency_counts, x="urgency", y="count",
            color="urgency",
            color_discrete_sequence=urgency_colors,
            labels={"urgency": "", "count": "Work Orders"},
        )
        fig2.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"), showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── AI Classifier accuracy ──
    if "predicted_trade" in work_orders.columns and work_orders["predicted_trade"].notna().any():
        section("AI Classifier Performance", "Gemini predictions vs ground-truth labels")
        classified = work_orders[work_orders["predicted_trade"].notna() & (work_orders["predicted_trade"] != "")]
        trade_acc   = (classified["trade_match"] == "true").mean() * 100 if "trade_match" in classified.columns else None
        urgency_acc = (classified["urgency_match"] == "true").mean() * 100 if "urgency_match" in classified.columns else None

        col1, col2, col3 = st.columns(3)
        with col1: kpi("Orders Classified", f"{len(classified):,}")
        with col2: kpi("Trade Accuracy", f"{trade_acc:.1f}%" if trade_acc else "—")
        with col3: kpi("Urgency Accuracy", f"{urgency_acc:.1f}%" if urgency_acc else "—")

        if "ai_confidence" in classified.columns:
            avg_conf = pd.to_numeric(classified["ai_confidence"], errors="coerce").mean()
            conf_col, _ = st.columns([1, 3])
            with conf_col:
                st.metric("Avg Confidence", f"{avg_conf:.2f}")
        st.divider()

    # ── Avg resolution by urgency ──
    section("Avg Resolution Time by Urgency (hours)")
    res_by_urgency = (
        work_orders[work_orders["status"] == "resolved"]
        .groupby("urgency")["resolution_hours"]
        .mean()
        .reset_index()
    )
    res_by_urgency.columns = ["urgency", "avg_hours"]
    res_by_urgency["urgency"] = pd.Categorical(
        res_by_urgency["urgency"], categories=["emergency","high","medium","low"], ordered=True
    )
    res_by_urgency = res_by_urgency.sort_values("urgency")

    fig3 = px.bar(
        res_by_urgency, x="urgency", y="avg_hours",
        color="urgency",
        color_discrete_sequence=[COLORS["danger"], COLORS["warning"], "#F59E0B", COLORS["success"]],
        labels={"urgency": "", "avg_hours": "Avg Hours"},
        text=res_by_urgency["avg_hours"].apply(lambda x: f"{x:.1f}h"),
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(
        height=280, margin=dict(t=30, b=10, l=0, r=0),
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"), showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # ── Open work orders with vendor recommendations ──
    section("Open Work Orders — AI Vendor Recommendations")
    open_orders = work_orders[work_orders["status"].isin(["open", "in-progress"])].copy()

    if not vendor_recs.empty:
        open_display = open_orders.merge(
            vendor_recs[["work_order_id","recommended_vendor_name","match_score","vendor_sla_pct","vendor_response_hrs"]],
            on="work_order_id", how="left"
        )
    else:
        open_display = open_orders.copy()
        open_display["recommended_vendor_name"] = "Run ai_engine.py"
        open_display["match_score"] = "—"

    cols_to_show = ["work_order_id","property_id","trade","urgency","status","description",
                    "recommended_vendor_name","match_score"]
    cols_available = [c for c in cols_to_show if c in open_display.columns]
    st.dataframe(
        open_display[cols_available].head(50).rename(columns={
            "work_order_id": "ID", "property_id": "Property",
            "recommended_vendor_name": "Recommended Vendor", "match_score": "Match Score",
        }),
        use_container_width=True, hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 4 — Tenant Health & Churn
# ═══════════════════════════════════════════════════════════════════════════════

elif panel == "Tenant Health & Churn":
    st.title("Tenant Health & Churn Risk")
    st.caption("AI-scored churn risk and payment health across 500 tenants")
    st.divider()

    # ── KPI row ──
    has_churn = "churn_risk_level" in tenants.columns
    total_tenants = len(tenants)
    at_risk_count = tenants["at_risk"].astype(str).str.lower().eq("true").sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi("Total Tenants", f"{total_tenants:,}")
    with col2: kpi("At-Risk Tenants", f"{at_risk_count:,}")
    with col3:
        if has_churn:
            critical = (tenants["churn_risk_level"] == "critical").sum()
            kpi("Critical Risk", f"{critical:,}", delta_color="inverse")
    with col4:
        missed_rev = payments[payments["payment_status"] == "missed"]["amount_due"].sum()
        kpi("Missed Revenue", f"${missed_rev:,.0f}", delta_color="inverse")

    st.divider()

    col_l, col_r = st.columns([1, 1.4])

    with col_l:
        section("Churn Risk Distribution")
        if has_churn:
            risk_counts = tenants["churn_risk_level"].value_counts().reset_index()
            risk_counts.columns = ["level", "count"]
            order = ["critical","high","medium","low"]
            risk_counts["level"] = pd.Categorical(risk_counts["level"], categories=order, ordered=True)
            risk_counts = risk_counts.sort_values("level")
            fig = px.bar(
                risk_counts, x="level", y="count",
                color="level",
                color_discrete_map=RISK_COLORS,
                labels={"level": "", "count": "Tenants"},
                text="count",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=300, margin=dict(t=30, b=10, l=0, r=0),
                plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run ai_engine.py to generate churn scores.")

    with col_r:
        section("Payment Outcomes")
        outcome_counts = payments["payment_status"].value_counts().reset_index()
        outcome_counts.columns = ["status", "count"]
        pct = outcome_counts.copy()
        pct["pct"] = (pct["count"] / pct["count"].sum() * 100).round(1)
        fig2 = px.pie(
            pct, names="status", values="count",
            color="status",
            color_discrete_map={
                "on_time":  COLORS["success"],
                "late":     COLORS["warning"],
                "missed":   COLORS["danger"],
            },
            hole=0.45,
        )
        fig2.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation="h", y=-0.1),
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Top at-risk tenants table ──
    section("Top 20 At-Risk Tenants")
    at_risk_df = tenants[tenants["at_risk"].astype(str).str.lower() == "true"].copy()

    if has_churn:
        at_risk_df = at_risk_df.sort_values("churn_score", ascending=False)
        cols = ["tenant_id","first_name","last_name","property_id","monthly_rent",
                "days_remaining","satisfaction_score","late_payment_rate",
                "missed_payment_rate","churn_score","churn_risk_level"]
    else:
        cols = ["tenant_id","first_name","last_name","property_id","monthly_rent",
                "satisfaction_score"]

    cols_available = [c for c in cols if c in at_risk_df.columns]
    display = at_risk_df[cols_available].head(20).copy()

    rename_map = {
        "tenant_id": "ID", "first_name": "First", "last_name": "Last",
        "property_id": "Property", "monthly_rent": "Rent",
        "days_remaining": "Days Left", "satisfaction_score": "Satisfaction",
        "late_payment_rate": "Late Rate", "missed_payment_rate": "Missed Rate",
        "churn_score": "Churn Score", "churn_risk_level": "Risk Level",
    }
    display = display.rename(columns={k: v for k, v in rename_map.items() if k in display.columns})
    if "Rent" in display.columns:
        display["Rent"] = display["Rent"].apply(lambda x: f"${x:,.0f}")
    if "Late Rate" in display.columns:
        display["Late Rate"] = display["Late Rate"].apply(lambda x: f"{float(x)*100:.0f}%")
    if "Missed Rate" in display.columns:
        display["Missed Rate"] = display["Missed Rate"].apply(lambda x: f"{float(x)*100:.0f}%")

    st.dataframe(display, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 5 — Vendor Scorecard
# ═══════════════════════════════════════════════════════════════════════════════

elif panel == "Vendor Scorecard":
    st.title("Vendor Scorecard")
    st.caption("Performance rankings across 30 vendors by specialty")
    st.divider()

    # ── KPI row ──
    avg_sla     = vendors["sla_compliance_pct"].mean()
    avg_quality = vendors["quality_rating"].mean()
    avg_resp    = vendors["avg_response_hours"].mean()
    top_vendor  = vendors.loc[vendors["quality_rating"].idxmax(), "company_name"]

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi("Avg SLA Compliance", f"{avg_sla:.1f}%")
    with col2: kpi("Avg Quality Rating", f"{avg_quality:.2f}/5.0")
    with col3: kpi("Avg Response Time", f"{avg_resp:.1f} hrs")
    with col4: kpi("Top Rated Vendor", top_vendor)

    st.divider()

    # ── Specialty filter ──
    specialty_filter = st.selectbox(
        "Filter by Specialty",
        ["All Specialties"] + sorted(vendors["specialty"].unique().tolist())
    )

    if specialty_filter != "All Specialties":
        vendors_f = vendors[vendors["specialty"] == specialty_filter].copy()
    else:
        vendors_f = vendors.copy()

    # ── Composite score ──
    max_resp = vendors["avg_response_hours"].max()
    vendors_f = vendors_f.copy()
    vendors_f["composite_score"] = (
        vendors_f["sla_compliance_pct"] / 100 * 40 +
        (vendors_f["quality_rating"] - 1) / 4 * 35 +
        (1 - vendors_f["avg_response_hours"] / max_resp) * 25
    ).round(1)
    vendors_f = vendors_f.sort_values("composite_score", ascending=False)

    # ── Scatter: quality vs SLA ──
    col_l, col_r = st.columns([1.5, 1])

    with col_l:
        section("Quality Rating vs SLA Compliance")
        fig = px.scatter(
            vendors_f,
            x="sla_compliance_pct", y="quality_rating",
            color="specialty", size="composite_score",
            hover_name="company_name",
            labels={
                "sla_compliance_pct": "SLA Compliance (%)",
                "quality_rating": "Quality Rating",
                "specialty": "Specialty",
            },
        )
        fig.update_layout(
            height=350, margin=dict(t=10, b=10, l=0, r=0),
            plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font=dict(color="#E2E8F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        section("Top Vendor per Specialty")
        top_per_specialty = (
            vendors.sort_values("quality_rating", ascending=False)
            .groupby("specialty")
            .first()
            .reset_index()[["specialty","company_name","quality_rating","sla_compliance_pct"]]
        )
        top_per_specialty.columns = ["Specialty","Top Vendor","Rating","SLA %"]
        st.dataframe(top_per_specialty, use_container_width=True, hide_index=True)

    st.divider()

    # ── Full vendor table ──
    section("All Vendors — Ranked by Composite Score")
    display = vendors_f[[
        "vendor_id","company_name","specialty","hourly_rate",
        "avg_response_hours","sla_compliance_pct","quality_rating","composite_score"
    ]].copy()
    display["hourly_rate"] = display["hourly_rate"].apply(lambda x: f"${x:.0f}/hr")
    display.columns = ["ID","Company","Specialty","Rate","Avg Response (hrs)","SLA %","Quality","Score"]
    st.dataframe(display, use_container_width=True, hide_index=True)
