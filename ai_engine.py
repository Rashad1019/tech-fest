"""
Phase 2: AI Engine
  1. Work Order Classifier  — Gemini classifies free-text descriptions → trade + urgency
  2. Churn Risk Predictor   — Scoring model flags at-risk tenants
  3. Smart Vendor Router    — Ranks vendors per open work order
"""

import csv
import json
from google import genai
import os
import time
from collections import defaultdict
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

MODEL_ID    = "gemini-3.1-flash-lite-preview"
API_KEY     = os.environ["GEMINI_API_KEY"]
DATA_DIR    = Path("data")
OUTPUT_DIR  = Path("data")
BATCH_SIZE  = 20   # work orders per API call

client = genai.Client(api_key=API_KEY)


# ─── Loaders ─────────────────────────────────────────────────────────────────

def load(name):
    return list(csv.DictReader(open(DATA_DIR / f"{name}.csv", encoding="utf-8")))

def write_csv(name, rows, fieldnames):
    path = OUTPUT_DIR / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>5} rows → {path}")


# ─── 1. Work Order Classifier ─────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
You are a property maintenance classifier. For each work order description below, return a JSON array where each element has:
  - "id": the work_order_id
  - "predicted_trade": one of ["plumbing", "HVAC", "electrical", "general"]
  - "predicted_urgency": one of ["emergency", "high", "medium", "low"]
  - "confidence": a float 0.0–1.0

Work orders:
{items}

Respond with ONLY the JSON array, no explanation.
"""

def classify_batch(batch):
    items = "\n".join(
        f'{i+1}. [{wo["work_order_id"]}] {wo["description"]}'
        for i, wo in enumerate(batch)
    )
    prompt = CLASSIFY_PROMPT.format(items=items)
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    text = response.text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def classify_work_orders(work_orders):
    print(f"\n[1/3] Classifying {len(work_orders)} work orders in batches of {BATCH_SIZE}...")
    results = {}  # work_order_id -> classification

    batches = [work_orders[i:i+BATCH_SIZE] for i in range(0, len(work_orders), BATCH_SIZE)]
    for idx, batch in enumerate(batches):
        print(f"  batch {idx+1}/{len(batches)} ({len(batch)} orders)...", end=" ", flush=True)
        try:
            classified = classify_batch(batch)
            for item in classified:
                results[item["id"]] = item
            print("ok")
        except Exception as e:
            print(f"error: {e} — skipping batch")
        time.sleep(0.5)  # gentle rate limiting

    # Merge classifications back into work orders
    output = []
    for wo in work_orders:
        c = results.get(wo["work_order_id"], {})
        output.append({
            **wo,
            "predicted_trade":    c.get("predicted_trade", ""),
            "predicted_urgency":  c.get("predicted_urgency", ""),
            "ai_confidence":      c.get("confidence", ""),
            "trade_match":        "true" if c.get("predicted_trade") == wo["trade"] else "false",
            "urgency_match":      "true" if c.get("predicted_urgency") == wo["urgency"] else "false",
        })

    write_csv("work_orders_classified", output, [
        "work_order_id","tenant_id","property_id","unit_number","trade","urgency","status",
        "description","created_at","resolved_at","resolution_hours","assigned_vendor",
        "predicted_trade","predicted_urgency","ai_confidence","trade_match","urgency_match",
    ])

    # Accuracy summary
    classified_count = sum(1 for wo in output if wo["predicted_trade"])
    trade_correct   = sum(1 for wo in output if wo["trade_match"] == "true")
    urgency_correct = sum(1 for wo in output if wo["urgency_match"] == "true")
    print(f"  Trade accuracy:   {trade_correct}/{classified_count} = {trade_correct/classified_count*100:.1f}%")
    print(f"  Urgency accuracy: {urgency_correct}/{classified_count} = {urgency_correct/classified_count*100:.1f}%")
    return output


# ─── 2. Churn Risk Predictor ──────────────────────────────────────────────────

"""
Churn score (0–100) built from 5 weighted signals:

  Signal                  Weight   Direction
  ─────────────────────── ──────   ─────────
  Late payment rate          25    higher = worse
  Missed payment rate        30    higher = worse
  Days remaining on lease    20    fewer days = worse
  Satisfaction score         15    lower = worse
  Work order complaint count 10    more complaints = worse
