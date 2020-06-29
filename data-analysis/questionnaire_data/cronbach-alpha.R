# perform Cronbach-alpha analysis to determine whether categories are consistent enough
library(psych)
library(crayon)

# open file and add version, split dataset on version.
df <- read.csv("questionnaire_data/BSc-thesis-questionnaire.csv")
df$version = c('extended', 'basic', 'basic', 'extended', 'basic', 'extended', 'extended', 'basic', 'basic', 
                  'extended', 'basic', 'extended', 'extended', 'basic', 'extended', 'basic', 'extended', 'basic', 
                  'basic', 'extended', 'basic', 'extended', 'extended', 'basic', 'basic', 'extended', 'extended', 
                  'basic', 'basic', 'extended', 'basic', 'extended', 'basic', 'extended', 'basic', 'extended')

# df$first = c('extended', 'extended', 'basic', 'basic', 'basic', 'basic', 'extended', 'extended', 'basic', 'basic', 
#                 'basic', 'basic', 'extended', 'extended', 'extended', 'extended', 'extended', 'extended', 
#                 'basic', 'basic', 'basic', 'basic', 'extended', 'extended', 'basic', 'basic', 'extended', 'extended', 
#                 'basic', 'basic', 'extended', 'extended', 'basic', 'basic', 'extended', 'extended')

df_basic <- subset(df, version=='basic')
df_extended <- subset(df, version=='extended')

# df_basic_first <- subset(df_basic, first=='basic')
# df_basic_second <- subset(df_basic, first=='extended')
# df_extended_first <- subset(df_extended, first=='extended')
# df_extended_second <- subset(df_extended, first=='basic')


# list of categories
categories <- list(positive_affect = c(6, 8, 13, 17), 
               negative_affect = c(9, 10, 15),
               competence = c(7, 14, 16, 18),
               challenge = c(11, 22, 24, 27, 28),        # probably should be dropped
               flow = c(12, 21, 23, 26),
               tension_annoyance = c(19, 20, 25),
               # social game behaviour
               empathy = c(28, 31, 35, 36, 37, 40),
               behavioural_involvement = c(29, 30, 32, 33, 41, 42),
               negative_feelings = c(34, 38, 39, 43, 44), # probably should be dropped
               # ...
               positive_experience = c(45, 48, 50, 51, 53, 56),
               negative_experience = c(46, 49, 52, 54),
               # friendship functions
               help = c(57, 60, 67, 69),
               emotional_security = c(58, 62, 63, 66, 67),
               self_validation = c(59, 61, 64, 65, 68))

# for (category in names(categories))
# {
#   cat(green('\n\n#---------------------------- ', category, ' ----------------------------#'))
#   cat(red('\n\nbasic'))
#   print(psych::alpha(df_basic[categories[[category]]]))
#   cat(red('\nextended'))
#   print(psych::alpha(df_extended[categories[[category]]]))
# }

# categories$negative_affect = c(10, 15)           # Not sure if two is enough... 
# categories$flow = c(12, 21, 23)
# categories$tension_annoyance = c(19, 20)         # Not sure if two is enough... 


for (category in names(categories))
{
  cat(green('\n\n#---------------------------- ', category, ' ----------------------------#'))
  cat(red('\n\nbasic'))
  print(psych::alpha(df_basic[categories[[category]]], delete = TRUE))
  cat(red('\nextended'))
  print(psych::alpha(df_extended[categories[[category]]], delete = TRUE))
}

