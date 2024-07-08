from pathlib import Path
import os
import sys
import time

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
timeStart = time.time()

experiment_name = "mineRL_test"

# List of times to ask about
query_times = [600]

# Set the "depth" of explanation (how many nodes deep to examine)
explanation_depth = 3

###########################################################

# Load trace data, including rules (as strings or trees)
print(Path.cwd())
trace_path = f'data/trace_data/{experiment_name}/trace3.json'
#trace_path = f'data/trace_data/{experiment_name}/traceTest.json'
path = Path(trace_path)
print(Path.cwd())
with open(path, "r") as f:
    trace_config = json.load(f)
    
num_rules = max([len(trace_config['formula_trees']), len(trace_config['formula_strs'])])
print('num_rules: ', num_rules)
timestep_of_interest = trace_config['trace'][query_times[0]]
print('timestep of interest: ', timestep_of_interest)
#file_output_path = f'data/results/plots/{experiment_name}'

#######################################################
# Attempt at recursive method
#######################################################

def get_query(t0, rule_idx, node):
    
    query = dict()
    query['t0*'] = t0
    query['ruleNo'] = rule_idx
    query['node'] = node
    query['t*'] = t0
    
    return query
    
def get_diagnostic_data(query_list, trace_path):
    
    # Set up trace data location info for explainer           
    trace_data_loc = {
        "base_path" : trace_path,
        "filename" : ''
        }

    # Expl mode set to 'default'. Allows us to input a query list
    expl_specs = {
        "mode" : 'default',
        "query_list" : query_list
    }
        
    # Prepare config for function call
    config = dict()
    config['trace_data_loc'] = trace_data_loc
    config['expl_specs'] = expl_specs

    _, rule_dicts = re.run_explanation(**config)
    
    return rule_dicts

# Do diagnostics using heuristics **given specific t times to explain**

# Initialize node list as top level
query_list = list()
node_dict = dict()
node_list = list()

# The initial t0 to check are just set to 0.
for rule_idx in range(0, num_rules):
    node = str(rule_idx)
    node_dict[node] = dict()
    node_dict[node]['t0'] = 0
    node_dict[node]['rule_idx'] = rule_idx
    query = get_query(0, rule_idx, node)
    
    query_list.append(query)
    node_list.append(node)

rule_dicts = get_diagnostic_data(query_list, trace_path)

# Begin iteration for each level of depth in the explanation
    
