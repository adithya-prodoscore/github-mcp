"""Business logic layer for Monthly KPI Report.

Handles triage classification, report assembly, and derived field computation.
Maintains full parity with Python's assemble.py and triage.py.
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Constants & Formatting Helpers (parity with assemble.py)
# ============================================================================

EMDASH = "—"
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_NAME = {2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday"}
EPS = 1e-9  # Half-up rounding epsilon


def _na(x):
    """Check if value is NA/None/NaN."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def _floor_half_up(x):
    """Half-up rounding (parity with R)."""
    return math.floor(x + 0.5 + EPS)


def fmt_hm(minutes):
    """Format minutes as 'Hh MMmin'."""
    if _na(minutes):
        return EMDASH
    m = _floor_half_up(minutes)
    return f"{m // 60}h {m % 60:02d}min"


def fmt_pct(x):
    """Format as percentage."""
    return EMDASH if _na(x) else f"{x:.1f}%"


def fmt_int(x):
    """Format as integer."""
    return EMDASH if _na(x) else str(_floor_half_up(x))


def fmt_clock(minutes):
    """Format minutes as clock time (e.g., '2:45pm')."""
    if _na(minutes):
        return EMDASH
    m = _floor_half_up(minutes) % 1440
    h, mm = m // 60, m % 60
    ap = "am" if h < 12 else "pm"
    h12 = ((h + 11) % 12) + 1
    return f"{h12}:{mm:02d}{ap}"


def fmt_date(s):
    """Format ISO date as 'Mon DD, YYYY'."""
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
        return f"{MONTHS[d.month]} {d.day:02d}, {d.year}"
    except:
        return EMDASH


# ============================================================================
# Triage Logic (parity with triage.py)
# ============================================================================

def r0(x: float) -> int:
    """Half-up rounding to integer (parity with triage.py)."""
    return math.floor(x + 0.5 + EPS)


def _median(vals: List[float]) -> float:
    """R type-7 median: mean of two middles for even n."""
    if not vals:
        return float("nan")
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _mean(vals: List[float]) -> float:
    """Compute mean."""
    return sum(vals) / len(vals) if vals else float("nan")


def classify_inactive(e: dict) -> Optional[str]:
    """Classify inactive (ordered gates; first match wins)."""
    if _na(e.get("avg_score")) or e.get("avg_score") == 0:
        return "zero activity"
    days_total = e.get("days_total")
    days_active = e.get("days_active")
    if days_total and days_total > 0 and days_active < days_total / 2:
        return "partial days"
    if e.get("avg_score", 0) < 30 and e.get("active_min", 0) < 60:
        return "low activity (<30 score & <1h)"
    if e.get("active_min", 0) < 20:
        return "minimal active time (<20min)"
    return None


def dev_below(value: float, base: float) -> float:
    """Compute deviation below baseline."""
    if _na(base) or base <= 0 or value >= base:
        return 0.0
    return (base - value) / base


def dev_above(value: float, base: float) -> float:
    """Compute deviation above baseline."""
    if _na(base) or base <= 0 or value <= base:
        return 0.0
    return (value - base) / base


def build_baselines(active: list, cfg: dict) -> dict:
    """Build baselines from ACTIVE pool only."""
    co_score = _median([e["avg_score"] for e in active])
    co_active = _median([e["active_min"] for e in active])
    all_score_mean = _mean([e["avg_score"] for e in active])
    all_active_mean = _mean([e["active_min"] for e in active])

    roles = {}
    for e in active:
        roles.setdefault(e["role"], []).append(e)

    role_tab = {}
    for rn, members in roles.items():
        n = len(members)
        role_tab[rn] = dict(
            role=rn, n=n,
            med_score=_median([m["avg_score"] for m in members]) if n >= cfg["min_role_sample"] else co_score,
            med_active=_median([m["active_min"] for m in members]) if n >= cfg["min_role_sample"] else co_active,
            role_is_fallback=n < cfg["min_role_sample"],
            mean_score=_mean([m["avg_score"] for m in members]) if n >= cfg["min_role_gate"] else all_score_mean,
            mean_active=_mean([m["active_min"] for m in members]) if n >= cfg["min_role_gate"] else all_active_mean,
        )
    return dict(co_score=co_score, co_active=co_active, role=role_tab)


