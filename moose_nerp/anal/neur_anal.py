import numpy as np
import glob
import neur_anal_class as nac
import plot_utils as pu

'''
filedir='/home/avrama/moose/moose_nerp/moose_nerp/ep/output/'
file_root='epPSP_'
param1=['str','GPe']
param2=[{'_freq': '10'},{'_freq': '20'},{'_freq': '40'}]#{'_freq': '5'},
param3=[{'_plas':'0','_inj':'-1.5e-11'},{'_plas':'1','_inj':'-1.5e-11'}]
vmtab_index=0
start_stim=0.2
end_stim=0.6
'''
#for calcium outputs
start_stim=1.0
transient=0.1
filedir='/home/avrama/moose/moose_nerp/moose_nerp/ep/'
file_root='epAP_'
param1=['none']
param2=[{'_freq': '10'},{'_freq': '20'},{'_freq': '40'},{'_freq': '50'}]
param3=[{'_plas':'0','_inj':'0.00'}]
plot_cal=False
start_stim=1.0
end_stim=4.0
measure='mean'
'''
to do:
1. cross_corr
'''
for parset in param3: #generate new fig each time through this loop
    #initialize structures to hold data
    plot_isis=False
    data_set=nac.neur_set(param1)
    cal_summary={}
    for cond in param1:
        for params in param2:
            #construct filename and key for data_set dictionaries
            key=''.join([str(k)+str(v) for k,v in params.items()])
            suffix=''.join([str(k)+str(v) for k,v in parset.items()])
            pattern=filedir+file_root+cond+key+suffix
            ################ npz files, with Vm, and possibly spiketimes and ISIs, synaptic stim time
            files=sorted(glob.glob(pattern+'*.npz'))
            if len(files)==0:
                print('************ no npz files found using',pattern)
            elif len(files)>1:
                print('***** multiple npz files found using',pattern)
            else:
                fname=files[0]
                ##### create neur_output object for each file, add to data_set
                data=nac.neur_output(fname)
                if len(data.isis):
                    plot_isis=True
                data.psp_amp()
                data_set.add_data(data,cond,key)
            ################ text files with calcium concentration
            files=sorted(glob.glob(pattern+'Ca.txt'))
            if len(files)==0:
                print('************ no txt files found using',pattern)
            elif len(files)>1:
                print('***** multiple txt files found using',pattern+'Ca.txt')
            else:
                fname=files[0]
                cdata=nac.neur_calcium(fname)
                cdata.cal_stats(start_stim,transient)
                cal_summary[key+suffix]=cdata.cal_min_max_mn
                if plot_cal:
                    pu.plot_dict(cdata.calcium,cdata.time,ylabel='Calcium (uM)',ftitle=suffix+key)
    data_set.freq_inj_curve(start_stim,end_stim)
    print([(data_set.spike_freq[p], data_set.inst_spike_freq[p]) for p in data_set.inst_spike_freq.keys()])
    if 'cdata' in globals():
        print('CALCIUM for ',cond)
        for k,v in cal_summary.items():
            line=sorted({comp:v[comp][measure] for comp in v}.items(),key=lambda x:len(x[0]))
            print('    ',k[1:],line[0:4])
        columns=sorted(list(cdata.column_map.keys()),key=lambda x:len(x))
        soma_index=columns.index(cdata.soma_name)
        columns.insert(soma_index-1,columns.pop(soma_index))
        xdata=[float(list(p.values())[0]) for p in param2]
        cal_mean={col:[cal_summary[p][col][measure] for p in cal_summary.keys()] for col in columns}
        pu.plot_dict(cal_mean,xdata,xlabel='Freq (Hz)',ftitle='calcium '+measure)
    else:
        print('No CALCIUM files found for', cond)
#################### plot the set of results from single neuron simulations, range of input frequencies
    if 'neurtypes' in data_set.__dict__:
        if len(data_set.psp_amp[cond]):
            #pu.plot_freq_dep(data_set.psp_amp,data_set.stim_tt,'PSP amp (mV)',suffix,len(data_set.neurtypes),xlabel='stim number',scale=1000,offset=0.01)
            pu.plot_freq_dep(data_set.psp_norm,data_set.stim_tt,'norm PSP amp',suffix,len(data_set.neurtypes),xlabel='stim number',offset=0.02)
        if len(data_set.vmdat[cond]):
            pu.plot_freq_dep(data_set.vmdat,data_set.time,'Vm (mV)',suffix,len(data_set.neurtypes),scale=1000,offset=0.1)
        if plot_isis:
            pu.plot_freq_dep(data_set.isis,data_set.isi_x,'ISI (sec)',suffix,len(data_set.neurtypes),xlabel='Spike time (sec)')

