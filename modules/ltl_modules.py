from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np
import scripts.run_explanation as run_expl

###############################################################################
# Initial tree evaluation modules (t0 assessments)
###############################################################################

def nextX(t0times, trace):
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    ta = [[]]*trace_len
    ts = [[]]*trace_len
    ti = [[]]*trace_len
    tv = [[]]*trace_len
    #print('t0times[0]: ', t0times[0])
    
    for timestep in range(0,trace_len-1):
        tau_a = np.zeros(trace_len - timestep)
        tau_s = np.zeros(trace_len - timestep)
        tau_i = np.zeros(trace_len - timestep)
        tau_v = np.ones(trace_len - timestep) 
        
        # Use formula for "next"
        if t0times[0][timestep+1] == 1:
            t0s[timestep] = 1
            tau_a[0]=1
            tau_a[1]=1
            tau_s[1]=1
            if not timestep == trace_len - 2:
                tau_i[2:None] = np.ones(trace_len - (timestep+2))
            tau_v = np.zeros(trace_len - timestep)
            
        ta[timestep]= tau_a
        ts[timestep]= tau_s
        ti[timestep]= tau_i
        tv[timestep]= tau_v
       
    return t0s, ta, ts, ti, tv


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
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)
                
    #print('until on-times: ', t0s)
    return t0s

def weakuntilW(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]               
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "weak until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 
                
    #print('weak until on-times: ', t0s)
    return t0s

def strongreleaseM(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "strong release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)     
                
    #print('strong release on-times: ', t0s)
    return t0s


def releaseR(t0times, trace):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 
                
    #print('release on-times: ', t0s)
    return t0s
    
def orMod(t0times, trace):
    t0s = np.zeros(len(trace))
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] > 0:
            t0s[timestep] = 1
        
    #print('t0s: ', t0s)
    return t0s

def andMod(t0times, trace):
    t0s = np.zeros(len(trace))
    noArgs = len(t0times)
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] == noArgs:
            t0s[timestep] = 1
        
    #print('t0s: ', t0s)
    return t0s

def negMod(t0times, trace):
    t0s = np.ones(len(trace)) - t0times[0]
    
    #print('t0s: ', t0s)
    return t0s

def impl(t0times, trace):
    t0s = np.ones(len(trace))
    
    for timestep in range(0,len(trace)):
        # A bit dumber than necessary for now:
        if t0times[0][timestep] == 1 and t0times[1][timestep] == 0:
            t0s[timestep] = 0
        
    #print('t0s: ', t0s)
    return t0s


###############################################################################
# Query modules (tau assessments)
###############################################################################

def nextXquery(t0times, trace):
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    ta = [[]]*trace_len
    ts = [[]]*trace_len
    ti = [[]]*trace_len
    tv = [[]]*trace_len
    #print('t0times[0]: ', t0times[0])
    
    for timestep in range(0,trace_len-1):
        tau_a = np.zeros(trace_len - timestep)
        tau_s = np.zeros(trace_len - timestep)
        tau_i = np.zeros(trace_len - timestep)
        tau_v = np.ones(trace_len - timestep) 
        
        # Use formula for "next"
        if t0times[0][timestep+1] == 1:
            t0s[timestep] = 1
            tau_a[0]=1
            tau_a[1]=1
            tau_s[1]=1
            if not timestep == trace_len - 2:
                tau_i[2:None] = np.ones(trace_len - (timestep+2))
            tau_v = np.zeros(trace_len - timestep)
            
        ta[timestep]= tau_a
        ts[timestep]= tau_s
        ti[timestep]= tau_i
        tv[timestep]= tau_v
       
    return t0s, ta, ts, ti, tv


