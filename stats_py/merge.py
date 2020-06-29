import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time

q_df = pd.read_csv("BSc Thesis AI questionnaire v1.csv")
r_df = pd.read_excel("simon_says_data_test.xlsx")

# print(q_df)
# print(r_df)

merged_df = pd.concat([q_df, r_df], axis=1, sort=False)

basic_df = merged_df.loc[merged_df['version'] == 'basic']
extended_df = merged_df.loc[merged_df['version'] == 'extended']

#for c in basic_df.columns:
    # b = basic_df[c]
    # e = extended_df[c]
    # print(b)

sns.set(style="ticks", rc={"lines.linewidth": 0.7})
# ax = sns.catplot(x="version", y="avg_score", data=merged_df, hue='id', palette='dark', kind='point', order=['basic', 'extended'], legend_out=False)
ax = sns.catplot(x="id", y="looking_at_experiment_leader", data=merged_df, hue='version', palette='dark', legend_out=False, alpha=.8, kind='bar')
plt.show()


# print(basic_df.iloc[: , 4])