#################################################
###### SI and COMPARISON FUNCTIONS ##############
#################################################

def princ_comp_perc(compound_accrued,si_accrued): # function that calculates the difference in simple interest and compound percentage
    interest_comp = si_accrued/compound_accrued*100
    final = 100-interest_comp
    return final

def accrued_comp_perc(compound_accrued,si_accrued): # percentage difference for accrued interests
    interest_comp = si_accrued/compound_accrued*100
    final = 100-interest_comp
    return final

def si_sum_pri_int(si_principal, si_interest): # function that shows the total simple interest amount with principal and interest added 
    total = si_principal+si_interest
    return round(total,2) # displays the principal plus interest to give the total

def comp_calc_years(months): # function to calculate number of years difference
    years = months/12
    return years

def month_comp(compound_list,si_list): # function that calculates month comparison between compound and si
    comp_month = compound_list-si_list
    return comp_month

 # function that calculates difference in payback between compound and simple
def comp_simp_total_comparison(compound_total,simple_total):
    difference_total = compound_total-simple_total
    #years = difference_total/12
    return difference_total

def percentage_diff(compound_accrued, simple_accrued): # function that calculates the difference between si and comp accrued interest as a percentage
    accrued_difference = simple_accrued/compound_accrued*100
    #final_diff = 100-accrued_difference
    return accrued_difference

def comp_calc_months(months): # function that calculates months left over
    months_left = months % 12
    return months_left

def total_comparison(total,si_total): # functiin that calculates difference between total compound and si balances
    comp_total = total-si_total
    return comp_total

###########################################
###########################################
############### end #######################
###########################################
###########################################