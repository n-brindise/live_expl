from pathlib import Path
import os
import sys

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.mathtext as mathtext
import pandas as pd

import cmasher as cmr

sys.path.insert(1, 'D:\\Repos\\live_expl\\pointwise_in_time')
import run_explanation as re


# Script to produce desired data for plotting
##########################################################
# User Input
##########################################################

experiment_name = "mineRL_test"

# Set the "depth" of explanation (how many nodes deep to examine)
explanation_depth = 3

###########################################################

# Load trace data, including rules (as strings or trees)
print(Path.cwd())
trace_path = f'data/trace_data/{experiment_name}/trace1.json'
path = Path(trace_path)
print(Path.cwd())
with open(path, "r") as f:
    trace_config = json.load(f)
    
num_rules = max([len(trace_config['formula_trees']), len(trace_config['formula_strs'])])
print('num_rules: ', num_rules)
    
#file_output_path = f'data/results/plots/{experiment_name}'


# Generate query at t0=0 each top-level rule
initial_queries = list()

for rule_idx in range(0,num_rules):
    
    query = dict()
    query['t0*'] = 0
    query['ruleNo'] = rule_idx
    query['node'] = str(rule_idx)
    query['t*'] = 0
    initial_queries.append(query)
    
# Set up trace data location info for explainer           
trace_data_loc = {
    "base_path" : trace_path,
    "filename" : ''
    }

# Expl mode set to 'default'. Allows us to input a query list
expl_specs = {
    "mode" : 'default',
    "query_list" : initial_queries
}
    
# Prepare config for function call
config = dict()
config['trace_data_loc'] = trace_data_loc
config['expl_specs'] = expl_specs

_, rule_dicts = re.run_explanation(**config)

# Find activation/deactivation times from rule_dicts for each rule (t0 = 0)
activity_record = dict()

for rule_idx in range(0,num_rules):
    tau_i = rule_dicts[rule_idx][str(rule_idx)]['tau_i'][0]
    activity_record[rule_idx] = list()
    # Check for transitions in tau_i
    for tstep in range(0, len(tau_i)-1):
        if (tau_i[tstep] - tau_i[tstep+1])**2 == 1: # change occurred
            activity_record[rule_idx].append(tstep)
            
print(activity_record[0])
print(activity_record[1])
print(activity_record[2])
print(activity_record[3])

# Next, check argument truth at each child node.

child_node_records = dict()

for rule_idx in range(0,num_rules):
    
    child_node_records[rule_idx] = dict()
    child_nodes_to_check = rule_dicts[rule_idx][str(rule_idx)]['children']
    print(child_nodes_to_check)
    
    for node in child_nodes_to_check:
        print('node: ', node)
        child_node_records[rule_idx][node] = list()
        for t0 in activity_record[rule_idx]:
            # Check preceding timestep first
            print('previous: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0-1])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0-1]:
                child_node_records[rule_idx][node].append(1)
            else:
                child_node_records[rule_idx][node].append(0)
            # Check t0
            print('t0sfortrue: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0]:
                child_node_records[rule_idx][node].append(1)
            else:
                child_node_records[rule_idx][node].append(0)

                
print(child_node_records[0])
print(child_node_records[1])
print(child_node_records[2])
print(child_node_records[3])
     
            
        
    