for q_t in query_times:
    
    for level_idx in range(0, explanation_depth):
        # Initialize list of children to use on next depth level:
        child_node_list = list()
        
        for node in node_list: 
            rule_idx = node_dict[node]['rule_idx']
            t0 = node_dict[node]['t0']
            tau_i = rule_dicts[rule_idx][node]['tau_i'][t0]
            tau_s = rule_dicts[rule_idx][node]['tau_s'][t0]
            tau_a = rule_dicts[rule_idx][node]['tau_a'][t0]
            tau_v = rule_dicts[rule_idx][node]['tau_v'][t0]
            
            children = rule_dicts[rule_idx][node]['children']
            
            # Check whether node is satisfied, active, inactive, or violated at q_t
            # Also store the 
            
            # If satisfied exactly at q_t, we'll store q_t for the next node level
            # and deliver the argument values at and before as expl
            if tau_s[q_t - t0] == 1:
                for child in children:
                    node_dict[child] = dict()
                    node_dict[child]['t0'] = q_t
                    node_dict[child]['rule_idx'] = rule_idx
                    child_node_list.append(child)
                    
                node_dict[node]['status_expl'] = f'Node {node} is satisfied at t0={t0}, t={q_t}.'
                print(node_dict[node]['status_expl'])
                node_dict[node]['short_status_expl'] = f'(s) t0={t0}, t={q_t}.'
                
            elif tau_a[q_t - t0] == 1:
                for child in children:
                    node_dict[child] = dict()
                    node_dict[child]['t0'] = q_t
                    node_dict[child]['rule_idx'] = rule_idx
                    child_node_list.append(child)
                    
                node_dict[node]['status_expl'] = f'Node {node} is active at t0={t0}, t={q_t}.'
                print(node_dict[node]['status_expl'])
                node_dict[node]['short_status_expl'] = f'(a) t0={q_t}, t={q_t}.'
            
            elif tau_i[q_t - t0] == 1:
                #print('tau_i: ', tau_i)
                #print('tau_s', tau_s)
                #print('tau_a', tau_a)
                # Check if the node was always inactive or previously active (handled differently)
                if tau_i[0] == 1: # Always inactive (must be an inactive implication formula)
                    for child in children:
                        node_dict[child] = dict()
                        node_dict[child]['t0'] = q_t  
                        node_dict[child]['rule_idx'] = rule_idx
                        child_node_list.append(child)
                        
                    node_dict[node]['status_expl'] = f'Node {node} is inactive on all t0={q_t}, t>=t0.' 
                    print(node_dict[node]['status_expl']) 
                    node_dict[node]['short_status_expl'] = f'(i) t0={q_t}, t>=t0.'          
                
                else: # Originally active but because inactive after satisfaction
                    # Sure hope that tstep + t0 is less than q_t, or something went wrong!
                    #print('length of tau_s: ', len(tau_s))
                    for tstep in range(0, len(tau_s)):
                        
                        if tau_s[tstep] == 1:
                            for child in children:
                                node_dict[child] = dict()
                                node_dict[child]['t0'] = t0 + tstep
                                node_dict[child]['rule_idx'] = rule_idx
                                child_node_list.append(child)
                            break
                                
                    node_dict[node]['status_expl'] = f'Node {node} was already satisfied at t0={t0}, t={t0+tstep}.'
                    print(node_dict[node]['status_expl'])
                    node_dict[node]['short_status_expl'] = f'(s) t0={t0}, t={t0+tstep}.' 
            
            elif tau_v[0] == 1: # The node is violated.
                for child in children:
                    node_dict[child] = dict()
                    node_dict[child]['t0'] = t0
                    node_dict[child]['rule_idx'] = rule_idx
                    child_node_list.append(child)
                    
                node_dict[node]['status_expl'] = f'Node {node} is violated on t0={t0}.' 
                print(node_dict[node]['status_expl'])
                node_dict[node]['short_status_expl'] = f'(v) t0={t0}, t>=t0.'       
                
        # Now set up analysis for next level.
        node_list = child_node_list
        
        query_list = list()
        for node in node_list:
            # node_dict[node]['t0'] already set from before:
            t0 = node_dict[node]['t0']
            rule_idx = node_dict[node]['rule_idx']
            query = get_query(t0, rule_idx, node)
            
            query_list.append(query)

        rule_dicts = get_diagnostic_data(query_list, trace_path)
netTime = time.time() - timeStart
print(netTime)


