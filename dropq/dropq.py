from __future__ import print_function
from taxcalc import (Calculator, Records, Policy, Behavior,
                     TABLE_LABELS, TABLE_COLUMNS, STATS_COLUMNS,
                     DIFF_TABLE_LABELS)
import taxcalc
import numpy as np
from pandas import DataFrame
import pandas as pd
import hashlib
import time
from .utils import *

planY_column_types = [float] * len(TABLE_LABELS)

diff_column_names = DIFF_TABLE_LABELS

diff_column_types = [int, int, int, float, float, str, str, str]

decile_row_names = ["perc0-10", "perc10-20", "perc20-30", "perc30-40",
                    "perc40-50", "perc50-60", "perc60-70", "perc70-80",
                    "perc80-90", "perc90-100", "all"]

bin_row_names = ["less_than_10", "ten_twenty", "twenty_thirty", "thirty_forty",
                 "forty_fifty", "fifty_seventyfive", "seventyfive_hundred",
                 "hundred_twohundred", "twohundred_fivehundred",
                 "fivehundred_thousand", "thousand_up", "all"]

total_row_names = ["ind_tax", "payroll_tax", "combined_tax"]

GDP_elasticity_row_names = ["gdp_elasticity"]

ogusa_row_names = ["GDP", "Consumption", "Investment", "Hours Worked", "Wages", "Interest Rates",
                   "Total Taxes"]
NUM_YEARS_DEFAULT = 1


def only_growth_assumptions(user_mods, start_year):
    """
    Extract any reform parameters that are pertinent to growth
    assumptions
    """
    growth_dd = taxcalc.growth.Growth.default_data(start_year=start_year)
    ga = {}
    for year, reforms in user_mods.items():
        overlap = set(growth_dd.keys()) & set(reforms.keys())
        if overlap:
            ga[year] = {param:reforms[param] for param in overlap}
    return ga


def only_behavior_assumptions(user_mods, start_year):
    """
    Extract any reform parameters that are pertinent to behavior
    assumptions
    """
    beh_dd = Behavior.default_data(start_year=start_year)
    ba = {}
    for year, reforms in user_mods.items():
        overlap = set(beh_dd.keys()) & set(reforms.keys())
        if overlap:
            ba[year] = {param:reforms[param] for param in overlap}
    return ba


def only_reform_mods(user_mods, start_year):
    """
    Extract parameters that are just for policy reforms
    """
    pol_refs = {}
    beh_dd = Behavior.default_data(start_year=start_year)
    growth_dd = taxcalc.growth.Growth.default_data(start_year=start_year)
    policy_dd = taxcalc.policy.Policy.default_data(start_year=start_year)
    for year, reforms in user_mods.items():
        all_cpis = {p for p in reforms.keys() if p.endswith("_cpi") and
                    p[:-4] in policy_dd.keys()}
        pols = set(reforms.keys()) - set(beh_dd.keys()) - set(growth_dd.keys())
        pols &= set(policy_dd.keys())
        pols ^= all_cpis
        if pols:
            pol_refs[year] = {param:reforms[param] for param in pols}
    return pol_refs

def elasticity_of_gdp_year_n(user_mods, year_n):
    """
    Extract elasticity of GDP parameter for the proper year
    """
    allkeys = sorted(user_mods.keys())
    reforms = user_mods[allkeys[0]]
    ELASTICITY_LIST = reforms.get("elastic_gdp", None)
    if not ELASTICITY_LIST:
        raise ValueError("user_mods should specify elastic_gdp")
    if year_n >= len(ELASTICITY_LIST):
        return ELASTICITY_LIST[-1]
    else:
        return ELASTICITY_LIST[year_n]


def random_seed_from_plan(calc):
    all_vals = []
    all_params = sorted([str(k) for k in taxcalc.policy.Policy.default_data()])
    for param in all_params:
        if hasattr(calc, param):
            print("calc has ", param)
            all_vals.append(str((param, tuple(getattr(calc, param)))))

    txt = u"".join(all_vals).encode("utf-8")
    hsh = hashlib.sha512(txt)
    seed = int(hsh.hexdigest(), 16)
    return seed % np.iinfo(np.uint32).max


