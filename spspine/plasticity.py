"""\
Make a plasticity device in that compartment/synapse
"""
from __future__ import print_function, division
import os
import re
import moose

from spspine import logutil
log = logutil.Logger()
NAME_PLAS='/plas'
NAME_CUM='Cum'

def plasticity(synchan,NAME_CALCIUM,Thigh,Tlow,highfac,lowfac):
    compname = os.path.dirname(synchan.path)
    calname = compname + '/'+NAME_CALCIUM
    cal=moose.element(calname)
    shname=synchan.path+'/SH'
    sh=moose.element(shname)

    log.info("{} {} {}", synchan.path, sh.synapse[0], cal.path)

    plasname=compname+'/'+NAME_PLAS
    plas=moose.Func(plasname)
    #FIRST: calculate the amount of plasticity
    #y is input plasticity trigger (e.g. Vm or Ca) 
    moose.connect(cal,'concOut',plas,'yIn')
    #x is the high threshold, z is the low threshold
    #This gives parabolic shape to plasticity between the low and high threshold
    #highfac and lowfac scale the weight change (set in SynParams.py)
    expression=highfac+"(y>x)*(y-x)+(y>z)*(x>y)*(y-z)*(x-y)"+lowfac
    plas.expr=expression
    #Must define plasticity expression first, else these next assignments do nothing
    plas.x=Thigh
    plas.z=Tlow
    #SECOND: accumulate all the changes, as percent increase or decrease
    plasCum=moose.Func(plasname+NAME_CUM)
    #need input from the plasticity thresholding function to y 
    moose.connect(plas,'valueOut',plasCum,'xIn')
    moose.connect(plasCum,'valueOut',plasCum, 'yIn')
    plasCum.expr="(x+1.0)*y*z"
    plasCum.z=sh.synapse[0].weight
    plasCum.y=1.0
    moose.connect(plasCum,'valueOut',sh.synapse[0],'setWeight')
    
    return {'cum':plasCum,'plas':plas}

def addPlasticity(cell_pop,caplas_params):
    log.debug("{} {}", cell_pop,dir(caplas_params))
    plascum=[]
    for cell in cell_pop:
        allsyncomp_list=moose.wildcardFind(cell+'/##/'+caplas_params.syntype+'[ISA=SynChan]')
        #allsyncomp_list=moose.wildcardFind(cell+'/##[ISA=SynChan]')
        for synchan in allsyncomp_list:
            #add another  condition - only if there is pre-synaptic connection
            #if caplas_params.syntype in synchan.path:
                log.debug("{} {}", cell, synchan.path)
                plascum.append(plasticity(synchan,caplas_params.NAME_CALCIUM,
                           caplas_params.highThresh,
                           caplas_params.lowThresh,
                           caplas_params.highfactor,
                           caplas_params.lowfactor))
    return plascum
