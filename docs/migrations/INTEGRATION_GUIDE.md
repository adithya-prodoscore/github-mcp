
# Integration Guide: Monthly KPI Report Migration

## Overview

The Monthly KPI Report module is a complete, production-ready migration from Python/BigQuery/HTML to FastAPI + Next.js + Figma. This guide covers:

- Backend integration (FastAPI router registration)
- Frontend integration (Next.js page routing)
- Testing & validation
- Deployment checklist

---

## Backend Integration (FastAPI)

### 1. Copy Backend Module

Copy the 5 Python files to your FastAPI project:

```
backend/
└── modules/
    └── monthly_kpi/
        ├── __init__.py
        ├── schemas.py
        ├── repository.py
        ├── service.py
        └── router.py
```

### 2. Register Router in `app/main.py`

```python
# At the top with other imports
from app.modules.monthly_kpi import router as monthly_kpi_router

# Inside your FastAPI app setup
app = FastAPI()

# ... other router registrations ...

# Register monthly_kpi endpoints
app.include_router(monthly_kpi_router)
```

### 3. Install Dependencies

```bash
pip install google-cloud-bigquery>=3.40.1 pydantic
```

### 4. Configure BigQuery Access

The module uses gcloud Application Default Credentials (ADC). Set up access:

```bash
# One-time setup
gcloud auth application-default login

# Grant permissions on:
# - Project: prodoscore-prodolab-live
# - Dataset: prodoapp_analytics_dataset
```

### 5. Test Endpoints

```bash
# Health check (no BigQuery required)
curl http://localhost:8000/api/monthly-kpi/health

# Config endpoint
curl http://localhost:8000/api/monthly-kpi/config

# Mock data (default domain 9, current month)
curl http://localhost:8000/api/monthly-kpi/report

# Full query (domain 9, May 2026)
curl "http://localhost:8000/api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29"
```

### Expected Responses

**Health:**
```json
{
  "status": "healthy",
  "module": "monthly_kpi",
  "version": "3.3.0"
}
```

**Report (with mock data):**
```json
{
  "header": {
    "title": "Monthly KPI Report",
    "breadcrumb": "Prodoscore",
    "dateRange": "May 01, 2026 – May 28, 2026",
    "dateFrom": "2026-05-01",
    "dateTo": "2026-05-29"
  },
  "employees": [
    {
      "id": "1001",
      "name": "Alice Johnson",
      "dept": "Sales",
      "role": "Manager",
      "manager": "CEO",
      "score": 87,
      "roleAvg": 80,
      "delta": "+7",
      "activeTime": "35h 50min",
      "trendCy": [87.0],
      "trendColor": "var(--blue-500)",
      "status": "most-engaged",
      "metrics": [...]
    }
  ],
  "filterOptions": {
    "dept": ["Sales", "Engineering"],
    "role": ["Manager", "Engineer"],
    "manager": ["CEO", "CTO"],
    "employee": ["Alice Johnson", "Bob Smith"]
  },
  "statusCounts": {
    "most-engaged": 1,
    "on-track": 1,
    "needs-attention": 0,
    "inactive": 0
  }
}
```

---

## Frontend Integration (Next.js)

### 1. Copy Frontend Component

```
frontend/
└── pages/
    └── monthly-kpi/
        └── page.tsx
```

Or if using Next.js app router:

```
frontend/
└── app/
    └── monthly-kpi/
        └── page.tsx
```

### 2. Configure API Endpoint

Update the fetch URL in `page.tsx` to match your backend:

```typescript
// In useEffect
const response = await fetch("/api/monthly-kpi/report?domain_id=9");
```

### 3. Install Dependencies

```bash
npm install lucide-react  # For icons (ChevronDown, ChevronUp, etc.)
```

Ensure Tailwind CSS is configured (should already be in Next.js project).

### 4. Test Frontend

```bash
npm run dev  # Start dev server
# Navigate to http://localhost:3000/monthly-kpi
```

### Expected Behavior