def chooser(agg):
    """
    This is a transformation function that should be called on each group.
    It is assumed that the chunk 'agg' is a chunk of the 'mask' column.
    This chooser selects three of those mask indices. the output at that
    index is zero. all other outputs for each index is 1.
    """
    indices = np.where(agg)

    if len(indices[0]) > 2:
        choices = np.random.choice(indices[0], size=3, replace=False)
    else:
        choices = []
        print("Not enough difference in taxable income when adding 1 dollar"
              "for chunk with name: " + agg.name)

    ans = [1] * len(agg)
    for ix in choices:
        ans[ix] = 0
    return ans


def label_and_group_size(grp, msg):
    print(msg)
    for k, v in grp.groups.items():
        print(str(k), ": ", str(len(v)))


def groupby_means_and_comparisons(df1, df2, mask, debug=False):
    """
    df1 is the standard plan X and X'
    df2 is the user-specified plan (Plan Y)
    mask is the boolean mask where X and X' match
    """

    # perform all statistics on (Y + X') - X
    # so df2['c05200'] should be replaced with df2['c05200_noise']

    # Group first
    df2['mask'] = mask
    df1['mask'] = mask

    df2 = taxcalc.add_weighted_decile_bins(df2)
    df1 = taxcalc.add_weighted_decile_bins(df1)
    gp2_dec = df2.groupby('bins')
    gp1_dec = df1.groupby('bins')

    income_bins = taxcalc.WEBAPP_INCOME_BINS

    df2 = taxcalc.add_income_bins(df2, bins=income_bins)
    df1 = taxcalc.add_income_bins(df1, bins=income_bins)
    gp2_bin = df2.groupby('bins')
    gp1_bin = df1.groupby('bins')

    if debug:
        label_and_group_size(gp2_dec, "decile groups:")
        label_and_group_size(gp2_bin, "income binned groups:")

    # Transform to get the 'flag' column (3 choices to drop in each bin)
    df2['flag_dec'] = gp2_dec['mask'].transform(chooser)
    df2['flag_bin'] = gp2_bin['mask'].transform(chooser)

    # first calculate all of X'
    COLUMNS_TO_MAKE_NOISY = set(TABLE_COLUMNS) | set(STATS_COLUMNS)
    # these don't exist yet
    COLUMNS_TO_MAKE_NOISY.remove('num_returns_ItemDed')
    COLUMNS_TO_MAKE_NOISY.remove('num_returns_StandardDed')
    COLUMNS_TO_MAKE_NOISY.remove('num_returns_AMT')
    for col in COLUMNS_TO_MAKE_NOISY:
        df2[col + '_dec'] = df2[col]*df2['flag_dec'] - df1[col]*df2['flag_dec'] + df1[col]
        df2[col + '_bin'] = df2[col]*df2['flag_bin'] - df1[col]*df2['flag_bin'] + df1[col]

    # Difference in plans
    # Positive values are the magnitude of the tax increase
    # Negative values are the magnitude of the tax decrease
    df2['tax_diff_dec'] = df2['_iitax_dec'] - df1['_iitax']
    df2['tax_diff_bin'] = df2['_iitax_bin'] - df1['_iitax']
    df2['fica_diff_dec'] = df2['_fica_dec'] - df1['_fica']
    df2['fica_diff_bin'] = df2['_fica_bin'] - df1['_fica']
    df2['combined_diff_dec'] = df2['_combined_dec'] - df1['_combined']
    df2['combined_diff_bin'] = df2['_combined_bin'] - df1['_combined']

    dec_sum = (df2['tax_diff_dec']*df2['s006']).sum()
    bin_sum = (df2['tax_diff_bin']*df2['s006']).sum()
    fica_dec_sum = (df2['fica_diff_dec']*df2['s006']).sum()
    fica_bin_sum = (df2['fica_diff_bin']*df2['s006']).sum()
    combined_dec_sum = (df2['combined_diff_dec']*df2['s006']).sum()
    combined_bin_sum = (df2['combined_diff_bin']*df2['s006']).sum()


    # Create Difference tables, grouped by deciles and bins

    diffs_dec = create_dropq_difference_table(df1, df2,
                                              groupby="weighted_deciles",
                                              res_col='tax_diff',
                                              diff_col='_iitax',
                                              suffix="_dec", wsum=dec_sum)

    diffs_bin = create_dropq_difference_table(df1, df2,
                                              groupby="webapp_income_bins",
                                              res_col='tax_diff',
                                              diff_col='_iitax',
                                              suffix="_bin", wsum=bin_sum)

    payroll_diffs_dec = create_dropq_difference_table(df1, df2,
                                              groupby="weighted_deciles",
                                              res_col='fica_diff',
                                              diff_col='_fica',
                                              suffix="_dec", wsum=fica_dec_sum)

    payroll_diffs_bin = create_dropq_difference_table(df1, df2,
                                              groupby="webapp_income_bins",
                                              res_col='fica_diff',
                                              diff_col='_fica',
                                              suffix="_bin", wsum=fica_bin_sum)

    comb_diffs_dec = create_dropq_difference_table(df1, df2,
                                              groupby="weighted_deciles",
                                              res_col='combined_diff',
                                              diff_col='_combined',
                                              suffix="_dec", wsum=combined_dec_sum)

    comb_diffs_bin = create_dropq_difference_table(df1, df2,
                                              groupby="webapp_income_bins",
                                              res_col='combined_diff',
                                              diff_col='_combined',
                                              suffix="_bin", wsum=combined_bin_sum)

    mX_dec = taxcalc.create_distribution_table(df1, groupby='weighted_deciles',
                                       result_type='weighted_sum')

    mY_dec = create_dropq_distribution_table(df2, groupby='weighted_deciles',
                                       result_type='weighted_sum', suffix='_dec')

    mX_bin = taxcalc.create_distribution_table(df1, groupby='webapp_income_bins',
                                       result_type='weighted_sum')

    mY_bin = create_dropq_distribution_table(df2, groupby='webapp_income_bins',
                                       result_type='weighted_sum', suffix='_bin')


    return (mY_dec, mX_dec, diffs_dec, payroll_diffs_dec, comb_diffs_dec,
            mY_bin, mX_bin, diffs_bin, payroll_diffs_bin, comb_diffs_bin,
            dec_sum, fica_dec_sum, combined_dec_sum)



