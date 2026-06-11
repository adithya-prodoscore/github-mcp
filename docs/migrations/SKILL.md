---
name: migrate-monthly-kpi
description: Migrate Anchor Monthly KPI Report from Python/BigQuery to cloud-native FastAPI+Next.js+Figma per SKILL.md protocol. Use ONLY when integrating report-monthly-kpi folder into github-mcp or similar architecture.
---

# AI Migration Skill: Monthly KPI Report (Anchor KPI)

**Version:** 3.3.0  
**Last Updated:** 2026-06-12  
**Status:** Production Ready  

---

## 1. Overview & Scope

The **Anchor KPI Report** is a lean monthly employee KPI report that mirrors the Prodoscore website. This skill automates the **complete migration** from local Python + BigQuery + static HTML to a cloud-native architecture:

- **Source:** Local folder `./report-monthly-kpi/` (Python, SQL, HTML template)
- **Target:** Cloud-native FastAPI backend + Next.js frontend + Figma design system
- **Contract:** REAL_DATA_SPEC.md (exact employee JSON shape, 4 status strings, metric structure)
- **Parity Requirements:** Half-up rounding (EPS=1e-9), R type-7 median, deterministic sorts, exact triage cascade

**This skill assumes:**
- You have read HANDOFF.md and understand the local pipeline
- You have access to BigQuery with `prodoscore-prodolab-live.prodoapp_analytics_dataset` (gcloud ADC)
- Target repository (e.g., `github-mcp`) already has FastAPI + Next.js scaffolding
- Figma design system is accessible (provided URL)

---

## 2. Section 1: Target Repository Metadata

### Input Requirements

Before executing the migration, confirm:

| Item | Example | Notes |
|------|---------|-------|
| **Target Repo URL** | `https://github.com/org/github-mcp` | The cloud-native repo accepting the migration |
| **API Strategy** | GitHub MCP (native) | NOT Composio wrapper; direct token auth |
| **Backend Path** | `backend/modules/monthly_kpi/` | Nested structure to avoid conflicts |
| **Frontend Path** | `frontend/pages/monthly-kpi/` | Next.js page layout |
| **Feature Branch** | `feat/migration-monthly-kpi` | Source branch for PR |
| **Base Branch** | `main` | Target branch for merge |
| **Design System URL** | `https://www.figma.com/file/AbCd.../Prodoscore-Design-System` | Figma tokens (provided) |

### Outputs

After this section, you will have:
- ✓ Feature branch created on remote
- ✓ SKILL.md and migration guide committed
- ✓ PR opened (empty code, documentation only)

---

## 3. Section 2: API-Driven Architecture (No Local Git Cloning)

The migration **must not rely on local git clones** for the primary workflow. Instead:

### Strategy

1. **Remote GitHub API first:**
   - Use `github_create_or_update_file` to push files directly
   - Avoid `git push` / local staging (reduces state complexity)
   - One file per commit to track provenance

2. **Local staging (reference only):**
   - Clone for reference at `/tmp/opencode/github-mcp/` to verify paths
   - Never the source of truth; GitHub is
   - Deleted after migration if needed

3. **Nested directory structure:**
   - `backend/modules/monthly_kpi/` — Python files (5 total)
   - `frontend/pages/monthly-kpi/` — TypeScript files (1 total)
   - No flat `backend/` / `frontend/` to avoid GitHub API path conflicts

### Conflict Prevention

GitHub API prevents creating nested paths when flat parents exist:

```
❌ ERROR: File exists where you're trying to create a subdirectory
   (e.g., backend/something.py blocks backend/modules/*/*)
```

**Solution:** Delete flat files before pushing nested structure, or use distinct naming:

```
✓ CORRECT: backend/modules/monthly_kpi/schemas.py
✓ CORRECT: backend/modules/monthly_kpi/repository.py
✓ CORRECT: frontend/pages/monthly-kpi/page.tsx
```

---

## 4. Section 3: Local Data Science Ingestion

Extract all source materials from `./report-monthly-kpi/`:

### Required Source Files

| File | Lines | Extractable | Purpose |
|------|-------|-------------|---------|
| `HANDOFF.md` | 146 | ✓ Complete | Pipeline overview, parity notes, safety gates |
| `REAL_DATA_SPEC.md` | 174 | ✓ Complete | Output contract (employee shape, status strings) |
| `assemble.py` | 400 | ✓ Complete | Data assembly logic (SQL runner, formatting, triage call) |
| `triage.py` | 291 | ✓ Complete | Status cascade (4 cascades + severity/tier + reason) |
| `sql/*` | 11 files | ✓ List only | BigQuery parameterized queries (01–09, 11, 12) |
| `kpi_web_template.html` | 29,067 | ✓ Complete | Report template (60 KB; embedded CSS/JS, employee array, filters) |

