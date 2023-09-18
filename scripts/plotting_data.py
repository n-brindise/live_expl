from pathlib import Path
import os
import sys
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.mathtext as mathtext
import pandas as pd

import cmasher as cmr

from scripts import run_explanation as re

# Script to produce desired data for plotting
##########################################################
# User Input
##########################################################

experiment_name = "PPO_treasure_hunt"
timeout_step_count = 50
#num_checkpoints = 6
#checkpoint_numbers = [20, 40, 60, 80, 100, 120]


###########################################################

plot_config_path = f'data/expl_configs/{experiment_name}/plot_data_config.json'
path = Path(plot_config_path)
with open(path, "r") as f:
    plot_config = json.load(f)
    

base_path = f'data/trace_data/{experiment_name}/plotting_data_traces'
file_output_path = f'data/results/plots/{experiment_name}'

plot_types = plot_config['plot_types']

if 'avg_sat_times_plots' in plot_types:
    base_path_actsat = f'{base_path}/avg_sat_times'
    avg_sat_time_config = plot_config['avg_sat_time_config']
    savePlotFilename = avg_sat_time_config['savePlotFilename']
    plot_title = avg_sat_time_config['plot_title']
    rules = avg_sat_time_config['ruleNos']
    sorted_trace_folders = sorted([p.as_posix() for p in Path(base_path_actsat).glob("*")])
    
    # Find how many checkpoints are used and which numbers
    num_checkpoints = len(sorted_trace_folders)
    checkpoint_numbers = list()
    for folder in sorted_trace_folders:
        # All numbers are given in 6 digits (with preceding zeros as necessary)
        checkpoint_numbers.append(int(folder[-6:]))
    
    avg_sat_times = np.zeros((len(rules), num_checkpoints))
    percent_satisfied_list = np.zeros((len(rules), num_checkpoints))
    #failures = np.zeros((len(rules), num_checkpoints))
    query_list = list()
    
    # Generate list of queries to make based on rules to be included
    for rule_no in rules:
        query = dict()
        query['t0*'] = 0
        query['ruleNo'] = rule_no
        query['branch'] = str(rule_no)
        query['t*'] = 0
        query_list.append(query)
    
    for chk in range(0, num_checkpoints):
        avg_sat_time_chkpt = dict()
        num_satisfied_chkpt = dict()
        failure_counter = dict()
        path_to_folder = sorted_trace_folders[chk]
        
        trace_list = [p.as_posix() for p in Path(path_to_folder).glob("*")]
        #print('trace list len: ', len(trace_list))
        
        for i in range(0,len(trace_list)):
            
            # Load individual traces
            trace_dir = trace_list[i]
            #print("HERE!! ###########################")
            #print('trace_dir: ', trace_dir)
            trace_path = Path(trace_dir)
            
            # pass query list to explainer for this trace            
            trace_data_loc = {
                "base_path" : trace_path,
                "filename" : ''
                }
            
            # Expl types: 'manual', 'interactive' (not yet supported), 'optimal'
            expl_specs = {
                "base_path" : f'./data/expl_configs/{experiment_name}',
                "filename" : 'explconfig1.json'
            }
                
            config = dict()
            config['trace_data_loc'] = trace_data_loc
            config['expl_specs'] = expl_specs
            config['data_for_plotting'] = True
            config['query_list_for_plotting'] = query_list
            
            _, _, plotting_data = re.run_explanation(**config)
            
            for rule_no in rules:
                #print('rule_no is: ', rule_no)
                if i == 0:
                    avg_sat_time_chkpt[str(rule_no)] = 0
                    num_satisfied_chkpt[str(rule_no)] = 0
                    failure_counter[str(rule_no)] = 0
                tau_s = plotting_data[rule_no][str(rule_no)]['tau_s'][0]
                for tstep in range(0, len(tau_s)):
                    if tau_s[tstep] == 1: # satisfied at this time (for the first time)
                        #print(f'Rule {rule_no} satisfied at time {tstep} (trace {i})')
                        avg_sat_time_chkpt[str(rule_no)] = avg_sat_time_chkpt[str(rule_no)] + tstep
                        num_satisfied_chkpt[str(rule_no)] = num_satisfied_chkpt[str(rule_no)] + 1
                        break
                    elif tstep == len(tau_s) - 1: #last step, still not satisfied
                        failure_counter[str(rule_no)] = failure_counter[str(rule_no)] + 1
        
        for rule_no in rules:
            if failure_counter[str(rule_no)] < len(trace_list):
                avg_sat_times[rule_no][chk] = avg_sat_time_chkpt[str(rule_no)] / (len(trace_list)-failure_counter[str(rule_no)])
                #failures[rule_no][chk] = 1000000
            else:
                # Record failures:
                avg_sat_times[rule_no][chk] = -1
                #failures[rule_no][chk] = timeout_step_count
            percent_satisfied_list[rule_no][chk] = num_satisfied_chkpt[str(rule_no)]/len(trace_list) * 100
            #print('rule number: ', rule_no, ' checkpoint: ', chk)
        
        #print(avg_sat_times)    
        
    ####################################################
    # Plot avg sat times
    ####################################################
    # Make list of dataframes:
    avg_sat_df_dict = dict()
    for rule_no in rules:
        #checkpoint_numbers = range(1,61)
        rule_sat_times = avg_sat_times[rule_no]
        #print('type of rule_sat_times: ', type(rule_sat_times))
        #print('rule_sat_times: ', rule_sat_times)
        #rule_sat_times = np.random.uniform(low=10, high = 40, size =(60,))
        #print('type of rule_sat_times later: ', type(rule_sat_times))
        #print('rule_sat_times: ', rule_sat_times)

        percent_satisfied = percent_satisfied_list[rule_no]
        #percent_satisfied = np.random.uniform(low=0, high = 100, size =(60,))
        avg_sat_df = pd.DataFrame({
            'checkpt' : checkpoint_numbers,
            'timestep' : rule_sat_times,
            'percent_satisfied' : percent_satisfied
        })
        avg_sat_df_dict[rule_no] = avg_sat_df
        #print('percent satisfied: ', percent_satisfied)
    
    plot_shape_list = ['v', 'o', 's']
    legend_strings = list()

    x_max = max(checkpoint_numbers) +1
    x_min = max(min(checkpoint_numbers)-5, 0)
    y_max = 40
    
    #fig = plt.figure()
    fig = plt.figure(figsize=(8, 4.9))
    ax = plt.subplot(111)
    mpl.rcParams.update({'font.size':14})
    plt.rcParams.update({
        "font.family": "sans-serif"
    })
    
    ax.set_xticks(range(x_min, x_max, 5))
    ax.set_yticks(range(0, y_max, 5))
    ax.set_axisbelow(True)
    
    # adjust color map
    cmap = cmr.get_sub_cmap('inferno_r', 0.15, 1.0)
    #cmap = 'inferno_r'

    for ridx, rule_no in enumerate(rules):
        rule_satisfaction_avg_times = avg_sat_times[rule_no]
        avg_sat_df = avg_sat_df_dict[rule_no]
        ax.scatter('checkpt', 'timestep', c='percent_satisfied', cmap=cmap, vmin=0, vmax=100, s=50, marker=plot_shape_list[ridx], data=avg_sat_df)

    ax.axis([x_min, x_max, 0, y_max])
    plt.title(plot_title)
    
    ax.legend([r'$\varphi_0=\mathbf{F}$key', r'$\varphi_1=\mathbf{F}$open_door', r'$\varphi_2=\mathbf{F}$treasure_chest'], labelspacing=0.2)
    
    ax.minorticks_on()
    ax.grid(which='minor', color='lightgray', linewidth=0.6)
    ax.tick_params(which='minor', bottom=False, left=False)
    
    plt.xlabel('Training iteration')
    plt.ylabel('Trajectory timestep')
    plt.grid()
    
    # Adjust font sizes
    plt.rc('axes', titlesize=15)
    plt.rc('font', size=15)
    for item in ([ax.xaxis.label, ax.yaxis.label] +
        ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(16)
    
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0+4, box.width, box.height*0.8])
    plt.subplots_adjust(bottom=0.19)
    #plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap), fraction=0.035, pad=0.04, ax=ax, orientation='horizontal', label='Some units')
    plt.colorbar(mpl.cm.ScalarMappable(cmap=cmap), fraction=0.018, ax=ax, orientation='vertical', label=r'proportion of traces satisfying $\varphi$')
  
    
    savepath = Path(file_output_path, savePlotFilename)
    Path(savepath).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    with plt.rc_context({'image.composite_image': False}):
        plt.savefig(savepath, dpi=400, format='pdf')
    plt.show()
    
    
    
