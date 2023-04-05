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
    
    def mineTree(branch, branchNo, rule_dicts, trace_len, leaf_list):
        # Function to create empty tree structure 
        # Tree will contain (1) branch number (e.g. "1.2.2"),
        # (2) branch type, and (3) empty on/off and tau timesets
        rule_dicts[rule_no][branchNo] = dict()
        
        # Find/store branch type 
        branchType = branch[0]
        #print('branchType: ', branchType)
        rule_dicts[rule_no][branchNo]['type'] = branchType
        # Create empty timesets
        rule_dicts[rule_no][branchNo]['tau_a'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['tau_s'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['tau_i'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['tau_v'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['tau*'] = [list()]*trace_len
        rule_dicts[rule_no][branchNo]['onTimes'] = list()
        rule_dicts[rule_no][branchNo]['offTimes'] = list()
        
        # Move on to branch arguments
        #   Handle if we've reached a leaf:
        if branchType == 'AP':
            leaf_list.append(branchNo)
            print('branchNo: ', branchNo)
            print('leaf_list now: ', leaf_list)
            return rule_dicts, leaf_list
        else:
            #   Num of arguments:
            branches = len(branch)-1
            
            #   Loop through each branch of current branch:
            for b in range(0,branches):
                branch_b=branch[b+1]
                branchNo_b = f"{branchNo}.{b}"
                rule_dicts, leaf_list = mineTree(branch_b, branchNo_b, rule_dicts, trace_len, leaf_list)
            return rule_dicts, leaf_list
      
    rule_dicts = [None]*num_rules
    trace_len = len(trace)
    
    full_leaf_list = list()
    for rule_no, tree in enumerate(formula_trees):
        rule_dicts[rule_no] = dict()
        
        branchNo = str(rule_no)
        emptyTree, leaf_list_tree = mineTree(tree, branchNo, rule_dicts, trace_len, list())
        print('leaf_list_tree: ', leaf_list_tree)
        full_leaf_list.append(leaf_list_tree)
        
   
    print('full_leaf_list: ', full_leaf_list)
    
    # We now have a list of all the leaves. 
    # We can easily go through each of them and assign intervals. 
    # To do this, we can first create entries for every \alpha\in AP and only populate the ones needed
    #   by the leaves (and avoid re-calculating any). 
    # Alternately, the "dumb" option is to just make the intervals for all \alpha\in AP from the start.
    # 
    # Either way, we can easily populate these boolean intervals. The question is what to do after that.
    # 

    #########################################################################
    # Explanation Algorithm ("Activeness Assessment")
    #########################################################################
    #print(emptyTree)


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