

library(ggplot2)
library(dplyr)


x <- read.csv('python_curation/CONUS_pr_testing_allesms.csv', stringsAsFactors = F)



x %>%
    filter(experiment == 'historical') %>%
    rename(historical_ens_pr = ens_avg_pr) %>%
    select(-experiment) %>%
    distinct %>%
    mutate(plotesm = paste0(letters[as.integer(row.names(.))], '.', esm)) ->
    historical

x %>%
    filter(experiment != 'historical') %>%
    left_join(historical, by = 'esm') %>%
    mutate(ens_avg_pr = if_else(ens_avg_pr == -999, Inf, ens_avg_pr)) %>%
    mutate(pct_change = 100 * (ens_avg_pr - historical_ens_pr)/historical_ens_pr) ->
    plot_tbl


p1 <- ggplot(plot_tbl %>% filter(experiment != 'ssp119',
                           experiment != 'ssp460',
                           experiment != 'ssp434',
                           experiment != 'ssp534-over')) +
    geom_tile(aes(x = plotesm, y = experiment, fill = pct_change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'skyblue1', high = 'skyblue4') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle('Percent change in 2080-2099 average CONUS precipitation \nfrom 1995-2014 CONUS precipitation')

ggsave('python_curation/CONUS_pr_pctchange.png', p1, width = 6, height = 4, units='in')

p2 <- ggplot(plot_tbl) +
    geom_tile(aes(x = plotesm, y = experiment, fill = pct_change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'skyblue1', high = 'skyblue4') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle('Percent change in 2080-2099 average CONUS precipitation \nfrom 1995-2014 CONUS precipitation')

ggsave('python_curation/CONUS_pr_pctchange_overshoots.png', p2, width = 6, height = 6, units='in')