""" # Begin working down tree depth from level 0
node_records = dict()
level_nodes = list()

# initial node data
for rule_idx in range(0, num_rules):
    node = str(rule_idx)
    level_nodes.append(node)
    
    node_records[node] = dict()
    node_records[node]['rule_idx'] = rule_idx
    node_records[node]['check_from'] = [0] # only t0 = 0
    node_records[node]['parent'] = list()
    node_records[node]['children'] = list()
    # store data for t0 = 0 only at highest level
    node_records[node][0] = dict()
    node_records[node][0]['t0s_of_interest'] = list()
    node_records[node][0]['child_values'] = list()
    
for level_idx in range(0, explanation_depth):
    print('#####################################')
    print('current level: ', level_idx)
    print('#####################################')
    
    query_list = list()

    for node in level_nodes:
        rule_idx = node_records[node]['rule_idx']
        for t0 in node_records[node]['check_from']:
            query = get_query(t0, rule_idx, node)
            query_list.append(query)

    rule_dicts = get_diagnostic_data(query_list, trace_path) 
    
    next_level_nodes = list()        
    
    for node in level_nodes:  
        rule_idx = node_records[node]['rule_idx']
        children = rule_dicts[rule_idx][node]['children']
        parent = rule_dicts[rule_idx][node]['parent']
        node_records[node]['children'] = children     
        node_records[node]['parent'] = parent
        
        for t0 in node_records[node]['check_from']:
            node_records[node][t0] = dict()   
            node_records[node][t0]['t0s_of_interest'] = list()
            node_records[node][t0]['child_values'] = list()
            
            tau_i = rule_dicts[rule_idx][node]['tau_i'][t0]
            
            for tstep in range(0, len(tau_i)-1):
                if (tau_i[tstep] - tau_i[tstep+1])**2 == 1: # change occurred
                    print('t0:', t0, ' tstep: ', tstep)
                    print('tau_i: ', tau_i)
                    node_records[node][t0]['t0s_of_interest'].append(t0+tstep)
                    
                    t0_truth_list = list()
                    t0_plus_1_truth_list = list()
                    
                    for child_node in children:
                        if rule_dicts[rule_idx][child_node]['t0sForTrue'][t0+tstep]:
                            t0_truth_list.append(1)
                        else:
                            t0_truth_list.append(0)
                        if rule_dicts[rule_idx][child_node]['t0sForTrue'][t0+tstep+1]:
                            t0_plus_1_truth_list.append(1)
                        else:
                            t0_plus_1_truth_list.append(0)
                    
                    node_records[node][t0]['child_values'].append([t0_truth_list, t0_plus_1_truth_list])

        # Now need to set up for the next round (level). 
        for child in children:
            next_level_nodes.append(child)
            node_records[child] = dict()
            node_records[child]['rule_idx'] = rule_idx
            node_records[child]['check_from'] = list()
            # If no times of interest passed down, set to t0=0 (?)
            #if len(node_records[node][t0]['t0s_of_interest']) == 0:
            #    node_records[node][t0]['t0s_of_interest'] = [0]
            # If no times of interest passed down, find first t0 in range 
            if len(node_records[node][t0]['t0s_of_interest']) == 0:
                node_records[node][t0]['t0s_of_interest'] = [0]
                
            # update t0 times to check for child node based on parent times of interest
            for t0_int in node_records[node][t0]['t0s_of_interest']:
                if len(node_records[child]['check_from']) != 0:
                    if node_records[child]['check_from'][-1] != t0_int: # prevents doubling (annoying)
                        node_records[child]['check_from'].append(t0_int)
                else: 
                    node_records[child]['check_from'].append(t0_int)
                node_records[child]['check_from'].append(t0_int + 1) 
                
                node_records[child][t0_int] = dict()
                node_records[child][t0_int]['t0s_of_interest'] = list()
                node_records[child][t0_int]['child_values'] = list()
                
            node_records[child]['parent'] = list()
            node_records[child]['children'] = list()

    level_nodes = next_level_nodes

for node in node_records.keys():
    print(node)
    print(node_records[node]) 
    print('###############################')      """
 
#######################################################
# Top level (depth 1)
#######################################################