### Extraction Steps

1. **Read REAL_DATA_SPEC.md** — lock in the output contract:
   - 12 required employee fields (name, dept, role, manager, score, roleAvg, delta, activeTime, trendCy, trendColor, status, metrics)
   - Metrics array structure (6 sections: SCORE, WORK HABITS, MOST & LEAST PRODUCTIVE, MEETINGS, TECH MODULES, WEB BROWSER)
   - 4 exact status strings: `"needs-attention"`, `"inactive"`, `"most-engaged"`, `"on-track"`
   - Filter options: dept, role, manager, employee

2. **Read assemble.py** — extract formatting & assembly logic:
   - Half-up rounding: `floor(x + 0.5 + 1e-9)`
   - Format helpers: `fmt_hm()`, `fmt_clock()`, `fmt_hour()`, `fmt_pct()`, `fmt_int()`, `fmt_munit()`
   - SQL runner with parameterization (domain_id, start, end)
   - Week label generation
   - Employee builder (core fields → metrics array)
   - Role average lookups with (COMPANY) fallback

3. **Read triage.py** — extract cascade logic:
   - Parity: R type-7 median, deterministic sorts
   - Config: thresholds, tier split weights, hard caps
   - Stage 1: Inactive gates (ordered; first match wins)
   - Stage 2: Baselines (medians from ACTIVE pool only)
   - Stage 3: Lenses (distinct deviation triggers)
   - Stage 4-6: Main cascade (small team guard, target range, flagged set eval, top performers)
   - Returns: modified employee list with status, severity, tier, reason

4. **List SQL queries:**
   - `01_employee_core.sql` — core employee data
   - `02_tech_modules.sql` — tech module metrics
   - `03_meetings.sql` — meeting metrics
   - `04_averages.sql` — company/role averages
   - `05_tech_module_averages.sql` — role tech module averages
   - `06_meeting_averages.sql` — role meeting averages
   - `07_work_habits.sql` — work habits (days, active time by day)
   - `08_meeting_popular_time.sql` — meeting popularity
   - `09_web_browser.sql` — web browser domains
   - `11_score_weekday.sql` — score by weekday (sparklines)
   - `12_most_least_productive.sql` — most/least productive week/day/hour

5. **Read template HTML** — extract structure & CSS:
   - 60+ KB embedded CSS (design tokens, filters, tabs, tables, cards, modals)
   - Filter strip (Dept, Role, Manager, Employee multi-select with search)
   - KPI cards (4-tile grid, color variants per status)
   - Employee table (sticky columns, tier color bars, pagination)
   - Methodology drawer (overlay, content tabs)
   - Employee modal (detail view)
   - Embedded 47-row mock employees array (reference for structure)

### Safety Gates

- **Domain 9 (Prodoscore) only** for testing; other domains are live customers
- **BigQuery access** via gcloud ADC required
- **No pandas dependency** — pure stdlib + google-cloud-bigquery

---

## 5. Section 4: Collision Detection & Module Naming

### Naming Strategy

Proposed module name: **`monthly_kpi`** (no collision detected in target repo)

### Collision Check

Search target repo for:

```bash
# Python side
grep -r "monthly_kpi" backend/
grep -r "MonthlyKPI" backend/

# JavaScript side
grep -r "monthly-kpi" frontend/
grep -r "monthly_kpi" frontend/
grep -r "MonthlyKpi" frontend/
```

**If collisions found**, rename to `anchor_kpi` or `employee_kpi`.

### Generated Artifacts

| Artifact | Type | Name | Collision Check |
|----------|------|------|-----------------|
| Pydantic models | Python | `schemas.py` | No collision (new file) |
| BigQuery DAL | Python | `repository.py` | No collision (new file) |
| Business logic | Python | `service.py` | No collision (new file) |
| FastAPI router | Python | `router.py` | No collision (new file) |
| Package init | Python | `__init__.py` | No collision (new file) |
| Next.js page | TypeScript | `page.tsx` | No collision (new file) |

---

## 6. Section 5: In-Memory Code Generation

### Backend Python Module (5 Files)

#### 6.1 `schemas.py` — Pydantic Data Models

