"""
Phase 1: Synthetic Property Management Data Generator
Outputs 7 CSV files: properties, tenants, work_orders, vendors, payments, invoices, financial_ledger
"""

import csv
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── Config ──────────────────────────────────────────────────────────────────

MARKETS = {
    "Atlanta": ["Midtown", "Buckhead", "Decatur", "Sandy Springs", "East Point"],
    "Dallas":  ["Uptown", "Deep Ellum", "Frisco", "Plano", "Oak Cliff"],
    "Charlotte": ["South End", "NoDa", "Ballantyne", "Dilworth", "University City"],
}

PROPERTY_TYPES = ["multifamily", "commercial", "mixed-use"]
PROPERTY_TYPE_WEIGHTS = [0.60, 0.25, 0.15]

VENDOR_SPECIALTIES = ["plumbing", "HVAC", "electrical", "general", "roofing", "painting", "landscaping"]

WORK_ORDER_TEMPLATES = {
    "plumbing": [
        "Kitchen faucet dripping nonstop, water pooling under the sink",
        "Toilet won't stop running, sounds like it's constantly refilling",
        "Shower drain completely clogged, water backing up",
        "Hot water heater making popping sounds, no hot water",
        "Pipe under bathroom vanity is leaking, cabinet floor is wet",
        "Garbage disposal jammed and won't turn on",
        "Low water pressure throughout entire unit",
        "Bathtub faucet handle broken off, can't turn water off",
        "Dishwasher not draining, standing water at the bottom",
        "Water stain appearing on ceiling — possible leak from unit above",
    ],
    "HVAC": [
        "AC unit making grinding noise, unit is 85 degrees",
        "Heater blowing cold air, thermostat set to 72",
        "HVAC filter clogged, air quality seems poor",
        "AC not cooling below 78 even on max setting",
        "Furnace won't ignite, no heat in unit",
        "Strange burning smell coming from air vents",
        "Thermostat unresponsive, screen is blank",
        "AC unit leaking water onto the floor",
        "Loud banging noise every time heat kicks on",
        "Vents blowing hot air when AC is set to cool",
    ],
    "electrical": [
        "Outlet in kitchen sparks when plugging in appliances",
        "Circuit breaker keeps tripping for bedroom circuit",
        "Two light switches not working, bulbs already replaced",
        "Power went out in half the unit, breaker won't reset",
        "Flickering lights throughout the apartment",
        "Ceiling fan making humming noise and spinning slowly",
        "Smoke detector chirping every 30 seconds",
        "Exterior outlet has no power, GFCI keeps tripping",
        "Dryer outlet not providing power",
        "Light fixture in bathroom buzzing loudly",
    ],
    "general": [
        "Front door lock sticking, key requires extreme force",
        "Window seal broken, condensation between panes",
        "Patio door off track, won't slide properly",
        "Hole in drywall in hallway, about the size of a fist",
        "Bedroom closet door won't close, keeps swinging open",
        "Mold spots appearing on bathroom ceiling near vent",
        "Cabinet hinge in kitchen broken, door hanging loose",
        "Garage door opener stopped responding to remote",
        "Carpet edge pulling up near entryway, tripping hazard",
        "Intercom/doorbell not working, can't hear buzzer",
    ],
}

URGENCY_WEIGHTS = {
    "emergency": 0.08,
    "high":      0.22,
    "medium":    0.45,
    "low":       0.25,
}

URGENCY_RESOLUTION_DAYS = {
    "emergency": (0.1, 1),
    "high":      (1,   4),
    "medium":    (3,  10),
    "low":       (7,  21),
}

STATUS_WEIGHTS = {"open": 0.15, "in-progress": 0.20, "resolved": 0.65}

PAYMENT_METHODS = ["ACH", "check", "credit_card", "money_order"]
PAYMENT_METHOD_WEIGHTS = [0.55, 0.20, 0.18, 0.07]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def uid():
    return str(uuid.uuid4())[:8].upper()

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

def write_csv(name: str, rows: list[dict], fieldnames: list[str]):
    path = OUTPUT_DIR / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>5} rows → {path}")


# ─── 1. Properties ───────────────────────────────────────────────────────────

