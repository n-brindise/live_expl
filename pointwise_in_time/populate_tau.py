from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"pointwise_in_time").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

###############################################################################################
# %% #
from pathlib import Path
import numpy as np
import pointwise_in_time.run_explanation as run_expl
import pointwise_in_time.ltl_modules as mods

# Optimal Explanation: (Under Construction)

def get_optimal_expl(t_star, rule_dicts, expl_depth):
    
    for ruleNo in rule_dicts:
        for node in rule_dicts[ruleNo]:

            query_node = dict()
            query_node['ruleNo'] = ruleNo
            query_node['node'] = node
            query_node['t*'] = t_star
    
            nodeType = rule_dicts[ruleNo][node]['type']
            module_name = nodeType
            
            rule_dicts, expl_output = populate_taus(rule_dicts, module_name, query_node)
            
    # Now we'll have all the taus for t* populated in rule_dicts.
    # From here, we can analyze those taus and select/order the optimal t*_0s.
            
            

def populate_taus(rule_dicts, module_name, query):
    
    #print('module name: ', module_name)
    # Send to appropriate module
    if module_name == 'X':
        expl_output = mods.nextXquery(query, rule_dicts)
    elif module_name == 'F':
        expl_output = mods.futureFquery(query, rule_dicts)
    elif module_name == 'G':
        expl_output = mods.alwaysGquery(query, rule_dicts)
    elif module_name == 'neg':
        expl_output = mods.negModquery(query, rule_dicts)     
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
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    rule_dicts[ruleNo][node]['tau_a'][t0_query] = expl_output['tau_a']
    rule_dicts[ruleNo][node]['tau_s'][t0_query] = expl_output['tau_s']
    rule_dicts[ruleNo][node]['tau_i'][t0_query] = expl_output['tau_i']
    rule_dicts[ruleNo][node]['tau_v'][t0_query] = expl_output['tau_v'] 
    
    return rule_dicts, expl_output

if __name__ == '__main__': 
    
    tstar = 5
    