# AI debt predictor — technical README

This document describes **only** the **AI-enhanced debt repayment predictor**: the mathematics, the machine-learning layer (implemented without sklearn), how results are prepared for the UI, and how the feature is exposed in **two** Flask applications.

For the **full repository** (compound calculator, routes, folder layout), see the project root **[`README.md`](../README.md)**.

---

## What this feature does (user-visible)

1. Collects **starting debt**, **annual interest rate (APR, %)**, **monthly repayment**, and a **forecast horizon in months** (1–120).
2. Computes a **month-by-month “formula” schedule**: each month, interest accrues on the opening balance at **APR ÷ 12**, then the payment is subtracted; balance is floored at **£0** when it would go negative.
3. Fits a **single straight line** in time (month index → balance) to those formula points using **ordinary least squares (OLS)** via **NumPy** `numpy.linalg.lstsq`, then evaluates that line at each forecast month to produce an **“AI prediction”** curve.
4. Presents **summary numbers**, a **line chart** (formula vs prediction), a **table** of month / formula / AI balances, and explanatory copy. The integrated app (`financecalc`) adds session-based **form prefill** after a successful run.

The UI wording uses **“AI”** in a **portfolio / educational** sense: the model is **transparent linear regression**, not a black-box neural network.

---

## Code map

| File | Responsibility |
|------|------------------|
| `utils/finance.py` | `calculate_debt_schedule(...)` — pure Python, no third-party imports. |
| `utils/ml_model.py` | `predict_debt_with_ml(...)` — NumPy design matrix + `lstsq`; trimming; clipping. |
| `utils/view_helpers.py` | `build_debt_predictor_view_context(...)` — MAE, chart payload, table trim, AI payoff month. |
| `app.py` | Standalone Flask: `GET /`, `POST /predict`. |
| `templates/index.html` | Standalone input form. |
| `templates/results.html` | Standalone results (simpler than `financecalc` templates). |

The **integrated** app imports the same three utilities from `../ai_debt_predictor` by inserting that directory on `sys.path` in `financecalc/main2.py`.

---

## 1. Formula schedule (`calculate_debt_schedule`)

**Inputs**

- `starting_debt` (float)  
- `annual_interest_rate` (float, **percent per year**, e.g. `18` for 18%)  
- `monthly_payment` (float)  
- `months` (int) — number of **forecast** months to emit (minimum 1 after guard)

**Monthly rate**

```text
monthly_rate = (annual_interest_rate / 100) / 12
```

**Loop** for `m = 1 .. months`

- If balance already ≤ 0: append month `m` and balance **0** (interest for that month is **not** added in this branch — the balance stays flat at zero for remaining months).
- Otherwise:
  - `interest = balance * monthly_rate`
  - `total_interest` accumulates `interest`
  - `balance = balance + interest - monthly_payment`
  - If `balance < 0`, set `balance = 0`
  - Record `payoff_month` the **first** time balance hits ≤ 0 after the update
  - Append `round(balance, 2)` to `formula_balances`

**Flags**

- **`never_decreasing`**: `True` when, on the **opening** balance, the payment does **not** exceed interest (`monthly_payment <= balance * monthly_rate`). The debt would grow or stall on the formula model; the UI can warn while still showing comparison curves.

**Return dict keys**

- `month_numbers` — `1 .. months`  
- `formula_balances` — end-of-month balances  
- `total_interest` — summed interest (rounded to 2 dp)  
- `payoff_month` — 1-based month index of first zero balance, or `None`  
- `never_decreasing` — boolean  

This schedule is **not** identical to the **compound calculator** in `main2.py`, which uses a **365-frequency compound_interest** helper for the credit-card style path. The predictor uses the **standard monthly APR/12** balance update — consistent with typical amortisation explanations and easier to pair with a linear trend.

---

## 2. “ML” prediction (`predict_debt_with_ml`)

### 2.1 Design intent

- **Features:** time as **month index**.  
- **Target:** **formula balance** (after training trim — see below).  
- **Model:** `balance ≈ intercept + slope * month`  
- **Solver:** OLS by stacking `[1, t]` into a design matrix **A** and solving **A β ≈ y** with `numpy.linalg.lstsq` — equivalent to `sklearn.linear_model.LinearRegression(fit_intercept=True)` on a single feature.

