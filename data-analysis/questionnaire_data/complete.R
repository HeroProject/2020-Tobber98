# complete code to run at once

# perform Cronbach-alpha analysis to determine whether categories are consistent enough

library(psych)

# open file and add version, split dataset on version.
df <- read.csv("BSc-thesis-questionnaire.csv")
df$version = list('extended', 'basic', 'basic', 'extended', 'basic', 'extended', 'extended', 'basic', 'basic', 
                  'extended', 'basic', 'extended', 'extended', 'basic', 'extended', 'basic', 'extended', 'basic', 
                  'basic', 'extended', 'basic', 'extended', 'extended', 'basic', 'basic', 'extended', 'extended', 
                  'basic', 'basic', 'extended', 'basic', 'extended', 'basic', 'extended', 'basic', 'extended')
df_basic <- subset(df, version=='basic')
df_extended <- subset(df, version=='extended')

# list of categories
categories = list(positive_affect = c(6, 8, 13, 17), 
                  negative_affect = c(9, 10, 15), 
                  competence = c(7, 14, 16, 18), 
                  challenge = c(11, 22, 24, 27, 28),
                  flow = c(12, 21, 23, 26),
                  tension_annoyance = c(19, 20, 25))

# list of indices of categories
# positive_affect = c(6, 8, 13, 17)
# negative_affect = c(9, 10, 15)
# competence = c(7, 14, 16, 18)
# challenge = c(11, 22, 24, 27, 28)
# flow = c(12, 21, 23, 26)
# tension_annoyance = c(19, 20, 25)

# calculate alpha values basic version
alpha(df_basic[categories$positive_affect])
alpha(df_basic[categories$negative_affect])      # remove ik was met andere zaken bezig
alpha(df_basic[categories$competence])
alpha(df_basic[categories$challenge])            # Probably not possible to get high enough
alpha(df_basic[categories$flow])                 # remove ik voelde tijdsdruk
alpha(df_basic[categories$tension_annoyance])    # remove ik was weg uit de buitenwereld

# calculate alpha values extended version
alpha(df_extended[categories$positive_affect])
alpha(df_extended[categories$negative_affect])
alpha(df_extended[categories$competence])
alpha(df_extended[categories$challenge])         # Probably not possible to get high enough
alpha(df_extended[categories$flow])              # remove ik voelde tijdsdruk
alpha(df_extended[categories$tension_annoyance])

categories$negative_affect = c(10, 15)           # Not sure if two is enough... 
categories$flow = c(12, 21, 23)
categories$tension_annoyance = c(19, 20)         # Not sure if two is enough... 

#-------------------------------------------------------------------------------

# calculate the means of categories of the questionnaire

df_basic$positive_affect_mean = rowMeans(df_basic[categories$positive_affect])
df_basic$negative_affect_mean = rowMeans(df_basic[categories$negative_affect])
df_basic$comptence_mean = rowMeans(df_basic[categories$competence])
# df_basic$challenge_mean = rowMeans(df_basic[categories$challenge]) // not high enough alpha 
df_basic$flow_mean = rowMeans(df_basic[categories$flow])
df_basic$tension_annoyance_mean = rowMeans(df_basic[categories$tension_annoyance])

df_extended$positive_affect_mean = rowMeans(df_extended[categories$positive_affect])
df_extended$negative_affect_mean = rowMeans(df_extended[categories$negative_affect])
df_extended$comptence_mean = rowMeans(df_extended[categories$competence])
# df_extended$challenge_mean = rowMeans(df_extended[categories$challenge]) // not high enough alpha 
df_extended$flow_mean = rowMeans(df_extended[categories$flow])
df_extended$tension_annoyance_mean = rowMeans(df_extended[categories$tension_annoyance])

#-------------------------------------------------------------------------------

# perform t-test

for (category in categories)
{
  print(t.test(df_basic[category], df_extended[category]))
  category
}

# t.test(df_basic[categories$challenge], df_extended[categories$challenge])
