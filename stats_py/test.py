import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df_one = pd.read_excel("clean_questionnaire_data.xlsx", sheet_name='Blad1', header=0)
df_two = pd.read_excel("clean_questionnaire_data.xlsx", sheet_name='Blad2', header=0)

r_df = pd.read_excel("simon_says_data_test.xlsx")

df_one = df_one.groupby('question_type', axis=0)


df_two.drop(0, inplace=True)
df_two.reset_index(inplace=True)
df_two = pd.concat([df_two, r_df], axis=1, sort=False)

for group in df_one:
    if group[0] != 'misc':
        print(group[0])
        df_two[group[0] + '_mean'] = list(df_one.get_group(group[0]).mean())
        df_two[group[0] + '_std-dev'] = list(df_one.get_group(group[0]).std())
        print(df_two[['id', group[0] + '_mean']])

# print(df_two[['id', 'version', 'competence_mean']])
#df_two['avg_competence'] = [pd.NaT] + list(df_one.get_group('competence').mean())
#merged = pd.concat([df_two, df_one.get_group('competence').mean()], axis=1, sort=False)
# print(df_two)

pal = sns.color_palette("coolwarm", 9)
sns.set(style="ticks", rc={"lines.linewidth": 0.7})
ax = sns.catplot(x="ID (gegeven door leider experiment", y="competence_mean", hue='version', data=df_two, palette=[pal[0], pal[8]], legend_out=False, kind='bar')
ax.despine(left=True)
#ax = sns.pairplot(df_two[1:])
plt.show()
