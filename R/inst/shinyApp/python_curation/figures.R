

library(ggplot2)
library(dplyr)



# #########################################################################
# TAS
# #########################################################################

x <- read.csv('python_curation/global_tas_allesms.csv', stringsAsFactors = F)



x %>%
    filter(experiment == 'historical') %>%
    rename(historical_ens = ens_avg,
           historical_iasd = ens_avg_iasd) %>%
    select(-experiment) %>%
    distinct %>%
    mutate(plotesm = paste0(letters[as.integer(row.names(.))], '.', esm),
           ECS_order = as.integer(row.names(.))) ->
    historicaltas

x %>%
    filter(experiment != 'historical') %>%
    left_join(historicaltas, by = c('esm', 'var')) %>%
    mutate(ens_avg = if_else(ens_avg == -999, Inf, ens_avg)) %>%
    mutate(pct_change = 100 * (ens_avg - historical_ens)/historical_ens,
           change = ens_avg-historical_ens,
           change_iasd = ens_avg_iasd - historical_iasd) ->
    plot_tas


p1 <- ggplot(plot_tas %>% filter(experiment != 'ssp119',
                           experiment != 'ssp460',
                           experiment != 'ssp434',
                           experiment != 'ssp534-over')) +
    geom_tile(aes(x = plotesm, y = experiment, fill = change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'yellowgreen', high = 'firebrick2') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Change in ensemble average 2080-2099 average \nCONUS', unique(plot_tas$var), 'from 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_tas$var), '_change.png'), p1, width = 6, height = 4, units='in')


p1a <- ggplot(plot_tas %>% filter(experiment != 'ssp119',
                                 experiment != 'ssp460',
                                 experiment != 'ssp434',
                                 experiment != 'ssp534-over')) +
    geom_tile(aes(x = plotesm, y = experiment, fill = ens_avg_iasd^2)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    #scale_fill_continuous(type = 'viridis') +
    scale_fill_gradient(low = 'blue', high = 'firebrick2') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Change in ensemble average 2080-2099 average \nCONUS', unique(plot_tas$var), 'from 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_tas$var), '_iasd_change.png'), p1a, width = 6, height = 4, units='in')




p2 <- ggplot(plot_tas) +
    geom_tile(aes(x = plotesm, y = experiment, fill = change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_continuous(type = 'viridis') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Change in ensemble average 2080-2099 average \nCONUS', unique(plot_tas$var), 'from 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_tas$var), '_change_overshoots.png'), p2, width = 6, height = 6, units='in')






# #########################################################################
# PR
# #########################################################################

pr <- read.csv('python_curation/CONUS_pr_allesms.csv', stringsAsFactors = F)



pr %>%
    filter(experiment == 'historical') %>%
    rename(historical_ens = ens_avg,
           historical_iasd = ens_avg_iasd) %>%
    select(-experiment) %>%
    distinct %>%
    mutate(plotesm = paste0(letters[as.integer(row.names(.))], '.', esm),
           ECS_order = as.integer(row.names(.))) ->
    historicalpr

pr %>%
    filter(experiment != 'historical') %>%
    left_join(historicalpr, by = c('esm', 'var')) %>%
    mutate(ens_avg = if_else(ens_avg == -999, Inf, ens_avg)) %>%
    mutate(pct_change = 100 * (ens_avg - historical_ens)/historical_ens,
           change = ens_avg-historical_ens) ->
    plot_pr


p3 <- ggplot(plot_pr %>% filter(experiment != 'ssp119',
                                 experiment != 'ssp460',
                                 experiment != 'ssp434',
                                 experiment != 'ssp534-over')) +
    geom_tile(aes(x = plotesm, y = experiment, fill = pct_change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'cadetblue1', high = 'cadetblue4') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Percent Change in ensemble average 2080-2099 average \nCONUS', unique(plot_pr$var), 'from 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_pr$var), '_change.png'), p3, width = 6, height = 4, units='in')


p4 <- ggplot(plot_pr) +
    geom_tile(aes(x = plotesm, y = experiment, fill = pct_change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'cadetblue1', high = 'cadetblue4') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Percent Change in ensemble average 2080-2099 average \nCONUS', unique(plot_pr$var), 'from 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_pr$var), '_change_overshoots.png'), p4, width = 6, height = 6, units='in')

