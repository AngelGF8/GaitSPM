"""Render a social card from an actual synthetic SPM analysis (not a screenshot)."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'tests')]
import gaitspm_engine as E
from simulation import synthetic_dataset, example_recipe
from test_audit import config
c,m,_,vm=synthetic_dataset('01_fai')
cfg=config(c,**example_recipe('01_fai'),lang='en')
r=E.run_analysis(c,m,vm.iloc[:1],cfg)[0][vm.variable.iloc[0]]
fig=E.plt.figure(figsize=(12.8,6.4),dpi=100,facecolor='#f4f6f9')
fig.text(.055,.88,'GaitSPM',fontsize=40,weight='bold',color='#102c4f')
fig.text(.055,.79,'Kinematic analysis with spm1d',fontsize=19,color='#102c4f')
fig.text(.055,.64,'CSV → design → SPM → export',fontsize=16,color='#102c4f')
fig.text(.055,.53,'Participant-aware import\nAdjusted and factorial models\nReproducible numerical validation',fontsize=14,linespacing=1.7,color='#334155',va='top')
fig.text(.055,.12,'github.com/AngelGF8/GaitSPM',fontsize=13,color='#102c4f')
ax=fig.add_axes([.55,.23,.40,.46]);E.plot_spm(ax,r,'en',cfg=cfg)
ax.set_title('Synthetic teaching example',fontsize=13)
fig.text(.55,.12,'Statistical concordance ≠ clinical validation',fontsize=10,color='#475569')
out=ROOT/'docs/assets/social-preview.png';out.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(out,dpi=100);E.plt.close(fig)
print(out)
