from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np
import scripts.run_explanation as run_expl

def nextX(t_0,T,form_tree, trace):
    pass
def futureF(t_0,T,form_tree, trace):
    pass
        
    
def alwaysG(t_0,T,form_tree, trace):
    pass
def untilU(t_0,T,form_tree, trace):
    pass
def weakuntilW(t_0,T,form_tree, trace):
    pass
def strongreleaseM(t_0,T,form_tree, trace):
    pass
def releaseR(t_0,T,form_tree, trace):
    pass

def atomprepAP(t_0,T,form_tree, trace):
    pass
    
def orMod(t_0,T,form_tree, trace):
    pass
def andMod(t_0,T,form_tree, trace):
    pass
def negMod(t_0,T,form_tree, trace):
    pass
def impl(t_0,T,form_tree, trace):
    pass
