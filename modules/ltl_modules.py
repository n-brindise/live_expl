from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np
import scripts.run_explanation as run_expl

def nextX(onTimes, offTimes, t0times, trace):
    ons = []
    offs = []
    onFlag = False
    t0s = np.zeros(len(trace))
    
    print('t0times[0]: ', t0times[0])
    
    for time in range(0,len(trace)-1):
        # Use formula for "next"
        if t0times[0][time+1] == 1:
            t0s[time] = 1
            if not onFlag:
                onFlag = True
                ons.append(time)
        else:
            if onFlag:
                onFlag = False
                offs.append(time)        
    return ons, offs, t0s


def futureF(onTimes, offTimes, t0times, trace):
    ons = []
    offs = []
    onFlag = False
    t0s = np.zeros(len(trace))
    
    print('t0times[0]: ', t0times[0])
    
    for time in range(0,len(trace)):
        # Use formula for "eventually"
        if np.sum(t0times[0][time:None] >= 1):
            t0s[time] = 1
            if not onFlag:
                onFlag = True
                ons.append(time)
        else:
            if onFlag:
                onFlag = False
                offs.append(time)        
    return ons, offs, t0s
    
def alwaysG(onTimes, offTimes, t0times, trace):
    ons = []
    offs = []
    onFlag = False
    t0s = np.zeros(len(trace))
    
    print('t0times[0]: ', t0times[0])
    
    for time in range(0,len(trace)):
        # Use formula for "always"
        print("Globally checks: ")
        print('time: ', time)
        print('length check: ', len(t0times[0][time:None]))
        print(np.sum(t0times[0][time:None]))
        print(len(trace)-time)
        if np.sum(t0times[0][time:None]) == len(trace)-time:
            t0s[time:None] = np.ones(len(trace)-time)
            ons.append(time)
            break 
        
    return ons, offs, t0s

def untilU(onTimes, offTimes, t0times, trace):
    # NOT FUNCTIONING
    ons = []
    offs = []
    onFlag = False
    t0s = np.zeros(len(trace))
    
    print('t0times[0]: ', t0times[0])
    print('t0times[1]: ', t0times[1])
    
    for time in range(0,len(trace)):
        # Use formula for "until"
        if np.sum(t0times[0][time:None] >= 1):
            t0s[time] = 1
            if not onFlag:
                onFlag = True
                ons.append(time)
        else:
            if onFlag:
                onFlag = False
                offs.append(time)        
    return ons, offs, t0s

def weakuntilW(onTimes, offTimes, t0times, trace):
    # NOT FUNCTIONING
    ons = []
    offs = []
    onFlag = False
    t0s = np.zeros(len(trace))
    
    print('t0times[0]: ', t0times[0])
    print('t0times[1]: ', t0times[1])
    
    for time in range(0,len(trace)):
        # Use formula for "until"
        if np.sum(t0times[0][time:None] >= 1):
            t0s[time] = 1
            if not onFlag:
                onFlag = True
                ons.append(time)
        else:
            if onFlag:
                onFlag = False
                offs.append(time)        
    return ons, offs, t0s
def strongreleaseM(onTimes, offTimes, trace):
    pass
def releaseR(onTimes, offTimes, trace):
    pass
    
def orMod(onTimes, offTimes, t0times, trace):
    t0s = np.zeros(len(trace))
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] > 0:
            t0s[timestep] = 1
        
    #on/off times not functional
    ons = offTimes[0]
    offs = onTimes[0]
    
    print('t0s: ', t0s)
    return ons, offs, t0s

def andMod(onTimes, offTimes, t0times, trace):
    t0s = np.zeros(len(trace))
    noArgs = len(onTimes)
    summedt0times = np.sum(t0times, axis=0)
    
    for timestep in range(0,len(trace)):
        if summedt0times[timestep] == noArgs:
            t0s[timestep] = 1
        
    #on/off times not functional
    ons = offTimes[0]
    offs = onTimes[0]
    
    print('t0s: ', t0s)
    return ons, offs, t0s

def negMod(onTimes, offTimes, t0times, trace):
    # Note: on and off times may be janky this way
    ons = offTimes[0]
    offs = onTimes[0]
    t0s = np.ones(len(trace)) - t0times[0]
    
    print('t0s: ', t0s)
    return ons, offs, t0s

def impl(onTimes, offTimes, t0times, trace):
    t0s = np.ones(len(trace))
    
    for timestep in range(0,len(trace)):
        # A bit dumber than necessary for now:
        
        if t0times[0][timestep] == 1 and t0times[1][timestep] == 0:
            t0s[timestep] = 0
        
    #on/off times not functional
    ons = offTimes[0]
    offs = onTimes[0]
    
    print('t0s: ', t0s)
    return ons, offs, t0s
