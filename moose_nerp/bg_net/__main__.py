# -*- coding:utf-8 -*-

######## bg_net/__main__.py ############
"""
Model of entire basal ganglia
Loads in all neuron modules and all network modules
Adds in connections between network modules
3. Test/Fix connections from external spike trains - bg_net
5. Adjust synaptic strength to match data (use smal number of neurons)
6. automatically replace external inputs used in single network simulations
"""
from __future__ import print_function, division

import numpy as np
import matplotlib.pyplot as plt
plt.ion()

import moose
import importlib
from moose_nerp.prototypes import (calcium,
                                   cell_proto,
                                   create_model_sim,
                                   clocks,
                                   inject_func,
                                   create_network,
                                   pop_funcs,
                                   tables,
                                   net_output,
                                   util,
                                   multi_module,
                                   net_sim_graph)
from moose_nerp import spn_1comp as model
from moose_nerp import bg_net as net

#names of additional neuron modules to import
neuron_modules=['ep_1comp','proto154_1compNoCal','Npas2005_1compNoCal','arky140_1compNoCal','fsi']
### By importing other modules, do not need to repeat all the information in param_net.py
net_modules=['moose_nerp.gp_net','moose_nerp.ep_net', 'moose_nerp.spn1_net']

#additional, optional parameter overrides specified from with python terminal
model.synYN = True
net.single=False

create_model_sim.setupOptions(model)
param_sim = model.param_sim
param_sim.injection_current = [-50e-12]
param_sim.save_txt = False
param_sim.simtime=0.05

#################################-----------create the model: neurons, and synaptic inputs
#### Do not setup hsolve yet, since there may be additional neuron_modules
model=create_model_sim.setupNeurons(model,network=True)

#create dictionary of BufferCapacityDensity - only needed if hsolve, simple calcium dynamics
buf_cap={neur:model.param_ca_plas.BufferCapacityDensity for neur in model.neurons.keys()}

#import additional neuron modules, add them to neurons and synapses
######## this is skipped if neuron_modules is empty
if len(neuron_modules):
    buf_cap=multi_module.multi_modules(neuron_modules,model,buf_cap)

########### Create Network. For multiple populations, send in net_modules ###########
population,connections,plas=create_network.create_network(model, net, model.neurons,network_list=net_modules)
print(net.connect_dict)
print(population['location'],population['pop'])
###### Set up stimulation - could be current injection or plasticity protocol
# set num_inject=0 to avoid current injection
if net.num_inject<np.inf :
    inject_pop=inject_func.inject_pop(population['pop'],net.num_inject)
    if net.num_inject==0:
        param_sim.injection_current=[0]
else:
    inject_pop=population['pop']
#Does setupStim work for network?  YES, see gp_net/__main__.py
#create_model_sim.setupStim(model)
pg=inject_func.setupinj(model, param_sim.injection_delay,param_sim.injection_width,inject_pop)
moose.showmsg(pg)

##############--------------output elements
if net.single:
    #fname=model.param_stim.Stimulation.Paradigm.name+'_'+model.param_stim.location.stim_dendrites[0]+'.npz'
    #simpath used to set-up simulation dt and hsolver
    simpath=['/'+neurotype for neurotype in model.neurons.keys()]
    create_model_sim.setupOutput(model)
else:   #population of neurons
    model.spiketab,model.vmtab,model.plastab,model.catab=net_output.SpikeTables(model, population['pop'], net.plot_netvm, plas, net.plots_per_neur)
    #simpath used to set-up simulation dt and hsolver
    simpath=[net.netname]

clocks.assign_clocks(simpath, param_sim.simdt, param_sim.plotdt, param_sim.hsolve,model.param_cond.NAME_SOMA)
# Fix calculation of B parameter in CaConc if using hsolve and calcium
######### Need to use CaPlasticityParams.BufferCapacityDensity from EACH neuron_module
if model.param_sim.hsolve and model.calYN:
    calcium.fix_calcium(model.neurons.keys(), model, buf_cap)

if model.synYN and (param_sim.plot_synapse or net.single):
    #overwrite plastab above, since it is empty
    model.syntab, model.plastab, model.stp_tab=tables.syn_plastabs(connections,model)

################### Actually run the simulation
net_sim_graph.sim_plot(model,net,connections,population)

if model.param_sim.save_txt:
    vmout={ntype:[tab.vector for tab in tabset] for ntype,tabset in model.vmtab.items()}
    if np.any([len(st) for tabset in spike_time.values() for st in tabset]):
        np.savez(outdir+net.outfile,spike_time=spike_time,isi=isis,vm=vmout)
    else:
        print('no spikes for',param_sim.fname, 'saving vm and parameters')
        np.savez(outdir+net.outfile,vm=vmout)
''' 
debugging:
4. deal with time tables - import ttables in netparam?  no need to specify ttables?
which time tables are being created? gp, ep or bg_net?  
1. test with tt specified in param_net (better comments in create_network)
if works:
2. figure out whether could read in (and accumulate?) from importlib - would need to call TableSet.create_all again


remaining issues
1. model.param_cond.NAME_SOMA needs to be dictionary, to allow different soma names for different neurons
2. network['location'] is now a dictionary of lists, instead of just a list; BUT, this is not used, so OK

'''
    
