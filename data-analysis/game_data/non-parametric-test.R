# non-parametric test

for (category in colnames(df))
{
  if (category != 'time' && category != 'version' && category != 'remarks' && category != 'id')
  {
    print(category)
    print(wilcox.test(df_basic[[category]], df_extended[[category]]))
  }
}
# kruskal.test()