**Purpose:** Type-safe contracts for employee data, matching REAL_DATA_SPEC.md exactly

**Structure:**

```python
class MetricRecord(BaseModel):
    """Single metric in a section."""
    section: str          # SCORE, WORK HABITS, MEETINGS, TECH MODULES, WEB BROWSER, MOST & LEAST PRODUCTIVE
    label: str            # "Productivity Score", "Salesforce: Activities", etc.
    value: Union[float, str]  # Number, percentage "58.1%", duration "2h 45min", or "—"
    roleAvg: Optional[Union[float, str]] = None  # Role average (same format as value)

class EmployeeKPI(BaseModel):
    """Complete KPI profile for one employee."""
    name: str
    dept: str
    role: str
    manager: str
    score: int            # Overall score (0–100)
    roleAvg: int          # Role average score (for delta computation)
    delta: str            # Signed string "+44" or "-15" (display only)
    activeTime: str       # "Hh MMmin" format (e.g., "10h 49min")
    trendCy: List[float]  # Sparkline points (~5–10 values)
    trendColor: str       # CSS var: "var(--blue-500)" or "var(--red-500)"
    status: Literal["needs-attention", "inactive", "most-engaged", "on-track"]  # Triage output
    metrics: List[MetricRecord]  # Detailed metrics (all 6 sections)

class FilterOptions(BaseModel):
    """Available filter options."""
    departments: List[str]
    roles: List[str]
    managers: List[str]
    employees: List[Dict[str, str]]  # [{id, name}, ...]

class ReportMetadata(BaseModel):
    """Report header metadata."""
    title: str            # "Monthly KPI Report"
    breadcrumb: str       # Company name
    dateRange: str        # "May 1–29, 2026"
    dateFrom: str         # ISO date: "2026-05-01"
    dateTo: str           # ISO date: "2026-05-29"

class MonthlyKPIReport(BaseModel):
    """Complete report payload."""
    header: ReportMetadata
    employees: List[EmployeeKPI]
    filterOptions: FilterOptions
    statusCounts: Dict[str, int]  # {status: count}
    roleTab: Dict[str, Dict]      # Role averages (optional, for dashboard)
```

**Validation Rules:**
- `status` must be one of exactly 4 strings (case-sensitive, hyphenated)
- `activeTime` must parse as `Hh MMmin` or `"—"` for missing
- `roleAvg` must equal the role's median score (from triage baseline)
- `metrics` must contain all expected sections (counts may vary by customer)

#### 6.2 `repository.py` — BigQuery Data Access Layer

**Purpose:** Execute 11 parameterized BigQuery queries, fetch manager lookup, return aggregated results

**Structure:**

```python
class MonthlyKPIRepository:
    def __init__(self, project: str = "prodoscore-prodolab-live", client=None):
        """Initialize with BigQuery client (ADC auth)."""
        self.client = client or bigquery.Client(project=project)
        self.project = project
        self.dataset = "prodoapp_analytics_dataset"

    def query(
        self,
        domain_id: int,
        start_date: str,  # YYYY-MM-DD
        end_date: str,    # YYYY-MM-DD
        **filters           # department, role, manager (optional post-query filters)
    ) -> Dict[str, Any]:
        """Execute 11 BigQuery queries, return aggregated employee + role data."""
        # 1. Run all 11 sql/ queries with parameterization
        # 2. Fetch manager lookup (id → fullname)
        # 3. Fetch company display name (domain title)
        # 4. Aggregate results into role-average lookups
        # 5. Return {
        #      employees: [...],      # raw query results (before triage)
        #      roleAverages: {...},   # role -> {score, activeTime, ...}
        #      companyAverage: {...}, # company-level medians
        #    }

    def _run_sql(self, filename: str, params: dict) -> List[dict]:
        """Run one SQL query from sql/ directory."""
        # Read sql/{filename}
        # Execute with parameterization: @domain_id, @start, @end
        # Return [dict, dict, ...] rows

    def _mock_data(self, domain_id: int, start_date: str, end_date: str) -> dict:
        """Mock fallback (no BigQuery required for development)."""
        # Return valid EMPLOYEES structure for domain=9, hard-coded
```

**Critical Parity Points:**
- Use **half-up rounding with EPS** for all aggregate calculations
- **R type-7 median** (mean of two middles for even n)
- **Deterministic sorting** — all tie-breaks end in employee_id
- **Role average fallback** — use company median if role < min_role_sample

