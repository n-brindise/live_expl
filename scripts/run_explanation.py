# Script to create explanations 

from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())


from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

from modules import ltl_modules as mods
from modules import parse_trees as pt

def load_scenario_data(**data_loc):
    
    base_path = data_loc['base_path']
    filename = data_loc['filename']
    path = Path(base_path,filename)
    print('path is: ', path)
    
    with open(path, "r") as f:
        data = json.load(f)
        
    return data        

def run_explanation(**expl_config):
    # load data
    scen_data = load_scenario_data(**data_loc)

    formula_trees = scen_data['formula_trees']
    formula_strs = scen_data['formula_strs']
    
    trace = scen_data['trace']
    vocab = scen_data['vocab']
    
    # Check if formulas are already expressed as trees:
    if len(formula_trees) == 0:
        formula_trees = []
        # Not yet functional
        for formula in formula_strs:
            formula_trees.append(pt.parse_tree(formula))
            
    num_rules = len(formula_trees)
    #print('numrules: ', num_rules)
    #print(formula_trees)
    
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
        #print('branchType: ', branchType)
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
            #print('atom: ', atom)
            leaf_atoms.append(atom)
            #print('branchNo: ', branchNo)
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
      
    rule_dicts = [None]*num_rules
    trace_len = len(trace)
    
    full_leaf_list = list()
    full_leaf_atoms = list()
    
    for rule_no, tree in enumerate(formula_trees):
        rule_dicts[rule_no] = dict()
        
        branchNo = str(rule_no)
        rule_dicts, leaf_list_tree, leaf_atoms = mineTree(tree, branchNo, rule_dicts, trace_len, list(), list(), '')
        full_leaf_list.append(leaf_list_tree)
        full_leaf_atoms.append(leaf_atoms)
    #print('full_leaf_list: ', full_leaf_list)
    #print('full_leaf_atoms: ', full_leaf_atoms)
    # We now have a list of all the leaves. 
    # We can easily go through each of them and assign intervals. 
    # To do this, we can first create entries for every \alpha\in AP and only populate the ones needed
    #   by the leaves (and avoid re-calculating any). 
    # Alternately, the "dumb" option is to just make the intervals for all \alpha\in AP from the start.
    # 
    # Either way, we can easily populate these boolean intervals. The question is what to do after that.
    # Each leaf has an associated branch number. We can:
    #   Move up the branch (by truncating the last .x in the branch number). 
    #   Once we get there, we check if the branch is fully "informed". If yes, 
    #       -call appropriate module to get current branch's intervals
    #       -move up again (continue)
    #   If not,
    #       -continue to next item in leaf list
    
    # For now, we'll do this the dumb way, and produce info for all alpha in AP.
    
    # Find on-times for boolean propositions in trace
    num_props = len(vocab)
    propnumlabels = dict()
    
    for idx, prop in enumerate(vocab):
        propnumlabels[prop] = idx
    
    # Create list of ALL initial times for which formula holds
    t0sForTrue = np.zeros(shape=(num_props, trace_len))
    
    for timestep in range(0, trace_len):
        # If prop on:
        for prop in trace[timestep]:
            propidx = propnumlabels[prop]
            t0sForTrue[propidx][timestep] = 1
                    
    #print('t0sForTrue: ', t0sForTrue)
    # We now will build up from the leaves in the trees to the top level, populating \tau as we go
            
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            #print(f'tree {tidx} leaf: {leaf}')
            # Find prop number corresponding to prop name for current leaf
            propName = full_leaf_atoms[tidx][lidx]
            #print('propName: ', propName)
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
    # We still need to implement timesets of interest (and timesets in general).
    
    # Query format: list of dictionaries.
    # Each entry is a dict() containing:
    #   -'ruleNo': number of the rule (int)
    #   -'branch': branch name (str)
    #   -'t0*': the query initial time (int)
    #   -'t*': the query time (must be >= t0*) (int)
    
    queryList = []
    
    query1 = dict()
    query1['ruleNo'] = 2
    query1['branch'] = '2.0.1'
    query1['t0*'] = 3
    query1['t*'] = 3
    queryList.append(query1)
    
    query1 = dict()
    query1['ruleNo'] = 2
    query1['branch'] = '2.0.1'
    query1['t0*'] = 3
    query1['t*'] = 4
    queryList.append(query1)
    
    query1 = dict()
    query1['ruleNo'] = 2
    query1['branch'] = '2.0.1'
    query1['t0*'] = 0
    query1['t*'] = 3
    queryList.append(query1)
    
    for query in queryList:
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
        #print('module name: ', module_name)
        # Send to appropriate module
        if module_name == 'X':
            expl_output = mods.nextXquery(query, rule_dicts)
        elif module_name == 'F':
            expl_output = mods.futureFquery(query, rule_dicts)
        elif module_name == 'G':
            expl_output = mods.alwaysGquery(query, rule_dicts)
        elif module_name == 'neg':
            expl_output = mods.negModquery(query, trace)     
        elif module_name == 'U':
            expl_output = mods.untilUquery(query, rule_dicts)
        elif module_name == 'W':
            expl_output = mods.weakuntilWquery(query, rule_dicts)
        elif module_name == 'M':
            expl_output = mods.strongreleaseMquery(query, rule_dicts)
        elif module_name == 'R':
            expl_output = mods.releaseRquery(query, rule_dicts)
        elif module_name == 'or':
            expl_output = mods.orModquery(query, rule_dicts)
        elif module_name == 'and':
            expl_output = mods.andModquery(query, rule_dicts)
        elif module_name == '->':
            expl_output = mods.implquery(query, rule_dicts)
        elif module_name == 'AP':
            expl_output = mods.APquery(query, rule_dicts)

        else: 
            print('Invalid LTL formula in tree.')
            return list()      
        
        t0_query = query['t0*']
        rule_dicts[ruleNo][branch]['tau_a'][t0_query] = expl_output['tau_a']
        rule_dicts[ruleNo][branch]['tau_s'][t0_query] = expl_output['tau_s']
        rule_dicts[ruleNo][branch]['tau_i'][t0_query] = expl_output['tau_i']
        rule_dicts[ruleNo][branch]['tau_v'][t0_query] = expl_output['tau_v'] 
        
        explanation_text = expl_output['t*_status']
        print(explanation_text)
        

if __name__ == '__main__':
    
    data_loc = {
        "base_path" : './data/trace_data',
        "filename" : 'trace1.json'
        }
    
    # Expl types: 'manual', 'custom'
    expl_specs = {
        "expl_type" : 'manual',
        "base_path" : './data/expl_configs',
        "filename" : 'explconfig1.json'
    }
        
    expl_config = dict()
    expl_config['data_loc'] = data_loc
    expl_config['expl_specs'] = expl_specs
    print(run_explanation(**expl_config))