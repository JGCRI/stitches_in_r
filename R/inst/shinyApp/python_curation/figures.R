

library(ggplot2)
library(dplyr)



#########################################################################
# TAS

x <- read.csv('python_curation/CONUS_tas_allesms.csv', stringsAsFactors = F)



x %>%
    filter(experiment == 'historical') %>%
    rename(historical_ens = ens_avg) %>%
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
           change = ens_avg-historical_ens) ->
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
    ggtitle(paste('Change in ensembled average 2080-2099 average CONUS', unique(plot_tas$var), '\nfrom 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_tas$var), '_change.png'), p1, width = 6, height = 4, units='in')


p2 <- ggplot(plot_tas) +
    geom_tile(aes(x = plotesm, y = experiment, fill = change)) +
    #scale_fill_distiller(palette = 'BrBG', direction = -1) +
    scale_fill_gradient(low = 'yellowgreen', high = 'firebrick2') +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
    ggtitle(paste('Change in ensembled average 2080-2099 average CONUS', unique(plot_tas$var), '\nfrom 1995-2014 CONUS'))

ggsave(paste0('python_curation/CONUS_', unique(plot_tas$var), '_change_overshoots.png'), p2, width = 6, height = 6, units='in')

