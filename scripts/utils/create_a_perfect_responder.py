# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 13:01:22 2021

@author: lb08
"""

# Description:

# This script will create a fake subject with perfect responses to the triplet 
# stimuli. For trials where a correct response doesn't exist, it will randomly
# choose the stimuli. 

# The code loads one of the existing participant data, substitutes the name, 
# and changes responses to be correct. Then, the rest of the script is the same
# as for the normal preprocessing.


# Import other libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import re
import json

# %% Global setup

print(os.getcwd())

# Set the working directory
os.chdir(r'C:\Users\levan\GitHub\norming_1_analysis')

save_tt_data = True

# %% Import the files

# Use a participant ran after the bug was fixed
file_list = ['jatos_prolific_id_5e8cb846e94a4406307d6da2.txt']

# Create empty data frames to append to
ind_tt  = []

# if it doesn't just start the loop
for iF in file_list:
    print(iF)
    
    f = open('./data/pilots/gui_downloads/' + iF,'r')    

    rawtext = f.read()
    f.close()
    
    # Get the data submission component
    if rawtext.find('[data_submission_start---') == -1:
        continue
        # # So there is no data submission. Take the last component
        # start_loc = rawtext.rfind('[break_start_---') + \
        #     len('[break_start_---')
        # end_loc   = rawtext.rfind('---_break_end]')
    else:
        start_loc = rawtext.find('[data_submission_start---') + \
            len('[data_submission_start---')
        end_loc   = rawtext.find('---data_submission_end]')
    
    data_submission_text = rawtext[start_loc:end_loc]

    # %% Decode the JSON
    data_decoded = json.loads(data_submission_text)
    
    # Deal with prolific_ID. Sometimes it was assigned to the inputData and sometimes not
    if 'prolific_ID' in data_decoded:
        data_decoded['inputData']['prolific_ID'] = data_decoded['prolific_ID']
    if 'prolific_ID' in data_decoded['inputData']:
        data_decoded['prolific_ID'] = data_decoded['inputData']['prolific_ID']        
    
    # Change the prolific ID
    data_decoded['inputData']['prolific_ID'] = 'perfect_responder'
    data_decoded['prolific_ID'] = 'perfect_responder'    
    
    
    practice_output = pd.DataFrame(data_decoded['outputData']['practice'])
    tt_output = pd.DataFrame(data_decoded['outputData']['triplet_task'])
    # tt = pd.concat([practice,tt],ignore_index=True)

    # Get the input data into long format
    
    # Concatenate the input info into one data frame
    tt_input = list(
        map(
            pd.DataFrame,data_decoded['inputData']['triplet_sessions']
            )
        )
    tt_input = pd.concat(tt_input,ignore_index=True)
    tt_input = tt_input.drop(columns=['correct_response'])
    
    
    # Join the input and output
    tt = pd.concat([tt_input,tt_output],axis=1,join='outer')
    
    # Do the same for practice
    practice_input = list(
        map(
            pd.DataFrame,data_decoded['inputData']['practice_sessions']
            )
        )
    practice_input = pd.concat(practice_input,ignore_index=True)
    practice_input = practice_input.drop(columns=['correct_response'])
    
    
    # Join the input and output
    practice = pd.concat([practice_input,practice_output],axis=1,join='outer')    
    
    tt = pd.concat([practice,tt],ignore_index=True)
    
    # Add the prolific ID as a column
    tt.insert(loc=0, column='prolific_id', value=data_decoded['prolific_ID'])
    
    # %% Now, change the responses to be correct responses. Where none exists,
    # retain the original participant's choice. 
    
    tt['response'] = np.where(
        (tt['correct_response']!='p') & (tt['correct_response']!='q'),tt['response'],
        tt['correct_response']
    )
       
    # Do the same for the correct columnt
    tt['correct'] = np.where(
        (tt['correct_response']!='p') & (tt['correct_response']!='q'),None,
        True
        )
    
    # %% Add extra columns to the triplet trials
    
    # Whats the query, ref_left, ref_right items? ref_left = ref left
    query_stim_df = tt['query_stimulus'].str.split('object9F0Level',expand=True)
    query_stim_df = query_stim_df[1].str.split('F1Level',expand=True)
    tt['query_item'] = query_stim_df[0].astype(int)
    
    ref_left_stim_df = tt['ref_left_stimulus'].str.split('object9F0Level',expand=True)
    ref_left_stim_df = ref_left_stim_df[1].str.split('F1Level',expand=True)
    tt['ref_left'] = ref_left_stim_df[0].astype(int)    

    ref_right_stim_df = tt['ref_right_stimulus'].str.split('object9F0Level',expand=True)
    ref_right_stim_df = ref_right_stim_df[1].str.split('F1Level',expand=True)
    tt['ref_right'] = ref_right_stim_df[0].astype(int)        
    
    # Distances:
    tt['dist_query_ref_left'] = tt['query_item'] - tt['ref_left']
    tt['dist_query_ref_right'] = tt['query_item'] - tt['ref_right']
    tt['dist_ref_left_ref_right'] = tt['ref_left'] - tt['ref_right']
    
    # Absolute distances
    tt['abs_dist_query_ref_left'] = abs(tt['query_item'] - tt['ref_left'])
    tt['abs_dist_query_ref_right'] = abs(tt['query_item'] - tt['ref_right'])
    tt['abs_dist_ref_left_ref_right'] = abs(tt['ref_left'] - tt['ref_right'])
    
    # Create the triplet column
    tt['triplet_left_right_name'] = tt['query_item'].astype(str) \
        + '_' + tt['ref_left'].astype(str) \
            + '_' + tt['ref_right'].astype(str)
            
    # %% Create the triplet name unique column
    
    # - create a column with ref l and ref r as a list per row
    ref_left_right_list = tt[['ref_left','ref_right']].values.tolist()
    
    # - sort each entry
    ref_left_right_list_sorted_df = pd.DataFrame(list(map(sorted,ref_left_right_list)))
    
    # - add these to dataframe
    tt['ref_lowdim'] = ref_left_right_list_sorted_df[0]
    tt['ref_highdim'] = ref_left_right_list_sorted_df[1]
    # - add distances to the ref_lowdim and ref_highdim
    tt['dist_query_ref_lowdim'] = tt['query_item']- tt['ref_lowdim']
    tt['dist_query_ref_highdim'] = tt['query_item']- tt['ref_highdim']
    tt['dist_ref_lowdim_ref_highdim'] = tt['ref_lowdim']- tt['ref_highdim']
    # - add absolute distances
    tt['dist_abs_query_ref_lowdim'] = abs(tt['dist_query_ref_lowdim'])
    tt['dist_abs_query_ref_highdim'] = abs(tt['dist_query_ref_highdim'])
    tt['dist_abs_ref_lowdim_ref_highdim']  = abs(tt['dist_ref_lowdim_ref_highdim'])
    
    tt['triplet_unique_name'] = tt['query_item'].astype(str) + \
        '_' + tt['ref_lowdim'].astype(str) + \
            '_' + tt['ref_highdim'].astype(str)
            
    # Create a template column based on distances 
    tt['template_distances'] = tt['dist_query_ref_lowdim'].astype(str) + \
        '_' + tt['dist_query_ref_highdim'].astype(str) + \
        '_' + tt['dist_ref_lowdim_ref_highdim'].astype(str)
        
    # Create a template column based on ABSOLUTE distances 
    
    # - for this, we should first sort the abs distances between q and r1 and q and r2
    temp_df = tt[['dist_abs_query_ref_lowdim','dist_abs_query_ref_highdim']].values.tolist()
    temp_df_sorted = pd.DataFrame(list(map(sorted,temp_df)))
    
    tt['template_abs_distances'] = temp_df_sorted[0].astype(str) + \
        '_' + temp_df_sorted[1].astype(str) + \
        '_' + tt['dist_abs_ref_lowdim_ref_highdim'].astype(str)    
        
    # Label each repetition of the unique triplet
    tt['triplet_rep'] = tt.groupby(['trial_stage','triplet_unique_name']).cumcount()+1    
    
    # Label each repetition of the template_distances
    tt['triplet_rep'] = tt.groupby(['trial_stage','triplet_unique_name']).cumcount()+1        
    
    # Label each repetition of the template_abs_dist
    tt['template_distances_rep'] = tt.groupby(['trial_stage','template_distances']).cumcount()+1    
    
    
    # %% How easy is the triplet?
    tt['triplet_easiness'] = abs(
        tt['dist_abs_query_ref_lowdim'] - tt['dist_abs_query_ref_highdim'])
    
    # %% Is query in the middle, left or right?
    tt['query_position'] = np.where(
        (
         tt['query_item'] < tt['ref_left']
         ) & (
             tt['query_item'] < tt['ref_right']
             ),
        'query_left',
        np.where(
        (
         tt['query_item'] > tt['ref_left']
         ) & (
             tt['query_item'] > tt['ref_right']
             ),
        'query_right',
        'query_middle')
        )
    
    # %% Which ref was chosen? ref_lowdim and ref_highdim
    
    # - identify which ref was chosen
    tt['chosen_ref_value'] = np.where(
        np.isnan(tt['rt']),float('nan'),
        np.where(
            tt['response'] == 'q',
            tt['ref_left'],
            tt['ref_right']
            )
        )
    
    # - was the chosen one ref_lowdim or ref_highdim
    tt['chosen_ref'] = np.where(
        np.isnan(tt['chosen_ref_value']),float('nan'),
        np.where(    
            tt['chosen_ref_value'] == tt['ref_lowdim'],
            'ref_lowdim','ref_highdim'
            )
        )
    
    # %% Which ref was the correct choice?
    
    # tt['correct_ref'] = np.where(
    #     tt['triplet_easiness']==0,float('nan'),
    #     np.where(
    #         (tt['correct_response'] == 'q') & (tt['ref_left'] < tt['ref_right']),
    #         'ref_lowdim',np.where(
    #             (tt['correct_response'] == 'q') & (tt['ref_left'] > tt['ref_right']),
    #             'ref_highdim',np.where(
    #                 (tt['correct_response'] == 'p') & (tt['ref_right'] < tt['ref_left']),
    #                 'ref_lowdim','ref_highdim'
    #                 )
    #             )
    #         )
    #     )  
    
    tt['correct_ref_lowdim_highdim'] = np.where(
        tt['triplet_easiness']==0,float('nan'),
        np.where(
            tt['dist_abs_query_ref_lowdim'] < tt['dist_abs_query_ref_highdim'],
            'ref_lowdim',
            np.where(tt['dist_abs_query_ref_lowdim'] > tt['dist_abs_query_ref_highdim'],
            'ref_highdim','error'
            )
        )
    )
    
    tt['correct_ref_left_right'] = np.where(
        tt['triplet_easiness']==0,float('nan'),
        np.where(
            tt['abs_dist_query_ref_left'] < tt['abs_dist_query_ref_right'],
            'ref_left',
            np.where(
                tt['abs_dist_query_ref_left'] > tt['abs_dist_query_ref_right'],
                'ref_right','error'
                )
            )
        )
    
    # %% Now, change the column saying whether the participant was correct or not
    tt['correct_numeric'] = np.where(
        tt['triplet_easiness'] == 0,float('nan'),
        np.where(
            tt['correct_response'] == tt['response'],
            1,0
            )
        )     
    
    # %% Is this person QC pass or fail?
    tt['qc_pass']  = 1  
    
    # %% Append dataframes 
    ind_tt.append(tt)

large_tt  = pd.concat(ind_tt, ignore_index=True)

# %% Save both data files
if save_tt_data:
    large_tt.to_csv('./results/pilots/preprocessed_data/perfect_responder_fake_data.csv',index=False)
    