################################################################################
# Trigger Plots for G (xxx -> xxx)
################################################################################
    
if 'trigger_plots' in plot_types:
    trigger_config = plot_config['trigger_config']
    savePlotFilename = trigger_config['savePlotFilename']
    plot_title = trigger_config['plot_title']
    
    rules = trigger_config['ruleNos']
    trace_folder = f'{base_path}/trigger_times_it20'
    trace_list = sorted([p.as_posix() for p in Path(trace_folder).glob("*")])
    num_traces = len(trace_list)
    
    query_list = list()
    
    # Generate list of queries to make based on rules to be included
    # Here, we structure this for formulas of form G ( xxx -> xxxx)
    #   and find their trigger instances.
    #
    # We do this very inefficiently here.     

    # This won't really matter; is overridden by plot_data_config
    expl_specs = {
        "base_path" : f'./data/expl_configs/{experiment_name}',
        "filename" : 'explconfig1.json'
    }
    
    config = dict()
    config['data_for_plotting'] = True
    config['expl_specs'] = expl_specs
    
    trigger_times = np.zeros((len(rules), num_traces))
    done_times = np.zeros((len(rules), num_traces))
    
    failed_traces = np.full((len(rules), num_traces), fill_value = -5)
    not_triggered_traces = np.full((len(rules), num_traces), fill_value = -5)

    total_traces_not_triggered = np.zeros(len(rules))
    total_traces_violated = np.zeros(len(rules))
    
    percent_traces_not_triggered = np.zeros(len(rules))
    percent_traces_violated = np.zeros(len(rules))
        
    for i in range(0,num_traces):
        #print('trace number is now ', i)
        trace_data_loc = {
            "base_path" : trace_list[i],
            "filename" : ''
        }
        config['trace_data_loc'] = trace_data_loc
        path = trace_list[i]
        with open(path, "r") as f:
            this_trace = json.load(f)
        this_trace_len = len(this_trace['trace'])
        
        # First find when xx -> xx is triggered.
        query_list = list()
        for rule_no in rules:
            for tstp in range (0, this_trace_len):
                query = dict()
                query['t0*'] = tstp
                query['ruleNo'] = rule_no
                query['branch'] = f'{rule_no}.0.0' # Want to find the (first) arg activation times
                query['t*'] = tstp
                query_list.append(query)
        
        config['query_list_for_plotting'] = query_list

        #print('query_list: ', query_list)
        #print('config query list: ', config['query_list_for_plotting'])
        _, _, plotting_data = re.run_explanation(**config)
        #print('first plotting data:')
        #print(plotting_data)
            
        for ridx, rule_no in enumerate(rules):
            trace_not_triggered = False
            
            for tstep in range(0, this_trace_len):
                tau_v = plotting_data[rule_no][f'{rule_no}.0.0']['tau_v'][tstep]
                #print('len of tau_a: ', len(tau_a))
                #print('####tau_v (first arg): ', tau_v)
                if not tau_v[0] == 1:
                    # rule holds at this time (for the first time)
                    #print(f'Rule {rule_no} true at time {tstep} (trace {i})')
                    trigger_times[ridx][i] = tstep
                    break
                elif tstep == this_trace_len - 1: # reached end of trace without triggering
                    trace_not_triggered = True

                    
                    
            if trace_not_triggered: 
                total_traces_not_triggered[ridx] = total_traces_not_triggered[ridx] + 1
                not_triggered_traces[ridx][i] = 2
                trigger_times[ridx][i] = -2
                done_times[ridx][i] = -2
            else:
                # Now we have a trigger time for the rule (tstep).
                # So we can check for satisfaction of its consequence (argument)
                tt = tstep
                #print('tt: ', tt)
                query = dict()
                query['t0*'] = tt
                query['ruleNo'] = rule_no
                query['branch'] = f'{rule_no}.0.1' # Want to find the (first) arg activation times
                query['t*'] = tt
                query_list_conseq = [query]
                
                config['query_list_for_plotting'] = query_list_conseq
                _, _, plotting_data_conseq = re.run_explanation(**config)
                
                tau_s = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_s'][tt]
                tau_i = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_i'][tt]
                tau_v = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_v'][tt]
                
                #print('###################tau_s: ', tau_s)
                #print('###################tau_v: ', tau_v)
                for t_step in range(0, len(tau_s)):   
                    if tau_v[t_step] == 1:
                        # Formula violated.
                        total_traces_violated[ridx] = total_traces_violated[ridx] + 1 
                        failed_traces[ridx][i] = trigger_times[ridx][i] + 5
                        done_times[ridx][i] = -2
                        break
                    elif tau_i[t_step] == 1: # inactive at this time
                        # For now, treat inactivity the same way as satisfaction
                        done_times[ridx][i] = t_step + tt
                        break
                    elif tau_s[t_step] == 1: # satisfied at this time
                        #print(f'Rule {rule_no} satisfied at time {tstep} (trace {i})')
                        done_times[ridx][i] = t_step + tt
                        #print('sat time: ', t_step + tt)
                        break            
                
        #for rule_no in rules:
        #    if failure_counter[str(rule_no)] < len(trace_list):
        #        avg_sat_times[rule_no][chk] = avg_sat_time_chkpt[str(rule_no)] / (len(trace_list)-failure_counter[str(rule_no)])
        #        failures[rule_no][chk] = 1000000
        #    else:
        #        # Record failures:
        #        avg_sat_times[rule_no][chk] = 1000000
        #        failures[rule_no][chk] = timeout_step_count
        #    #print('rule number: ', rule_no, ' checkpoint: ', chk)
            
        #print(trigger_times)
        #print(done_times)    
    
    for ridx in range(0, len(rules)):
        percent_traces_not_triggered[ridx] = total_traces_not_triggered[ridx] / num_traces
        percent_traces_violated = total_traces_violated[ridx] / num_traces
        
    ####################################################
    # Plot trigger/consequence times
    ####################################################
    plot_point_list = [' ^', 'bs']
    fail_point = r'x'
    nontriggered_point = r'$*$'
    legend_strings = list()

    x_max = num_traces + 1
    
    fig = plt.figure(figsize=(7.2, 4.8))
    ax = plt.subplot(111)
    mpl.rcParams.update({'font.size':14})
    plt.rcParams.update({
        "font.family": "sans-serif"
    })
    
    #mpl.rc("font", family="Times New Roman",weight='normal')
    plt.rcParams.update({'mathtext.default':  'regular' })
    
    ax.set_xticks(range(0, x_max, 5))
    ax.set_yticks(range(0, timeout_step_count+5, 5))
    ax.set_axisbelow(True)
    trace_x = range(1, x_max)
    
    # Adjust font sizes
    plt.rc('axes', titlesize=15)
    plt.rc('font', size=15)
    for item in ([ax.xaxis.label, ax.yaxis.label] +
        ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(16)
    
    for ridx in range(0, len(rules)):
        plot_trigger_times = trigger_times[ridx]
        ax.scatter(x=trace_x, y=plot_trigger_times, marker='^', c='blue', s=100)
        plot_done_times = done_times[ridx]
        ax.scatter(x=trace_x, y=plot_done_times, marker='s', c='navy', s=100)
        plot_failed_times = failed_traces[ridx]
        ax.scatter(x=trace_x, y=plot_failed_times, marker=fail_point, s=50, c='r')
        plot_nontriggered_times = not_triggered_traces[ridx]
        ax.scatter(x=trace_x, y=plot_nontriggered_times, marker=nontriggered_point, s=100, c='cornflowerblue')
        
    #for rule_no in rules:
    #    plot_trace_failures = trace_failures[rule_no]
    #    ax.plot(trace_x, plot_trace_failures, 'rx', markersize=10, mew=3)
        
    ax.axis([0, x_max, 0, timeout_step_count+2])
    
    plt.title(plot_title)
    
    ax.legend(['triggered', 'done', r'$\varphi$ violated', r'$\varphi_0$ inactive'], title=r"$\varphi=\mathbf{G}($key$\rightarrow\mathbf{F}$ open_door)", labelspacing = 0.1, ncol=2)

    #ax.legend([], loc='center left', bbox_to_anchor=(1, 0.5))
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0+.05, box.width, box.height*0.95])
    ax.minorticks_on()
    ax.grid(which='minor', color='lightgray', linewidth=0.6)
    ax.tick_params(which='minor', bottom=False, left=False)
    
    plt.xlabel('Trace')
    plt.ylabel('Trajectory timestep')
    plt.grid()
    
    #plt.subplots_adjust(bottom=0.14)
    
    savepath = Path(file_output_path, savePlotFilename)
    Path(savepath).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    plt.savefig(savepath, dpi='figure', format='pdf')
    plt.show()
    
    