def results(c):
    outputs = []
    for col in STATS_COLUMNS:
        if hasattr(c.policy, col):
            outputs.append(getattr(c.policy, col))
        else:
            outputs.append(getattr(c.records, col))

    return DataFrame(data=np.column_stack(outputs), columns=STATS_COLUMNS)


def run_nth_year_mtr_calc(year_n, start_year, tax_dta, user_mods="", return_json=True):

    #Only makes sense to run for budget years 1 through n-1 (not for year 0)
    assert year_n > 0

    elasticity_gdp = elasticity_of_gdp_year_n(user_mods, year_n)


    #########################################################################
    #   Create Calculators and Masks
    #########################################################################
    records = Records(tax_dta.copy(deep=True))
    records3 = Records(tax_dta.copy(deep=True))

    # Default Plans
    # Create a default Policy object
    params = Policy(start_year=2013)
    # Create a Calculator
    calc1 = Calculator(policy=params, records=records)

    growth_assumptions = only_growth_assumptions(user_mods, start_year)
    if growth_assumptions:
        calc1.growth.update_economic_growth(growth_assumptions)

    while calc1.current_year < start_year:
        calc1.increment_year()
    assert calc1.current_year == start_year


    # User specified Plans
    reform_mods = only_reform_mods(user_mods, start_year)
    params3 = Policy(start_year=2013)
    params3.implement_reform(reform_mods)

    behavior3 = Behavior(start_year=2013)
    # Create a Calculator for the user specified plan
    calc3 = Calculator(policy=params3, records=records3, behavior=behavior3)
    if growth_assumptions:
        calc3.growth.update_economic_growth(growth_assumptions)

    while calc3.current_year < start_year:
        calc3.increment_year()
    assert calc3.current_year == start_year
    # Get a random seed based on user specified plan
    seed = random_seed_from_plan(calc3)
    np.random.seed(seed)

    for i in range(0, year_n-1):
        calc1.increment_year()
        calc3.increment_year()

    calc1.calc_all()
    calc3.calc_all()

    mtr_fica_x, mtr_iit_x, mtr_combined_x = calc1.mtr()
    mtr_fica_y, mtr_iit_y, mtr_combined_y = calc3.mtr()

    #Assert that the current year is one behind the year we are calculating
    assert (calc1.current_year + 1) == (start_year + year_n)
    assert (calc3.current_year + 1) == (start_year + year_n)

    after_tax_mtr_x = 1 - ((mtr_combined_x * calc1.records.c00100 *
                        calc1.records.s006).sum()/
                        (calc1.records.c00100 * calc1.records.s006).sum())

    after_tax_mtr_y = 1 - ((mtr_combined_y * calc3.records.c00100 *
                        calc3.records.s006).sum()/
                        (calc3.records.c00100 * calc3.records.s006).sum())

    diff_avg_mtr_combined_y = after_tax_mtr_y - after_tax_mtr_x
    percent_diff_mtr = diff_avg_mtr_combined_y / after_tax_mtr_x

    gdp_effect_y = percent_diff_mtr * elasticity_gdp

    gdp_df = pd.DataFrame(data=[gdp_effect_y], columns=["col0"])

    if not return_json:
        return gdp_effect_y

    gdp_elast_names_i = [x+'_'+str(year_n) for x in GDP_elasticity_row_names]

    gdp_elast_total = create_json_table(gdp_df, row_names=gdp_elast_names_i, num_decimals=5)

    # Make the one-item lists of strings just strings
    gdp_elast_total = dict((k, v[0]) for k,v in gdp_elast_total.items())

    return gdp_elast_total