def gen_properties(n=50):
    rows = []
    markets = list(MARKETS.keys())
    per_market = n // len(markets)
    remainder  = n % len(markets)

    prop_id = 1
    for i, market in enumerate(markets):
        count = per_market + (1 if i < remainder else 0)
        neighborhoods = MARKETS[market]
        for _ in range(count):
            ptype = weighted_choice(PROPERTY_TYPES, PROPERTY_TYPE_WEIGHTS)
            if ptype == "multifamily":
                units = random.randint(20, 200)
                sqft  = units * random.randint(750, 1200)
            elif ptype == "commercial":
                units = random.randint(5, 40)
                sqft  = units * random.randint(800, 3000)
            else:
                units = random.randint(10, 80)
                sqft  = units * random.randint(900, 1800)

            year_built    = random.randint(1975, 2022)
            age           = 2025 - year_built
            market_value  = round(sqft * random.uniform(120, 380), -3)
            rows.append({
                "property_id":    f"P{prop_id:03d}",
                "name":           f"{random.choice(neighborhoods)} {random.choice(['Place','Commons','Residences','Park','Point','Flats'])}",
                "market":         market,
                "neighborhood":   random.choice(neighborhoods),
                "property_type":  ptype,
                "unit_count":     units,
                "total_sqft":     sqft,
                "year_built":     year_built,
                "age_years":      age,
                "market_value":   int(market_value),
            })
            prop_id += 1
    return rows

PROPERTIES = gen_properties()


# ─── 2. Vendors ──────────────────────────────────────────────────────────────

COMPANY_PREFIXES = ["Apex", "BlueStar", "Cardinal", "Delta", "Elite", "Falcon",
                    "Granite", "Harbor", "Iron", "Keystone", "Liberty", "Metro",
                    "Noble", "Omega", "Peak", "Quantum", "Rapid", "Summit",
                    "Titan", "United", "Valor", "Western", "Xcel", "Zenith"]
COMPANY_SUFFIXES = ["Services", "Solutions", "Group", "Contractors", "Pro", "Works"]

def gen_vendors(n=30):
    rows = []
    used_names = set()
    specialties = (VENDOR_SPECIALTIES * 5)[:n]
    random.shuffle(specialties)

    for i in range(n):
        while True:
            name = f"{random.choice(COMPANY_PREFIXES)} {specialties[i].title()} {random.choice(COMPANY_SUFFIXES)}"
            if name not in used_names:
                used_names.add(name)
                break
        hourly_rate    = round(random.uniform(65, 195), 2)
        avg_response_h = round(random.uniform(1.5, 48), 1)
        sla_pct        = round(random.uniform(72, 99), 1)
        quality_rating = round(random.uniform(3.0, 5.0), 1)
        rows.append({
            "vendor_id":          f"V{i+1:03d}",
            "company_name":       name,
            "specialty":          specialties[i],
            "hourly_rate":        hourly_rate,
            "avg_response_hours": avg_response_h,
            "sla_compliance_pct": sla_pct,
            "quality_rating":     quality_rating,
            "active":             True,
        })
    return rows

VENDORS = gen_vendors()
VENDOR_BY_SPECIALTY = {}
for v in VENDORS:
    VENDOR_BY_SPECIALTY.setdefault(v["specialty"], []).append(v["vendor_id"])


# ─── 3. Tenants ──────────────────────────────────────────────────────────────

FIRST_NAMES = ["James","Maria","David","Sarah","Michael","Jennifer","Robert","Lisa",
               "William","Karen","Richard","Nancy","Joseph","Betty","Thomas","Sandra",
               "Charles","Dorothy","Christopher","Ashley","Daniel","Kimberly","Matthew",
               "Emily","Anthony","Donna","Mark","Michelle","Donald","Carol","Paul",
               "Amanda","Steven","Melissa","Andrew","Deborah","Kenneth","Stephanie",
               "George","Rebecca","Joshua","Laura","Kevin","Sharon","Brian","Cynthia",
               "Edward","Kathleen","Ronald","Amy","Timothy","Angela","Jason","Shirley",
               "Jeffrey","Anna","Ryan","Brenda","Jacob","Pamela","Gary","Emma",
               "Nicholas","Nicole","Eric","Helen","Jonathan","Samantha","Stephen","Katherine"]

