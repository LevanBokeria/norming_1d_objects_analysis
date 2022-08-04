# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 13:01:22 2021

@author: lb08
"""

# Description:

# This script will take the bulk-downloaded results files from jatos, find 
# prolific IDs, substitute them with anonymized IDs, and save individual 
# participant files with the anonymous ID in the ./data/ folder. It will also
# save the mapping between the prolific IDs and anonymouse IDs.

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

saveData = True

# %% Import the files

file_name = 'jatos_data.txt'

f = open('./data/' + file_name,'r')    

rawtext = f.read()

rawtext_split = rawtext.splitlines()
f.close()
# %% How many prolific ID components do we have?
pid_counter = 0
pid_idxs = []
for idx, iLine in enumerate(rawtext_split):
    if iLine.find('[get_pid_comp_start---') !=-1:
        pid_counter += 1
        pid_idxs.append(idx)

# %% Create a dataframe for prolific IDs and anonymized IDs
pid_map_df = pd.DataFrame(columns=['prolific_id','anonymous_id','multiple_tries'])
duplicate = 0

# %% Look to split the file and save individual txt files
    
# Loop over all get_pid_component start positions.
for iP in range(0,len(pid_idxs)):
    print(iP)
    
    # Get the component before iP
    iIdx_start = pid_idxs[iP]
    
    # If its the last 'get_pid' component, the next one doesn't exist so, the 
    # iIdx_end has to be the length of rawtext_split
    if iP == len(pid_idxs)-1:
        iIdx_end = len(rawtext_split) + 1
    else:
        iIdx_end = pid_idxs[iP+1]
    
    # Join all these componenets
    tosave = '\n'.join(rawtext_split[iIdx_start:iIdx_end])
    
    # Whats the prolific ID
    json_start_loc = rawtext_split[iIdx_start].find('[get_pid_comp_start---') + \
        len('[get_pid_comp_start---')
    json_end_loc = rawtext_split[iIdx_start].find('---get_pid_comp_end')
    json_text = rawtext_split[iIdx_start][json_start_loc:json_end_loc]    
    iData_decoded = json.loads(json_text)
    if 'prolific_ID' in iData_decoded:
        iPID = iData_decoded['prolific_ID']
    elif 'prolific_ID' in iData_decoded['inputData']:
        iPID = iData_decoded['inputData']['prolific_ID']
    
    # Did this participant already try?
    if iP > 0:
                
        if pid_map_df.prolific_id.str.contains(iPID).any():
            duplicate = 1
            
            # Assign duplicate to the matching rows too
            pid_map_df.multiple_tries[pid_map_df.prolific_id.str.contains(iPID)] = 1
            
            
        else:
            duplicate = 0
    
    # Assign an anonymized ID and record in a dataframe
    aid = 'sub' + str(iP+1).zfill(3)
    
    pid_map_df = pid_map_df.append({'prolific_id': iPID, \
                                    'anonymous_id': aid, \
                                        'multiple_tries': duplicate},\
                                   ignore_index=True)
        
    # Substitute the pid with aid
    tosave = tosave.replace(iPID,aid)
        
    if saveData:
        # Save this data
        f= open('./data/anonymized_jatos_data/jatos_id_' + aid + '.txt',"w+")    
        
        f.write(tosave)
        f.close()
        
        # save the pid mapping
        pid_map_df.to_csv('../../OwnCloud/Cambridge/PhD/projects/norming_1/pid_map.csv',index=False)