def run_nth_year(year_n, start_year, tax_dta="", user_mods="", return_json=True):


    #########################################################################
    #   Create Calculators and Masks
    #########################################################################
    records = Records(tax_dta.copy(deep=True))
    records2 = Records(tax_dta.copy(deep=True))
    records3 = Records(tax_dta.copy(deep=True))
    # add 1 dollar to gross income
    records2.e00200 += 1
    records2.e02000 += 1
    records2.e02615 += 1
    # Default Plans
    # Create a default Policy object
    params = Policy(start_year=2013)
    # Create a Calculator
    calc1 = Calculator(policy=params, records=records)

    growth_assumptions = only_growth_assumptions(user_mods, start_year)
    if growth_assumptions:
        calc1.growth.update_economic_growth(growth_assumptions)

    while calc1.current_year < start_year:
        calc1.increment_year()
    calc1.calc_all()
    assert calc1.current_year == start_year

    params2 = Policy(start_year=2013)
    # Create a Calculator with one extra dollar of income
    calc2 = Calculator(policy=params2, records=records2)
    if growth_assumptions:
        calc2.growth.update_economic_growth(growth_assumptions)

    while calc2.current_year < start_year:
        calc2.increment_year()
    calc2.calc_all()
    assert calc2.current_year == start_year

    # where do the results differ..
    soit1 = results(calc1)
    soit2 = results(calc2)
    mask = (soit1._iitax != soit2._iitax)

    # User specified Plans
    behavior_assumptions = only_behavior_assumptions(user_mods, start_year)

    reform_mods = only_reform_mods(user_mods, start_year)

    params3 = Policy(start_year=2013)
    params3.implement_reform(reform_mods)

    behavior3 = Behavior(start_year=2013)
    # Create a Calculator for the user specified plan
    calc3 = Calculator(policy=params3, records=records3, behavior=behavior3)
    if growth_assumptions:
        calc3.growth.update_economic_growth(growth_assumptions)

    if behavior_assumptions:
        calc3.behavior.update_behavior(behavior_assumptions)

    while calc3.current_year < start_year:
        calc3.increment_year()
    assert calc3.current_year == start_year
    calc3.calc_all()
    # Get a random seed based on user specified plan
    seed = random_seed_from_plan(calc3)
    np.random.seed(seed)

    start_time = time.time()
    for i in range(0, year_n):
        calc1.increment_year()
        calc3.increment_year()

    calc1.calc_all()
    has_behavior = (calc3.behavior.BE_sub or calc3.behavior.BE_inc or
                    calc3.behavior.BE_cg)
    if has_behavior:
        calc3 = calc3.behavior.response(calc1, calc3)
    else:
        calc3.calc_all()
    soit1 = results(calc1)
    soit3 = results(calc3)
    # Means of plan Y by decile
    # diffs of plan Y by decile
    # Means of plan Y by income bin
    # diffs of plan Y by income bin
    mY_dec, mX_dec, df_dec, pdf_dec, cdf_dec, mY_bin, mX_bin, df_bin, \
        pdf_bin, cdf_bin, diff_sum, payroll_diff_sum, combined_diff_sum = \
        groupby_means_and_comparisons(soit1, soit3, mask)

    elapsed_time = time.time() - start_time
    print("elapsed time for this run: ", elapsed_time)
    start_year += 1

    #num_fiscal_year_total = format_print(diff_sum)
    #fica_fiscal_year_total = format_print(payroll_diff_sum)
    #combined_fiscal_year_total = format_print(combined_diff_sum)
    tots = [diff_sum, payroll_diff_sum, combined_diff_sum]
    fiscal_tots= pd.DataFrame(data=tots, index=total_row_names)

    # Get rid of negative incomes
    df_bin.drop(df_bin.index[0], inplace=True)
    pdf_bin.drop(pdf_bin.index[0], inplace=True)
    cdf_bin.drop(cdf_bin.index[0], inplace=True)
    mY_bin.drop(mY_bin.index[0], inplace=True)
    mX_bin.drop(mX_bin.index[0], inplace=True)

    if not return_json:
        return (mY_dec, mX_dec, df_dec, pdf_dec, cdf_dec, mY_bin, mX_bin,
                df_bin, pdf_bin, cdf_bin, fiscal_tots)


    decile_row_names_i = [x+'_'+str(year_n) for x in decile_row_names]

    bin_row_names_i = [x+'_'+str(year_n) for x in bin_row_names]

    total_row_names_i = [x+'_'+str(year_n) for x in total_row_names]

    mY_dec_table_i = create_json_table(mY_dec,
                                        row_names=decile_row_names_i,
                                        column_types=planY_column_types)
    mX_dec_table_i = create_json_table(mX_dec,
                                        row_names=decile_row_names_i,
                                        column_types=planY_column_types)
    df_dec_table_i = create_json_table(df_dec,
                                        row_names=decile_row_names_i,
                                        column_types=diff_column_types)

    pdf_dec_table_i = create_json_table(pdf_dec,
                                        row_names=decile_row_names_i,
                                        column_types=diff_column_types)

    cdf_dec_table_i = create_json_table(cdf_dec,
                                        row_names=decile_row_names_i,
                                        column_types=diff_column_types)

    mY_bin_table_i = create_json_table(mY_bin,
                                        row_names=bin_row_names_i,
                                        column_types=planY_column_types)
    mX_bin_table_i = create_json_table(mX_bin,
                                        row_names=bin_row_names_i,
                                        column_types=planY_column_types)

    df_bin_table_i = create_json_table(df_bin,
                                        row_names=bin_row_names_i,
                                        column_types=diff_column_types)

    pdf_bin_table_i = create_json_table(pdf_bin,
                                        row_names=bin_row_names_i,
                                        column_types=diff_column_types)

    cdf_bin_table_i = create_json_table(cdf_bin,
                                        row_names=bin_row_names_i,
                                        column_types=diff_column_types)

    fiscal_yr_total = create_json_table(fiscal_tots, row_names=total_row_names_i)
    # Make the one-item lists of strings just strings
    fiscal_yr_total = dict((k, v[0]) for k,v in fiscal_yr_total.items())

    return (mY_dec_table_i, mX_dec_table_i, df_dec_table_i, pdf_dec_table_i,
            cdf_dec_table_i, mY_bin_table_i, mX_bin_table_i, df_bin_table_i,
            pdf_bin_table_i, cdf_bin_table_i, fiscal_yr_total)


