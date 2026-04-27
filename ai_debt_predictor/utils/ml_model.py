########################################
############ ML debt prediction ##########
########################################

########################################
############ Third-party imports #########
########################################

import numpy as np


def _trim_at_payoff(month_numbers: list, formula_balances: list) -> tuple[list, list]:
    """Use formula points up to and including the first month at zero balance."""
    for i, bal in enumerate(formula_balances):
        if bal <= 0:
            return month_numbers[: i + 1], formula_balances[: i + 1]
    return month_numbers, formula_balances


def predict_debt_with_ml(
    starting_debt: float,
    month_numbers: list,
    formula_balances: list,
    future_months: int,
) -> list[float]:
    """
    Ordinary least squares linear regression (month index -> balance), same model
    class as sklearn.linear_model.LinearRegression with one feature and intercept.

    Training includes t=0 with starting debt. Predictions are clipped at 0.
    """
    if future_months < 1:
        future_months = 1

    ########################################
    ############ Build training set ##########
    ########################################

    m_trim, b_trim = _trim_at_payoff(month_numbers, formula_balances)

    t_rows = [0.0]
    y_rows = [float(starting_debt)]

    for m, bal in zip(m_trim, b_trim):
        t_rows.append(float(m))
        y_rows.append(float(bal))

    t_train = np.array(t_rows, dtype=float)
    y_train = np.array(y_rows, dtype=float)

    if len(y_train) < 2:
        return [max(0.0, float(formula_balances[0]))] if formula_balances else [0.0]

    # y = intercept + slope * month  ->  lstsq on [1, t]
    a_design = np.column_stack([np.ones(len(t_train)), t_train])
    coef, *_ = np.linalg.lstsq(a_design, y_train, rcond=None)
    intercept, slope = float(coef[0]), float(coef[1])

    predict_months = np.arange(1, future_months + 1, dtype=float)
    preds = intercept + slope * predict_months
    clipped = [max(0.0, round(float(p), 2)) for p in preds]
    return clipped