LAST_NAMES  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
               "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
               "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
               "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
               "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
               "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell",
               "Carter","Roberts"]

def gen_tenants(n=500):
    rows = []
    prop_units = {}  # property_id -> list of available unit numbers
    for p in PROPERTIES:
        prop_units[p["property_id"]] = list(range(1, p["unit_count"] + 1))
        random.shuffle(prop_units[p["property_id"]])

    # Build pool of (property_id, unit_number) pairs proportional to unit count
    pool = []
    for p in PROPERTIES:
        for u in range(1, p["unit_count"] + 1):
            pool.append((p["property_id"], u))
    random.shuffle(pool)
    assignments = pool[:n]

    today = date(2025, 6, 1)

    for i, (prop_id, unit_num) in enumerate(assignments):
        prop = next(p for p in PROPERTIES if p["property_id"] == prop_id)
        ptype = prop["property_type"]

        # Rent range by property type
        if ptype == "multifamily":
            monthly_rent = round(random.uniform(950, 3200), -1)
        elif ptype == "commercial":
            monthly_rent = round(random.uniform(2000, 12000), -2)
        else:
            monthly_rent = round(random.uniform(1200, 5500), -2)

        lease_start = rand_date(date(2022, 1, 1), date(2024, 12, 1))
        lease_months = random.choice([6, 12, 12, 12, 24])
        lease_end   = lease_start + timedelta(days=lease_months * 30)
        move_in     = lease_start

        days_remaining = (lease_end - today).days
        # ~15% at-risk: lease expiring within 90 days, or small random cohort
        lease_expiring_soon = 0 <= days_remaining <= 90
        at_risk = (
            lease_expiring_soon and random.random() < 0.60
        ) or random.random() < 0.07

        satisfaction = round(random.uniform(1.5, 5.0) if at_risk else random.uniform(2.8, 5.0), 1)

        rows.append({
            "tenant_id":        f"T{i+1:04d}",
            "first_name":       random.choice(FIRST_NAMES),
            "last_name":        random.choice(LAST_NAMES),
            "property_id":      prop_id,
            "unit_number":      unit_num,
            "lease_start":      lease_start.isoformat(),
            "lease_end":        lease_end.isoformat(),
            "monthly_rent":     monthly_rent,
            "security_deposit": monthly_rent * random.choice([1, 1.5, 2]),
            "move_in_date":     move_in.isoformat(),
            "satisfaction_score": satisfaction,
            "at_risk":          at_risk,
        })
    return rows

TENANTS = gen_tenants()


# ─── 4. Work Orders ──────────────────────────────────────────────────────────

def gen_work_orders(n=2200):
    rows = []
    trade_list   = list(WORK_ORDER_TEMPLATES.keys())
    status_opts  = list(STATUS_WEIGHTS.keys())
    status_wts   = list(STATUS_WEIGHTS.values())
    urgency_opts = list(URGENCY_WEIGHTS.keys())
    urgency_wts  = list(URGENCY_WEIGHTS.values())

    start_window = date(2024, 6, 1)
    end_window   = date(2025, 6, 1)

    for i in range(n):
        tenant  = random.choice(TENANTS)
        trade   = random.choice(trade_list)
        urgency = weighted_choice(urgency_opts, urgency_wts)
        status  = weighted_choice(status_opts, status_wts)
        desc    = random.choice(WORK_ORDER_TEMPLATES[trade])

        created_dt = datetime.combine(rand_date(start_window, end_window),
                                      datetime.min.time()) + timedelta(hours=random.randint(7, 20))

        # Resolution time
        if status == "resolved":
            lo, hi = URGENCY_RESOLUTION_DAYS[urgency]
            res_days = random.uniform(lo, hi)
            resolved_dt = created_dt + timedelta(days=res_days)
            resolved_str = resolved_dt.strftime("%Y-%m-%d %H:%M")
            resolution_hours = round(res_days * 24, 1)
        else:
            resolved_str     = ""
            resolution_hours = ""

        # Assign vendor if in-progress or resolved
        if status in ("in-progress", "resolved"):
            vendor_pool = VENDOR_BY_SPECIALTY.get(trade, []) or [v["vendor_id"] for v in VENDORS]
            assigned_vendor = random.choice(vendor_pool)
        else:
            assigned_vendor = ""

        rows.append({
            "work_order_id":    f"WO{i+1:05d}",
            "tenant_id":        tenant["tenant_id"],
            "property_id":      tenant["property_id"],
            "unit_number":      tenant["unit_number"],
            "trade":            trade,
            "urgency":          urgency,
            "status":           status,
            "description":      desc,
            "created_at":       created_dt.strftime("%Y-%m-%d %H:%M"),
            "resolved_at":      resolved_str,
            "resolution_hours": resolution_hours,
            "assigned_vendor":  assigned_vendor,
        })
    return rows