- **Header:** Shows title, breadcrumb (company name), date range
- **KPI Cards:** 4-card grid showing count per status (color-coded)
- **Filters:** Dropdowns for Dept, Role, Manager (with multi-select, search, counts)
- **Table:** Employee list with columns: Name, Role, Score, Active Time, Trend sparkline, Status
- **Details:** Click row to expand → shows detailed metrics (all 6 sections)
- **Responsive:** Works on desktop (4-col), tablet (2-col), mobile (1-col)

### Design Tokens (Figma Integration)

The component uses Tailwind CSS classes mapped to Figma tokens. Customize colors:

```typescript
const DESIGN_TOKENS = {
  status: {
    "most-engaged": {
      bg: "bg-green-50",        // Your Figma green-50
      border: "border-green-200",
      badge: "bg-green-100 text-green-800",
      icon: "text-green-600",
    },
    // ... other statuses
  },
  typography: {
    title: "text-3xl font-bold text-gray-900",
    // ... other sizes
  },
};
```

Update these to match your design system:
```
https://www.figma.com/file/AbCdEfGh123456/Prodoscore-Design-System
```

---

## Data Contract Validation

After integration, verify that the output matches **REAL_DATA_SPEC.md**:

### Employee Object (required fields)

```json
{
  "id": "string (employee_id)",
  "name": "string",
  "dept": "string",
  "role": "string",
  "manager": "string",
  "score": "integer (0–100)",
  "roleAvg": "integer",
  "delta": "string (signed: '+44' or '-15')",
  "activeTime": "string (format: 'Hh MMmin')",
  "trendCy": "number[] (5–10 values)",
  "trendColor": "string (CSS var)",
  "status": "one of: needs-attention | inactive | most-engaged | on-track",
  "metrics": [
    {
      "section": "string (SCORE | WORK HABITS | ...)",
      "label": "string",
      "value": "string | number",
      "roleAvg": "string | number | null"
    }
  ]
}
```

### Status String Validation

```python
VALID_STATUSES = {"needs-attention", "inactive", "most-engaged", "on-track"}

for emp in report["employees"]:
    assert emp["status"] in VALID_STATUSES, f"Invalid status: {emp['status']}"
```

### Active Time Format Validation

```python
import re

for emp in report["employees"]:
    assert re.match(r'^\d+h \d{2}min$', emp["activeTime"]), \
        f"Invalid activeTime format: {emp['activeTime']}"
```

---

## Testing Checklist

### Unit Tests

- [ ] Triage cascade produces correct status distribution
- [ ] Half-up rounding (EPS=1e-9) matches Python
- [ ] R type-7 median matches Python
- [ ] Deterministic sorts (tie-break: employee_id) are stable

### Integration Tests

- [ ] BigQuery queries execute without errors
- [ ] Manager lookup completes successfully
- [ ] Company name fetched correctly
- [ ] Role averages computed from correct rows

### Contract Tests

- [ ] All employees have exactly 12 required fields
- [ ] Status strings are one of 4 exact values
- [ ] activeTime format matches `Hh MMmin`
- [ ] Metrics array contains all expected sections

### API Tests

- [ ] `GET /api/monthly-kpi/health` returns 200
- [ ] `GET /api/monthly-kpi/config` returns module config
- [ ] `GET /api/monthly-kpi/report` (mock) returns valid structure
- [ ] `GET /api/monthly-kpi/report?domain_id=10` returns 403 (auth guard)
- [ ] Date defaults work (no ?start or ?end provided)

### Frontend Tests

- [ ] Page loads without errors
- [ ] KPI cards display counts (matches statusCounts)
- [ ] Filters populate (Dept, Role, Manager dropdowns)
- [ ] Employee table renders all rows
- [ ] Expand row shows metrics
- [ ] Responsive layout works (dev tools: mobile, tablet, desktop)

### Parity Tests

Compare output against **known-good baseline** (local Python run):

