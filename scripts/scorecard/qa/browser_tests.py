"""Browser/CLI interoperability tests using explicitly synthetic QA fixtures.
These are software tests, not candidate evaluations or genuine human reviews.
Run: PYTHONPATH=/path/to/benchmark python tests/test_scorecard.py
Requires Playwright and Chromium only for tests, never for the shipped HTML.
"""
import json
from pathlib import Path
import tempfile
from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from nrb_v1.grading import review_packet, attach_review
from nrb_v1.registry import spec

ROOT=Path(__file__).resolve().parents[3]
HTML=ROOT/'docs/v1.1/scorecard.html'
results=[]
def ok(name):
    results.append(name)
    print('PASS',name)

with tempfile.TemporaryDirectory(prefix='nrb-scorecard-qa-') as tmp:
    tmp=Path(tmp)
    for tid in ['R03','C01','R01','X04','X05']:
        submission={'task_id':tid,'artifacts':{name:'SYNTHETIC UI QA FIXTURE, NOT A CANDIDATE RESULT\n' for name in spec(tid)['required_artifacts']}}
        review_packet(tid,submission,tmp/tid,backend='none')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
        requests=[];errors=[]
        page.on('request',lambda r:requests.append(r.url))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(HTML.as_uri())
        assert page.locator('#manual-value').inner_text()=='未评'
        assert page.locator('[data-kind="criterion"][data-key="score"]').first.is_disabled()
        assert page.locator('#task-list button').count()==10
        ok('Offline preview: no fabricated values and edits disabled before bound import')
        page.locator('#language').click()
        assert page.locator('#app-title').inner_text()=='Offline review scorecard'
        assert page.locator('html').get_attribute('lang')=='en'
        page.locator('#track-select').select_option('research')
        assert page.locator('#task-list button').count()==6
        ok('ZH/EN toggle and separate track navigation')
        page.locator('#file-input').set_input_files([str(tmp/'R03/review.json'),str(tmp/'R03/automatic.json')])
        assert 'Imported:' in page.locator('#messages').inner_text()
        assert page.locator('#manual-value').inner_text()=='Unassessed'
        assert page.locator('#auto-value').inner_text()=='Not applicable'
        with page.expect_download() as info: page.locator('#export-draft').click()
        draft=tmp/'R03/draft.json';info.value.save_as(draft)
        assert json.loads(draft.read_text())==json.loads((tmp/'R03/review.json').read_text())
        ok('Untouched draft round-trip preserves every field and null score exactly')
        page.locator('#export-checked').click()
        assert 'Record actual reviewer type' in page.locator('#messages').inner_text()
        ok('Checked export blocks missing identity, levels, evidence and rationale')
        page.locator('[data-kind="reviewer"][data-key="type"]').select_option('human')
        page.locator('[data-kind="reviewer"][data-key="id"]').fill('SYNTHETIC UI TEST — not a real reviewer')
        for i in range(5):
            page.locator(f'[data-kind="criterion"][data-index="{i}"][data-key="score"]').select_option('2')
            page.locator(f'[data-kind="criterion"][data-index="{i}"][data-key="evidence"]').fill('Synthetic QA input; not actual quality evidence.')
            page.locator(f'[data-kind="criterion"][data-index="{i}"][data-key="rationale"]').fill('Exercise serialization only; not a model evaluation.')
        assert page.locator('#manual-value').inner_text()=='50'
        assert page.locator('#total-value').inner_text()=='50'
        # Mark a deliberate fail rather than claiming any synthetic artifact passed.
        page.locator('[data-kind="essential"][data-index="0"][data-key="outcome"]').select_option('fail')
        page.locator('[data-kind="essential"][data-index="0"][data-key="evidence"]').fill('Placeholder QA artifact.')
        page.locator('[data-kind="essential"][data-index="0"][data-key="rationale"]').fill('No actual candidate work exists.')
        with page.expect_download() as info:page.locator('#export-checked').click()
        saved=tmp/'R03/checked.json';info.value.save_as(saved)
        submission=json.loads((tmp/'R03/submission.json').read_text())
        report=attach_review(submission,saved)
        assert report['review_points']==50 and report['completion_status']=='failed' and report['quality_qualified'] is False
        ok('Browser export consumed by actual attach_review; core failure survives numeric score')
        page.locator('[data-kind="reviewer"][data-key="type"]').select_option('llm')
        page.locator('#validate').click()
        assert 'LLM review needs actual model' in page.locator('#messages').inner_text()
        assert page.locator('#authority-label').inner_text()=='LLM · provisional'
        ok('LLM reviewer remains provisional; model and prompt fingerprint required')
        page.locator('#file-input').set_input_files([str(tmp/'C01/review.json'),str(tmp/'C01/automatic.json')])
        assert page.locator('#auto-value').inner_text()=='Unassessed'
        assert page.locator('#total-value').inner_text()=='Unassessed'
        assert page.evaluate("records.get('C01').auto.auto_points") == 0
        ok('Unexecuted C01 auto_points=0 is never displayed as an observed zero score')
        # Reject malformed or altered source metadata before replacing any state.
        bad=json.loads((tmp/'R01/review.json').read_text());bad['criteria'][0]['weight']+=1
        (tmp/'bad-weight.json').write_text(json.dumps(bad))
        page.locator('#file-input').set_input_files(str(tmp/'bad-weight.json'))
        assert 'Canonical rubric changed' in page.locator('#messages').inner_text()
        bad=json.loads((tmp/'R01/review.json').read_text());bad['criteria'][0]['score']=False
        (tmp/'bad-score.json').write_text(json.dumps(bad))
        page.locator('#file-input').set_input_files(str(tmp/'bad-score.json'))
        assert 'integer 0..4' in page.locator('#messages').inner_text()
        ok('Tampered rubric weights and boolean scores rejected')
        page.locator('#file-input').set_input_files([str(tmp/'R01/review.json'),str(tmp/'R01/automatic.json')])
        page.locator('[data-kind="essential"][data-index="0"][data-key="outcome"]').select_option('pass')
        page.locator('#validate').click()
        assert 'core pass or video scoring requires actual observation' in page.locator('#messages').inner_text()
        ok('Core pass blocked when required artifact observation is unperformed')
        # Candidate-provided HTML-like evidence is always rendered as text.
        page.locator('[data-kind="criterion"][data-index="0"][data-key="evidence"]').fill('<img src="https://example.invalid/" onerror="window.PWNED=1">')
        page.locator('#language').click()
        assert page.evaluate('window.PWNED===undefined')
        assert page.locator('img').count()==0
        ok('Imported/evidence markup remains escaped text, no injected elements or requests')
        page.locator('#file-input').set_input_files([str(tmp/'X04/review.json'),str(tmp/'X04/automatic.json')])
        assert page.locator('#track-select').input_value()=='optional_video_a'
        assert page.locator('[data-kind="media-scene"][data-key="timecodes_seconds"]').count()==6
        assert page.locator('[data-kind="media-observation"][data-key="performed"]').count()==2
        with page.expect_download() as info:page.locator('#export-draft').click()
        saved=tmp/'X04/browser-draft.json';info.value.save_as(saved)
        assert json.loads(saved.read_text())==json.loads((tmp/'X04/review.json').read_text())
        page.locator('[data-kind="media-scene"][data-index="0"][data-key="timecodes_seconds"]').fill('9')
        page.locator('#export-draft').click()
        assert 'timecodes must be finite seconds within 0–1.5' in page.locator('#messages').inner_text()
        page.locator('[data-kind="media-scene"][data-index="0"][data-key="timecodes_seconds"]').fill('0.1, invalid')
        page.locator('#export-draft').click()
        assert 'timecodes must be finite seconds' in page.locator('#messages').inner_text()
        ok('Video A full protocol round-trips; out-of-range/nonfinite timecodes blocked even for drafts')
        page.locator('#file-input').set_input_files([str(tmp/'X05/review.json'),str(tmp/'X05/automatic.json')])
        assert page.locator('#track-select').input_value()=='optional_video_b'
        assert page.locator('[data-kind="media-observation"][data-key="performed"]').count()==3
        assert page.locator('[data-kind="criterion"][data-key="score"]').count()==8
        page.locator('[data-kind="media-audio"][data-key="status"]').select_option('missing')
        page.locator('#validate').click()
        assert 'Missing soundtrack requires audio core outcome=fail' in page.locator('#messages').inner_text()
        ok('Video B reference observation and 8-dimensional rubric; missing soundtrack gate enforced')
        # Inspect responsive layout and PDF output using real Chromium.
        page.locator('#language').click()
        page.screenshot(path=str(ROOT/'validation/v1.1/scorecard-desktop.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(ROOT/'validation/v1.1/scorecard-mobile.png'),full_page=False)
        page.emulate_media(media='print')
        page.pdf(path=str(ROOT/'validation/v1.1/scorecard-print.pdf'),format='A4',print_background=True)
        assert (ROOT/'validation/v1.1/scorecard-print.pdf').stat().st_size>10000
        ok('390px mobile view has no page overflow; print PDF generated')
        assert not errors,errors
        assert all(url.startswith('file:') for url in requests),requests
        assert page.evaluate('localStorage.length')==0
        ok('No JavaScript runtime errors, external requests or local-storage writes')
        browser.close()
(ROOT/'validation/v1.1/scorecard-browser-results.json').write_text(json.dumps({'scope':'Synthetic software QA only; not model evaluation or genuine artifact assessment','tests_passed':len(results),'checks':results},indent=2)+'\n')
print(f'{len(results)} checks passed')