"""

def score_tenants(tenants, payments, work_orders):
    print("\n[2/3] Scoring tenant churn risk...")

    # Payment stats per tenant
    pay_stats = defaultdict(lambda: {"total": 0, "late": 0, "missed": 0})
    for p in payments:
        tid = p["tenant_id"]
        pay_stats[tid]["total"] += 1
        if p["payment_status"] == "late":
            pay_stats[tid]["late"] += 1
        elif p["payment_status"] == "missed":
            pay_stats[tid]["missed"] += 1

    # Work order count per tenant
    wo_count = defaultdict(int)
    for wo in work_orders:
        wo_count[wo["tenant_id"]] += 1

    from datetime import date
    today = date(2025, 6, 1)

    output = []
    for t in tenants:
        tid  = t["tenant_id"]
        ps   = pay_stats[tid]
        total_pays = ps["total"] or 1

        late_rate   = ps["late"]   / total_pays
        missed_rate = ps["missed"] / total_pays

        lease_end      = date.fromisoformat(t["lease_end"])
        days_remaining = (lease_end - today).days
        # Normalize: 0 days or less → 1.0 risk, 365+ days → 0.0 risk
        lease_risk = max(0.0, min(1.0, 1 - (days_remaining / 365)))

        satisfaction = float(t["satisfaction_score"])
        sat_risk = (5.0 - satisfaction) / 4.0   # 1.0 = worst (1.0 score), 0.0 = best (5.0)

        complaints = wo_count[tid]
        complaint_risk = min(1.0, complaints / 8)  # cap at 8 complaints = full risk

        score = (
            late_rate    * 25 +
            missed_rate  * 30 +
            lease_risk   * 20 +
            sat_risk     * 15 +
            complaint_risk * 10
        )
        score = round(min(100, score * 100 / 100 * 1.8), 1)  # scale to 0-100 range
        score = round(min(100, score), 1)

        if score >= 70:
            risk_level = "critical"
        elif score >= 45:
            risk_level = "high"
        elif score >= 22:
            risk_level = "medium"
        else:
            risk_level = "low"

        output.append({
            **t,
            "late_payment_rate":   round(late_rate, 3),
            "missed_payment_rate": round(missed_rate, 3),
            "days_remaining":      days_remaining,
            "complaint_count":     complaints,
            "churn_score":         score,
            "churn_risk_level":    risk_level,
        })

    write_csv("tenants_scored", output, [
        "tenant_id","first_name","last_name","property_id","unit_number",
        "lease_start","lease_end","monthly_rent","security_deposit","move_in_date",
        "satisfaction_score","at_risk",
        "late_payment_rate","missed_payment_rate","days_remaining",
        "complaint_count","churn_score","churn_risk_level",
    ])

    dist = defaultdict(int)
    for row in output:
        dist[row["churn_risk_level"]] += 1
    print(f"  critical={dist['critical']}  high={dist['high']}  medium={dist['medium']}  low={dist['low']}")
    return output


# ─── 3. Smart Vendor Router ───────────────────────────────────────────────────

"""
Vendor match score (0–100) for a given work order:

  Factor              Weight
  ──────────────────  ──────
  SLA compliance %      40
  Quality rating        35
  Response time (inv)   25   (faster = higher score)
"""

def route_vendors(work_orders, vendors):
    print("\n[3/3] Routing vendors for open/in-progress work orders...")

    # Index vendors by specialty
    by_specialty = defaultdict(list)
    for v in vendors:
        by_specialty[v["specialty"]].append(v)

    # Max response time across all vendors (for normalization)
    max_response = max(float(v["avg_response_hours"]) for v in vendors)

    open_orders = [wo for wo in work_orders if wo["status"] in ("open", "in-progress")]

    output = []
    for wo in open_orders:
        candidates = by_specialty.get(wo["trade"], [])
        if not candidates:
            candidates = vendors  # fallback to all vendors

        scored = []
        for v in candidates:
            sla_score      = float(v["sla_compliance_pct"]) / 100 * 40
            quality_score  = (float(v["quality_rating"]) - 1) / 4 * 35  # 1–5 → 0–35
            response_score = (1 - float(v["avg_response_hours"]) / max_response) * 25
            total = round(sla_score + quality_score + response_score, 2)
            scored.append((total, v))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_score, top_vendor = scored[0]

        output.append({
            "work_order_id":        wo["work_order_id"],
            "property_id":          wo["property_id"],
            "trade":                wo["trade"],
            "urgency":              wo["urgency"],
            "status":               wo["status"],
            "recommended_vendor_id":   top_vendor["vendor_id"],
            "recommended_vendor_name": top_vendor["company_name"],
            "match_score":          round(top_score, 1),
            "vendor_sla_pct":       top_vendor["sla_compliance_pct"],
            "vendor_quality":       top_vendor["quality_rating"],
            "vendor_response_hrs":  top_vendor["avg_response_hours"],
        })

    write_csv("vendor_recommendations", output, [
        "work_order_id","property_id","trade","urgency","status",
        "recommended_vendor_id","recommended_vendor_name","match_score",
        "vendor_sla_pct","vendor_quality","vendor_response_hrs",
    ])
    print(f"  routed {len(output)} open/in-progress work orders")
    return output


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Phase 2: AI Engine starting...\n")

    work_orders = load("work_orders")
    tenants     = load("tenants")
    payments    = load("payments")
    vendors     = load("vendors")

    classify_work_orders(work_orders)
    score_tenants(tenants, payments, work_orders)
    route_vendors(work_orders, vendors)

    print("\nPhase 2 complete. Output files:")
    print("  data/work_orders_classified.csv")
    print("  data/tenants_scored.csv")
    print("  data/vendor_recommendations.csv")