def run_models(tax_dta, start_year, user_mods="", num_years=NUM_YEARS_DEFAULT):

    mY_dec_table = {}
    mX_dec_table = {}
    df_dec_table = {}
    pdf_dec_table = {}
    cdf_dec_table = {}
    mY_bin_table = {}
    mX_bin_table = {}
    df_bin_table = {}
    pdf_bin_table = {}
    cdf_bin_table = {}
    num_fiscal_year_totals = []

    #########################################################################
    #   Create Calculators and Masks
    #########################################################################
    for year_n in range(0, num_years):
        json_tables = run_nth_year(year_n, tax_dta=tax_dta,
                                   user_mods=user_mods, start_year=start_year)
        (mY_dec_table_i, mX_dec_table_i, df_dec_table_i, pdf_dec_table_i, 
         cdf_dec_table_i, mY_bin_table_i, mX_bin_table_i, df_bin_table_i,
         pdf_bin_table_i, cdf_bin_table_i, num_fiscal_year_total) = json_tables

        num_fiscal_year_totals.append(num_fiscal_year_total)
        mY_dec_table.update(mY_dec_table_i)
        mX_dec_table.update(mX_dec_table_i)
        df_dec_table.update(df_dec_table_i)
        pdf_dec_table.update(pdf_dec_table_i)
        cdf_dec_table.update(cdf_dec_table_i)
        mY_bin_table.update(mY_bin_table_i)
        mX_bin_table.update(mX_bin_table_i)
        df_bin_table.update(df_bin_table_i)

    return (mY_dec_table, mX_dec_table, df_dec_table, pdf_dec_table,
            cdf_dec_table, mY_bin_table, mX_bin_table, df_bin_table,
            pdf_bin_table, cdf_bin_table, num_fiscal_year_totals)


