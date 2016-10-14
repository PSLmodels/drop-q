import os
import sys
cur_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(cur_path, "../../"))
sys.path.append(os.path.join(cur_path, "../"))
import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas.util.testing import assert_frame_equal

from dropq.utils import *
from dropq import *
import json


def test_only_growth_assumptions():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    myvars['_BE_inc'] = [0.8]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = only_growth_assumptions(user_mods, 2015)
    exp = {first_year: {'_factor_target': [0.02]} }
    assert ans == exp


def test_only_behavior_assumptions():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    myvars['_BE_inc'] = [0.8]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = only_behavior_assumptions(user_mods, 2015)
    exp = {first_year: {'_BE_inc': [0.8]} }
    assert ans == exp


def test_only_reform_mods():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    myvars['_BE_inc'] = [0.8]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = only_reform_mods(user_mods, 2015)
    exp = {first_year: {'_FICA_ss_trt': [0.15], '_II_em': [4700.0]}}
    assert ans == exp


def test_only_reform_mods():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    myvars['_BE_inc'] = [0.8]
    myvars['ELASTICITY_GDP_WRT_AMTR'] = [.54]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = only_reform_mods(user_mods, 2015)
    exp = {first_year: {'_FICA_ss_trt': [0.15], '_II_em': [4700.0]}}
    assert ans == exp

def test_only_reform_mods_with_cpi():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    # A known CPI flag
    myvars['_II_em_cpi'] = False
    # A unknown CPI flag
    myvars['NOGOOD_cpi'] = False
    # A small parameter name
    myvars['NO'] = [0.42]
    myvars['_BE_inc'] = [0.8]
    myvars['ELASTICITY_GDP_WRT_AMTR'] = [.54]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = only_reform_mods(user_mods, 2015)
    exp = {first_year: {'_FICA_ss_trt': [0.15], '_II_em': [4700.0], '_II_em_cpi': False}}
    assert ans == exp

def test_unknown_parameters_with_cpi():
    myvars = {}
    myvars['_FICA_ss_trt'] = [0.15]
    myvars['_factor_target'] = [0.02]
    myvars['_II_em'] = [4700.0]
    # A known CPI flag
    myvars['_II_em_cpi'] = False
    # A unknown CPI flag
    myvars['NOGOOD_cpi'] = False
    # A small parameter name
    myvars['NO'] = [0.42]
    myvars['_BE_inc'] = [0.8]
    myvars['ELASTICITY_GDP_WRT_AMTR'] = [.54]
    first_year = 2013
    user_mods = {first_year: myvars}
    ans = get_unknown_parameters(user_mods, 2015)
    exp = set(["NOGOOD_cpi", "NO", "ELASTICITY_GDP_WRT_AMTR"])
    assert set(ans) == exp



def test_format_macro_results():

    data = [[  1.875e-03,  1.960e-03,  2.069e-03,  2.131e-03,  2.179e-03,  2.226e-03,
                2.277e-03,  2.324e-03,  2.375e-03,  2.426e-03,  2.184e-03,  2.806e-03],
            [  2.538e-04,  4.452e-04,  6.253e-04,  7.886e-04,  9.343e-04,  1.064e-03,
                1.180e-03,  1.284e-03,  1.378e-03,  1.463e-03,  9.419e-04,  2.224e-03],
            [  5.740e-03,  5.580e-03,  5.524e-03,  5.347e-03,  5.161e-03,  5.011e-03,
                4.907e-03,  4.818e-03,  4.768e-03,  4.739e-03,  5.160e-03,  4.211e-03],
            [  2.883e-03,  2.771e-03,  2.721e-03,  2.620e-03,  2.520e-03,  2.440e-03,
                2.384e-03,  2.337e-03,  2.309e-03,  2.292e-03,  2.528e-03,  2.051e-03],
            [ -1.012e-03, -8.141e-04, -6.552e-04, -4.912e-04, -3.424e-04, -2.150e-04,
            -1.081e-04, -1.372e-05,  6.513e-05,  1.336e-04, -3.450e-04,  7.538e-04],
            [  3.900e-03,  3.143e-03,  2.532e-03,  1.900e-03,  1.325e-03,  8.325e-04,
                4.189e-04,  5.315e-05, -2.525e-04, -5.180e-04,  1.337e-03, -2.917e-03],
            [ -2.577e-02, -2.517e-02, -2.507e-02, -2.464e-02, -2.419e-02, -2.388e-02,
            -2.368e-02, -2.350e-02, -2.342e-02, -2.341e-02, -2.427e-02, -2.275e-02]]

    data = np.array(data)
    diff_table = format_macro_results(data)

    x = {'GDP': ['0.002', '0.002', '0.002', '0.002', '0.002', '0.002',
                 '0.002', '0.002', '0.002', '0.002', '0.002', '0.003'],
         'Consumption': ['0.000', '0.000', '0.001', '0.001', '0.001',
                     '0.001', '0.001', '0.001', '0.001', '0.001', '0.001',
                     '0.002'], 'Interest Rates': ['0.004', '0.003', '0.003',
                     '0.002', '0.001', '0.001', '0.000', '0.000', '-0.000',
                     '-0.001', '0.001', '-0.003'],
         'Total Taxes': ['-0.026', '-0.025', '-0.025', '-0.025', '-0.024',
                         '-0.024', '-0.024', '-0.024', '-0.023', '-0.023',
                         '-0.024', '-0.023'], 'Wages': ['-0.001', '-0.001',
                         '-0.001', '-0.000', '-0.000', '-0.000', '-0.000',
                         '-0.000', '0.000', '0.000', '-0.000', '0.001'],
        'Investment': ['0.006', '0.006', '0.006', '0.005', '0.005', '0.005',
                       '0.005', '0.005', '0.005', '0.005', '0.005', '0.004'],
        'Hours Worked': ['0.003', '0.003', '0.003', '0.003', '0.003', '0.002',
                         '0.002', '0.002', '0.002', '0.002', '0.003', '0.002']}

    assert diff_table == x


def test_elasticity_of_gdp_year_n():

    x = {2016: {'_PT_rt7': [0.41], 'elastic_gdp': [0.14, 0.15, 0.16], '_II_rt7': [0.41]}}

    assert elasticity_of_gdp_year_n(x, 0) == 0.14
    assert elasticity_of_gdp_year_n(x, 1) == 0.15
    assert elasticity_of_gdp_year_n(x, 2) == 0.16
    assert elasticity_of_gdp_year_n(x, 3) == 0.16

def test_elasticity_of_gdp_year_n_multiple_year_keys():

    x = {2016: {'_PT_rt7': [0.41], '_II_rt7': [0.41]}, 2017: {'elastic_gdp': [0.15]} }
    assert elasticity_of_gdp_year_n(x, 0) == 0.
    assert elasticity_of_gdp_year_n(x, 1) == 0.15
    assert elasticity_of_gdp_year_n(x, 2) == 0.15
    assert elasticity_of_gdp_year_n(x, 3) == 0.15
