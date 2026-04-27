# FinanceCalc Predictor

**FinanceCalc Predictor** is a small **Python / Flask** learning project built around **debt and interest calculators**. It has two deployable surfaces:

1. **`financecalc/`** — a single Flask application that serves a **compound-interest repayment calculator** (with a **simple-interest comparison** lane) and an **integrated AI debt predictor** on a separate URL.
2. **`ai_debt_predictor/`** — the same **predictor logic** packaged as a **minimal standalone Flask app** (useful for demos or isolating the “AI vs formula” feature).

Shared predictor math and the linear-regression layer live under **`ai_debt_predictor/utils/`**. The main app adds that directory to `sys.path` and imports those modules when the debt-predictor routes run.

---

## Repository layout

| Path | Role |
|------|------|
| `financecalc/main2.py` | Flask app: routes, compound/SI orchestration, debt-predictor wiring, `DebtDataForm`. |
| `financecalc/myfunctions.py` | Helpers for **comparing** compound vs simple totals, month differences, percentage differences, etc. |
| `financecalc/templates/` | Jinja2 HTML: landing (`C_results.html`), compound results (`index2.html`), debt predictor pages, `base.html`. |
| `financecalc/static/css/style.css` | Shared styling; includes debt-predictor-specific rules. |
| `financecalc/requirements.txt` | Flask, Flask-WTF, WTForms, Werkzeug stack, **numpy** (required for debt predictor). |
| `ai_debt_predictor/app.py` | Standalone Flask factory + routes `/` and `/predict`. |
| `ai_debt_predictor/utils/finance.py` | **Formula** month-by-month debt schedule (amortising balance). |
| `ai_debt_predictor/utils/ml_model.py` | **NumPy OLS** linear regression on month → balance; prediction + clip at zero. |
| `ai_debt_predictor/utils/view_helpers.py` | Builds **table rows**, **chart JSON**, **mean absolute difference**, **AI payoff month**, **trimmed table** + tail note. |
| `ai_debt_predictor/templates/` | Standalone `index.html` / `results.html` (lighter UI than the integrated flow). |
| `ai_debt_predictor/requirements.txt` | Flask + numpy only (no WTForms in standalone). |

There are local virtualenv folders (`financecalc/myenv`, `ai_debt_predictor/.venv`) in some checkouts; they are **not** required by the documentation and should stay out of version control if you use git.

---

## Part A — `financecalc` (main application)

### How to run

```bash
cd financecalc
pip install -r requirements.txt
python3 main2.py
```

Default development server: **http://127.0.0.1:5000** with Flask `debug=True`.

The debt predictor **requires** the `ai_debt_predictor` package layout to exist **next to** `financecalc` (sibling folder `../ai_debt_predictor`) and **requires numpy**. If imports fail, **`/debt-predictor`** returns **503** and renders `debt_predictor_missing.html`.

---

### Route map (`main2.py`)

| Method | Path | Behaviour |
|--------|------|-----------|
| `GET`, `POST` | `/` | **Compound calculator**: show instructions + form (`C_results.html`) on GET or failed validation; on valid POST, run schedules and show **`index2.html`**. |
| `GET` | `/debt-predictor` | **Debt predictor** input form (`debt_predictor_index.html`). Passes `dp_last` from the session when present (see below). |
| `POST` | `/debt-predictor/predict` | Validates numeric inputs, builds schedule + ML line, renders **`debt_predictor_results.html`**, stores last successful inputs in the session. |

There is commented-out legacy code for PDF export; it is **not** active.

---

### A.1 Compound interest calculator (`/`)

**Purpose:** Model a **revolving-style debt** with a **fixed minimum monthly payment**, using a **compound interest** accrual model, and compare several headline numbers against a **simple-interest amortisation** run in parallel.

#### User inputs (`DebtDataForm`)

- **Interest rate (APR)** — `FloatField`; must be **> 0** and **≤ 80%**. Stored as a percentage in the form; `conv_apr_to_dec()` divides by 100 for calculations.
- **Monthly payment** — integer, minimum 1; custom validator ensures payment is **strictly less than** opening debt (cannot equal or exceed full balance in one go).
- **Debt balance** — integer principal, minimum 1.
- **Currency** — select (USD, EUR, GBP, CNY, JPY, INR, BRL). Symbols map in the view for display; the **math is currency-agnostic** (numbers only).

#### “20-year” viability gate (`debt_validate`)

Before the heavy calculation, the app simulates whether the debt could be cleared within **20 years** ( **`max_years = 20` → 240 months** ) using the same compound helper as the main loop (`compound_interest` with **365** as compounding frequency in the interest step). If after that horizon the balance would still be positive, **`check_debt_valid` is `False`** and the UI shows a validity failure without populating full amortisation tables.

#### Compound schedule (`debt_calculate_monthly`)

