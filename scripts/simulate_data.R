# Description #####################################################

# Ordinal metrics from triplet data


# Global setup ###################################################
rm(list=ls())

source('./scripts/utils/load_all_libraries.R')

tt_long <- import('./results/pilots/preprocessed_data/triplet_task_long_form.csv')

# Any clearning?
tt_long <- tt_long %>%
        mutate(across(c(triplet_easiness,
                        prolific_id,
                        ref_left,
                        ref_right,                        
                        response,
                        trial_stage,
                        session,
                        correct_response,
                        triplet_left_right_name,
                        triplet_unique_name,
                        template_distances,
                        template_abs_distances,
                        query_position,
                        correct_ref_lowdim_highdim,
                        correct_ref_left_right),as.factor)) %>%
        filter(trial_stage != 'practice',
               qc_pass == 1)

# Start Simulating #################################

## Select relevant columns -------------------
simdf <- tt_long %>%
        select(c(prolific_id,
                 query_item,
                 ref_highdim,
                 ref_lowdim,
                 chosen_ref,
                 dist_abs_query_ref_highdim,
                 dist_abs_query_ref_lowdim,
                 dist_abs_ref_lowdim_ref_highdim))

## Select only one participant? ------------------
simdf <- simdf %>%
        filter(prolific_id == '5757ae3316d587000824700d') %>%
        mutate(prolific_id = 'sim1')

# Add a lambda and generate responses
simdf <- simdf %>%
        mutate(lambda = 1, .before = 'query_item') %>%
        mutate(delta_query_ref_highdim = dist_abs_query_ref_highdim^(1/lambda),
               delta_query_ref_lowdim = dist_abs_query_ref_lowdim^(1/lambda),
               chosen_ref = case_when(
                       delta_query_ref_highdim < delta_query_ref_lowdim ~ 'ref_highdim',
                       delta_query_ref_highdim > delta_query_ref_lowdim ~ 'ref_lowdim',
                       TRUE ~ 'tie'
               )) 

## Combine the doublets ---------------------
simdf <- simdf %>%
        mutate(query_ref_lowdim  = paste(query_item,ref_lowdim,sep = '_'),
               query_ref_highdim = paste(query_item,ref_highdim,sep = '_'))

## Create a sorted triplet name, unique identifier ----------------
triplet_sorted_df <- simdf %>% 
        select(query_item,ref_highdim,ref_lowdim) %>% 
        apply(1,sort) %>% 
        t() %>% 
        as_tibble() %>%
        unite('triplet_sorted',V1:V3, remove = T)

simdf <- cbind(simdf,triplet_sorted_df)

## Go long ----------------------------------
simdf_long <- simdf %>%
        pivot_longer(cols = c(query_ref_highdim,query_ref_lowdim),
                     names_to = 'query_ref_doublet_type',
                     names_prefix = 'query_',
                     values_to = 'query_ref_doublet')

## Sort the query_ref doublet ----------------
simdf_long <- simdf_long %>%
        separate(query_ref_doublet, c('query','ref'),
                 remove = F) %>%
        mutate(across(c(query,ref),as.numeric))

doublet_sorted <- simdf_long %>%
        select('query','ref') %>%
        apply(1,sort) %>% 
        t() %>% 
        as_tibble() %>%
        unite('doublet_sorted',V1:V2, remove = F)

simdf_long <- cbind(simdf_long,doublet_sorted)

## Did the ref win? --------------------------
simdf_long <- simdf_long %>%
        mutate(ref_won = chosen_ref == query_ref_doublet_type,
               unit_dist = abs(query-ref))

## Now count --------------------------------
sumstats <- simdf_long %>%
        group_by(prolific_id,
                 doublet_sorted) %>%
        summarise(n = n(),
                  n_won = sum(ref_won)/2) %>%
        ungroup()

## Calculate the actual, unit distance ---------------
sumstats <- sumstats %>%
        separate(doublet_sorted, c('ex1','ex2'),
                 remove = F) %>%
        mutate(across(c(ex1,ex2),as.numeric),
               unit_dist = abs(ex1-ex2))

plot(sumstats$unit_dist,sumstats$n_won)

# Get all existing triplets ##############################

# Unique units
exemplars <- unique(c(sumstats$ex1,sumstats$ex2))

# Get all possible triplet combinations

all_triplets <- combn(exemplars,3) %>% t()

# Sort the examples
all_triplets <- t(apply(all_triplets,1,sort)) %>% as_tibble()

names(all_triplets) <- c('ex1','ex2','ex3')

# Create the doublets

all_triplets <- all_triplets %>%
        mutate(doublet_1 = paste(ex1,ex2,sep = '_'),
               doublet_2 = paste(ex1,ex3,sep = '_'),
               doublet_3 = paste(ex2,ex3,sep = '_'),
               triplet = paste(ex1,ex2,ex3,sep = '_'))

# Go long
all_triplets_long <- all_triplets %>%
        pivot_longer(cols = starts_with('doublet'),
                     names_to = 'doublet_index',
                     values_to = 'doublet')


## Now, combine with the main data ---------------------------

all_triplets_long <- merge(all_triplets_long,
                      select(sumstats,prolific_id,doublet_sorted,n_won,unit_dist),
                      by.x = 'doublet',
                      by.y = 'doublet_sorted',
                      all.x = T)

all_triplets_long <- all_triplets_long %>%
        mutate(dissimilarity = 9 - n_won + 1)

## Calculate additivity summary stats -------------------
all_triplets_sumstats <- all_triplets_long %>%
        group_by(prolific_id,
                 triplet) %>%
        summarise(n = n(),
                  doublet_1 = dissimilarity[doublet_index == 'doublet_1'],
                  doublet_2 = dissimilarity[doublet_index == 'doublet_2'],
                  doublet_3 = dissimilarity[doublet_index == 'doublet_3']) %>% 
        ungroup() %>%
        mutate(sum_1_3 = doublet_1 + doublet_3)


all_triplets_sumstats_cross_ptp <- all_triplets_sumstats %>%
        group_by(triplet) %>%
        summarise(n = n(),
                  doublet_1_mean = mean(doublet_1),
                  doublet_2_mean = mean(doublet_2),
                  doublet_3_mean = mean(doublet_3),
                  sum_1_3_mean = mean(sum_1_3),
                  additivity_violation_magnitude = sum_1_3_mean - doublet_2_mean)

# Plot this shit!!!! ##############################
axis_lims <- c(0,15)

all_triplets_sumstats %>%
        ggplot(aes(x=sum_1_3,y=doublet_2)) +
        geom_density_2d_filled() +
        geom_jitter(width = 0.1,
                    height = 0.1,
                    color = 'white',
                    alpha = 0.1) +
        geom_abline(intercept = 0, slope = 1, size = 0.5) +
        coord_cartesian(xlim = axis_lims,ylim = axis_lims)
        
# Across participants
all_triplets_sumstats_cross_ptp %>%
        ggplot(aes(x=sum_1_3_mean,y=doublet_2_mean)) +
        geom_density_2d_filled() +
        geom_jitter(width = 0,
                    height = 0,
                    color = 'red',
                    alpha = 0.3) +
        geom_abline(intercept = 0, slope = 1, size = 0.5) +
        coord_cartesian(xlim = axis_lims,ylim = axis_lims)
