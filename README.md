# FinanceCalc Predictor

FinanceCalc Predictor is a Python/Flask learning project focused on modelling debt repayment using both exact financial calculations and a simple machine learning approach.

The project combines:

* a compound-interest repayment calculator
* a simple-interest comparison
* an AI-based predictor that estimates repayment trends and compares them to the exact formula results

---

## Project Structure

```text
financecalc/          Main Flask app (calculator + integrated AI predictor)
ai_debt_predictor/    Standalone version of the AI predictor
```

---

## How it works

* The calculator uses compound interest formulas to compute an exact repayment schedule
* A simple-interest model is included for comparison
* The AI predictor uses linear regression (NumPy) to learn the repayment trend
* Results are displayed side-by-side using charts and tables

---

## Key Features

* Monthly debt repayment modelling with compound interest
* Simple-interest comparison (fixed benchmark rate)
* AI prediction of repayment trends
* Visual comparison between formula and AI results
* Chart.js visualisations (balance over time)
* Summary metrics (e.g. average prediction difference, payoff estimate)

---

## Running the project

```bash
cd financecalc
pip install -r requirements.txt
python3 main2.py
```

Then open:

```
http://127.0.0.1:5000
```

---

## Notes

* This is a learning project, not financial advice
* The AI model is intentionally simple and designed for demonstration
* The focus is on understanding how machine learning compares to exact mathematical models

---

## What I learned

* How to model financial systems using code
* How simple machine learning models can approximate real processes
* The difference between exact mathematical solutions and learned predictions