WORK_ORDERS = gen_work_orders()


# ─── 5. Payments ─────────────────────────────────────────────────────────────

def gen_payments():
    rows = []
    pay_id = 1
    methods = PAYMENT_METHODS
    method_wts = PAYMENT_METHOD_WEIGHTS

    for tenant in TENANTS:
        lease_start = date.fromisoformat(tenant["lease_start"])
        lease_end   = date.fromisoformat(tenant["lease_end"])
        at_risk     = tenant["at_risk"]
        rent        = tenant["monthly_rent"]

        # Generate up to 12 months of history capped by lease dates and today
        today = date(2025, 6, 1)
        month_start = date(lease_start.year, lease_start.month, 1)
        months_generated = 0

        while month_start <= min(lease_end, today) and months_generated < 12:
            due_date = month_start.replace(day=1)

            # At-risk tenants have higher late/missed probability
            if at_risk:
                outcome = random.choices(
                    ["on_time", "late", "missed"],
                    weights=[0.55, 0.30, 0.15]
                )[0]
            else:
                outcome = random.choices(
                    ["on_time", "late", "missed"],
                    weights=[0.88, 0.10, 0.02]
                )[0]

            if outcome == "on_time":
                pay_date = due_date + timedelta(days=random.randint(0, 3))
                amount   = rent
                late_fee = 0
            elif outcome == "late":
                pay_date = due_date + timedelta(days=random.randint(4, 25))
                amount   = rent
                late_fee = round(rent * 0.05, 2)
            else:  # missed
                pay_date = None
                amount   = 0
                late_fee = round(rent * 0.10, 2)

            rows.append({
                "payment_id":  f"PAY{pay_id:06d}",
                "tenant_id":   tenant["tenant_id"],
                "property_id": tenant["property_id"],
                "due_date":    due_date.isoformat(),
                "pay_date":    pay_date.isoformat() if pay_date else "",
                "amount_due":  rent,
                "amount_paid": amount,
                "late_fee":    late_fee,
                "payment_status": outcome,
                "payment_method": weighted_choice(methods, method_wts) if outcome != "missed" else "",
            })
            pay_id += 1
            months_generated += 1
            # Advance to next month
            if month_start.month == 12:
                month_start = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_start = month_start.replace(month=month_start.month + 1)

    return rows

PAYMENTS = gen_payments()


# ─── 6. Invoices ─────────────────────────────────────────────────────────────

VENDOR_LOOKUP = {v["vendor_id"]: v for v in VENDORS}

def gen_invoices():
    rows = []
    inv_id = 1
    resolved_orders = [wo for wo in WORK_ORDERS if wo["status"] == "resolved" and wo["assigned_vendor"]]

    for wo in resolved_orders:
        vendor = VENDOR_LOOKUP.get(wo["assigned_vendor"])
        if not vendor:
            continue

        res_hours = float(wo["resolution_hours"]) if wo["resolution_hours"] else 2.0
        # Labor: clamp realistic on-site hours (a 0.2h "resolution" still needs min 0.5h on-site)
        labor_hours = round(max(0.5, min(res_hours * random.uniform(0.3, 0.7), 16)), 2)
        labor_cost  = round(labor_hours * vendor["hourly_rate"], 2)

        # Parts cost varies by trade
        trade_parts = {
            "plumbing":    (0, 420),
            "HVAC":        (0, 850),
            "electrical":  (0, 380),
            "general":     (0, 220),
            "roofing":     (100, 1200),
            "painting":    (30, 350),
            "landscaping": (0, 180),
        }
        lo, hi = trade_parts.get(wo["trade"], (0, 300))
        parts_cost = round(random.uniform(lo, hi), 2)

        total = round(labor_cost + parts_cost, 2)
        invoice_date = wo["resolved_at"][:10] if wo["resolved_at"] else ""

        rows.append({
            "invoice_id":    f"INV{inv_id:05d}",
            "work_order_id": wo["work_order_id"],
            "vendor_id":     wo["assigned_vendor"],
            "property_id":   wo["property_id"],
            "invoice_date":  invoice_date,
            "labor_hours":   labor_hours,
            "labor_cost":    labor_cost,
            "parts_cost":    parts_cost,
            "total_amount":  total,
        })
        inv_id += 1
    return rows