def run_triage_cascade(emp: list, cfg: dict) -> tuple[list, dict]:
    """Run the full triage cascade (4 stages + severity/tier/reason)."""
    # Initialize all to None
    for e in emp:
        e["status"] = None
        e["severity"] = None
        e["tier"] = None
        e["reason"] = None

    # Stage 1: Inactive classification
    for e in emp:
        rsn = classify_inactive(e)
        if rsn is not None:
            e["status"] = "inactive"
            e["reason"] = rsn

    active = [e for e in emp if e["status"] is None]
    meta = dict(threshold=None, target=None, triage_skipped=False)

    # Stage 2: Small-team guard
    n_active = len(active)
    if n_active < 4:
        for e in emp:
            if e["status"] is None:
                e["status"] = "on-track"
        meta["triage_skipped"] = True
        return emp, meta

    target_lo = 1 if n_active <= 9 else 3
    target_hi = 3 if n_active <= 9 else 8

    b = build_baselines(active, cfg)
    for e in active:
        e["comp_dev"] = (cfg["w_score"] * dev_below(e["avg_score"], b["co_score"])
                         + cfg["w_active"] * dev_below(e["active_min"], b["co_active"]))

    # Stage 3: Gating (exclude from flagging pool)
    pool = []
    for idx, e in enumerate(active):
        rb = b["role"].get(e["role"])
        if not rb:
            rb = b["role"].get("(COMPANY)")  # fallback
        if rb:
            ms, ma = rb["mean_score"], rb["mean_active"]
            hard = (r0(e["avg_score"]) >= r0(ms)) and (r0(e["active_min"]) >= r0(ma))
            effort = (e["avg_score"] < ms) and (e["active_min"] >= cfg["effort_factor"] * ma)
            if not (hard or effort):
                pool.append(idx)

    # Stage 4: Bidirectional cascade on medium threshold
    def count_flagged(thr):
        c = 0
        for i in pool:
            e = active[i]
            rb = b["role"].get(e["role"])
            if not rb or rb["role_is_fallback"]:
                cs = dev_below(e["avg_score"], b["co_score"])
                ca = dev_below(e["active_min"], b["co_active"])
                trig = (cs >= thr) or (ca >= thr * cfg["active_time_thresh_factor"])
            else:
                cs = dev_below(e["avg_score"], rb["med_score"])
                ca = dev_below(e["active_min"], rb["med_active"])
                trig = (cs >= thr) or (ca >= thr * cfg["active_time_thresh_factor"])
            if trig:
                c += 1
        return c

    thr = cfg["medium"]
    while count_flagged(thr) > target_hi and thr < cfg["cascade_hi"]:
        thr += cfg["cascade_step"]
    while count_flagged(thr) < target_lo and thr > cfg["cascade_lo"]:
        thr -= cfg["cascade_step"]

    # Stage 5: Evaluate flagged set at settled threshold
    flagged = []
    for i in pool:
        e = active[i]
        rb = b["role"].get(e["role"])
        if not rb or rb["role_is_fallback"]:
            cs = dev_below(e["avg_score"], b["co_score"])
            ca = dev_below(e["active_min"], b["co_active"])
            lenses = [{"trig": cs >= thr or ca >= thr * cfg["active_time_thresh_factor"], "dev": max(cs, ca)}]
        else:
            cs = dev_below(e["avg_score"], rb["med_score"])
            ca = dev_below(e["active_min"], rb["med_active"])
            lenses = [{"trig": cs >= thr or ca >= thr * cfg["active_time_thresh_factor"], "dev": max(cs, ca)}]

        if not any(x["trig"] for x in lenses):
            continue
        n_trig = sum(1 for x in lenses if x["trig"])
        max_dev = max(x["dev"] for x in lenses)
        sev = "CRITICAL" if n_trig >= 3 else ("HIGH" if n_trig == 2 else "MEDIUM")
        if max_dev >= cfg["critical"]:
            sev = "CRITICAL"
        elif max_dev >= cfg["high"] and sev == "MEDIUM":
            sev = "HIGH"
        if sev != "CRITICAL" and e["comp_dev"] < cfg["severity_floor"]:
            continue
        flagged.append(dict(idx=i, sev=sev, rank=e["comp_dev"]))

    sev_rank = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    flagged_ids = set()
    if flagged:
        flagged.sort(key=lambda f: (-sev_rank[f["sev"]], -f["rank"], active[f["idx"]]["employee_id"]))
        if len(flagged) > cfg["hard_cap"]:
            flagged = flagged[:cfg["hard_cap"]]
        for f in flagged:
            e = active[f["idx"]]
            e["status"] = "needs-attention"
            e["severity"] = f["sev"]
            flagged_ids.add(e["employee_id"])

    # Stage 6: Top performers
    tp_pool = [e for e in active if e["employee_id"] not in flagged_ids]
    tps = []
    for e in tp_pool:
        rb = b["role"].get(e["role"])
        if not rb or e["avg_score"] < rb["mean_score"]:
            continue
        cs = dev_above(e["avg_score"], b["co_score"])
        ca = dev_above(e["active_min"], b["co_active"])
        n_trig = 0
        max_dev = 0.0
        if (cs >= cfg["tp_stable"]) or (ca >= cfg["tp_stable"] * cfg["active_time_thresh_factor"]):
            n_trig += 1
        max_dev = max(max_dev, cs, ca)
        if rb and not rb["role_is_fallback"]:
            rs = dev_above(e["avg_score"], rb["med_score"])
            ra = dev_above(e["active_min"], rb["med_active"])
            if (rs >= cfg["tp_stable"]) or (ra >= cfg["tp_stable"] * cfg["active_time_thresh_factor"]):
                n_trig += 1
            max_dev = max(max_dev, rs, ra)
        if n_trig == 0:
            continue
        tier = "STAR" if n_trig >= 3 else ("STRONG" if n_trig == 2 else "STABLE")
        if max_dev >= cfg["tp_star"]:
            tier = "STAR"
        elif max_dev >= cfg["tp_strong"] and tier == "STABLE":
            tier = "STRONG"
        rank = cfg["w_score"] * cs + cfg["w_active"] * ca
        tps.append(dict(id=e["employee_id"], role=e["role"], tier=tier, rank=rank))

    if tps:
        tier_rank = {"STAR": 3, "STRONG": 2, "STABLE": 1}
        tps.sort(key=lambda t: (-tier_rank[t["tier"]], -t["rank"], t["id"]))
        chosen = []
        seen_roles = set()
        for t in tps:
            if t["role"] not in seen_roles:
                chosen.append(t)
                seen_roles.add(t["role"])
        for t in tps:
            if len(chosen) < cfg["hard_cap"] and not any(c["id"] == t["id"] for c in chosen):
                chosen.append(t)
        chosen = chosen[:cfg["hard_cap"]]
        for t in chosen:
            for e in active:
                if e["employee_id"] == t["id"]:
                    e["status"] = "most-engaged"
                    e["tier"] = t["tier"]

    for e in emp:
        if e["status"] is None:
            e["status"] = "on-track"

    meta["threshold"] = thr
    meta["target"] = (target_lo, target_hi)
    return emp, meta


