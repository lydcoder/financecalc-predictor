import sys
from pathlib import Path

from flask import Flask,render_template, request, session
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, FloatField, SelectField
from wtforms.validators import InputRequired
from wtforms import validators
from flask import send_file
from myfunctions import *
import re
import os
#import pdfkit 

#app = Flask(__name__)



## Function apr to convert to decimal ##
def conv_apr_to_dec(apr):
    apr = apr/100
    return apr


################################
### Variable Parameter vars ####
################################

#debt_apr = 0.28 #Interest APR applied to debt
#principal = 5000 #Initial debt amount
#min_payment = 200 #Minimum monthly payment

###########################
### Fixed counter vars ####
###########################

max_years = 20 #Maximum number of years
#compound_frequency = 365 #Daily compound. Number of times compounded per year
max_months = max_years*12 #maxium no months multiplies by number of years
max_months_exceed = max_months + 1 #Added to max months to test if been exceededf


########################################
#######        Function         ######## 
#### Calculate Compound Interest   #####
########################################

def compound_interest(debt_apr,compound_frequency):

    debt_base_no = 1 #Fixed and necessary              
    debt_int_interval = debt_apr/compound_frequency #Calculate interest,     #divides interest rate and frequency of compound to calculate interest
    base_apr = debt_base_no+debt_int_interval       
    one_month =  1/12 #  0.0833333.... For yearly multiplication, number of months or years 0.0833333....       #to calculate monthly compounding
    total_time = compound_frequency*one_month #For yearly multiplication, number of months or years
    debt_compound_calc = pow(base_apr,total_time) #Calc 1+(int/interval) ^ total months
    return debt_compound_calc #compund interest calculated

########################################
#######        Function         ######## 
####### Validate Debt 20 years  ########
########################################

def debt_validate(principal,debt_apr,min_payment):
    max_years = 20 # or whatever value you want
    max_months = max_years*12
    max_months_exceed = max_months + 1

    principal_var = principal #Need this for while loop and to vary
    month_no = 1 #month starting number

    #use min_payment in while loop so ammounts do not enter negatives
    while principal_var > min_payment and month_no<max_months_exceed:
        #debt_compound_calc = pow(base_apr,total_time) #Calc 1+(int/interval) ^ total months
        debt_compound_calc = compound_interest(debt_apr,365)
        interest = principal_var*debt_compound_calc-principal_var #Accrued amount only
        #print(f"interest: {round(interest,2)}")
        principal_var = principal_var+interest-min_payment #Add interest to principal less min payment
        #print(f"Month: {month_no}: {round(principal_var,2)}")
        month_no +=1
    
        #Validate maximum years have been exceeded and return false
        if principal_var > 0 and month_no >= max_months_exceed:
            debt_validated = False
            print(debt_validated)
            return debt_validated #return result

    #Return true if max years have not been exceeded
    else: 
        debt_validated = True
        print(debt_validated)
        return debt_validated #return result

###########################
####### List Vars  ########
###########################

# These lists will be passed to flask
month_list = []
principal_list = []
interest_list = []
principle_payment_list = []
accrued_interest_list = []


#### simple interest Lists #### 
si_principal_list = [] # a list of varying principal amount
si_total_interest_list = []
si_total_months_list = []
###############################

#################################################
##              >> Function <<                 ##
##               Clear lists                   ##
#################################################

def clear_list(list_name):
    list_name.clear()

#################################################
##              >> Functions <<                ##
##        Calculate years/months to pay        ##
#################################################

#Both of the below functions use an offset because the first line in month list
#is not counted

def get_years():
    years_to_pay = int(len(month_list[1:])/12) #Years to pay offset list by one
    return years_to_pay

def get_months():
    months_to_pay = len(month_list[1:]) % 12 #Months to pay using modulus, get remainder
    return months_to_pay

#################################################
##              >> Function  <<                ##
## Percentage of total accrued over principle  ##
## for info panel                               ##
#################################################

def get_percentage(principal, accrued):
    x = principal*100
    y = x/int(accrued)
    accrued_percentage = 100-y
    return accrued_percentage

#################################################
##              >> Function  <<                ##
##    Get principle payment for info panel     ##
#################################################

def get_principal_payment(p_int, p_min):
    p_payment = p_min - p_int
    return round(p_payment,2)

#################################################
##              >> Function  <<                ##
##    simple interest - calculate years        ##
#################################################

def si_calc_years(months):
    years = months/12
    return int(years)

