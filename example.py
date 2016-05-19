import dropq
import pandas as pd
import taxcalc
import json

myvars = {}
#myvars['_II_rt4'] = [0.39, 0.40, 0.41]
#myvars['_II_rt3'] = [0.31, 0.32, 0.33]
#myvars['_FICA_ss_trt'] = [0.15]
##myvars['_CTC_c'] = [2000]
#myvars['_factor_target'] = [0.02]
myvars['_II_em_cpi'] = False
#myvars['_BE_inc'] = [0.8]
#myvars['_BE_CG_per'] = [1.2]
first_year = 2016
user_mods = {first_year: myvars}
#user_mods = {2015: {}}


#Create a Public Use File object
tax_dta = pd.read_csv("puf.csv.gz", compression='gzip')
#records = PUF(tax_dta)
mY_dec, mX_dec, df_dec, pdf_dec, cdf_dec, mY_bin, mX_bin, df_bin, pdf_bin, cdf_bin, fiscal_tots = dropq.run_models(tax_dta, num_years=3, start_year=first_year, user_mods=user_mods)


suffix = "exp1"

with open("mY_dec" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(mY_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("mX_dec" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(mX_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("df_dec" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(df_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("pdf_dec" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(pdf_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("cdf_dec" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(cdf_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("mY_bin" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(mY_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("mX_bin" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(mX_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("df_bin" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(df_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("pdf_bin" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(pdf_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("cdf_bin" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(cdf_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

with open("fiscal_tots" + suffix + ".txt", "w") as f1:
    f1.write(json.dumps(fiscal_tots, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')


#print(mY_dec)
#print(mX_dec)
#print(df_dec)
#print(mY_bin)
#print(mX_bin)
#print(df_bin)
#print(fiscal_tots)
