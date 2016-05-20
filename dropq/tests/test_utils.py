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
import json

def test_create_json_blob():
    _types = [int] * 3
    df = DataFrame(data=[[1,2,3],[4,5,6],[7,8,9]], columns=['a','b','c'])
    ans = create_json_blob(df, column_types=_types)
    exp = {'0': {'a': '1', 'b': '2', 'c': '3'},
           '1': {'a': '4', 'b': '5', 'c': '6'},
           '2': {'a': '7', 'b': '8', 'c': '9'}}
    assert ans == json.dumps(exp)


def test_create_json_blob_column_names():
    _types = [int] * 3
    df = DataFrame(data=[[1,2,3],[4,5,6],[7,8,9]], columns=['a','b','c'])
    ans = create_json_blob(df, column_names=['d', 'e', 'f'],
                           column_types=_types)
    exp = {'0': {'d': '1', 'e': '2', 'f': '3'},
           '1': {'d': '4', 'e': '5', 'f': '6'},
           '2': {'d': '7', 'e': '8', 'f': '9'}}
    assert ans == json.dumps(exp)

def test_create_json_blob_row_names():
    _types = [int] * 3
    df = DataFrame(data=[[1,2,3],[4,5,6],[7,8,9]], columns=['a','b','c'])
    ans = create_json_blob(df, row_names=['4', '5', '6'],
                           column_types=_types)
    exp = {'4': {'a': '1', 'b': '2', 'c': '3'},
           '5': {'a': '4', 'b': '5', 'c': '6'},
           '6': {'a': '7', 'b': '8', 'c': '9'}}
    assert ans == json.dumps(exp)

def test_create_json_blob_float():
    df = DataFrame(data=[[1.,2.,3.],[4.,5.,6.],[7.,8.,9.]], columns=['a','b','c'])
    ans = create_json_blob(df)
    exp = {'0': {'a': '1.00', 'b': '2.00', 'c': '3.00'},
           '1': {'a': '4.00', 'b': '5.00', 'c': '6.00'},
           '2': {'a': '7.00', 'b': '8.00', 'c': '9.00'}}
    assert ans == json.dumps(exp)

def test_create_json_table():
    df = DataFrame(data=[[1.,2,3],[4.,5,6],[7,8,9]], columns=['a','b','c'])
    ans = create_json_table(df)
    exp = {'0': ['1.00', '2', '3'],
           '1': ['4.00', '5', '6'],
           '2': ['7.00', '8', '9']}
    assert ans == exp