#################################################
##              >> Function  <<                ##
##    simple interest - calculate months       ##
#################################################

def si_calc_months(months):
    months_left = months % 12
    return months_left

#################################################
##              >> Function  <<                ##
##    simple interest - calculate percentage   ##
#################################################

def si_calc_percentage(si_interest,si_principal):
    #final_interest = ac_interest/p_start_int*100
    si_int_percent = si_interest*100/si_principal # percentage paid on top in interest
    return round(si_int_percent, 2)

#################################################
##              >> Function  <<                ##
##compare simple interest and compound interest##
#################################################

def compare_values(si_pri_interest, total_payback):
    si_pri_interest = str(si_pri_interest).replace(',', '')
    total_payback = str(total_payback).replace(',', '')
    if float(total_payback) > float(si_pri_interest):
        return True
    else:
        return False

########## Test loop #######################


#################################################
##              >> Function <<                 ##
##    Calculate and display debt if viable     ##
#################################################

def debt_calculate_monthly(principal,debt_apr,min_payment):

    principal_var = principal #Need this for while loop and to vary
    month_no = 1 #month starting number
    #accrued_interest = 0 #starting accrued interest
    min_payment_check = min_payment
    
    #Ensure lists are empty in case flask page refresh
    clear_list(month_list) 
    clear_list(principal_list)
    clear_list(interest_list)
    clear_list(principle_payment_list)
    clear_list(accrued_interest_list)

    #Clear simple interest lists
    
    clear_list(si_principal_list)
    clear_list(si_total_interest_list)
    clear_list(si_total_months_list)

    #First line of list
    zero_add = 0 #needed for first line, manual add

    month_list.append(zero_add) #Add to month list
    interest_list.append(zero_add) #Add to interest list
    principle_payment_list.append(zero_add) #Add to principal payment list
    accrued_interest_list.append(zero_add) #Add to accrued interest list
    principal_list.append(principal) #Add to principal list

    #Loop for compound interest only
    for i in range(0,max_months):
        
        if principal_var > 0 and month_no < max_months_exceed:

            ### Vars ###

            #debt_compound_calc = pow(base_apr,total_time) #Calc 1+(int/interval) ^ total months
            debt_compound_calc = compound_interest(debt_apr,365)
        
            interest = principal_var*debt_compound_calc-principal_var #Accrued amount only
            #print(f"int_accrued: {int_accrued}")
            interest_list.append(round(interest,2)) #Add to interest list

            principle_payment_list.append(get_principal_payment(interest,min_payment))

            month_list.append(month_no) #Add to month list
        
            principal_var = principal_var+interest-min_payment

            principal_list.append(round(principal_var,2)) #Add to principal var list
            
            #### Accrued interest counter ####
            ### Take previous month and add to current month ####

            #print(f"Month No: {month_no}"".\n")

            #Check that last month is smaller then min payment and set to zero
            #Used for ensuring that the last line principal is 0
            if principal_var < min_payment_check and principal_var < 0:
                principal_var = min_payment_check
                principal_list[-1] = 0 # add zero to the end of the principal list
                break
            month_no +=1                

    month_no2 = month_list[-1]
        # lists needed for comparison ########
        
#################################
###         Function          ###
###   Calc Accrued Interest   ###
#################################

def debt_accrued_int():

    accrued_holder = interest_list[1] #Start list with second amount of interest list

    for i in range(1,len(interest_list)): #loop through interest list

        accrued_interest_list.append(round(accrued_holder,2)) #append accrued amount to list

        #print(f"holder_var: {accrued_holder} + interest_var: {interest_list[i]} = {accrued_holder}")
        accrued_holder  = accrued_holder + interest_list[i] #Calculate new accrued interest

    #Specific to calculate the last item of the holder var list, as there is an offset
    accrued_interest_list.append(round(interest_list[-1]+accrued_interest_list[-1],2))

######## Function End ##########

si_month_list = []
si_interest_list = []

#################################
###         Function          ###
###   Calc simple Interest    ###
#################################