################################################################################
# Trigger Plot + Extra Rule for G (xxx -> xxx) & Fxxx
################################################################################
    
if 'trigger_plots_plus' in plot_types:
    trigger_config = plot_config['trigger_config_plus']
    savePlotFilename = trigger_config['savePlotFilename']
    plot_title = trigger_config['plot_title']
    
    rules = trigger_config['ruleNos']
    extraRules = trigger_config['extraRules']
    trace_folder = f'{base_path}/trigger_times'
    trace_list = sorted([p.as_posix() for p in Path(trace_folder).glob("*")])
    num_traces = len(trace_list)
    
    query_list = list()
    
    expl_specs = {
        "base_path" : f'./data/expl_configs/{experiment_name}',
        "filename" : 'explconfig1.json'
    }
    
    config = dict()
    config['data_for_plotting'] = True
    config['expl_specs'] = expl_specs
    
    trigger_times = np.zeros((len(rules), num_traces))
    done_times = np.zeros((len(rules), num_traces))
    extra_sat_times = np.zeros((len(extraRules), num_traces))
    
    failed_traces = np.full((len(rules), num_traces), fill_value = -5)
    not_triggered_traces = np.full((len(rules), num_traces), fill_value = -5)

    total_traces_not_triggered = np.zeros(len(rules))
    total_traces_violated = np.zeros(len(rules))
    
    percent_traces_not_triggered = np.zeros(len(rules))
    percent_traces_violated = np.zeros(len(rules))
        
    for i in range(0,num_traces):
        #print('trace number is now ', i)
        trace_data_loc = {
            "base_path" : trace_list[i],
            "filename" : ''
        }
        config['trace_data_loc'] = trace_data_loc
        path = trace_list[i]
        with open(path, "r") as f:
            this_trace = json.load(f)
        this_trace_len = len(this_trace['trace'])
        
        # First find when xx -> xx is triggered.
        query_list = list()
        for rule_no in rules:
            for tstp in range (0, this_trace_len):
                query = dict()
                query['t0*'] = tstp
                query['ruleNo'] = rule_no
                query['branch'] = f'{rule_no}.0.0' # Want to find the (first) arg activation times
                query['t*'] = tstp
                query_list.append(query)
        
        for rule_no in extraRules:
            query = dict()
            query['t0*'] = 0
            query['ruleNo'] = rule_no
            query['branch'] = str(rule_no) # Want to find the sat times of extra rule
            query['t*'] = 0
            query_list.append(query)
        
        config['query_list_for_plotting'] = query_list

        #print('query_list: ', query_list)
        #print('config query list: ', config['query_list_for_plotting'])
        _, _, plotting_data = re.run_explanation(**config)
        #print('first plotting data:')
        #print(plotting_data)
        
        # First handle the easy satisfaction extra rules
        for ridx, rule_no in enumerate(extraRules):
            #print('rule_no is: ', rule_no)
            tau_s = plotting_data[rule_no][str(rule_no)]['tau_s'][0]
            for tstep in range(0, len(tau_s)):
                if tau_s[tstep] == 1: # satisfied at this time (for the first time)
                    #print(f'Rule {rule_no} satisfied at time {tstep} (trace {i})')
                    extra_sat_times[ridx][i] = tstep
                    break
                elif tstep == len(tau_s) - 1: #last step, still not satisfied
                    extra_sat_times[ridx][i] = -2
            
        for ridx, rule_no in enumerate(rules):
            trace_not_triggered = False
            
            for tstep in range(0, this_trace_len):
                tau_v = plotting_data[rule_no][f'{rule_no}.0.0']['tau_v'][tstep]
                #print('len of tau_a: ', len(tau_a))
                #print('####tau_v (first arg): ', tau_v)
                if not tau_v[0] == 1:
                    # rule holds at this time (for the first time)
                    #print(f'Rule {rule_no} true at time {tstep} (trace {i})')
                    trigger_times[ridx][i] = tstep
                    break
                elif tstep == this_trace_len - 1: # reached end of trace without triggering
                    trace_not_triggered = True

                    
                    
            if trace_not_triggered: 
                total_traces_not_triggered[ridx] = total_traces_not_triggered[ridx] + 1
                not_triggered_traces[ridx][i] = 2
                trigger_times[ridx][i] = -2
                done_times[ridx][i] = -2
            else:
                # Now we have a trigger time for the rule (tstep).
                # So we can check for satisfaction of its consequence (argument)
                tt = tstep
                #print('tt: ', tt)
                query = dict()
                query['t0*'] = tt
                query['ruleNo'] = rule_no
                query['branch'] = f'{rule_no}.0.1' # Want to find the (first) arg activation times
                query['t*'] = tt
                query_list_conseq = [query]
                
                config['query_list_for_plotting'] = query_list_conseq
                _, _, plotting_data_conseq = re.run_explanation(**config)
                
                tau_s = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_s'][tt]
                tau_i = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_i'][tt]
                tau_v = plotting_data_conseq[rule_no][f'{rule_no}.0.1']['tau_v'][tt]
                
                #print('###################tau_s: ', tau_s)
                #print('###################tau_v: ', tau_v)
                for t_step in range(0, len(tau_s)):   
                    if tau_v[t_step] == 1:
                        # Formula violated.
                        total_traces_violated[ridx] = total_traces_violated[ridx] + 1 
                        failed_traces[ridx][i] = trigger_times[ridx][i] + 5
                        done_times[ridx][i] = -2
                        break
                    elif tau_i[t_step] == 1: # inactive at this time
                        # For now, treat inactivity the same way as satisfaction
                        done_times[ridx][i] = t_step + tt
                        break
                    elif tau_s[t_step] == 1: # satisfied at this time
                        #print(f'Rule {rule_no} satisfied at time {tstep} (trace {i})')
                        done_times[ridx][i] = t_step + tt
                        #print('sat time: ', t_step + tt)
                        break               
    
    for ridx in range(0, len(rules)):
        percent_traces_not_triggered[ridx] = total_traces_not_triggered[ridx] / num_traces
        percent_traces_violated = total_traces_violated[ridx] / num_traces
        
    ####################################################
    # Plot trigger/consequence times
    ####################################################
    plot_point_list = [' ^', 'bs']
    fail_point = r'x'
    nontriggered_point = r'$*$'
    legend_strings = list()

    x_max = num_traces + 1
    
    fig = plt.figure(figsize=(7.2, 4.8))
    ax = plt.subplot(111)
    mpl.rcParams.update({'font.size':14})
    plt.rcParams.update({
        "font.family": "sans-serif"
    })
    
    #mpl.rc("font", family="Times New Roman",weight='normal')
    plt.rcParams.update({'mathtext.default':  'regular' })
    
    ax.set_xticks(range(0, x_max, 10))
    ax.set_yticks(range(0, timeout_step_count+5, 5))
    ax.set_axisbelow(True)
    trace_x = range(1, x_max)
    
    # Adjust font sizes
    plt.rc('axes', titlesize=15)
    plt.rc('font', size=15)
    for item in ([ax.xaxis.label, ax.yaxis.label] +
        ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(16)
        
    for ridx in range(0, len(extraRules)):
        plot_extra_rule_times = extra_sat_times[ridx]
        ax.scatter(x=trace_x, y=plot_extra_rule_times, marker='o', c='magenta', s=100)
        
    
    for ridx in range(0, len(rules)):
        plot_trigger_times = trigger_times[ridx]
        ax.scatter(x=trace_x, y=plot_trigger_times, marker='^', c='blue', s=100)
        plot_done_times = done_times[ridx]
        ax.scatter(x=trace_x, y=plot_done_times, marker='s', c='navy', s=100)
        plot_failed_times = failed_traces[ridx]
        ax.scatter(x=trace_x, y=plot_failed_times, marker=fail_point, s=50, c='r')
        plot_nontriggered_times = not_triggered_traces[ridx]
        ax.scatter(x=trace_x, y=plot_nontriggered_times, marker=nontriggered_point, s=100, c='cornflowerblue')
        

    #for rule_no in rules:
    #    plot_trace_failures = trace_failures[rule_no]
    #    ax.plot(trace_x, plot_trace_failures, 'rx', markersize=10, mew=3)
        
    ax.axis([0, x_max, 0, timeout_step_count+2])
    
    plt.title(plot_title)
    
    #ax.legend(['triggered', 'done', r'$\varphi$ violated', r'$\varphi_0$ inactive'], title=r"$\varphi=\mathbf{G}($key$\rightarrow\mathbf{F}$ open_door)", labelspacing = 0.1, ncol=2)
    ax.legend([r'$\mathbf{F}$(treasure_chest) satisfied'], labelspacing = 0.1)
    #ax.legend([], loc='center left', bbox_to_anchor=(1, 0.5))
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0+.05, box.width, box.height*0.95])
    ax.minorticks_on()
    ax.grid(which='minor', color='lightgray', linewidth=0.6)
    ax.tick_params(which='minor', bottom=False, left=False)
    
    plt.xlabel('Trace')
    plt.ylabel('Trajectory timestep')
    plt.grid()
    
    #plt.subplots_adjust(bottom=0.14)
    
    savepath = Path(file_output_path, savePlotFilename)
    Path(savepath).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    plt.savefig(savepath, dpi='figure', format='pdf')
    plt.show()

else:
    print('not a valid plot type. Choose from: ')
    print('trigger_plots, avg_sat_times')           
        