def run_gdp_elast_models(tax_dta, start_year, user_mods="", num_years=NUM_YEARS_DEFAULT):

    gdp_elasticity_totals = []

    #########################################################################
    #   Create Calculators and Masks
    #########################################################################
    for year_n in range(0, num_years):
        gdp_elast_i = run_nth_year_mtr_calc(year_n, tax_dta=tax_dta,
                                   user_mods=user_mods, start_year=start_year)

        gdp_elasticity_totals.append(gdp_elast_i)

    return gdp_elasticity_totals


def example_data(start_year, tax_dta="", user_mods="", return_json=True):

    data = [0.0164] * 12
    dfdata = [data] * 7
    cols = list(map(str, range(2015, 2025))) + ["2015-2024"] + ["Steady State"]
    ogusadf = pd.DataFrame(dfdata, columns=cols)

    if not return_json:
        return df

    column_types = [float] * len(cols)

    df_ogusa_table = create_json_table(ogusadf,
                                 row_names=ogusa_row_names,
                                 column_types=column_types,
                                 num_decimals=3)

    return df_ogusa_table


def format_macro_results(diff_data, return_json=True):

    ogusadf = pd.DataFrame(diff_data)

    if not return_json:
        return df

    column_types = [float] * diff_data.shape[1]

    df_ogusa_table = create_json_table(ogusadf,
                                 row_names=ogusa_row_names,
                                 column_types=column_types,
                                 num_decimals=3)

    return df_ogusa_table