INVOICES = gen_invoices()


# ─── 7. Financial Ledger ─────────────────────────────────────────────────────

def gen_financial_ledger():
    from collections import defaultdict

    # Revenue: sum payments by property + month
    rev_map = defaultdict(float)
    for p in PAYMENTS:
        if p["pay_date"]:
            ym = p["pay_date"][:7]
            rev_map[(p["property_id"], ym)] += p["amount_paid"]

    # Expenses: sum invoices by property + month
    exp_map = defaultdict(float)
    for inv in INVOICES:
        if inv["invoice_date"]:
            ym = inv["invoice_date"][:7]
            exp_map[(inv["property_id"], ym)] += inv["total_amount"]

    all_keys = set(rev_map.keys()) | set(exp_map.keys())

    rows = []
    ledger_id = 1
    for (prop_id, ym) in sorted(all_keys):
        revenue  = round(rev_map.get((prop_id, ym), 0), 2)
        expenses = round(exp_map.get((prop_id, ym), 0), 2)
        noi      = round(revenue - expenses, 2)
        rows.append({
            "ledger_id":   f"LED{ledger_id:05d}",
            "property_id": prop_id,
            "year_month":  ym,
            "revenue":     revenue,
            "expenses":    expenses,
            "noi":         noi,
        })
        ledger_id += 1
    return rows

FINANCIAL_LEDGER = gen_financial_ledger()


# ─── Write CSVs ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Phase 1 synthetic data...\n")

    write_csv("properties", PROPERTIES, [
        "property_id","name","market","neighborhood","property_type",
        "unit_count","total_sqft","year_built","age_years","market_value",
    ])
    write_csv("vendors", VENDORS, [
        "vendor_id","company_name","specialty","hourly_rate",
        "avg_response_hours","sla_compliance_pct","quality_rating","active",
    ])
    write_csv("tenants", TENANTS, [
        "tenant_id","first_name","last_name","property_id","unit_number",
        "lease_start","lease_end","monthly_rent","security_deposit",
        "move_in_date","satisfaction_score","at_risk",
    ])
    write_csv("work_orders", WORK_ORDERS, [
        "work_order_id","tenant_id","property_id","unit_number","trade",
        "urgency","status","description","created_at","resolved_at",
        "resolution_hours","assigned_vendor",
    ])
    write_csv("payments", PAYMENTS, [
        "payment_id","tenant_id","property_id","due_date","pay_date",
        "amount_due","amount_paid","late_fee","payment_status","payment_method",
    ])
    write_csv("invoices", INVOICES, [
        "invoice_id","work_order_id","vendor_id","property_id",
        "invoice_date","labor_hours","labor_cost","parts_cost","total_amount",
    ])
    write_csv("financial_ledger", FINANCIAL_LEDGER, [
        "ledger_id","property_id","year_month","revenue","expenses","noi",
    ])

    print("\nDone. Summary:")
    print(f"  {len(PROPERTIES)} properties across {len(MARKETS)} markets")
    print(f"  {len(VENDORS)} vendors")
    print(f"  {len(TENANTS)} tenants  ({sum(1 for t in TENANTS if t['at_risk'])} at-risk)")
    print(f"  {len(WORK_ORDERS)} work orders")
    print(f"  {len(PAYMENTS)} payment records")
    print(f"  {len(INVOICES)} invoices")
    print(f"  {len(FINANCIAL_LEDGER)} ledger entries")
