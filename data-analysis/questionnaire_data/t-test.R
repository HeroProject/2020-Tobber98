# perform t-test

for (category in categories_means)
{
  print(category)
  print(t.test(df_basic[[category]], df_extended[[category]]))
  }

# t.test(df_basic[categories$challenge], df_extended[categories$challenge])
