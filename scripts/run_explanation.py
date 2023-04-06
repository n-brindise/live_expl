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


def send_to_module(formtype, trace, onTimes, offTimes):
    module_name = formtype
    
    # onTimes and offTimes will always be structured as follows:
    #   -One entry per argument of the formula to be checked.
    #   -Each entry is a list of switch-on-times for that argument (branch)
    #       (Reminder: a time being "on" correponds to a t_0 for which the trace 
    #        pi^{t_0...} satisfies the formula)
    
    # e.g. example for formula phi1 OR phi2 OR phi3:
    # ontimesExample = [[0, 5, 7], 
    #                   [],  # Entries may be empty if formula is never satisfied!
    #                   [6]]
    
    # e.g. example for formula F phi1:    
    # ontimesExample2 = [[6, 11]]
    
    
    # Modules should return the following:
    #   (1) onTimes and offTimes
    #   (2) the four tau timesets
    #   (3) the timeset of interest tau*
    
    if module_name == 'X':
        return mods.nextX(onTimes, offTimes, trace)
    elif module_name == 'F':
        return mods.futureF(onTimes, offTimes, trace)
    elif module_name == 'G':
        return mods.alwaysG(onTimes, offTimes, trace)
    elif module_name == 'U':
        return mods.untilU(onTimes, offTimes, trace)
    elif module_name == 'W':
        return mods.weakuntilW(onTimes, offTimes, trace)
    elif module_name == 'M':
        return mods.strongreleaseM(onTimes, offTimes, trace)
    elif module_name == 'R':
        return mods.releaseR(onTimes, offTimes, trace)
    elif module_name == 'AP':
        return mods.atomprepAP(onTimes, offTimes, trace)
    elif module_name == 'or':
        return mods.orMod(onTimes, offTimes, trace)
    elif module_name == 'and':
        return mods.andMod(onTimes, offTimes, trace)
    elif module_name == 'impl':
        return mods.impl(onTimes, offTimes, trace)
    elif module_name == 'not':
        return mods.negMod(onTimes, offTimes, trace)
    else: 
        print('Invalid LTL formula in tree.')
        return list()
        

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
    print('numrules: ', num_rules)
    print(formula_trees)
    
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
        #rule_dicts[rule_no][branchNo]['tau_a'] = [list()]*trace_len
        #rule_dicts[rule_no][branchNo]['tau_s'] = [list()]*trace_len
        #rule_dicts[rule_no][branchNo]['tau_i'] = [list()]*trace_len
        #rule_dicts[rule_no][branchNo]['tau_v'] = [list()]*trace_len
        #rule_dicts[rule_no][branchNo]['tau*'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['onTimes'] = list()
        rule_dicts[rule_no][branchNo]['offTimes'] = list()
        rule_dicts[rule_no][branchNo]['t0sForTrue'] = list()
        rule_dicts[rule_no][branchNo]['instantiated?'] = False
        rule_dicts[rule_no][branchNo]['children'] = list()
        rule_dicts[rule_no][branchNo]['parent'] = parent
        
        # Move on to branch arguments
        #   Handle if we've reached a leaf:
        if branchType == 'AP':
            leaf_list.append(branchNo)
            atom = branch[1][0]
            print('atom: ', atom)
            leaf_atoms.append(atom)
            print('branchNo: ', branchNo)
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
    print('full_leaf_list: ', full_leaf_list)
    print('full_leaf_atoms: ', full_leaf_atoms)
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
    
    # Find on/off times for boolean propositions in trace
    num_props = len(vocab)
    propnumlabels = dict()
    
    for idx, prop in enumerate(vocab):
        propnumlabels[prop] = idx
    
    # Create lists of JUST transitional times
    onFlags = [False]*num_props
    onTimes = [[] for x in range (num_props)]
    offTimes = [[] for x in range (num_props)]
    
    # Create list of ALL initial times for which formula holds
    t0sForTrue = np.zeros(shape=(num_props, trace_len))
    
    for timestep in range(0, trace_len):
        for prop in trace[timestep]:
            propidx = propnumlabels[prop]
            t0sForTrue[propidx][timestep] = 1
            
            if not onFlags[propidx]:
                onFlags[propidx] = True
                onTimes[propidx].append(timestep)
            
            if timestep + 1 < trace_len:
                if prop not in trace[timestep+1]:
                    offTimes[propidx].append(timestep+1)
                    onFlags[propidx] = False
                    

    print('onTimes: ', onTimes)               
    print('offTimes: ', offTimes)
    print('t0sForTrue: ', t0sForTrue)
    # We now will build up from the leaves in the trees to the top level, populating \tau as we go
            
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            #print(f'tree {tidx} leaf: {leaf}')
            # Find prop number corresponding to prop name for current leaf
            propName = full_leaf_atoms[tidx][lidx]
            #print('propName: ', propName)
            propNo = propnumlabels[propName]
            
            # Store on/off interval data for leaves
            rule_dicts[tidx][leaf]['onTimes'] = onTimes[propNo]
            rule_dicts[tidx][leaf]['offTimes'] = offTimes[propNo]
            rule_dicts[tidx][leaf]['t0sForTrue'] = t0sForTrue[propNo]
            rule_dicts[tidx][leaf]['instantiated?'] = True
            
    # Leaves are now finished. Time to build up the rest of the tree, incl using modules.
    
    def onOffTimesBranch(tidx, branch, rule_dicts, trace):
        
        argOnTimes = []
        argOffTimes = []
        argt0Times = []
        for child in rule_dicts[tidx][branch]['children']:
            # Check whether any children are still empty...
            # ...in that case, we can't continue yet.
            if not rule_dicts[tidx][child]['instantiated?']:
                return rule_dicts
            else:
                argOnTimes.append(rule_dicts[tidx][child]['onTimes'])
                argOffTimes.append(rule_dicts[tidx][child]['offTimes'])
                argt0Times.append(rule_dicts[tidx][child]['t0sForTrue'])
                print('Branch evaluated: ', branch)
                
        branch_type = rule_dicts[tidx][branch]['type']
        
        module_name = branch_type
        print('module name: ', module_name)
        # Send to appropriate module
        if module_name == 'X':
            onTimes, offTimes, t0sForTrue = mods.nextX(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'F':
            onTimes, offTimes, t0sForTrue = mods.futureF(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'G':
            onTimes, offTimes, t0sForTrue = mods.alwaysG(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'neg':
            onTimes, offTimes, t0sForTrue = mods.negMod(argOnTimes, argOffTimes, argt0Times, trace)        
        elif module_name == 'U':
            onTimes, offTimes, t0sForTrue = mods.untilU(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'W':
            onTimes, offTimes, t0sForTrue = mods.weakuntilW(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'M':
            onTimes, offTimes, t0sForTrue = mods.strongreleaseM(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'R':
            onTimes, offTimes, t0sForTrue = mods.releaseR(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'or':
            onTimes, offTimes, t0sForTrue = mods.orMod(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == 'and':
            onTimes, offTimes, t0sForTrue = mods.andMod(argOnTimes, argOffTimes, argt0Times, trace)
        elif module_name == '->':
            onTimes, offTimes, t0sForTrue = mods.impl(argOnTimes, argOffTimes, argt0Times, trace)

        else: 
            print('Invalid LTL formula in tree.')
            return list()
              
        rule_dicts[tidx][branch]['onTimes'] = onTimes
        rule_dicts[tidx][branch]['offTimes'] = offTimes   
        rule_dicts[tidx][branch]['t0sForTrue'] = t0sForTrue
        rule_dicts[tidx][branch]['instantiated?'] = True
        
        nextBranchUp = rule_dicts[tidx][branch]['parent']
        
        if len(nextBranchUp)>0:
            rule_dicts = onOffTimesBranch(tidx, nextBranchUp, rule_dicts, trace)
        
        return rule_dicts
    
    for tidx, tree in enumerate(full_leaf_list):
        for lidx, leaf in enumerate(tree):
            
            # Find name of branch above (parent branch)
            branchUp = rule_dicts[tidx][leaf]['parent']  
            # Recursively work up the tree (dead-ends when a branch isn't fully instantiated)
            rule_dicts = onOffTimesBranch(tidx, branchUp, rule_dicts, trace)

    #########################################################################
    # Explanation Algorithm ("Activeness Assessment")
    #########################################################################
    #print(emptyTree)
    for tree in rule_dicts:
        for branch in tree:
            print(branch, ' (type ', tree[branch]['type'],'):')
            print(tree[branch]['t0sForTrue'])
        

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