"""Prepare synthetic QA packets, run JS logic, verify actual CLI attachment."""
import json, subprocess, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from nrb_v1.grading import review_packet, attach_review
from nrb_v1.registry import spec
ROOT=Path(__file__).resolve().parents[3]
with tempfile.TemporaryDirectory(prefix='nrb-scorecard-qa-') as tmp:
    tmp=Path(tmp)
    for tid in ['R03','C01','R01','X04','X05']:
        submission={'task_id':tid,'artifacts':{name:'SYNTHETIC UI QA FIXTURE, NOT A CANDIDATE RESULT\n' for name in spec(tid)['required_artifacts']}}
        review_packet(tid,submission,tmp/tid,backend='none')
    subprocess.run(['node',str(ROOT/'scripts/scorecard/qa/logic_tests.cjs'),str(tmp)],check=True)
    for tid in ['R03','X05']:
        submission=json.loads((tmp/tid/'submission.json').read_text())
        report=attach_review(submission,tmp/tid/'browser-checked.json')
        assert report['review_points']==50
        assert report['completion_status']=='failed'
        assert report['quality_qualified'] is False
        print('PASS actual attach_review consumes JS-exported',tid,'with preserved failure state')
    result_path=ROOT/'validation/v1.1/scorecard-test-results.json'
    data=json.loads(result_path.read_text())
    data['cli_round_trips']=['R03: manual 50, core failed, quality_qualified false','X05: manual 50, core failed, audio missing branch, quality_qualified false']
    result_path.write_text(json.dumps(data,indent=2)+'\n')
