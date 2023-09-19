# Main script for Pointwise-in-Time Rule Status Assessment 
# Brindise and Langbort (2023)

from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

import json
import numpy as np
import matplotlib.pyplot as plt

from modules import ltl_modules as mods
from modules import parse_trees as pt
from modules import populate_tau as oe

def load_json_data(**data_loc):
    # Function to load any data in json file as a dictionary
    base_path = data_loc['base_path']
    filename = data_loc['filename']
    path = Path(base_path,filename)
    with open(path, "r") as f:
        data = json.load(f)
        
    return data        

def run_explanation(**config):
    # Main function for generating diagnostics based on traces and a list of queries.
    #
    # Input: 
    #   config contains two dictionaries:
    #   trace_data_loc : contains 'base_path' and 'filename' paths to json trace data
    #   expl_specs : contains a diagnostic mode 'mode' (either 'default' or 'manual')
    #       if 'manual', expl_specs must also contain entries for 'base_path' and 'filename' to 
    #           a json file with a list of queries
    #       if 'default', expl_specs must contain an entry 'query_list' containing a list of queries 
    #           to evaluate
    #
    # Output: 
    # 
    
    # Parse configuration details
    trace_data_loc = config['trace_data_loc']
    expl_specs = config['expl_specs']
    
    # Load trace data
    trace_data = load_json_data(**trace_data_loc)
    
    # Check which mode is to be used (manual or default)
    expl_mode = expl_specs['mode']
    
    # Load query data depending on mode
    if expl_mode == 'default':
        query_list = expl_specs['query_list']
    else:
        expl_data = load_json_data(**expl_specs)
        query_list = expl_data['query_list']

    # LTL Formula handling (construct trees from strings if necessary)
    formula_trees = trace_data['formula_trees']
    if 'formula_strs' in trace_data:
        formula_strs = trace_data['formula_strs']
    else: 
        formula_strs = []
    trace = trace_data['trace']
    vocab = trace_data['vocab']
    
    # Check if formulas are already expressed as trees:
    if len(formula_trees) == 0:
        formula_trees = []
        
        for formula in formula_strs:
            formula_trees.append(pt.parse_tree(formula))
            
    # number of LTL rules listed
    num_rules = len(formula_trees)        
    
    #################################################################################
    # Timeset Construction (tree structure to extract diagnostics from each rule)
    #################################################################################
    
    def constructTree(node, nodeID, rule_dicts, trace_len, leaf_list, leaf_labels, parent):
        # Recursive function to create empty tree structure 
        # Tree will contain (1) node ID number as string (e.g. "1.2.2"),
        # (2) node type, and (3) empty on/off and tau timesets
        rule_dicts[rule_no][nodeID] = dict()
        
        # Identify/store node type 
        # (Node structure is ['type', arg1, arg2...])
        nodeType = node[0]
        rule_dicts[rule_no][nodeID]['type'] = nodeType
        # Create empty time sets (one for each t_0 in the trace)
        rule_dicts[rule_no][nodeID]['tau_a'] = [[]]*trace_len
        rule_dicts[rule_no][nodeID]['tau_s'] = [[]]*trace_len
        rule_dicts[rule_no][nodeID]['tau_i'] = [[]]*trace_len
        rule_dicts[rule_no][nodeID]['tau_v'] = [[]]*trace_len
        rule_dicts[rule_no][nodeID]['tau*'] = [[]]*trace_len
        # Create empty list to store whether the formula is true for each trace suffix t_0...
        rule_dicts[rule_no][nodeID]['t0sForTrue'] = list()
        # Create entry to store whether node has been instantiated (evaluated) yet or not
        rule_dicts[rule_no][nodeID]['instantiated?'] = False
        # Store node parent and create empty list to store children
        rule_dicts[rule_no][nodeID]['children'] = list()
        rule_dicts[rule_no][nodeID]['parent'] = parent
        
        # Evaluate node 
        #   Identify "leaves" (with labels as formula) and store these in a list
        if nodeType == 'AP':
            leaf_list.append(nodeID)
            atom = node[1][0]
            leaf_labels.append(atom)
            return rule_dicts, leaf_list, leaf_labels
        else:
            #   Num of arguments:
            # (Node structure is ['type', arg1, arg2...])
            noNodes = len(node)-1
            
            #   Loop through each child of current node:
            for childNo in range(0,noNodes):
                child=node[childNo+1]
                childID = f"{nodeID}.{childNo}"
                rule_dicts[rule_no][nodeID]['children'].append(childID)
                rule_dicts, leaf_list, leaf_labels = constructTree(child, childID, rule_dicts, trace_len, leaf_list, leaf_labels, nodeID)
            return rule_dicts, leaf_list, leaf_labels
      
    ########################################################
    # Call constructTree to produce a tree for each rule
    
    # Tree construction
    # Create a dictionary which will contain an entry for each rule
    rule_dicts = [None]*num_rules
    
    trace_len = len(trace)
    full_leaf_list = list()
    full_leaf_labels = list()
    
    # Construct tree for each rule, one at a time
    for rule_no, tree in enumerate(formula_trees):
        rule_dicts[rule_no] = dict()
        
        nodeID = str(rule_no)
        rule_dicts, leaf_list_tree, leaf_labels = constructTree(tree, nodeID, rule_dicts, trace_len, list(), list(), '')
        full_leaf_list.append(leaf_list_tree)
        full_leaf_labels.append(leaf_labels)
        
    ########################################################
    # Populate all "t_0 for true" sets for the empty tree

    # We now have a list of all the leaves, each of which contains a single label.
    # We can evaluate each label on the trace, checking when it is true and when not.
    # This is enough to populate the list of t_0 for which \alpha is true on \rho^t_0...

    # Then, for each node, we can:
    #   Identify the parent node (by truncating the last .x in the current node id). 
    #   Once we get there, we check if all the node's children are already instantiated. 
    #   If yes, 
    #       -call appropriate module to get current node's truth values for each t_0
    #       -move up again (continue to next parent node)
    #   If no,
    #       -continue to next item in leaf list

    # Start with the leaves:
    # Find all times on trace when each label is true.
    num_labels = len(vocab)
    labelIDs = dict()
    
    # Assign a numerical index to each label
    for idx, label in enumerate(vocab):
        labelIDs[label] = idx
    
    # Create list of ALL initial times for which formula holds
    t0sForTrue = np.zeros(shape=(num_labels, trace_len))
    
    for timestep in range(0, trace_len):
        # If label is present at timestep, set to 1:
        for label in trace[timestep]:
            labelidx = labelIDs[label]
            t0sForTrue[labelidx][timestep] = 1
                    
    # We now will build up from the leaves in the trees to the top level, populating as we go.
    # Leaves first:
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            # Find label number corresponding to label name for current leaf
            labelName = full_leaf_labels[tidx][lidx]
            labelNo = labelIDs[labelName]
            
            # Store on/off interval data for leaves
            rule_dicts[tidx][leaf]['t0sForTrue'] = t0sForTrue[labelNo]
            rule_dicts[tidx][leaf]['instantiated?'] = True
            
    # Leaves are finished; time to build up the rest of the tree using modules.
    
    def onTimesNode(tidx, node, rule_dicts, trace):
        # onTimesNode is a function to find when a node's formula is true on \rho^t_0...
        # It accomplishes this by checking the node type and calling the appropriate LTL module.
        # It then updates rule_dicts to contain the instantiated set of times
        argt0Times = []
        for child in rule_dicts[tidx][node]['children']:
            # Check whether any children are still empty...
            # ...in that case, we can't continue yet.
            if not rule_dicts[tidx][child]['instantiated?']:
                return rule_dicts
            else:
                argt0Times.append(rule_dicts[tidx][child]['t0sForTrue'])
         
        # Identify correct module to evaluate with, given node type    
        node_type = rule_dicts[tidx][node]['type']
        module_name = node_type

        if module_name == 'X':
            t0sForTrue = mods.nextX(argt0Times, trace)
        elif module_name == 'F':
           t0sForTrue = mods.futureF(argt0Times, trace)
        elif module_name == 'G':
            t0sForTrue = mods.alwaysG(argt0Times, trace)
        elif module_name == 'neg':
            t0sForTrue = mods.negMod(argt0Times, trace)     
        elif module_name == 'U':
            t0sForTrue = mods.untilU(argt0Times, trace)
        elif module_name == 'W':
            t0sForTrue= mods.weakuntilW(argt0Times, trace)
        elif module_name == 'M':
            t0sForTrue= mods.strongreleaseM(argt0Times, trace)
        elif module_name == 'R':
            t0sForTrue = mods.releaseR(argt0Times, trace)
        elif module_name == 'or':
            t0sForTrue = mods.orMod(argt0Times, trace)
        elif module_name == 'and':
            t0sForTrue= mods.andMod(argt0Times, trace)
        elif module_name == '->':
            t0sForTrue = mods.impl(argt0Times, trace)

        else: 
            print('Invalid LTL formula in tree.')
            return list()
        # Instantiate node t0 truth values from module output and mark as instantiated
        rule_dicts[tidx][node]['t0sForTrue'] = t0sForTrue
        rule_dicts[tidx][node]['instantiated?'] = True
        # Use existing tree structure to identify parent node ID of current module
        nextNodeUp = rule_dicts[tidx][node]['parent']
        # If we have not yet reached the top of the tree (no parent):
        if len(nextNodeUp)>0:
            rule_dicts = onTimesNode(tidx, nextNodeUp, rule_dicts, trace)
        
        return rule_dicts
    
    # Iterate through each leaf in each rule tree
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            
            # Find name of node above (parent node)
            nodeUp = rule_dicts[tidx][leaf]['parent']  
            # Recursively work up the tree (dead-ends when a node isn't fully instantiated)
            rule_dicts = onTimesNode(tidx, nodeUp, rule_dicts, trace)

    #########################################################################
    # Explanation Algorithm ("Rule Status Assessment")
    #########################################################################
            
    # Using this section, it is possible to:
    #   1) pick a node of a rule
    #   2) select a t*_0 and t*
    #   3) receive status information
    
    # Query format: list of dictionaries.
    # Each entry is a dict() containing:
    #   -'ruleNo': number of the rule (int)
    #   -'node': node name (str)
    #   -'t0*': the query initial time (int)
    #   -'t*': the query time (must be >= t0*) (int)
    
    #############################################################################
    # Diagnostics given specific t*,t*_0 pairs and rule arg (from json or input)
    #############################################################################
    # Generate output:
    #   output_list will contain the "verbal" (string) answers to each query concerning
    #       rule status. 
    #   rule_dicts will contain the entire rule trees, including all time sets that have
    #       been instantiated during query evaluation. NOTE: unless all nodes have
    #       been queried at all t_0, there WILL be empty time sets in the tree.
    #       The only way to guarantee an instantiated node is to place a query there.
    output_list = list()

    # Iterate through each query (t*, t*_0, and node) in query_list
    for query in query_list:
        ruleNo = query['ruleNo']
        node = query['node']
        nodeType = rule_dicts[ruleNo][node]['type']
        
        # Bad query handling
        if query['t*'] < 0 or query['t*'] >= len(rule_dicts[0]['0']['t0sForTrue']):
            print('Error: Query time t* not in range.')
            return list()
        if query['t0*'] < 0 or query['t0*'] >= len(rule_dicts[0]['0']['t0sForTrue']):
            print('Error: Query initial time t0* not in range.')
            return list()
        
        module_name = nodeType
        
        # For each query, call populate_taus to populate status time sets as needed (based on t_0 times)
        rule_dicts, expl_output = oe.populate_taus(rule_dicts, module_name, query)
        
        output_list.append(expl_output['t*_status'])

    return output_list, rule_dicts
        

