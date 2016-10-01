# -*- coding:utf-8 -*-

######## SPneuronSim.py ############
## Code to create two SP neuron classes 
##      using dictionaries for channels and synapses
##      calcium based learning rule/plasticity function, optional
##      spines, optionally with ion channels and synpases
##      Synapses to test the plasticity function, optional
##      used to tune parameters and channel kinetics (but using larger morphology)

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
                     tables,
                     plastic_synapse,
                     logutil,
                     util,
                     standard_options)
from spspine import ca1
from spspine.graph import plot_channel, neuron_graph

option_parser = standard_options.standard_options(default_injection_current=[50e-12, 100e-12])
param_sim = option_parser.parse_args()

logging.basicConfig(level=logging.INFO)
log = logutil.Logger()

#################################-----------create the model
##create 2 neuron prototypes, optionally with synapses, calcium, and spines

MSNsyn,neuron,capools,synarray,spineHeads = cell_proto.neuronclasses(ca1)

#If calcium and synapses created, could test plasticity at a single synapse in syncomp
if ca1.synYN:
    syn,plas,stimtab=plastic_synapse.plastic_synapse(ca1, param_sim.syncomp, MSNsyn, param_sim.stimtimes)
else:
    syn,plas = {}, {}

####---------------Current Injection

pg=inject_func.setupinj(ca1, param_sim.injection_delay, param_sim.injection_width, neuron)

###############--------------output elements
if param_sim.plot_channels:
    for chan in ca1.Channels.keys():
        libchan=moose.element('/library/'+chan)
        plot_channel.plot_gate_params(libchan,param_sim.plot_activation,
                                      ca1.VMIN, ca1.VMAX, ca1.CAMIN, ca1.CAMAX)

vmtab,catab,plastab,currtab = tables.graphtables(ca1, neuron,
                                                 param_sim.plot_current,
                                                 param_sim.plot_current_message,
                                                 capools,plas,syn)
#if sim.spineYesNo:
#    spinecatab,spinevmtab=spinetabs()
########## clocks are critical. assign_clocks also sets up the hsolver
simpaths=['/'+neurotype for neurotype in ca1.neurontypes()]
clocks.assign_clocks(simpaths, '/data', param_sim.simdt, param_sim.plotdt, param_sim.hsolve)

###########Actually run the simulation
def run_simulation(injection_current, simtime):
    print(u'◢◤◢◤◢◤◢◤ injection_current = {} ◢◤◢◤◢◤◢◤'.format(injection_current))
    pg.firstLevel = injection_current
    moose.reinit()
    moose.start(simtime)

if __name__ == '__main__':
    traces, names = [], []
    for inj in param_sim.injection_current:
        run_simulation(injection_current=inj, simtime=param_sim.simtime)
        neuron_graph.graphs(ca1, vmtab, param_sim.plot_current, param_sim.simtime,
                            currtab,param_sim.plot_current_label, catab, plastab)
        traces.append(vmtab[0][0].vector)
        names.append('ca1 @ {}'.format(inj))
        #if ca1.spineYN:
        #    spineFig(spinecatab,spinevmtab)
    neuron_graph.SingleGraphSet(traces, names, param_sim.simtime)

    # block in non-interactive mode
    util.block_if_noninteractive()

    #End of inject loop