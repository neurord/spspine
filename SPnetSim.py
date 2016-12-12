# -*- coding:utf-8 -*-

######## SPnetSim.py ############
"""\
Create a network of SP neurons using dictionaries for channels, synapses, and network parameters

Can use ghk for calcium permeable channels if ghkYesNo=1
Optional calcium concentration in compartments (calcium=1)
Optional synaptic plasticity based on calcium (plasyesno=1)
Spines are optional (spineYesNo=1), but not allowed for network
The graphs won't work for multiple spines per compartment
"""
from __future__ import print_function, division
import logging

import os
os.environ['NUMPTHREADS'] = '1'
import numpy as np
import matplotlib.pyplot as plt
plt.ion()

from pprint import pprint
import moose 

from spspine import (cell_proto,
                     clocks,
                     inject_func,
                     create_network,
                     tables,
                     net_output,
                     logutil,
                     util,
                     standard_options)
from spspine import (param_net, d1d2)
#from spspine.graph import net_graph

option_parser = standard_options.standard_options(default_injection_current=[50e-12, 100e-12])
param_sim = option_parser.parse_args()

logging.basicConfig(level=logging.INFO)
log = logutil.Logger()

#################################-----------create the model
#overrides:
d1d2.synYN=True
d1d2.single=False

##create neuron prototypes with synapses and calcium
MSNsyn,neuron = cell_proto.neuronclasses(d1d2)

all_neur_types=neuron
#FSIsyn,neuron = cell_proto.neuronclasses(FSI)
#all_neur_types.append(neuron)  #how to append/merge dictionaries?

#create network and plasticity
if d1d2.single:
    population,connections,plas=create_network.create_network(d1d2, param_net, all_neur_types)
else:
    population,connections,plas=create_network.create_network(d1d2, param_net)

#NEXT:
#debug network tables & graphs
#a. why no AMPA input to network?
#b. randomly select one synapse per neuron to plot
#c. plastab and syntab in tables.py only work for SPneuronSim, with a single synapse per neuron
#    how to configure these tables if multiple synapses?  Should the plascum element returned from add_plastic synapse be changed?

#if passed MSNsyn into create_network, could eliminate creating such array in connect and if syntype statement
#to eliminate MSNsyn, need to change specification of the synapse in plastic_synapse

#PYTHONPATH=. py.test -v
#runs the tests - do this prior to commit.
#Types of spike train correlations
#1. number of synaptic terminals between single axon and single neuron
#       parameter specifying range or mean number.  Randomly select how many and repeat calls to
#           synpath,syncomps=select_entry(syncomps)
#           synconn(synpath,dist,presyn_tt,netparams.mindelay)
#2. with and between neuron correlation due to correlation of the cortical region projecting to striatum
#      account for both of these (same source) with correlated spike trains
#3.  between neuron correlations because a single axon can contact multiple neurons
#       implement using parameter syn_per_tt - associated with table object
#       this will also allow multiple synapses within single neuron, but unlikely if large neuron population

#Code Refinements
#A. refine NamedLists for connections to specify post-syn location dependence (optional)
#B. refine select_branch to make use of location dependence 
#C. refine count_presyn to account for a. non-dist dependence, and multiple connections per neuron with location dependence
#                                      b. 3D arrays of elements
#D. debug case where neurons to have both intrinsic (pre-cell) and extern (timetable) inputs of same syntype
#E: Think about how to connect two different networks, e.g. striatum and GP

###------------------Current Injection
pg=inject_func.setupinj(d1d2, param_sim.injection_delay,param_sim.injection_width,population['pop'])

##############--------------output elements
if d1d2.single:
    vmtab,syntab,catab,plastab = tables.graphtables(d1d2, all_neur_types,
                                                 param_sim.plot_current,
                                                 param_sim.plot_current_message,
                                                 plas,syn)
else:
    spiketab, vmtab = net_output.SpikeTables(d1d2, population['pop'], param_sim.plot_netvm)

########## clocks are critical
## these function needs to be tailored for each simulation
## if things are not working, you've probably messed up here.
if d1d2.single:
    simpath=['/'+neurotype for neurotype in all_neur_types]
else:
    #possibly need to setup an hsolver separately for each cell in the network
    simpath=[param_net.netname]
clocks.assign_clocks(simpath, param_sim.simdt, param_sim.plotdt, param_sim.hsolve)

################### Actually run the simulation
def run_simulation(injection_current, simtime):
    print(u'◢◤◢◤◢◤◢◤ injection_current = {} ◢◤◢◤◢◤◢◤'.format(injection_current))
    pg.firstLevel = injection_current
    moose.reinit()
    moose.start(simtime)

if __name__ == '__main__':
    for inj in param_sim.injection_current:
        run_simulation(injection_current=inj, simtime=param_sim.simtime)
        if param_sim.plot_netvm:
            #net_graph.graphs(d1d2, vmtab,syntab,graphsyn,catab,plastab,sptab)
            plt.show()
        if not d1d2.single:
            writeOutput(d1d2, param_net.outfile+str(inj),spiketab,vmtab,population)

    # block in non-interactive mode
    _util.block_if_noninteractive()