if __name__ == '__main__':
    
    # To use the diagnostic algorithm, several inputs are supported.
    
    # REQUIRED INPUTS
    # 1) trace data: a json containing the following.
    #   {  "id": 0, (an arbitrary trace id integer)
    #      "trace": [[],["label3"],...,["label4","label1"]], (a list rho of lists L_t at each time step. Each label is a string)
    #      "vocab": ["label1", "label2"...], (a list of labels appearing in the trace. Each label is a string)
    #      "formula_trees": [], (a list of nested lists representing each LTL rule to be checked. May be left empty)
    #      "formula_strs": [] (a list of strings representing LTL formulas, for example "(X apple) -> F pear")
    # }
    # 
    #
    # 2) explanation specifications: a json containing the following.
    #   {  
    #      "expl_type" : [type], (type must be either "manual" or "default")
    #      "query_list" :  (a list of dictionaries containing an entry for each query)
    #       [{
    #        "ruleNo" : 0, (which rule to be queried (integer))
    #        "node" : "0.1", (nodeID for the desired node (string "x.x.x"))
    #        "t0*" : 0, (t0 value for query (integer))
    #        "t*" : 2 (t value for query (integer))
    #        }, ...]
    
    experiment_name = 'manual_play'
    explanation_mode = 'manual'
    
    trace_data_location = {
        "base_path" : f'./data/trace_data/{experiment_name}',
        "filename" : 'trace0.json'
        }
    
    # Explanation mode: 'manual', 'default'
    # Manual allows for JSON input of specific queries
    # Default assumes that explanation queries will be entered as part of function call
    # (typically only applicable when this script is NOT run as main)
    
    if explanation_mode == 'default':
        expl_specs = {
            "mode" : 'default',
            "query_list" : list()
        }
    else: 
        expl_specs = {
            "mode" : f'{explanation_mode}',
            "base_path" : f'./data/expl_configs/{experiment_name}',
            "filename" : 'explconfig1.json'
        }
        
    # Set up configs for function call. 
    config = dict()
    config['trace_data_loc'] = trace_data_location
    config['expl_specs'] = expl_specs

    print(run_explanation(**config)[0])