from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"pointwise_in_time").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np
#import pointwise_in_time.run_explanation as run_expl
import run_explanation as run_expl

###############################################################################
# Initial tree evaluation modules (t0 assessments)
###############################################################################
# These modules calculate whether a formula is true on the trace suffix starting 
# at each t_0. These truth values (1: formula true at t_0 or 0: formula not true) 
# are then stored in the variable 't0s' at t_0 = timestep.
#
# This evaluation is based on the truth values of the formula argument(s) at each t0.
# In the formal module description, 
#   (argument true at t0) <==> (argument's tau^v @ t0 == empty)
#   (argument false at t0) <==> (argument's tau^v @ t0 == nonempty)
# so this approach is equivalent to the approach specified in the modules. 

def nextX(t0times, trace):
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    
    for timestep in range(0,trace_len-1):
        
        # Use formula for "next"
        if t0times[0][timestep+1] == 1:
            t0s[timestep] = 1
            
    return t0s


def futureF(t0times, trace):

    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    #print('t0times[0]: ', t0times[0])
    
    for timestep in range(0,trace_len):
        
        # Use formula for "eventually"
        if np.sum(t0times[0][timestep:None] >= 1):
            t0s[timestep] = 1

    return t0s
    
def alwaysG(t0times, trace):
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    
    for timestep in range(0,trace_len):
        
        # Use formula for "always"
        if np.sum(t0times[0][timestep:None]) == trace_len-timestep:
            t0s[timestep:None] = np.ones(trace_len-timestep)
            
            break 
        
    return t0s

def untilU(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    # Want to check if arg1 holds up to the min time that arg2 
    # starts holding (within our range set by t0)
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)
                
    return t0s

def weakuntilW(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]               
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "weak until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 

    return t0s

def strongreleaseM(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "strong release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)     

    return t0s


def releaseR(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)

    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 

    return t0s
    
def orMod(t0times, trace):
    t0s = np.zeros(len(trace))
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] > 0:
            t0s[timestep] = 1
        
    return t0s

def andMod(t0times, trace):
    t0s = np.zeros(len(trace))
    noArgs = len(t0times)
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] == noArgs:
            t0s[timestep] = 1

    return t0s

def negMod(t0times, trace):
    t0s = np.ones(len(trace)) - t0times[0]
    
    return t0s

def impl(t0times, trace):
    t0s = np.ones(len(trace))
    
    for timestep in range(0,len(trace)):
        if t0times[0][timestep] == 1 and t0times[1][timestep] == 0:
            t0s[timestep] = 0
        
    return t0s


###############################################################################
# Query modules (tau assessments)
###############################################################################
# In the interest of efficiency, tau time sets are not populated during initial
# tree population as specified in the formal algorithm description. Instead,
# these time sets are populated on-demand; however, they are stored after population 
# and reused if necessary.

# In this iteration, our tau star heuristics are not yet implemented.

def evaluateTStar(t_star, tau_a, tau_s, tau_i, tau_v):

    if tau_s[t_star] == 1:
        return 'satisfied'
    elif tau_a[t_star] == 1:
        return 'active'
    elif tau_i[t_star] == 1:
        return 'inactive'
    elif tau_v[t_star] == 1:
        return 'violated'
    else:
        return 'INDETERMINATE (check input)'

def nextXquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.ones(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len-1):
            # Use formula for "next"
            if t0sArg1[timestep+1] == 1:
                tau_a[0]=1
                tau_a[1]=1
                tau_s[1]=1
                if not timestep == trace_len - 2:
                    tau_i[2:None] = np.ones(trace_len - (timestep+2))
                tau_v = np.zeros(trace_len - timestep)
                break
            
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out


def futureFquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.ones(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len):
            # Use formula for "next"
            if t0sArg1[timestep] == 1:
                tau_a[0:timestep-t0_star +1]=np.ones(timestep-t0_star+1)
                tau_s[timestep-t0_star]=1
                if timestep+1 < trace_len:
                    tau_i[(timestep+1)-t0_star:None] = np.ones(trace_len-(timestep+1))
                tau_v = np.zeros(trace_len - t0_star)
                break
            
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out
    
def alwaysGquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   

        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.ones(trace_len - t0_star)
         
        if np.sum(t0sArg1[t0_star:None]) == trace_len - t0_star:
            tau_a = np.ones(trace_len - t0_star)
            tau_s[-1]=1
            tau_v = np.zeros(trace_len - t0_star) 
            
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def untilUquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        arg2 = children[1]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
        t0sArg2 = rule_dicts[ruleNo][arg2]['t0sForTrue'] 
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len):
            # Use formula for "until"
            if t0sArg1[timestep] == 1:
                tau_a[timestep-t0_star] = 1
                if t0sArg2[timestep] ==1:
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep-t0_star+1:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg2 doesn't hold at t0=timestep
                    # For Until, we must have arg2 be satisfied eventually...
                    # ...so we fail the trace if it never is.
                    if timestep + 1 == trace_len:
                        tau_a = np.zeros(trace_len - t0_star)
                        tau_s = np.zeros(trace_len - t0_star)
                        tau_i = np.zeros(trace_len - t0_star)
                        tau_v = np.ones(trace_len - t0_star)
                        break
            else: # arg1 doesn't hold at t0 = timestep
                if t0sArg2[timestep] ==1: # UNTIL: if arg2 holds...
                    tau_a[timestep-t0_star] = 1
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep+1-t0_star:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg1 gave up without arg2 stepping in
                    tau_a = np.zeros(trace_len - t0_star)
                    tau_s = np.zeros(trace_len - t0_star)
                    tau_i = np.zeros(trace_len - t0_star)
                    tau_v = np.ones(trace_len - t0_star)   
                    break                             
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def weakuntilWquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        arg2 = children[1]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
        t0sArg2 = rule_dicts[ruleNo][arg2]['t0sForTrue'] 
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len):
            # Use formula for "next"
            if t0sArg1[timestep] == 1:
                tau_a[timestep-t0_star] = 1
                if t0sArg2[timestep] ==1:
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep-t0_star:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg2 doesn't hold at t0=timestep
                    # For Weak Until, we don't need to have arg2 be satisfied eventually...
                    # ...so we pass the trace if it reaches the end with only arg1.
                    if timestep + 1 == trace_len:
                        tau_a = np.ones(trace_len - t0_star)
                        tau_s[-1] = 1
                        tau_i = np.zeros(trace_len - t0_star)
                        break
            else: # arg1 doesn't hold at t0 = timestep
                if t0sArg2[timestep] ==1: # UNTIL: if arg2 holds...
                    tau_a[timestep-t0_star] = 1
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep+1-t0_star:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg1 gave up without arg2 stepping in
                    tau_a = np.zeros(trace_len - t0_star)
                    tau_s = np.zeros(trace_len - t0_star)
                    tau_i = np.zeros(trace_len - t0_star)
                    tau_v = np.ones(trace_len - t0_star)   
                    break                             
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def strongreleaseMquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        arg2 = children[1]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
        t0sArg2 = rule_dicts[ruleNo][arg2]['t0sForTrue'] 
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len):
            # Use formula for "next"
            if t0sArg1[timestep] == 1:
                tau_a[timestep-t0_star] = 1
                if t0sArg2[timestep] ==1:
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep+1-t0_star:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg2 doesn't hold at t0=timestep
                    # For Strong Release, we must have arg2 be satisfied eventually...
                    # ...so we fail the trace if it never is.
                    if timestep + 1 == trace_len:
                        tau_a = np.zeros(trace_len - t0_star)
                        tau_s = np.zeros(trace_len - t0_star)
                        tau_i = np.zeros(trace_len - t0_star)
                        tau_v = np.ones(trace_len - t0_star)
                        break
            else: # arg1 doesn't hold at t0 = timestep
                # arg1 gave up without arg2 stepping in
                tau_a = np.zeros(trace_len - t0_star)
                tau_s = np.zeros(trace_len - t0_star)
                tau_i = np.zeros(trace_len - t0_star)
                tau_v = np.ones(trace_len - t0_star)   
                break                             
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out


def releaseRquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else:
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        children = rule_dicts[ruleNo][node]['children']
        arg1 = children[0]
        arg2 = children[1]
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue']   
        t0sArg2 = rule_dicts[ruleNo][arg2]['t0sForTrue'] 
    
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.zeros(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star) 
    
        for timestep in range(t0_star,trace_len):
            # Use formula for "next"
            if t0sArg1[timestep] == 1:
                tau_a[timestep-t0_star] = 1
                if t0sArg2[timestep] ==1:
                    tau_s[timestep-t0_star] = 1
                    if timestep + 1 < trace_len:
                        tau_i[timestep+1-t0_star:None] = np.ones(trace_len - (timestep+1))
                    break
                else: # arg2 doesn't hold at t0=timestep
                    # For Release, we don't need arg2 true if arg1 holds the whole time.
                    if timestep + 1 == trace_len:
                        tau_a = np.ones(trace_len - t0_star)
                        tau_s[-1] = 1                     
                        break
            else: # arg1 doesn't hold at t0 = timestep
                # arg1 gave up without arg2 stepping in
                tau_a = np.zeros(trace_len - t0_star)
                tau_s = np.zeros(trace_len - t0_star)
                tau_i = np.zeros(trace_len - t0_star)
                tau_v = np.ones(trace_len - t0_star)   
                break                             
        # Store results

        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out
    
def orModquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else: 
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.ones(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star)
        disjunctTrue = False
        
        children = rule_dicts[ruleNo][node]['children']
        
        for argidx, arg in enumerate(children):
            t0sArg = rule_dicts[ruleNo][arg]['t0sForTrue']  
            # If a single argument holds, then OR is satisfied:
            if t0sArg[t0_star] == 1:
                tau_a[0] = 1
                tau_s[0] = 1
                tau_i[0] = 0
                disjunctTrue = True
                break
        # If none of the arguments were true:
        if not disjunctTrue:
            tau_i = np.zeros(trace_len - t0_star)
            tau_v = np.ones(trace_len - t0_star)
                                       
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def andModquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else: 
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.ones(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star)
        
        tau_a[0] = 1
        tau_s[0] = 1
        tau_i[0] = 0
        
        
        children = rule_dicts[ruleNo][node]['children']
        
        for argidx, arg in enumerate(children):
            t0sArg = rule_dicts[ruleNo][arg]['t0sForTrue']  
            # If a single argument is false, then AND is violated:
            if t0sArg[t0_star] == 0:
                tau_a = np.zeros(trace_len - t0_star)
                tau_s = np.zeros(trace_len - t0_star)
                tau_i = np.zeros(trace_len - t0_star)
                tau_v = np.ones(trace_len - t0_star)
                break
                      
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def negModquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else: 
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue']) 
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.ones(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star)
        
        arg1 = rule_dicts[ruleNo][node]['children'][0]        
        
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue'] 
        
        if t0sArg1[t0_star] == 0:
            tau_a[0] = 1
            tau_s[0] = 1
            tau_i[0] = 0
        else:
            tau_i = np.zeros(trace_len - t0_star)
            tau_v = np.ones(trace_len - t0_star)
                                       
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def implquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else: 
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue'])
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.ones(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star)
              
        arg1 = rule_dicts[ruleNo][node]['children'][0]        
        arg2 = rule_dicts[ruleNo][node]['children'][1]
        
        t0sArg1 = rule_dicts[ruleNo][arg1]['t0sForTrue'] 
        t0sArg2= rule_dicts[ruleNo][arg2]['t0sForTrue'] 
        
        # If implication is violated:
        if t0sArg1[t0_star] == 1 and t0sArg2[t0_star] == 0:
            tau_v = np.ones(trace_len - t0_star)
            tau_i = np.zeros(trace_len - t0_star)
        elif t0sArg1[t0_star] == 1 and t0sArg2[t0_star] == 1:
            tau_a[0] = 1
            tau_s[0] = 1
            tau_i[0] = 0            
        else:
            tau_a[0] = 0
            tau_s[0] = 0
            tau_i[0] = 1
                                       
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out

def APquery(query, rule_dicts):
    
    ruleNo = query['ruleNo'] 
    node = query['node'] 
    t0_star = query['t0*'] 
    t_star = query['t*'] 
    
    # Check if we already have these tau intervals stored.
    # If so, just evaluate for t* and return.
    if len(rule_dicts[ruleNo][node]['tau_a'][t0_star])>0:
        tau_a = rule_dicts[ruleNo][node]['tau_a'][t0_star]
        tau_s = rule_dicts[ruleNo][node]['tau_s'][t0_star]
        tau_i = rule_dicts[ruleNo][node]['tau_i'][t0_star]
        tau_v = rule_dicts[ruleNo][node]['tau_v'][t0_star]
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)
    else: 
        trace_len = len(rule_dicts[ruleNo][node]['t0sForTrue']) 
        tau_a = np.zeros(trace_len - t0_star)
        tau_s = np.zeros(trace_len - t0_star)
        tau_i = np.ones(trace_len - t0_star)
        tau_v = np.zeros(trace_len - t0_star)     
        
        t0s = rule_dicts[ruleNo][node]['t0sForTrue'] 
        
        if t0s[t0_star] == 0:
            tau_v = np.ones(trace_len - t0_star)
            tau_i = np.zeros(trace_len - t0_star)
        else:
            tau_a[0] = 1
            tau_s[0] = 1
            tau_i[0] = 0
                                       
        # Store results
        status = evaluateTStar(t_star-t0_star, tau_a, tau_s, tau_i, tau_v)

    tau_star = []
    curr_rule_name = query['node']
    t_star_status=f'Rule {curr_rule_name} is {status} at t*_0={t0_star},t*={t_star}'
    expl_out = dict()
    
    expl_out['tau_a'] = tau_a
    expl_out['tau_s'] = tau_s
    expl_out['tau_i'] = tau_i
    expl_out['tau_v'] = tau_v
    expl_out['tau_star'] = tau_star
    expl_out['t*_status'] = t_star_status
    return expl_out