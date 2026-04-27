########################################
############ Flask application ###########
########################################

########################################
############ Standard library ############
########################################

import os

########################################
############ Third-party imports #########
########################################

from flask import Flask, render_template, request

########################################
############ Local application ############
########################################

from utils.finance import calculate_debt_schedule
from utils.ml_model import predict_debt_with_ml
from utils.view_helpers import build_debt_predictor_view_context


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-in-production")

    ########################################
    ############ Routes ######################
    ########################################

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/predict", methods=["POST"])
    def predict():
        try:
            starting_debt = float(request.form.get("starting_debt", 0))
            annual_interest_rate = float(request.form.get("annual_interest_rate", 0))
            monthly_payment = float(request.form.get("monthly_payment", 0))
            forecast_months = int(request.form.get("forecast_months", 24))
        except (TypeError, ValueError):
            return render_template(
                "index.html",
                error="Please enter valid numbers for all fields.",
            ), 400

        if starting_debt <= 0:
            return render_template(
                "index.html",
                error="Starting debt must be greater than zero.",
            ), 400
        if annual_interest_rate < 0:
            return render_template(
                "index.html",
                error="Interest rate cannot be negative.",
            ), 400
        if monthly_payment <= 0:
            return render_template(
                "index.html",
                error="Monthly repayment must be greater than zero.",
            ), 400
        if forecast_months < 1 or forecast_months > 120:
            return render_template(
                "index.html",
                error="Forecast months must be between 1 and 120.",
            ), 400

        schedule = calculate_debt_schedule(
            starting_debt,
            annual_interest_rate,
            monthly_payment,
            forecast_months,
        )

        ml_balances = predict_debt_with_ml(
            starting_debt,
            schedule["month_numbers"],
            schedule["formula_balances"],
            forecast_months,
        )

        ctx = build_debt_predictor_view_context(schedule, ml_balances)

        return render_template(
            "results.html",
            starting_debt=starting_debt,
            annual_interest_rate=annual_interest_rate,
            monthly_payment=monthly_payment,
            forecast_months=forecast_months,
            total_interest=schedule["total_interest"],
            payoff_month=schedule["payoff_month"],
            never_decreasing=schedule["never_decreasing"],
            table_rows=ctx["table_rows"],
            table_tail_note=ctx["table_tail_note"],
            mean_abs_difference=ctx["mean_abs_difference"],
            ai_payoff_month=ctx["ai_payoff_month"],
            chart_data=ctx["chart_data"],
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