# ============================================================================
# Service Layer
# ============================================================================

class MonthlyKPIService:
    """Service layer for KPI report generation."""

    def __init__(self, repository):
        """Initialize service with data repository."""
        self.repository = repository
        self.triage_config = {
            "critical": 0.40, "high": 0.30, "medium": 0.30,
            "tp_star": 0.40, "tp_strong": 0.30, "tp_stable": 0.30,
            "min_role_sample": 5,
            "min_role_gate": 3,
            "active_time_thresh_factor": 2.0,
            "effort_factor": 1.25,
            "hard_cap": 8,
            "severity_floor": 0.10,
            "cascade_lo": 0.15, "cascade_hi": 0.55, "cascade_step": 0.05,
            "w_score": 0.75, "w_active": 0.25,
        }

    def assemble_report(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
        manager: Optional[str] = None,
        employee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assemble complete monthly KPI report."""
        # 1. Query repository
        raw = self.repository.query(domain_id, start_date, end_date)

        # 2. Prepare triage input
        emp_triage = []
        for c in raw.get("employees", []):
            emp_triage.append(dict(
                employee_id=float(c.get("employee_id", 0)),
                name=c.get("name", "Unknown"),
                role=c.get("role") if c.get("role") not in (None, "") else "Unassigned",
                avg_score=0.0 if _na(c.get("avg_score")) else float(c.get("avg_score")),
                active_min=0.0 if _na(c.get("avg_active_min_raw")) else float(c.get("avg_active_min_raw")),
                days_active=0 if _na(c.get("days_active")) else int(c.get("days_active")),
                days_total=0 if _na(c.get("days_counted")) else int(c.get("days_counted")),
            ))

        # 3. Run triage
        triaged, meta = run_triage_cascade(emp_triage, self.triage_config)
        status_by_id = {int(e["employee_id"]): e["status"] for e in triaged}
        role_by_id = {int(e["employee_id"]): e["role"] for e in triaged}

        logger.info(f"[service] Triage: {dict(Counter(e['status'] for e in triaged))}")

        # 4. Build employees (add metrics, format fields)
        employees = []
        for c in raw.get("employees", []):
            emp = self._build_employee(c, raw, status_by_id, role_by_id)
            employees.append(emp)

        # 5. Generate filter options
        filter_options = self._generate_filters(employees)

        # 6. Build header
        header = self._build_header(domain_id, raw, start_date, end_date)

        # 7. Count statuses
        status_counts = self._count_statuses(employees)

        return {
            "header": header,
            "employees": employees,
            "filter_options": filter_options,
            "statusCounts": status_counts,
        }

    def _build_employee(self, c: dict, raw: dict, status_by_id: dict, role_by_id: dict) -> dict:
        """Build one employee object."""
        eid = c["employee_id"]
        role = role_by_id.get(int(eid), "Unassigned")
        score = 0 if _na(c.get("avg_score")) else int(c.get("avg_score"))

        # Role average
        arow = next((r for r in raw.get("roleAverages", {}) if r.get("role") == role), None)
        rAvg = int(arow.get("role_score", 0)) if arow else 0

        # Delta
        delta = score - rAvg
        delta_s = ("+" if delta >= 0 else "") + str(delta)

        # Active time
        active_min = c.get("avg_active_min_raw")
        active_time = fmt_hm(active_min) if not _na(active_min) else "0h 00min"

        # Status
        status = status_by_id.get(int(eid), "on-track")

        # Trends (mock sparkline)
        trend = [float(score)]
        tcol = "var(--blue-500)"

        # Metrics (placeholder; would be populated from raw data)
        metrics = [
            {"section": "SCORE", "label": "Avg Score", "value": str(score), "roleAvg": str(rAvg)},
            {"section": "WORK HABITS", "label": "Active Time", "value": active_time},
        ]

        return {
            "id": str(eid),
            "name": c.get("name", "Unknown"),
            "dept": c.get("dept", "Unassigned"),
            "role": role,
            "manager": raw.get("manager_lookup", {}).get(c.get("manager_id"), ""),
            "score": score,
            "roleAvg": rAvg,
            "delta": delta_s,
            "activeTime": active_time,
            "trendCy": trend,
            "trendColor": tcol,
            "status": status,
            "metrics": metrics,
        }

    def _generate_filters(self, employees: list) -> Dict[str, List[str]]:
        """Generate unique filter options."""
        depts = sorted(set(e.get("dept", "Unassigned") for e in employees))
        roles = sorted(set(e.get("role", "Unassigned") for e in employees))
        mgrs = sorted(set(e.get("manager", "") for e in employees if e.get("manager")))
        emps = sorted(set(e.get("name", "") for e in employees))
        return {
            "dept": depts,
            "role": roles,
            "manager": mgrs,
            "employee": emps,
        }

    def _build_header(self, domain_id: int, raw: dict, start_date: str, end_date: str) -> Dict[str, str]:
        """Build report header."""
        company_name = raw.get("company_name", f"Domain {domain_id}")
        date_from = fmt_date(start_date)
        date_to = fmt_date(end_date)
        date_range = f"{date_from} – {date_to}" if date_from != EMDASH and date_to != EMDASH else "Custom Range"
        return {
            "title": "Monthly KPI Report",
            "breadcrumb": company_name,
            "dateRange": date_range,
            "dateFrom": start_date,
            "dateTo": end_date,
        }

    def _count_statuses(self, employees: list) -> Dict[str, int]:
        """Count employees per status."""
        counts = Counter(e.get("status", "on-track") for e in employees)
        return {
            "needs-attention": counts.get("needs-attention", 0),
            "inactive": counts.get("inactive", 0),
            "most-engaged": counts.get("most-engaged", 0),
            "on-track": counts.get("on-track", 0),
        }
