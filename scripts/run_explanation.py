# Script to create explanations 

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
from modules import optimal_expl as oe

def load_scenario_data(**data_loc):
    
    base_path = data_loc['base_path']
    filename = data_loc['filename']
    path = Path(base_path,filename)
    print('path is: ', path)
    
    with open(path, "r") as f:
        data = json.load(f)
        
    return data        

def run_explanation(**config):
    # load data
    trace_data = load_scenario_data(**trace_data_loc)
    expl_data = load_scenario_data(**expl_specs)

    # LTL Formula handling (tree parsing if necessary)
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
            
    num_rules = len(formula_trees)
    
    # Explanation preprocessing
    optimal_expl = False
    manual_expl = False
    
    if 'manual' in expl_data['expl_type']:
        query_list = expl_data['manual_query_list']
        manual_expl = True
        print('Manual expl requested')
    if 'optimal' in  expl_data['expl_type']:
        print('Optimal expl requested')
        optimal_expl = True
        query_times = expl_data['query_times']
        explanation_depth = expl_data['explanation_depth']
    
    #print('Expl type not yet supported, sorry!')
    
    #########################################################################
    # Timeset Construction (Structure from which to extract expls)
    ######################################################################### 
    
    def mineTree(branch, branchNo, rule_dicts, trace_len, leaf_list, leaf_atoms, parent):
        # Function to create empty tree structure 
        # Tree will contain (1) branch number (e.g. "1.2.2"),
        # (2) branch type, and (3) empty on/off and tau timesets
        rule_dicts[rule_no][branchNo] = dict()
        
        # Find/store branch type 
        branchType = branch[0]
        rule_dicts[rule_no][branchNo]['type'] = branchType
        # Create empty timesets
        rule_dicts[rule_no][branchNo]['tau_a'] = [[]]*trace_len
        rule_dicts[rule_no][branchNo]['tau_s'] = [[]]*trace_len
        rule_dicts[rule_no][branchNo]['tau_i'] = [[]]*trace_len
        rule_dicts[rule_no][branchNo]['tau_v'] = [[]]*trace_len
        rule_dicts[rule_no][branchNo]['tau*'] = [[]]*trace_len

        rule_dicts[rule_no][branchNo]['t0sForTrue'] = list()
        rule_dicts[rule_no][branchNo]['instantiated?'] = False
        rule_dicts[rule_no][branchNo]['children'] = list()
        rule_dicts[rule_no][branchNo]['parent'] = parent
        
        # Move on to branch arguments
        #   Handle if we've reached a leaf:
        if branchType == 'AP':
            leaf_list.append(branchNo)
            atom = branch[1][0]
            leaf_atoms.append(atom)
            return rule_dicts, leaf_list, leaf_atoms
        else:
            #   Num of arguments:
            branches = len(branch)-1
            
            #   Loop through each branch of current branch:
            for b in range(0,branches):
                branch_b=branch[b+1]
                branchNo_b = f"{branchNo}.{b}"
                rule_dicts[rule_no][branchNo]['children'].append(branchNo_b)
                rule_dicts, leaf_list, leaf_atoms = mineTree(branch_b, branchNo_b, rule_dicts, trace_len, leaf_list, leaf_atoms, branchNo)
            return rule_dicts, leaf_list, leaf_atoms
      
    # Empty tree production
    rule_dicts = [None]*num_rules
    trace_len = len(trace)
    
    full_leaf_list = list()
    full_leaf_atoms = list()
    
    # Construct tree for each rule, one at a time
    for rule_no, tree in enumerate(formula_trees):
        rule_dicts[rule_no] = dict()
        
        branchNo = str(rule_no)
        rule_dicts, leaf_list_tree, leaf_atoms = mineTree(tree, branchNo, rule_dicts, trace_len, list(), list(), '')
        full_leaf_list.append(leaf_list_tree)
        full_leaf_atoms.append(leaf_atoms)

    # We now have a list of all the leaves. 
    # We can easily go through each of them and assign intervals. 
    # To do this, we can first create entries for every \alpha\in AP and only populate the ones needed
    #   by the leaves (and avoid re-calculating any). 
    # Alternately, the "dumb" option is to just make the intervals for all \alpha\in AP from the start.
    # 
    # Either way, we can easily populate these boolean intervals.
    # Then, for the rest of the tree (branches), we can:
    #   Move up the branch to parent node (by truncating the last .x in the current node number). 
    #   Once we get there, we check if all the node's children are already instantiated. If yes, 
    #       -call appropriate module to get current branch's intervals
    #       -move up again (continue)
    #   If not,
    #       -continue to next item in leaf list

    # Start with the leaves:
    # Find all times on trace when each boolean prop is true.
    num_props = len(vocab)
    propnumlabels = dict()
    
    # Assign a numerical index to each boolean proposition
    for idx, prop in enumerate(vocab):
        propnumlabels[prop] = idx
    
    # Create list of ALL initial times for which formula holds
    t0sForTrue = np.zeros(shape=(num_props, trace_len))
    
    for timestep in range(0, trace_len):
        # If prop on:
        for prop in trace[timestep]:
            propidx = propnumlabels[prop]
            t0sForTrue[propidx][timestep] = 1
                    
    # We now will build up from the leaves in the trees to the top level, populating \tau as we go
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            # Find prop number corresponding to prop name for current leaf
            propName = full_leaf_atoms[tidx][lidx]
            propNo = propnumlabels[propName]
            
            # Store on/off interval data for leaves
            rule_dicts[tidx][leaf]['t0sForTrue'] = t0sForTrue[propNo]
            rule_dicts[tidx][leaf]['instantiated?'] = True
            
    # Leaves are now finished. Time to build up the rest of the tree, incl using modules.
    
    def onTimesBranch(tidx, branch, rule_dicts, trace):
        argt0Times = []
        for child in rule_dicts[tidx][branch]['children']:
            # Check whether any children are still empty...
            # ...in that case, we can't continue yet.
            if not rule_dicts[tidx][child]['instantiated?']:
                return rule_dicts
            else:
                argt0Times.append(rule_dicts[tidx][child]['t0sForTrue'])
                #print('Branch evaluated: ', branch)
                
        branch_type = rule_dicts[tidx][branch]['type']
        
        module_name = branch_type
        print('module name: ', module_name)
        # Send to appropriate module
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

        rule_dicts[tidx][branch]['t0sForTrue'] = t0sForTrue
        rule_dicts[tidx][branch]['instantiated?'] = True
        
        nextBranchUp = rule_dicts[tidx][branch]['parent']
        
        if len(nextBranchUp)>0:
            rule_dicts = onTimesBranch(tidx, nextBranchUp, rule_dicts, trace)
        
        return rule_dicts
    
    # Iterate through each leaf in each rule tree
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            
            # Find name of branch above (parent branch)
            branchUp = rule_dicts[tidx][leaf]['parent']  
            # Recursively work up the tree (dead-ends when a branch isn't fully instantiated)
            rule_dicts = onTimesBranch(tidx, branchUp, rule_dicts, trace)

    #########################################################################
    # Explanation Algorithm ("Activeness Assessment")
    #########################################################################

    for tree in rule_dicts:
        for branch in tree:
            print(branch, ' (type ', tree[branch]['type'],'):')
            print(tree[branch]['t0sForTrue'])
            
    # Start thinking about support for query types here.
    # You will be able to...
    #   1) pick a branch of a rule
    #   2) select a t*_0 and t*
    #   3) receive status information
    
    # Query format: list of dictionaries.
    # Each entry is a dict() containing:
    #   -'ruleNo': number of the rule (int)
    #   -'branch': branch name (str)
    #   -'t0*': the query initial time (int)
    #   -'t*': the query time (must be >= t0*) (int)
    
    optimal_expls_list = list()
    manual_expls_list = list()
    
    ######################################################################
    # Optimal Explanation given individual t*
    ######################################################################
    
    if optimal_expl:
        # We will (at least for now) need to populate ALL status intervals for a given t*, 
        # not just those for individual queries.
        for t_star in query_times:
            optimal_expls_list.append(oe.get_optimal_expl(t_star, rule_dicts, explanation_depth))
                   
        
        pass
    
    #####################################################################
    # Explanation given specific t*,t*_0 pairs and rule arg (from json)
    #####################################################################
    print('query list: ', query_list)
    for rule in rule_dicts:
        print('rule branches:', rule.keys())

    
    for query in query_list:
        ruleNo = query['ruleNo']
        branch = query['branch']
        branchType = rule_dicts[ruleNo][branch]['type']
        
        # Bad query handling
        if query['t*'] < 0 or query['t*'] >= len(rule_dicts[0]['0']['t0sForTrue']):
            print('Error: Query time t* not in range.')
            return list()
        if query['t0*'] < 0 or query['t0*'] >= len(rule_dicts[0]['0']['t0sForTrue']):
            print('Error: Query initial time t0* not in range.')
            return list()
        
        module_name = branchType
        
        rule_dicts, expl_output = oe.populate_taus(rule_dicts, module_name, query)
        
        manual_expls_list.append(expl_output['t*_status'])
    return manual_expls_list, optimal_expls_list
        

if __name__ == '__main__':
    
    experiment_name = 'manual_play'
    
    trace_data_loc = {
        "base_path" : f'./data/trace_data/{experiment_name}',
        "filename" : 'trace0.json'
        }
    
    # Expl types: 'manual', 'interactive' (not yet supported), 'optimal'
    expl_specs = {
        "base_path" : f'./data/expl_configs/{experiment_name}',
        "filename" : 'explconfig1.json'
    }
        
    config = dict()
    config['trace_data_loc'] = trace_data_loc
    config['expl_specs'] = expl_specs
    print(run_explanation(**config))