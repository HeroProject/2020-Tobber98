# check normality of data

library("dplyr")
library("ggpubr")


value = 'emotional_security_mean'

shapiro.test(df_basic[[value]])
basic_qqplot <- ggqqplot(df_basic[[value]])
basic_densityplot <- ggdensity(df_basic[[value]])

shapiro.test(df_extended[[value]])
extended_qqplot <- ggqqplot(df_extended[[value]])
extended_densityplot <- ggdensity(df_extended[[value]])

ggarrange(basic_qqplot, extended_qqplot, basic_densityplot, extended_densityplot,
          ncol = 2, nrow = 2)