""" # Generate query at t0=0 each top-level rule
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
    activity_record[rule_idx] = dict()
    activity_record[rule_idx][str(rule_idx)] = dict()
    # For top-level we only care about activity for t0 = 0
    activity_record[rule_idx][str(rule_idx)]['0'] = list()
    # Check for transitions in tau_i
    for tstep in range(0, len(tau_i)-1):
        if (tau_i[tstep] - tau_i[tstep+1])**2 == 1: # change occurred
            activity_record[rule_idx][str(rule_idx)]['0'].append(tstep)
            activity_record[rule_idx][str(rule_idx)]['0'].append(tstep+1)
            
print(activity_record[0]['0']['0'])
print(activity_record[1]['1']['0'])
print(activity_record[2]['2']['0'])
print(activity_record[3]['3']['0'])

# Next, check argument truth at each child node.

child_node_records = dict()
child_node_list = dict()

for rule_idx in range(0,num_rules):
    
    child_node_records[rule_idx] = dict()
    child_node_records[rule_idx][str(rule_idx)] = dict()
    child_nodes_to_check = rule_dicts[rule_idx][str(rule_idx)]['children']
    print(child_nodes_to_check)
    child_node_list[rule_idx] = list()
    child_node_list[rule_idx] = child_nodes_to_check
    
    for node in child_nodes_to_check:
        print('node: ', node)
        child_node_records[rule_idx][str(rule_idx)][node] = dict()
        child_node_records[rule_idx][str(rule_idx)][node]['t0_times_of_interest'] = list()
        child_node_records[rule_idx][str(rule_idx)][node]['t0_times_of_interest'] = activity_record[rule_idx][str(rule_idx)]
        child_node_records[rule_idx][str(rule_idx)][node]['truth_vals_at_t0'] = list()
        
        
        for t0 in activity_record[rule_idx][str(rule_idx)]['0']:
            # Check preceding timestep first
            print('previous: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0-1])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0-1]:
                child_node_records[rule_idx][str(rule_idx)][node].append(1)
            else:
                child_node_records[rule_idx][str(rule_idx)][node].append(0)
            # Check t0 
            print('t0sfortrue: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0]:
                child_node_records[rule_idx][str(rule_idx)][node]['truth_vals_at_t0'].append(1)
            else:
                child_node_records[rule_idx][str(rule_idx)][node]['truth_vals_at_t0'].append(0)

                
print(child_node_records[0]['0'])
print(child_node_records[1]['1'])
print(child_node_records[2]['2'])
print(child_node_records[3]['3'])



def query_t0_generator(node_activity, rule_dicts):
    
    for rule_idx in activity_record:

        pass
    #######################################################
    # Generate query times 
    #######################################################  
    pass
    
     
#######################################################
# Subsequent levels (depth 2+)
#######################################################   

# Previous child nodes become current nodes to check
current_nodes = child_node_list   
     
for depth in range(2, explanation_depth+1):
    print(depth)
    # Determine which nodes we're checking
    
    # Need a loop depending on rule_idx too... sigh
    for rule_idx in activity_record:
        # Update child_node_list every iteration to include the current level nodes only
        for node in current_nodes[rule_idx]:
            node_activity = query_t0_generator(node_activity, rule_dicts)
            activity_record[rule_idx][node] = node_activity
            child_nodes_to_check = rule_dicts[rule_idx][str(rule_idx)]['children']
            child_node_list.append()  

new_queries = list()
            
for rule_idx in range(0,num_rules):
    for node in current_nodes[rule_idx]:
        for t0 in child_node_records[rule_idx][str(rule_idx)][node]['t0_times_of_interest']:
    
            query = dict()
            query['t0*'] = t0
            query['ruleNo'] = rule_idx
            query['node'] = node
            query['t*'] = t0
            new_queries.append(query)
            print('query and node: ', t0, ' ', node)
        # If the list is empty, we query at t0 = 0.
        if len(child_node_records[rule_idx][str(rule_idx)][node]['t0_times_of_interest']) == 0: 
            query = dict()
            query['t0*'] = 0
            query['ruleNo'] = rule_idx
            query['node'] = node
            query['t*'] = 0
            new_queries.append(query)
            print('query and node: ', t0, ' ', node)       
                 
# Expl mode set to 'default'. Allows us to input a query list
expl_specs = {
    "mode" : 'default',
    "query_list" : new_queries
}
    
# Prepare config for function call
config = dict()
config['trace_data_loc'] = trace_data_loc
config['expl_specs'] = expl_specs

_, rule_dicts = re.run_explanation(**config)

# Find activation/deactivation times from rule_dicts for each rule 

for rule_idx in range(0,num_rules):
    for node in current_nodes[rule_idx]:
        for t0 in child_node_records[rule_idx][str(rule_idx)][node]['t0_times_of_interest']:
    
            tau_i = rule_dicts[rule_idx][node]['tau_i'][t0]
            activity_record[rule_idx][node] = list()
            # Check for transitions in tau_i
            for tstep in range(0, len(tau_i)-1):
                if (tau_i[tstep] - tau_i[tstep+1])**2 == 1: # change occurred
                    activity_record[rule_idx][str(rule_idx)].append(tstep)
            
print(activity_record[0]['0'])
print(activity_record[1]['1'])
print(activity_record[2]['2'])
print(activity_record[3]['3'])

# Next, check argument truth at each child node.

child_node_records = dict()
child_node_list = dict()

for rule_idx in range(0,num_rules):
    
    child_node_records[rule_idx] = dict()
    child_node_records[rule_idx][str(rule_idx)] = dict()
    child_nodes_to_check = rule_dicts[rule_idx][str(rule_idx)]['children']
    print(child_nodes_to_check)
    child_node_list[rule_idx] = list()
    child_node_list[rule_idx].append(child_nodes_to_check)
    
    for node in child_nodes_to_check:
        print('node: ', node)
        child_node_records[rule_idx][str(rule_idx)][node] = list()
        for t0 in activity_record[rule_idx][str(rule_idx)]:
            # Check preceding timestep first
            print('previous: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0-1])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0-1]:
                child_node_records[rule_idx][str(rule_idx)][node].append(1)
            else:
                child_node_records[rule_idx][str(rule_idx)][node].append(0)
            # Check t0
            print('t0sfortrue: ', rule_dicts[rule_idx][node]['t0sForTrue'][t0])
            if rule_dicts[rule_idx][node]['t0sForTrue'][t0]:
                child_node_records[rule_idx][str(rule_idx)][node].append(1)
            else:
                child_node_records[rule_idx][str(rule_idx)][node].append(0)
 """