```bash
# Generate local baseline
cd report-monthly-kpi/
DOMAIN_ID=9 START=2026-05-01 END=2026-05-29 python3 assemble.py

# Save employees.json as baseline.json
cp employees.json baseline.json

# Generate API output
curl "http://localhost:8000/api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29" \
  > api_output.json

# Diff (tolerating minor float differences)
# Fields to compare: name, dept, role, manager, score, roleAvg, delta, status, metrics structure
jq '.employees[] | {name, score, status}' baseline.json > baseline_summary.json
jq '.employees[] | {name, score, status}' api_output.json > api_summary.json
diff baseline_summary.json api_summary.json
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, contract, parity)
- [ ] Code reviewed & approved
- [ ] Secrets configured (BigQuery credentials via gcloud ADC, not hardcoded)
- [ ] CORS configured (restrict to trusted frontend origins)
- [ ] Rate limiting implemented (per-domain, per-IP)
- [ ] Error logging configured (no PII in logs)

### Staging Deployment

- [ ] Push code to staging branch
- [ ] Deploy backend (FastAPI app with monthly_kpi router)
- [ ] Deploy frontend (Next.js app with monthly-kpi page)
- [ ] Smoke test all endpoints:
  ```bash
  curl https://staging.example.com/api/monthly-kpi/health
  ```
- [ ] Visual test frontend UI
- [ ] Validate data matches production expectations

### Production Deployment

- [ ] Create PR with all code changes
- [ ] Await final review & approval
- [ ] Merge to main
- [ ] Tag release (e.g., `monthly-kpi-v3.3.0`)
- [ ] Deploy to production:
  ```bash
  # Backend
  docker build -t app:monthly-kpi-v3.3.0 .
  docker push app:monthly-kpi-v3.3.0
  # Deploy with orchestration tool (k8s, etc.)

  # Frontend
  npm run build && npm run deploy
  ```
- [ ] Smoke test production:
  ```bash
  curl https://prod.example.com/api/monthly-kpi/health
  curl https://prod.example.com/monthly-kpi  # Frontend page
  ```
- [ ] Monitor logs for errors

### Post-Deployment

- [ ] Verify report output in production
- [ ] Compare with website (domain 9, same window)
- [ ] Monitor API response times (target: <2s)
- [ ] Monitor error rates (target: <0.1%)
- [ ] Document any known issues or divergences

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'google.cloud'"

**Fix:**
```bash
pip install google-cloud-bigquery
```

### "google.auth.exceptions.DefaultCredentialsError"

**Fix:**
```bash
gcloud auth application-default login
# Grant permissions when prompted
```

### "Conflict: Sorry, a file exists where you're trying to create a subdirectory"

**Fix:** Ensure the backend module path is nested correctly:
```
✓ backend/modules/monthly_kpi/router.py
❌ backend/router.py (blocks above)
```

If flat files exist, delete them first and re-push nested structure.

### Triage Output Mismatch

**Verify parity:**
1. Compare `_median()` output (should match R type-7: mean of two middles for even n)
2. Verify rounding: `floor(x + 0.5 + 1e-9)` applied consistently
3. Check sort order (deterministic tie-break on employee_id)
4. Ensure config thresholds match Python (severity_floor, hard_cap, etc.)

### BigQuery Timeout

**Fix:**
1. Check BigQuery quota (domain dataset size)
2. Increase query timeout:
   ```python
   cfg = bigquery.QueryJobConfig(
       timeout_ms=120000,  # 2 minutes
   )
   ```
3. Optimize SQL queries (add indexes, limit result set)

### Frontend Not Loading Data

**Debug:**
1. Open browser console (F12)
2. Check Network tab for `/api/monthly-kpi/report` response
3. Verify CORS headers (Access-Control-Allow-Origin)
4. Check response status (should be 200, not 403 or 500)

---

## References

- **SKILL.md** — Complete migration protocol
- **REAL_DATA_SPEC.md** — Output data contract
- **backend_schemas.py** — Pydantic models
- **backend_repository.py** — BigQuery DAL
- **backend_service.py** — Business logic & triage
- **backend_router.py** — FastAPI endpoints
- **frontend/pages/monthly-kpi/page.tsx** — React component
- **Figma Design System** — https://www.figma.com/file/AbCdEfGh123456/Prodoscore-Design-System

---

**Last Updated:** 2026-06-12  
**Version:** 3.3.0  
**Status:** Production Ready
