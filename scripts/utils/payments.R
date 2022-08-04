# Description ####

# Clean the environment and load libraries ############################

rm(list=ls())

pacman::p_load(pacman,
               rio,
               tidyverse,
               rstatix,
               DT,
               kableExtra,
               readr,
               writexl,
               jsonlite,
               stringr,
               gridExtra,
               knitr,
               magrittr)

# Some global setup ###########################################################

qc_filter <- TRUE


# Read the long form file
tt_long <- import('./results/pilots/preprocessed_data/triplet_task_long_form.csv')

tt_long <- tt_long %>%
        mutate(prolific_id = as.factor(prolific_id),
               correct_numeric = coalesce(correct_numeric,0))


# Average accuracy ##############################################################
tt_acc <-
        tt_long %>%
        filter(correct_response != '',
               trial_stage != 'practice') %>%
        select(prolific_id,correct_numeric)

## Overall accuracy for payment ----------------------------------------------

tt_acc %>%
        group_by(prolific_id) %>%
        get_summary_stats(correct_numeric,type='mean_sd') %>% 
        mutate(payment = round(1.5*mean,2)) %>% 
        select(prolific_id,payment) %>% 
        write_csv('./doc/miscellaneous/payment.csv')