#### 6.3 `service.py` — Business Logic & Triage

**Purpose:** Assemble final report, apply triage cascade, compute derived fields

**Structure:**

```python
class MonthlyKPIService:
    def __init__(self, repository: MonthlyKPIRepository):
        """Initialize with data repository."""
        self.repository = repository

    @staticmethod
    def r0(x: float) -> int:
        """Half-up rounding (parity with triage.py)."""
        import math
        EPS = 1e-9
        return math.floor(x + 0.5 + EPS)

    @staticmethod
    def median_r7(values: List[float]) -> float:
        """R type-7 median."""
        s = sorted(values)
        n = len(s)
        if n % 2 == 1:
            return float(s[n // 2])
        return (s[n // 2 - 1] + s[n // 2]) / 2.0

    def assemble_report(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        **filters
    ) -> MonthlyKPIReport:
        """Assemble complete report: fetch → triage → format → validate."""
        # 1. Query repository
        raw = self.repository.query(domain_id, start_date, end_date, **filters)
        
        # 2. Run triage cascade (convert to triage.py input format)
        triaged = self._run_triage(raw["employees"], raw["roleAverages"])
        
        # 3. Compute derived fields (delta, trendCy, trendColor)
        employees = [self._build_employee(e) for e in triaged]
        
        # 4. Generate filter options
        filter_opts = self._generate_filters(employees)
        
        # 5. Build report metadata
        header = self._build_header(domain_id, start_date, end_date)
        
        # 6. Count status distribution
        status_counts = self._count_statuses(employees)
        
        return MonthlyKPIReport(
            header=header,
            employees=employees,
            filterOptions=filter_opts,
            statusCounts=status_counts,
        )

    def _run_triage(self, employees: list, role_avgs: dict) -> list:
        """Convert repository output to triage.py format, run cascade."""
        # Convert to triage input: {employee_id, name, role, avg_score, active_min, days_active, days_total, ...}
        # Call triage_config() and run_triage(emp, cfg)
        # Return modified list with status, severity, tier, reason

    def _build_employee(self, emp: dict) -> EmployeeKPI:
        """Construct EmployeeKPI from raw + triage data."""
        # Compute delta = score - roleAvg
        # Format activeTime via fmt_hm()
        # Build metrics array (all 6 sections)
        # Build trendCy from score_weekday query
        # Assign trendColor (blue if up/stable, red if down)

    def _generate_filters(self, employees: list) -> FilterOptions:
        """Generate unique dept, role, manager, employee lists."""
        # Extract unique values
        # Sort deterministically
        # Return FilterOptions

    def _count_statuses(self, employees: list) -> Dict[str, int]:
        """Count employees per status."""
        return {
            "needs-attention": len([e for e in employees if e.status == "needs-attention"]),
            "inactive": len([e for e in employees if e.status == "inactive"]),
            "most-engaged": len([e for e in employees if e.status == "most-engaged"]),
            "on-track": len([e for e in employees if e.status == "on-track"]),
        }
```

**Parity Checklist:**
- ✓ Half-up rounding on all calculations
- ✓ R type-7 median for role/company averages
- ✓ Deterministic sorts (tie-break: employee_id)
- ✓ Exact 4 status strings (no variations)
- ✓ activeTime formatted exactly as `"Hh MMmin"`
- ✓ delta computed as `score - roleAvg` (signed string)
- ✓ trendCy from weekday scores (sparkline)

#### 6.4 `router.py` — FastAPI Endpoints

**Purpose:** REST API for report generation

**Endpoints:**

```python
router = APIRouter(prefix="/api/monthly-kpi", tags=["monthly-kpi"])

@router.get("/report")
async def get_monthly_kpi_report(
    domain_id: int = Query(9, description="Prodoscore domain ID (default: 9 = safe)"),
    start: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end: str = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
    manager: Optional[str] = Query(None, description="Filter by manager"),
    employee: Optional[str] = Query(None, description="Filter by employee ID"),
) -> MonthlyKPIReport:
    """
    Get monthly KPI report for specified domain and date range.
    
    Safety: domain 9 (Prodoscore) is the only safe default.
    Other domains are live customers — require authorization.
    """
    # Auto-default to current month if not provided
    if not start or not end:
        today = datetime.utcnow()
        start = f"{today.year}-{today.month:02d}-01"
        end = f"{today.year}-{today.month:02d}-28"
    
    service = MonthlyKPIService(MonthlyKPIRepository())
    return service.assemble_report(
        domain_id=domain_id,
        start_date=start,
        end_date=end,
        department=department,
        role=role,
        manager=manager,
        employee=employee,
    )

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "module": "monthly_kpi"}

@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Return config (thresholds, status strings, version)."""
    return {
        "version": "3.3.0",
        "status_strings": ["needs-attention", "inactive", "most-engaged", "on-track"],
        "safe_domain_id": 9,
        "safe_domain_name": "Prodoscore",
    }
```

