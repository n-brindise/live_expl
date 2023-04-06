from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np
import scripts.run_explanation as run_expl

def nextX(onTimes, offTimes, trace):
    ons = []
    offs = []
    onFlag = False
    for time, entry in enumerate(trace):
        
        
    return ons, offs

    for timestep in range(0, trace_len):
        for prop in trace[timestep]:
            propidx = propnumlabels[prop]
            
            if not onFlags[propidx]:
                onFlags[propidx] = True
                onTimes[propidx].append(timestep)
            
            if timestep + 1 < trace_len:
                if prop not in trace[timestep+1]:
                    offTimes[propidx].append(timestep+1)
                    onFlags[propidx] = False

def futureF(onTimes, offTimes, trace):
    pass
    
def alwaysG(onTimes, offTimes, trace):
    pass
def untilU(onTimes, offTimes, trace):
    pass
def weakuntilW(onTimes, offTimes, trace):
    pass
def strongreleaseM(onTimes, offTimes, trace):
    pass
def releaseR(onTimes, offTimes, trace):
    pass

def atomprepAP(onTimes, offTimes, trace):
    pass
    
def orMod(onTimes, offTimes, trace):
    pass
def andMod(onTimes, offTimes, trace):
    pass
def negMod(onTimes, offTimes, trace):
    pass
def impl(onTimes, offTimes, trace):
    pass
