# non-parametric test
library("ggpubr")

x <- rbind(df_basic, df_extended)

ggboxplot(rbind(df_basic, df_extended), x= 'version', y = 'negative_affect_mean', 
          color = "version", palette = c("#00AFBB", "#E7B800"),
          ylab = "Self Validation Mean", xlab = "Groups")


for (category in categories_means)
{
  print(category)
  print(wilcox.test(df_basic[[category]], df_extended[[category]], conf.int = TRUE))
}
# kruskal.test()