### 2.2 Trimming training data (`_trim_at_payoff`)

Training pairs are taken from the formula schedule **only up to and including the first month where formula balance ≤ 0**.  

**Why:** Trailing long runs of **£0.00** would pull the regression toward a flat line and misrepresent the **paydown** segment.

### 2.3 Training rows construction

The function builds:

- `t_rows = [0.0]` and `y_rows = [starting_debt]` — an explicit **t = 0** point at opening balance.  
- For each `(m, bal)` in the **trimmed** `(month_numbers, formula_balances)` pairs, append `float(m)` and `float(bal)`.

So the regressor sees **discrete month indices** from the schedule (1, 2, …) plus the origin row.

### 2.4 Edge case

If fewer than **two** training **y** values exist after construction, the implementation returns a minimal safe list (e.g. one clipped value from the first formula balance) instead of calling `lstsq`.

### 2.5 Prediction horizon

`predict_months = np.arange(1, future_months + 1)` — predictions are **only** for months **1 … future_months** (not re-predicting month 0 for the chart series; month 0 is implicit in the fit but the returned list aligns with forecast months).

Each prediction is **`max(0, round(pred, 2))`** — balances never go negative on the AI line.

---

## 3. View context (`build_debt_predictor_view_context`)

**Inputs:** `schedule` dict from finance, `ml_balances` list (same length as months in schedule for normal paths).

### 3.1 Full row list

For each month index `i`, builds:

```python
{"month": m, "formula": schedule["formula_balances"][i], "ml": ml_balances[i]}
```

### 3.2 Mean absolute difference (displayed as “average difference”)

```text
mean_abs_difference = round( sum_i |formula_i - ml_i| / n , 2 )
```

where `n` is the number of rows in that **full** comparison (same as number of forecast months). This is **not** the same as RMSE; it is **mean absolute error** between the two curves over the window.

### 3.3 AI “payoff” month

First month where **`ml <= 0.005`** (tolerance for float / rounding). `None` if never hit in the window.

### 3.4 Trimmed table + tail note

The HTML table **stops at the first month the formula balance ≤ 0.005** to avoid dozens of identical **£0.00** rows. If months remain in the forecast after that, `table_tail_note` explains that the debt is cleared and remaining months are zero.

### 3.5 Chart payload

```python
chart_data = {
    "labels": schedule["month_numbers"],
    "formula": schedule["formula_balances"],
    "ml": ml_balances,
}
```

The **integrated** `financecalc` template embeds this as JSON and drives **Chart.js** (line chart, fills, band between series — see template `debt_predictor_results.html`).

---

## 4. HTTP validation (both apps)

| Rule | Integrated (`main2.py`) | Standalone (`app.py`) |
|------|-------------------------|------------------------|
| Parse failure | 400 + error message | 400 + error message |
| Starting debt | Must be positive | Same |
| APR | Must be non-negative | Same |
| Monthly payment | Must be positive | Same |
| Forecast months | 1–120 inclusive | 1–120 inclusive |

Standalone does **not** write sessions. Integrated stores **`dp_last_form`** after success for **prefill** on `GET /debt-predictor`.

---

## 5. Limitations (honest list)

1. **Linear model:** Real amortisation is **curved**; a line is a **deliberately weak** approximator — error often **grows near payoff** or when rates/payments would imply sharp curvature.
2. **Training on formula, not on real bank data:** The “AI” line is **fitted to the same synthetic schedule** it is compared against — this is an **epistemic** exercise (how close can a line track a known curve?), not a forecast from external data.
3. **Monthly APR/12:** High-level “compound interest” labels in copy refer to **monthly balance mechanics**, not daily compounding.
4. **Not advice:** Educational / portfolio use only.

---

## 6. Running tests / smoke checks

From the repo root, a minimal import check:

```bash
cd financecalc
python3 -c "import main2; print('main2 import OK')"
```

Requires `../ai_debt_predictor` present and `numpy` installed.

Standalone:

```bash
cd ai_debt_predictor
pip install -r requirements.txt
python3 app.py
```

---

## 7. Optional sklearn note

`ml_model.py` does **not** import scikit-learn. Dependencies for this package are **Flask + numpy** only. Any mention of sklearn in comments is **conceptual** (same linear model class), not a runtime dependency.