def calc_simple_interest(si_principal,si_apr,si_min_payment):

    #si_principal = 1000
    #si_apr = 0.10
    #si_min_payment = 50

    si_no_payments = 12 # number of payments in a year

    si_principal_var = si_principal # another variable for the principal 
    si_month_no = 1 # starting month number
    si_monthly_int = si_apr/si_no_payments # interest divided by number of payments in a year to give the monthly payment
    
    ############# Si lists ##############
    
    clear_list(si_month_list) # lists need to be cleared before loops starts
    clear_list(si_interest_list)

    #si_month_list = []
    #si_interest_list = []

    while si_principal_var > 0:

        si_month_list.append(si_month_no) # appending the month list into an empty list     
        print(f"the simple interest month number is {si_month_no}") # displays month number 
        interest = si_monthly_int*si_principal_var # monthly interest times principal to get the total amount of interest paid in a year
        si_interest_list.append(interest) # appending the interest list into an empty list
        p_payment = si_min_payment-interest # taking away the interest from the monthly payment
        si_principal_var -= p_payment # taking the variable minimum payment-interest and taking it away from the principal
        print(f"si principal var is {si_principal_var}") # the new principal after the monthly payments are being taken away from it
        si_month_no += 1 # adding the month number 

    si_sum_pri_int = si_principal+sum(si_interest_list) # total principal + accrued interest
    si_int_percent = sum(si_interest_list)*100/si_principal # percentage paid on top in interest
    si_total_months = len(si_month_list) # total number of months
    si_accrued_int = sum(si_interest_list) # total accrued interest


    print(len(si_month_list)) # total months
    print(sum(si_interest_list)) # total accrued interest 
    print(si_sum_pri_int) # principal + accrued simple interest
    print(f"hallo {si_int_percent}")

#############################
######## FLASK FORM #########
#############################

def validate_only_numbers(form,field):
    value = field.data
    if isinstance(value, str):
        pattern = r'^[+-]?\d+$'
        if not re.match(pattern, value):
            raise validators.ValidationError('Value must contain only numbers.')
    elif not isinstance(value, (int, float)):
        raise validators.ValidationError('Invalid input. Value must contain only numbers.')

class DebtDataForm(FlaskForm):
        #,validators.NumberRange(min=1)
    #apr = IntegerField(label=('Interest Rate:'), validators =[InputRequired(message="input required"), NumberRange(min=1,max=None,message="Number  cannot be 0")])
    apr = FloatField(label=('Interest Rate:'), validators =[InputRequired(message="input required"),validate_only_numbers])
    min_pay = IntegerField(label=('Montly Payment:'), validators =[InputRequired(message="input required"),validators.NumberRange(min=1),validate_only_numbers])
    debt_balance = IntegerField(label=('Debt Balance:'), validators =[InputRequired(message="input required"),validators.NumberRange(min=1),validate_only_numbers])
    currency = SelectField(label='Currency:', choices=[
        ('USD', '$ USD'),
        ('EUR', '€ EUR'),
        ('GBP', '£ GBP'),
        ('CNY', '¥ CNY'),
        ('JPY', '¥ JPY'),
        ('INR', '₹ INR'),
        ('BRL', 'R$ BRL')
    ], validators=[InputRequired()])
    submit = SubmitField(label=('Calculate'))

#def validate_decimal_input(form, field):
    #if '.' in str(field.data):
        #raise ValidationError('Decimal numbers are not allowed.')

    def validate_min_pay(form, field): # validate_ must be the start of a custom form validator name
        if form.debt_balance.data == None:
            raise validators.ValidationError('Data_must_fully be filled')
        if field.data == form.debt_balance.data or field.data > form.debt_balance.data:
            raise validators.ValidationError('cannot_be greater that debt balance')
        

    def validate_apr(form, field):
        if field.data <= 0:
            raise validators.ValidationError('Cannot be 0, or less than 0')
        elif field.data > 80:
            raise validators.ValidationError('Cannot be more than 80%')
        
    def validate_all(form, field):
        if field.data == None:
            raise validators.ValidationError('must have a value')

        
#if any(char in field.data for char in ['*'])

        

#        if field.data % 1 != 0 :
 #           raise validators.ValidationError('integer input is required')


#        new_val = str(field.data)
      #  if new_val  == '*':
       #     raise validators.ValidationError('cannot have that symbol')

##############################
######## FLASK VIEWS #########
##############################


app = Flask(__name__) #creat app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

########################################
############ AI debt predictor ##########
########################################

_DEBT_PREDICTOR_ROOT = Path(__file__).resolve().parent.parent / "ai_debt_predictor"
if str(_DEBT_PREDICTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEBT_PREDICTOR_ROOT))

try:
    from utils.finance import calculate_debt_schedule as _dp_calculate_schedule
    from utils.ml_model import predict_debt_with_ml as _dp_predict_ml
    from utils.view_helpers import build_debt_predictor_view_context as _dp_view_context
    _DEBT_PREDICTOR_LIBS = True
