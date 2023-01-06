

library(ggplot2)
library(dplyr)


x <- read.csv('test.csv')
head(x)


ggplot(x, aes(x = lon, y = lat, fill = pr))+geom_tile()



x2 <- read.csv('test2.csv', stringsAsFactors = F)
head(x2)

ggplot(x2, aes(x = lon, y = lat, fill = pr))+geom_tile()


x2 %>%
    left_join(x, by = c('time', 'lon', 'lat')) %>%
    na.omit()->
    y

all(y$pr.y==y$pr.x)


x %>%
    left_join(x2, by = c('time', 'lon', 'lat')) %>%
    na.omit()->
    y

all(y$pr.y==y$pr.x)
