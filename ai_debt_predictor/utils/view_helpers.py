########################################
############ Shared view logic ##########
########################################


def build_debt_predictor_view_context(
    schedule: dict,
    ml_balances: list,
):
    """
    Build table rows, chart payload, MAE, AI payoff month, and trimmed table for display.
    """
    table_rows = []
    for i, m in enumerate(schedule["month_numbers"]):
        ml_val = ml_balances[i] if i < len(ml_balances) else 0.0
        table_rows.append(
            {
                "month": m,
                "formula": schedule["formula_balances"][i],
                "ml": ml_val,
            }
        )

    n = len(table_rows)
    mean_abs_difference = (
        round(sum(abs(r["formula"] - r["ml"]) for r in table_rows) / n, 2) if n else 0.0
    )

    ai_payoff_month = None
    for r in table_rows:
        if r["ml"] <= 0.005:
            ai_payoff_month = r["month"]
            break

    table_display = list(table_rows)
    table_tail_note = None
    for i, r in enumerate(table_rows):
        if r["formula"] <= 0.005:
            table_display = table_rows[: i + 1]
            remaining = n - len(table_display)
            if remaining > 0:
                table_tail_note = (
                    f"Debt cleared after month {r['month']}. "
                    "Remaining forecast months are £0.00."
                )
            break

    chart_data = {
        "labels": schedule["month_numbers"],
        "formula": schedule["formula_balances"],
        "ml": ml_balances,
    }

    return {
        "table_rows": table_display,
        "table_tail_note": table_tail_note,
        "mean_abs_difference": mean_abs_difference,
        "ai_payoff_month": ai_payoff_month,
        "chart_data": chart_data,
        "full_row_count": n,
    }
