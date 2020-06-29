#two-way repeated anova

library(tidyverse)
library(ggpubr)
library(rstatix)

x$ID..gegeven.door.leider.experiment

res.aov <- anova_test(data = x, dv = self_validation_mean, wid = ID..gegeven.door.leider.experiment, within = version)
get_anova_table(res.aov)
