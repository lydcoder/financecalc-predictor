########################################
############ Debt schedule math ##########
########################################

# (no external imports — pure Python numerics)


def calculate_debt_schedule(
    starting_debt: float,
    annual_interest_rate: float,
    monthly_payment: float,
    months: int,
):
    """
    Amortising balance: interest accrues monthly, then payment is applied.

    Returns a dict with:
        month_numbers: 1..months
        formula_balances: balance at end of each month
        total_interest: sum of interest charged over the schedule window
        payoff_month: first month index (1-based) where balance hits 0, or None
        never_decreasing: True if payment does not cover interest on opening balance
    """
    if months < 1:
        months = 1

    monthly_rate = (annual_interest_rate / 100.0) / 12.0
    balance = float(starting_debt)
    total_interest = 0.0
    month_numbers = []
    formula_balances = []
    payoff_month = None
    never_decreasing = False

    if balance > 0 and monthly_payment <= balance * monthly_rate:
        never_decreasing = monthly_payment <= balance * monthly_rate

    for m in range(1, months + 1):
        month_numbers.append(m)
        if balance <= 0:
            formula_balances.append(0.0)
            continue

        interest = balance * monthly_rate
        total_interest += interest
        balance = balance + interest - monthly_payment

        if balance < 0:
            balance = 0.0
        if payoff_month is None and balance <= 0:
            payoff_month = m

        formula_balances.append(round(balance, 2))

    return {
        "month_numbers": month_numbers,
        "formula_balances": formula_balances,
        "total_interest": round(total_interest, 2),
        "payoff_month": payoff_month,
        "never_decreasing": never_decreasing,
    }