def futureFquery(t0times, trace):
    
    # Taus not functional
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    ta = [[]]*trace_len
    ts = [[]]*trace_len
    ti = [[]]*trace_len
    tv = [[]]*trace_len
    #print('t0times[0]: ', t0times[0])
    
    for timestep in range(0,trace_len):
        tau_a = np.zeros(trace_len - timestep)
        tau_s = np.zeros(trace_len - timestep)
        tau_i = np.zeros(trace_len - timestep)
        tau_v = np.ones(trace_len - timestep) 
        
        # Use formula for "eventually"
        if np.sum(t0times[0][timestep:None] >= 1):
            t0s[timestep] = 1

            
            #tau_a[]
            tau_v = np.zeros(trace_len - timestep)
            
        ta[timestep]= tau_a
        ts[timestep]= tau_s
        ti[timestep]= tau_i
        tv[timestep]= tau_v
     
    return t0s, ta, ts, ti, tv
    
def alwaysGquery(t0times, trace, rule_dicts):
    trace_len = len(trace)
    t0s = np.zeros(trace_len)
    ta = [[]]*trace_len
    ts = [[]]*trace_len
    ti = [[]]*trace_len
    tv = [[]]*trace_len
    
    for timestep in range(0,trace_len):
        tau_a = np.zeros(trace_len - timestep)
        tau_s = np.zeros(trace_len - timestep)
        tau_i = np.zeros(trace_len - timestep)
        tau_v = np.ones(trace_len - timestep)
        
        # Use formula for "always"
        if np.sum(t0times[0][timestep:None]) == trace_len-timestep:
            t0s[timestep:None] = np.ones(trace_len-timestep)
            
            break 
        
    return t0s, rule_dicts

def untilUquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    # Want to check if arg1 holds up to the min time that arg2 
    # starts holding (within our range set by t0)
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)
                
    #print('until on-times: ', t0s)
    return t0s, rule_dicts

def weakuntilWquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]               
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "weak until"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On]) == (minArg2On)-time:
                t0s[time:minArg2On] = np.ones((minArg2On)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 
                
    #print('weak until on-times: ', t0s)
    return t0s, rule_dicts

def strongreleaseMquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "strong release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)     
                
    #print('strong release on-times: ', t0s)
    return t0s, rule_dicts


def releaseRquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    t0timesArg2 = t0times[1]            
    
    arg2OnIndices = []
    
    for time in range(0, len(trace)):
        if t0timesArg2[time] == 1:
            arg2OnIndices.append(time)
    
    #print('arg2OnIndices: ', arg2OnIndices)
    for time in range(0,len(trace)):
        arg2inRange = arg2OnIndices[time:None]
        
        # Use formula for "release"
        if len(arg2inRange) > 0:
            minArg2On = min(arg2inRange)
            #print('minArg2On: ', minArg2On)
            
            if np.sum(t0times[0][time:minArg2On+1]) == (minArg2On+1)-time:
                t0s[time:minArg2On+1] = np.ones((minArg2On+1)-time)    
        else:
            if np.sum(t0times[0][time:None]) == len(trace)-time:
                t0s[time:None] = np.ones(len(trace)-time)
                break 
                
    #print('release on-times: ', t0s)
    return t0s, rule_dicts
    
def orModquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] > 0:
            t0s[timestep] = 1
        
    #print('t0s: ', t0s)
    return t0s, rule_dicts

def andModquery(t0times, trace, rule_dicts):
    t0s = np.zeros(len(trace))
    noArgs = len(t0times)
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] == noArgs:
            t0s[timestep] = 1
        
    #print('t0s: ', t0s)
    return t0s, rule_dicts

def negModquery(t0times, trace, rule_dicts):
    t0s = np.ones(len(trace)) - t0times[0]
    
    #print('t0s: ', t0s)
    return t0s, rule_dicts

def implquery(t0times, trace, rule_dicts):
    t0s = np.ones(len(trace))
    
    for timestep in range(0,len(trace)):
        # A bit dumber than necessary for now:
        if t0times[0][timestep] == 1 and t0times[1][timestep] == 0:
            t0s[timestep] = 0
        
    #print('t0s: ', t0s)
    return t0s, rule_dicts