#### 6.5 `__init__.py` — Package Initialization

```python
"""Monthly KPI Report module.

FastAPI router for monthly KPI report generation and retrieval.
Integrates with BigQuery for data access and service layer for business logic.
"""

from .router import router

__all__ = ["router"]
```

### Frontend Next.js Component (1 File)

#### 6.6 `page.tsx` — React Dashboard

**Purpose:** Type-safe Next.js page with Tailwind CSS, Figma design tokens

**Structure:**

```typescript
"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Download, Settings } from "lucide-react";

// ============================================================================
// Types (matching REAL_DATA_SPEC.md)
// ============================================================================

interface Metric {
  section: string;
  label: string;
  value: string | number;  // May include units, percentages, or "—"
  roleAvg?: string | number;
}

interface Employee {
  name: string;
  dept: string;
  role: string;
  manager: string;
  score: number;
  roleAvg: number;
  delta: string;
  activeTime: string;
  trendCy: number[];
  trendColor: string;
  status: "needs-attention" | "inactive" | "most-engaged" | "on-track";
  metrics: Metric[];
}

interface MonthlyKPIReport {
  header: {
    title: string;
    breadcrumb: string;
    dateRange: string;
    dateFrom: string;
    dateTo: string;
  };
  employees: Employee[];
  filterOptions: {
    departments: string[];
    roles: string[];
    managers: string[];
    employees: Array<{ id: string; name: string }>;
  };
  statusCounts: {
    "needs-attention": number;
    inactive: number;
    "most-engaged": number;
    "on-track": number;
  };
}

// ============================================================================
// Design Tokens (Figma: Prodoscore Design System)
// ============================================================================

const DESIGN_TOKENS = {
  // Status colors (from Figma)
  status: {
    "most-engaged": {
      bg: "bg-green-50",
      border: "border-green-200",
      badge: "bg-green-100 text-green-800",
      icon: "text-green-600",
    },
    "needs-attention": {
      bg: "bg-red-50",
      border: "border-red-200",
      badge: "bg-red-100 text-red-800",
      icon: "text-red-600",
    },
    "on-track": {
      bg: "bg-blue-50",
      border: "border-blue-200",
      badge: "bg-blue-100 text-blue-800",
      icon: "text-blue-600",
    },
    inactive: {
      bg: "bg-gray-50",
      border: "border-gray-200",
      badge: "bg-gray-100 text-gray-800",
      icon: "text-gray-500",
    },
  },
  // Typography (Figma: Nunito font stack)
  typography: {
    title: "text-3xl font-bold text-gray-900",
    heading: "text-lg font-semibold text-gray-900",
    body: "text-sm text-gray-600",
    caption: "text-xs text-gray-500",
  },
  // Spacing grid
  spacing: {
    xs: "p-2",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  },
};

// ============================================================================
// Main Component
// ============================================================================

export default function MonthlyKPIPage() {
  // Component implementation here
}
```

**Design Token Mapping (Figma):**

Use design tokens from the provided Figma file:
```
https://www.figma.com/file/AbCdEfGh123456/Prodoscore-Design-System
```

Map to Tailwind CSS custom properties (or inline styles):
- Colors: `--green-500`, `--red-500`, `--blue-500`, `--gray-200`
- Typography: `Nunito` font family
- Spacing: 4px, 8px, 16px, 24px grid
- Shadows: Figma component shadow definitions

---

## 7. Section 6: Remote GitHub API Pipeline

### Execution Plan

#### 7.1 Pre-Execution

1. **Feature branch:** Create `feat/migration-monthly-kpi` on remote
2. **Documentation:** Commit SKILL.md + MIGRATION_SUMMARY.md
3. **PR:** Open PR (documentation only)

#### 7.2 Code Push

**Push order (nested paths to avoid conflicts):**

1. Backend Python module (5 files):
   ```
   backend/modules/monthly_kpi/__init__.py
   backend/modules/monthly_kpi/schemas.py
   backend/modules/monthly_kpi/repository.py
   backend/modules/monthly_kpi/service.py
   backend/modules/monthly_kpi/router.py
   ```

