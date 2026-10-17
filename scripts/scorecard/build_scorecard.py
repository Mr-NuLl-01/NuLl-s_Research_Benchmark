"""Build the dependency-free bilingual review editor from the real NRB registry.
Run from the repository: python scripts/scorecard/build_scorecard.py
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nrb_v1.registry import ids, spec, rubric
from nrb_v1.provenance import fingerprint
ROOT = Path(__file__).resolve().parent
out=[]
for tid in ids('all'):
    task=spec(tid)
    keys=['id','title','track','difficulty','required_artifacts','optional_artifacts','modal_observation_artifacts','modality','essential']
    item={**{k:task.get(k,[]) for k in keys},'rubric':rubric(tid)}
    item['rubric_hash']=fingerprint({'rubric':item['rubric'],'essential':item['essential']})
    if tid in ('X04', 'X05'):
        from nrb_v1.video import add_review_protocol
        ledger={'task_id':tid,'artifact_manifest':{}}
        add_review_protocol(ledger)
        item['media_protocol']=ledger['media_review']
    out.append(item)
tr=json.loads((ROOT/'translations.json').read_text())
payload=json.dumps({'tasks':out,'translations':tr},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
html=(ROOT/'scorecard.template.html').read_text().replace('/*__CATALOG__*/',payload)
output=ROOT.parents[1]/'docs/v1.1/scorecard.html'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(html)
print('Built',len(out),'tasks;',len(html.encode()),'bytes')
