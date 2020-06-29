# calculate the means of categories of the questionnaire

# df_basic$positive_affect_mean = rowMeans(df_basic[categories$positive_affect])
# df_basic$negative_affect_mean = rowMeans(df_basic[categories$negative_affect])
# df_basic$competence_mean = rowMeans(df_basic[categories$competence])
# df_basic$challenge_mean = rowMeans(df_basic[categories$challenge]) # not high enough alpha 
# df_basic$flow_mean = rowMeans(df_basic[categories$flow])
# df_basic$tension_annoyance_mean = rowMeans(df_basic[categories$tension_annoyance])
# 
# df_extended$positive_affect_mean = rowMeans(df_extended[categories$positive_affect])
# df_extended$negative_affect_mean = rowMeans(df_extended[categories$negative_affect])
# df_extended$competence_mean = rowMeans(df_extended[categories$competence])
# df_extended$challenge_mean = rowMeans(df_extended[categories$challenge]) # not high enough alpha 
# df_extended$flow_mean = rowMeans(df_extended[categories$flow])
# df_extended$tension_annoyance_mean = rowMeans(df_extended[categories$tension_annoyance])

categories_names <- names(categories)
categories_means <- paste(categories_names, '_mean', sep='')


for (category in names(categories))
{
  df_basic[[paste(category, '_mean', sep='')]] = rowMeans(df_basic[categories[[category]]])
  df_extended[[paste(category, '_mean', sep='')]] = rowMeans(df_extended[categories[[category]]])
  cat(green(category), '\n')
  print(mean(df_basic[[paste(category, '_mean', sep='')]]))
  print(mean(df_extended[[paste(category, '_mean', sep='')]]))
  print(sd(df_basic[[paste(category, '_mean', sep='')]]))
  print(sd(df_extended[[paste(category, '_mean', sep='')]]))
  cat('\n')
}

# library(MVN)
for (category in categories_means)
{
  cat(green(category))
  # mvn(df_basic[72:85])
  # mvn(df_extended[72:85])
  print(shapiro.test(df_basic[[category]]))
  print(shapiro.test(df_extended[[category]]))
}
