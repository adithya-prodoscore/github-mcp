# Monthly KPI Report Migration

**Status:** Generated code ready for integration  
**Module:** `monthly_kpi`  
**Feature Branch:** `feat/migration-monthly-kpi`  
**Protocol:** SKILL.md v3.2.0

## Overview

This migration integrates the **Anchor KPI Report** from the local `report-monthly-kpi/` folder into a cloud-native FastAPI + Next.js architecture.

The Anchor KPI Report is a lean monthly KPI report that mirrors the Prodoscore website, producing self-contained analytics with per-employee metrics, role-based peer comparisons, and a sophisticated triage-based status classification.

## Generated Files

### Backend (5 Python files)
Location: `prodoscore-reporting-backend/app/modules/monthly_kpi/`

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | ~20 | Package initialization, router export |
| `schemas.py` | 66 | Pydantic models (EmployeeKPI, MonthlyKPIReport, etc.) |
| `repository.py` | 75 | BigQuery data access layer with 11 parameterized queries |
| `service.py` | 156 | Triage cascade + report assembly (parity with Python) |
| `router.py` | 65 | FastAPI routes: GET /api/monthly-kpi/report, /health |

### Frontend (1 TypeScript file)
Location: `prodoscore-reporting-frontend/app/monthly-kpi/`

| File | Lines | Purpose |
|------|-------|---------|
| `page.tsx` | 284 | Type-safe React page with Tailwind CSS styling |

## API Endpoint

```http
GET /api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29
```

Response: `MonthlyKPIReport` (Pydantic) with employees, filter_options, header, statusCounts

## Key Features

✓ **Data Contract Parity with Local**
- `employees.json` shape matches exactly per REAL_DATA_SPEC.md
- Per-employee metrics with role-based comparisons
- Status triage: 4 exact strings (inactive | needs-attention | most-engaged | on-track)

✓ **Calculation Parity with Python**
- Half-up rounding: `floor(x + 0.5 + 1e-9)` (prevents ~1-ULP gaps in BigQuery deserialization)
- R type-7 median: mean of two middles for even n
- Deterministic tie-breaks on `employee_id`

✓ **BigQuery Integration**
- 11 parameterized queries (01..09, 11, 12)
- Domain + date window filtering
- Mock fallbacks for development

✓ **API Endpoint**
```http
GET /api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29
```

✓ **Frontend Dashboard**
- 4-card status overview (most-engaged, needs-attention, on-track, inactive)
- Employee table with score, active time, status badge
- Expandable detailed metrics tabs per employee
- Responsive Tailwind CSS layout

## Backend Module Structure

### schemas.py
- `MetricRecord`: Individual metric (section, label, value, roleAvg, companyAvg)
- `EmployeeKPI`: Complete KPI profile per employee
- `FilterOptions`: Department, role, manager, employee filter lists
- `ReportHeader`: Title, company name, date range metadata
- `MonthlyKPIReport`: Complete report container

### repository.py
- `MonthlyKPIRepository` class
- `query()` method: Executes 11 BigQuery queries
- Mock fallback for dev/test without BigQuery

### service.py
- `r0()`: Half-up rounding (parity with R)
- `fmt_hm()`: Format minutes as "Hh MMmin"
- `median_r7()`: R type-7 median
- `classify_status()`: Triage status assignment
- `assemble_report()`: Build complete report from raw data

### router.py
- `GET /api/monthly-kpi/report`: Main report endpoint
- `GET /api/monthly-kpi/health`: Health check

## Frontend Features

### Status Overview Cards
- **Most Engaged** (green): Count of top-tier employees
- **Needs Attention** (red): Flagged employees below thresholds
- **On Track** (blue): Everyone else
- **Inactive** (gray): Filtered from active pool

### Employee Table
Sortable table with name, role, score, active time, status badge

### Detailed Metrics
Per-employee expandable tabs: SCORE, WORK HABITS, MEETINGS, TECH MODULES

## Implementation Steps

1. **Create directory structure**
   ```
   prodoscore-reporting-backend/app/modules/monthly_kpi/
   prodoscore-reporting-frontend/app/monthly-kpi/
   ```

2. **Copy backend files** to `prodoscore-reporting-backend/app/modules/monthly_kpi/`
   - `__init__.py`
   - `schemas.py`
   - `repository.py`
   - `service.py`
   - `router.py`

3. **Copy frontend file** to `prodoscore-reporting-frontend/app/monthly-kpi/`
   - `page.tsx`

4. **Patch registry** in `prodoscore-reporting-backend/app/main.py`
   ```python
   from app.modules.monthly_kpi import router as monthly_kpi_router
   app.include_router(monthly_kpi_router)
   ```

5. **Test endpoints**
   ```bash
   # Health check
   curl http://localhost:8000/api/monthly-kpi/health
   
   # Mock data (no BigQuery required)
   curl http://localhost:8000/api/monthly-kpi/report
   
   # Full domain 9 report
   curl "http://localhost:8000/api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29"
   ```

## Data Sources

All code generated from local directory `report-monthly-kpi/`:

| Source | Integration |
|--------|-------------|
| HANDOFF.md | Pipeline overview, parity notes |
| README.md | Run instructions, metrics definitions |
| REAL_DATA_SPEC.md | employees.json shape → Pydantic models |
| assemble.py | Data assembly logic → service.py |
| triage.py | Status cascade → service.py classify_status() |
| sql/ (11 files) | BigQuery queries → repository.py query() |
| kpi_web_template.html | HTML structure → page.tsx layout |
| example_output/ | Reference JSON for validation |

## Safety Notes

- **Domain 9 (Prodoscore)** is the only safe default for testing
- Other domains are **live customers** — require explicit authorization
- Access controlled via `domain_id` parameter + gcloud ADC

## SKILL.md Protocol Compliance

✓ Section 1: Target repository metadata configured  
✓ Section 2: API-driven cloud architecture (no local git operations)  
✓ Section 3: Local data science ingestion (report-monthly-kpi/)  
✓ Section 4: Collision detection (no collision found)  
✓ Section 5: In-memory code generation (6 files generated)  
✓ Section 6: Remote GitHub API pipeline (files pushed, PR pending)  

---

**Generated:** 2026-06-11T15:20:00Z  
**Module:** `monthly_kpi`  
**Status:** Ready for code review & registry patch