2. Frontend TypeScript component (1 file):
   ```
   frontend/pages/monthly-kpi/page.tsx
   ```

3. Integration guide:
   ```
   INTEGRATION_GUIDE.md (registry patch, testing steps)
   ```

#### 7.3 Registry Patch

After code push, patch the app's main FastAPI file (e.g., `app/main.py`):

```python
# Add this import
from app.modules.monthly_kpi import router as monthly_kpi_router

# Add this in app setup
app.include_router(monthly_kpi_router)
```

#### 7.4 Testing

```bash
# Health check (no BigQuery required)
curl http://localhost:8000/api/monthly-kpi/health

# Mock data (default domain 9, current month)
curl http://localhost:8000/api/monthly-kpi/report

# Full query (domain 9, May 2026)
curl "http://localhost:8000/api/monthly-kpi/report?domain_id=9&start=2026-05-01&end=2026-05-29"
```

#### 7.5 Merge & Deploy

1. Update PR description with code asset links
2. Await code review
3. Merge to `main`
4. Deploy to staging → validate endpoints → production

---

## 8. Safety & Compliance

### Access Control

- **Domain 9 (Prodoscore)** is the only safe default for testing
- **Other domains** are live customers — require explicit authorization
- Implement role-based access control (RBAC) on `domain_id` parameter
- Audit log all API calls to `/api/monthly-kpi/report`

### Data Privacy

- **No PII in logs** — strip sensitive fields before logging
- **BigQuery results** — use gcloud ADC; no hardcoded credentials
- **CORS** — restrict frontend origin to trusted domains
- **Rate limiting** — implement per-domain rate limits

### Testing & Validation

- **Unit tests:** Triage logic, rounding, median calculations
- **Integration tests:** BigQuery query results vs. expected shape
- **Contract validation:** Every employee output against REAL_DATA_SPEC.md
- **Visual regression:** Compare rendered report with known-good baseline

---

## 9. Deliverables Checklist

After execution, confirm:

- ✓ Feature branch created on remote
- ✓ SKILL.md committed (this file)
- ✓ 6 code files pushed (nested structure, no conflicts)
- ✓ PR opened with full description
- ✓ Integration guide (registry patch, testing steps)
- ✓ All endpoints testable (health, mock data, full query)
- ✓ Design tokens applied (Figma → Tailwind CSS)
- ✓ REAL_DATA_SPEC.md contract validated
- ✓ Triage parity verified (Python ↔ R, if applicable)
- ✓ PR reviewed and merged
- ✓ Staged & production deployment links documented

---

## 10. References

- **HANDOFF.md** — Local pipeline overview, parity notes
- **REAL_DATA_SPEC.md** — Output contract (employee shape, status strings, metrics)
- **assemble.py** — Python data assembly logic (formatting, SQL execution)
- **triage.py** — Python status cascade (4 stages, severity/tier/reason)
- **kpi_web_template.html** — Report template (60 KB; CSS, filters, tables)
- **Figma Design System** — https://www.figma.com/file/AbCdEfGh123456/Prodoscore-Design-System
- **docs/WORKING_DAY_GATES.md** — 6 gates for active day classification
- **docs/TRIAGE_LOGIC.md** — Cascade thresholds and stage descriptions

---

## 11. Troubleshooting

### GitHub API Path Conflicts

**Problem:** Error creating nested path (e.g., `backend/modules/monthly_kpi/`)

**Cause:** Flat-path files block nested subdirectories

**Solution:**
1. Delete flat files from remote: `backend/`, `frontend/` if they exist as files (not directories)
2. Use distinct naming scheme if forced to coexist
3. Retry nested path push

### Triage Output Mismatch

**Problem:** Status distribution doesn't match expected

**Cause:** Rounding, median, or sort order differences

**Verification:**
1. Run triage on same input as R version
2. Compare `_median()`, `r0()`, sort order
3. Ensure EPS=1e-9 applied consistently

### BigQuery Access Denied

**Problem:** `google.auth.exceptions.DefaultCredentialsError`

**Cause:** gcloud ADC not configured

**Solution:**
```bash
gcloud auth application-default login
# Grant: prodoscore-prodolab-live (project), prodoapp_analytics_dataset (dataset)
```

---

**End of SKILL.md**

**Version:** 3.3.0 | **Last Updated:** 2026-06-12 | **Status:** Production Ready
