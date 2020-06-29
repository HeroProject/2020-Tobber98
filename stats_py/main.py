import pandas as pd
import seaborn as sb

def make_scatterplot():
    pass

gs_df = pd.read_excel("processing/python/simon_says_data.xlsx")
# q_df = pd.read_excel("questionnaire_results.xlsx")


gs_basic = gs_df.loc[gs_df['version'] == 'basic']
gs_extended = gs_df.loc[gs_df['version'] == 'extended']
