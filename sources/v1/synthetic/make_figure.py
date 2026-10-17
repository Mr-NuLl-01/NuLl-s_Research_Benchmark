"""Benchmark-created synthetic fixture. No source paper measurements are used."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
paired=list(csv.DictReader((ROOT/'paired.csv').open()))
time=list(csv.DictReader((ROOT/'transient.csv').open()))
fig,axs=plt.subplots(1,2,figsize=(7.09,3.15),layout='constrained')
colors={'B1':'#0072B2','B2':'#D55E00','B3':'#009E73'}
ax=axs[0]
for row in paired:
 ax.plot([0,1],[float(row['before_mV']),float(row['after_mV'])],'-o',color=colors[row['batch']],lw=.9,ms=3,alpha=.8)
ax.set(xticks=[0,1],xticklabels=['Before','After'],ylabel='Potential (mV)',ylim=(995,1008),title='a  Paired potential')
ax.ticklabel_format(axis='y',style='plain',useOffset=False)
ax.text(.03,.97,'12 devices; 3 batches',transform=ax.transAxes,va='top',fontsize=8)
ax=axs[1];t=np.array([float(r['time_s']) for r in time]);keys=list(time[0])[1:]
y=np.array([[float(r[k]) for k in keys] for r in time]);mean=y.mean(axis=1);sd=y.std(axis=1,ddof=1)
for j,k in enumerate(keys):ax.plot(t,y[:,j],color=colors[k[:2]],lw=.8,alpha=.45)
ax.fill_between(t,mean-sd,mean+sd,color='#424b55',alpha=.16,label='Mean ± SD')
ax.plot(t,mean,'o-',color='#17232d',lw=1.5,ms=3,label='Mean')
ax.set(xlabel='Time after step (s)',ylabel='Normalized response',title='b  Separate transient experiment',xticks=[0,2,4,8,12],ylim=(-.06,1.12))
ax.text(.97,.06,'6 devices; 2 per batch',transform=ax.transAxes,ha='right',fontsize=8)
ax.legend(frameon=False,fontsize=8,loc='upper left')
fig.savefig(ROOT/'input-figure.svg',metadata={'Title':'Synthetic conditioning fixture for NRB R04','Description':'Two distinct synthetic experiments; no article data are used.'})
fig.savefig(ROOT/'input-figure.png',dpi=180)
