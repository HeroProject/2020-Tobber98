# perform t-test

for (category in colnames(df))
{
  if (category != 'time' && category != 'version' && category != 'remarks' && category != 'id')
  {
    print(category)
    print(t.test(df_basic[[category]], df_extended[[category]]))
  }
}


# t.test(df_basic[categories$challenge], df_extended[categories$challenge])