except ImportError:
    _DEBT_PREDICTOR_LIBS = False


@app.route('/debt-predictor', methods=['GET'])
def debt_predictor():
    if not _DEBT_PREDICTOR_LIBS:
        return render_template('debt_predictor_missing.html'), 503
    return render_template(
        'debt_predictor_index.html',
        dp_last=session.get('dp_last_form'),
    )


@app.route('/debt-predictor/predict', methods=['POST'])
def debt_predictor_predict():
    if not _DEBT_PREDICTOR_LIBS:
        return render_template('debt_predictor_missing.html'), 503
    try:
        starting_debt = float(request.form.get('starting_debt', 0))
        annual_interest_rate = float(request.form.get('annual_interest_rate', 0))
        monthly_payment = float(request.form.get('monthly_payment', 0))
        forecast_months = int(request.form.get('forecast_months', 24))
    except (TypeError, ValueError):
        return render_template(
            'debt_predictor_index.html',
            error='Please enter valid numbers for all fields.',
            dp_last=session.get('dp_last_form'),
        ), 400

    if starting_debt <= 0:
        return render_template(
            'debt_predictor_index.html',
            error='Starting debt must be greater than zero.',
            dp_last=session.get('dp_last_form'),
        ), 400
    if annual_interest_rate < 0:
        return render_template(
            'debt_predictor_index.html',
            error='Interest rate cannot be negative.',
            dp_last=session.get('dp_last_form'),
        ), 400
    if monthly_payment <= 0:
        return render_template(
            'debt_predictor_index.html',
            error='Monthly repayment must be greater than zero.',
            dp_last=session.get('dp_last_form'),
        ), 400
    if forecast_months < 1 or forecast_months > 120:
        return render_template(
            'debt_predictor_index.html',
            error='Forecast months must be between 1 and 120.',
            dp_last=session.get('dp_last_form'),
        ), 400

    schedule = _dp_calculate_schedule(
        starting_debt,
        annual_interest_rate,
        monthly_payment,
        forecast_months,
    )
    ml_balances = _dp_predict_ml(
        starting_debt,
        schedule['month_numbers'],
        schedule['formula_balances'],
        forecast_months,
    )

    ctx = _dp_view_context(schedule, ml_balances)

    session['dp_last_form'] = {
        'starting_debt': str(starting_debt),
        'annual_interest_rate': str(annual_interest_rate),
        'monthly_payment': str(monthly_payment),
        'forecast_months': str(forecast_months),
    }

    return render_template(
        'debt_predictor_results.html',
        starting_debt=starting_debt,
        annual_interest_rate=annual_interest_rate,
        monthly_payment=monthly_payment,
        forecast_months=forecast_months,
        total_interest=schedule['total_interest'],
        payoff_month=schedule['payoff_month'],
        never_decreasing=schedule['never_decreasing'],
        table_rows=ctx['table_rows'],
        table_tail_note=ctx['table_tail_note'],
        mean_abs_difference=ctx['mean_abs_difference'],
        ai_payoff_month=ctx['ai_payoff_month'],
        chart_data=ctx['chart_data'],
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    form = DebtDataForm(request.form)

    if form.validate_on_submit():

        principal = form.debt_balance.data
        apr = conv_apr_to_dec(form.apr.data)
        min_payment = form.min_pay.data 
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'AUD': '$',
            'CAD': '$',
            'CNY': '¥',
            'JPY': '¥',
            'INR': '₹',
            'BRL': 'R$'
        }
        currency = request.form['currency']
        currency_symbol = currency_symbols.get(currency, '')  # Convert code to symbol

        #if apr == 0:
        #   raise ValidationError("CANOTTTTTTTTTTT")

        #print(error_check_apr)


        #Perform checks
        check_debt_valid = debt_validate(principal,apr,min_payment)

        if check_debt_valid == True:
            
            ######## manual insert start of list ########
            si_principal_list.insert(0, principal)
            si_total_interest_list.insert(0, 0)
            si_total_months_list.insert(0, 1)
            #############################################

            
            print(si_principal_list)

            debt_calculate_monthly(principal,apr,min_payment)
            debt_accrued_int()

            print(f"Month List len: {len(month_list)}"".\n")
            print(f"Principal List len: {len(principal_list)}"".\n")
            print(f"Interest list len: {len(interest_list)}"".\n") 
            print(f"Accrued list: {len(accrued_interest_list)}"".\n")
            print(f"Principal Payment List: {principle_payment_list}"".\n")

            calc_simple_interest(principal,0.10,min_payment)
            si_pri_interest = si_sum_pri_int(principal,sum(si_interest_list))
            print(f"the toal {si_pri_interest}")
            si_years_no = si_calc_years(si_month_list[-1]) # calls function that calculates number of years
            si_month_no = si_calc_months(si_month_list[-1]) # calls another function that calculates number of months
            si_accrued_int = round(sum(si_interest_list),2)
            si_percent_paid = si_calc_percentage(sum(si_interest_list),principal)

            years_to_pay = get_years() #Number years to pay
            months_to_pay = get_months() #Remainder months to pay
            accrued_total = "{:,}".format(accrued_interest_list[-2])
            total_payback = "{:,}".format(round(accrued_interest_list[-2] + principal, 2))
            total_payback_int = total_payback
            total_payback_int = round(accrued_interest_list[-2] + principal, 2)
            accrued_percentage = get_percentage(principal,total_payback_int) #Accrued percentage
            
            
            print(f" Time to pay is {years_to_pay} Years and {months_to_pay} months")
            
            #dog_poo = accrued_int_perc_diff(int(accrued_interest_list[-1]), int(si_accrued_int[-1]))
            accrued_percent_comparison = round(percentage_diff(int(accrued_interest_list[-1]), si_accrued_int),2)
            comp_simp_display = round(comp_simp_total_comparison(accrued_interest_list[-2] + principal,si_pri_interest),2)

            
            comp_month = len(month_list)-1 # var that has length of compound month list
            comp_month2 = len(si_month_list) # var that has length of simple interest list
            comparison_months = month_comp(comp_month,comp_month2) #calling that function month_comp to calculate month comparison
            comp_years = round(comp_calc_years(comparison_months)) # calling function to calculate years
            print(f" amound of years {comp_years}") 
            final_month = comp_calc_months(comparison_months) # calculate months left over
            print(f"left over months {final_month}")

            accrued_comparison = accrued_comp_perc(accrued_interest_list[-2],si_accrued_int) # var that tells us the percentage diff between acrrued interest
            final_accrued_comparison = round(accrued_comparison,2)
            principal_perc_comp = princ_comp_perc(round(accrued_interest_list[-2] + principal, 2),si_pri_interest)
            final_princ_perc_comp = round(principal_perc_comp,2)

            validate_greater_int = compare_values(total_payback,si_pri_interest)
            pdf_apr = form.apr.data



        #if len(month_list) != 0:
            return render_template("index2.html", month_list = month_list, \
                                                currency = currency_symbol, \
                                                principle_payment_list = principle_payment_list, \
                                                principal_list =principal_list, \
                                                interest_list = interest_list, \
                                                accrued_interest_list = accrued_interest_list, \
                                                check_debt_valid = check_debt_valid, \
                                                form = form, \
                                                years_to_pay = years_to_pay, \
                                                months_to_pay = months_to_pay, \
                                                accrued_total = accrued_total, \
                                                total_payback = total_payback,\
                                                principal = principal, \
                                                accrued_percentage = round(accrued_percentage), \
                                                min_payment = min_payment, \
                                                p_payment = get_principal_payment, \
                                                si_pri_interest = si_pri_interest, \
                                                si_years_no = si_years_no, \
                                                si_month_no = si_month_no, \
                                                si_accrued_int = si_accrued_int, \
                                                si_percent_paid = si_percent_paid, \
                                                accrued_percent_comparison = accrued_percent_comparison, \
                                                comp_simp_display = comp_simp_display, \
                                                comp_years = comp_years, \
                                                final_month = final_month, \
                                                final_accrued_comparison = final_accrued_comparison, \
                                                final_princ_perc_comp = final_princ_perc_comp, \
                                                #var_sesh_apr = var_sesh_apr, \
                                                total_payback_int = total_payback_int, \
                                                validate_greater_int = validate_greater_int, \
                                                pdf_apr = pdf_apr, \
                                                )

        elif check_debt_valid == False:
            #print("This debt would take more than 20 years to pay. It is not valid")

            return render_template("index2.html", form = form, \
                                                check_debt_valid = check_debt_valid
                                                )

    else:
        #    # tomorrow, make a second html page, this will be the results page. the first html page needs to be a form and then once submitted it takes you to the 
                #second html page with the results as well as the form
        return render_template("C_results.html", form = form)


# Define a route in the Flask app. Variables in the URL are passed to the pdf function.
if __name__ == '__main__':
    app.run(debug = True)
    #app.run(debug=True)