- Clears global lists: `month_list`, `principal_list`, `interest_list`, `principle_payment_list`, `accrued_interest_list`, plus simple-interest lists.
- Seeds index **0** with zeros / opening principal so later “years/months to pay” logic can offset by one month.
- For up to **240 months**, while the balance stays positive:
  - Computes a **compound factor** via `compound_interest(debt_apr, 365)` (APR interpreted with a **365-times-per-year** stepping model, then a **one-twelfth-of-year** exponent slice — i.e. not the same closed form as the AI predictor’s simple `APR/12` monthly rate).
  - **Interest** = balance × (compound factor − 1).
  - **Principal portion of payment** = payment − interest (`get_principal_payment`).
  - **New balance** = balance + interest − payment.
- List lengths and accrued-interest running totals feed the results template and comparisons.

#### Simple-interest lane (`calc_simple_interest`)

- Runs a **separate** amortisation where monthly interest is **`(si_apr / 12) * current_balance`**, then principal reduced by `(payment − interest)`.
- **Important:** In `index()`, this is invoked as **`calc_simple_interest(principal, 0.10, min_payment)`** — a **fixed 10% annual rate** for the simple-interest path, **not** the user’s entered APR. The UI therefore compares **user APR compound path** vs **10% simple benchmark** (a pedagogical contrast, not a same-rate A/B).

#### Derived outputs passed to `index2.html`

Including but not limited to: years/months to pay (`get_years` / `get_months`), formatted total accrued interest and total payback, percentage-of-principal style metrics, **simple-interest** duration and total payback, **difference in months/years** between compound and simple schedules, **percentage gaps** on accrued interest and totals, flags for which total is larger, and raw lists for **Chart.js** tables/graphs of balance, interest, principal payment, and cumulative interest.

#### Templates / UX

- **`C_results.html`** — first screen: explanatory copy, the form, link toward the compound flow.
- **`index2.html`** — results + embedded recalculation form, navigation back to instructions, link to **“AI-enhanced predictor”** (`url_for('debt_predictor')`), charts (Chart.js), Bootstrap layout, optional client scripts (e.g. html2canvas/jspdf references in template — verify if still used for export).

Styling is primarily **`financecalc/static/css/style.css`** (global + calculator + debt-predictor sections).

---

### A.2 Integrated AI debt predictor (`/debt-predictor`)

**Purpose:** For user-chosen **starting debt**, **annual APR**, **fixed monthly payment**, and **forecast length (1–120 months)**, compute:

1. A **transparent formula schedule** (`calculate_debt_schedule` in `utils/finance.py`).
2. A **linear regression “AI” line** fitted to the formula curve (`predict_debt_with_ml` in `utils/ml_model.py`).
3. A **rich results page**: summary metrics, model comparison copy, Chart.js chart (formula vs ML, fills / band), trimmed month table, educational panels, **“Run another prediction”** (returns to form with **session-prefilled** values from the last successful run).

**Server validation** (POST): numeric parse; starting debt must be positive; APR must be non-negative; payment must be positive; forecast months in **[1, 120]**. Errors re-render the index template with `error` and `dp_last`.

**Session key:** `dp_last_form` — dict of string fields `starting_debt`, `annual_interest_rate`, `monthly_payment`, `forecast_months` after a **successful** prediction.

For **every** field-level and architectural detail of the predictor (formula steps, regression design matrix, trimming, metrics), see **`ai_debt_predictor/README.md`**.

---

## Part B — `ai_debt_predictor` (standalone app)

Minimal Flask app created by `create_app()` in `app.py`:

- **`GET /`** — predictor form.
- **`POST /predict`** — same validation and pipeline as integrated POST, renders `results.html`.

**Differences vs integrated app:**

- No **Flask-WTF** form class; plain `request.form`.
- No **session prefill** of last inputs.
- Different templates and styling footprint.
- Uses `SECRET_KEY` from environment with a dev default.

Run:

```bash
cd ai_debt_predictor
pip install -r requirements.txt
export FLASK_APP=app.py   # optional; or python app.py
flask run
# or: python3 app.py
```

---

## Dependencies (summary)

| Area | Packages |
|------|----------|
| `financecalc` | Flask, Flask-WTF, WTForms, Jinja2, Werkzeug, blinker, etc. (see `requirements.txt`) + **numpy** for predictor. |
| `ai_debt_predictor` | Flask, **numpy** only (`requirements.txt`). |

Front-end libraries (Chart.js, Bootstrap) are loaded from **CDNs** in templates, not vendored in the repo.

---

## Security and production notes

- `financecalc/main2.py` sets a **hard-coded `SECRET_KEY`**. For any real deployment, use an environment variable and a strong random secret.
- The app runs with **`debug=True`** in the `if __name__ == '__main__'` block — never use that in production as-is.
- This project is for **learning and illustration**, not regulated financial advice.

---

## Where to read next

- **AI-only deep dive** (mathematics, training data, metrics, limitations, dual deployment): [`ai_debt_predictor/README.md`](ai_debt_predictor/README.md)
- **Short `financecalc` quick start**: [`financecalc/README.md`](financecalc/README.md)
