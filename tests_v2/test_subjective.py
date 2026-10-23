"""Protocol controls, not model/visual-quality evaluations."""
from copy import deepcopy
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

from nrb_v2.subjective import (
    SUBJECTIVE_IDS, blank_review, candidate_inputs, get_task, rubric_hash,
    rubric_spec, score_review, tasks,
)

ROOT = Path(__file__).resolve().parents[1]
CONTROL = 'CONTROL ONLY: simulated reviewer evidence for scoring tests; no model result.'


def filled_control(task_id='R01', mode=None, kind='human'):
    review = blank_review(task_id, mode, reviewer_id='test-reviewer',
                          reviewer_kind=kind, submission_id='synthetic-control')
    for r in review['ratings']:
        r.update(level=4, evidence=CONTROL)
    for r in review['requirements']:
        r.update(status='pass', evidence=CONTROL)
    for r in review['observations']:
        r.update(status='observed', evidence=CONTROL)
    return review


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.external_dependencies = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'img':
            self.images.append(a.get('src', ''))
        if tag in ('img', 'script', 'iframe', 'video', 'audio', 'source'):
            value = a.get('src', '')
            if value.startswith(('http:', 'https:', '//')):
                self.external_dependencies.append(value)
        if tag == 'link' and a.get('rel') == 'stylesheet' and a.get('href', '').startswith(('http:', 'https:', '//')):
            self.external_dependencies.append(a['href'])


class SubjectiveAssets(unittest.TestCase):
    def test_seven_tasks_eight_mode_rubrics(self):
        self.assertEqual(tuple(t['id'] for t in tasks()), SUBJECTIVE_IDS)
        count = 0
        for tid in SUBJECTIVE_IDS:
            for mode in ('A', 'B') if tid == 'R06' else (None,):
                spec = rubric_spec(tid, mode)
                self.assertEqual(sum(d['weight'] for d in spec['rubric']), 100)
                self.assertEqual(len({d['id'] for d in spec['rubric']}), len(spec['rubric']))
                self.assertTrue(spec['required_observations'])
                count += 1
        self.assertEqual(count, 8)

    def test_allowlisted_materials_exist_and_are_separate(self):
        for tid in SUBJECTIVE_IDS:
            for mode in ('A', 'B') if tid == 'R06' else (None,):
                files = candidate_inputs(tid, mode)
                self.assertEqual(files[0]['path'], tid + '.md')
                self.assertEqual(len({f['path'] for f in files}), len(files))
                for f in files:
                    p = ROOT / f['source']
                    self.assertTrue(p.is_file(), f)
                    self.assertTrue(p.stat().st_size > 0, f)
                    self.assertTrue(p.resolve().is_relative_to(ROOT.resolve()), f)
                    self.assertNotIn('subjective_rubrics', f['source'])
                    self.assertNotIn('/evaluator/', f['source'])
                    self.assertNotIn('/demo_project/', f['source'])

    def test_video_modes_share_inputs_except_declared_reference_and_mode(self):
        a = candidate_inputs('R06', 'A'); b = candidate_inputs('R06', 'B')
        amap = {f['path']: f['source'] for f in a if '/mode-' not in f['path']}
        bmap = {f['path']: f['source'] for f in b if '/mode-' not in f['path']}
        self.assertNotIn('assets/R06/reference.mp4', amap)
        self.assertIn('assets/R06/reference.mp4', bmap)
        bmap.pop('assets/R06/reference.mp4')
        self.assertEqual(amap, bmap)
        self.assertNotIn('R06-A-reference', {x['id'] for x in rubric_spec('R06', 'A')['rubric']})
        self.assertIn('R06-B-reference', {x['id'] for x in rubric_spec('R06', 'B')['rubric']})

    def test_real_figures_and_offline_reading_room(self):
        for path, image_count in [('R01/style-references.html', 3), ('R05/reading-room.html', 17)]:
            data = (ROOT / 'tasks/v2.0/assets' / path).read_text(encoding='utf-8')
            parser = Images(); parser.feed(data)
            self.assertEqual(len(parser.images), image_count)
            if path.startswith('R01/'):
                self.assertTrue(all(src.startswith('data:image/') for src in parser.images))
            else:
                inputs = {item['path']: item['source'] for item in candidate_inputs('R05')}
                for src in parser.images:
                    self.assertTrue(src.startswith('images/') and src.endswith('.png'), src)
                    asset = 'assets/R05/' + src
                    self.assertIn(asset, inputs)
                    image = (ROOT / inputs[asset]).read_bytes()
                    original = ROOT / 'sources/v1/offline-figures' / Path(src).name
                    self.assertEqual(image, original.read_bytes(), src)
            self.assertEqual(parser.external_dependencies, [])
            for title in ('Beyond Bar and Line Graphs', 'Ten Simple Rules', 'misuse of colour'):
                self.assertIn(title, data)
        room = (ROOT / 'tasks/v2.0/assets/R05/reading-room.html').read_text()
        self.assertGreater(len(room), 100_000)
        self.assertIn('S1', room)
        self.assertIn('Methods', room)

    def test_fixture_semantic_controls_are_present(self):
        def rows(path):
            with (ROOT/'tasks/v2.0/assets'/path).open() as stream:
                return list(csv.DictReader(stream))
        paired = rows('H01/paired.csv')
        self.assertEqual(len(paired), 12)
        self.assertEqual(sum(x['batch'] == 'B2' for x in paired), 4)
        d08 = next(x for x in paired if x['device'] == 'D08')
        self.assertLess(float(d08['after_mV']) - float(d08['before_mV']), 0)
        signed = rows('R02/blank_corrected.csv')
        self.assertEqual(sum(x['status'] == 'left_censored' and x['corrected_signal_au'] == '' for x in signed), 2)
        self.assertTrue(any(x['corrected_signal_au'] == '0.0' for x in signed))
        self.assertTrue(any(x['corrected_signal_au'].startswith('-') for x in signed))
        pairs = rows('R05/replication_pairs.csv')
        first = [x for x in pairs if x['variant'] == 'A']
        second = [x for x in pairs if x['variant'] == 'B']
        self.assertEqual(sorted(float(x['after']) for x in first), sorted(float(x['after']) for x in second))
        self.assertNotEqual([x['after'] for x in first], [x['after'] for x in second])

    def test_input_figure_preserved_without_regeneration(self):
        for ext in ('svg', 'png'):
            self.assertEqual((ROOT/f'tasks/v2.0/assets/R04/input-figure.{ext}').read_bytes(),
                             (ROOT/f'sources/v1/synthetic/input-figure.{ext}').read_bytes())


class SubjectiveScoreControls(unittest.TestCase):
    def test_blank_reviews_are_unassessed_not_zero(self):
        for tid in SUBJECTIVE_IDS:
            for mode in ('A', 'B') if tid == 'R06' else (None,):
                result = score_review(blank_review(tid, mode))
                self.assertIsNone(result['score'])
                self.assertIsNone(result['requirements_passed'])
                self.assertEqual(result['rated_weight'], 0)
                self.assertTrue(result['missing_items'])

    def test_full_control_and_exact_weighted_score(self):
        r = filled_control()
        r['ratings'][0]['level'] = 2  # 30 points -> 15
        result = score_review(r)
        self.assertEqual(result['raw_score'], 85)
        self.assertEqual(result['score'], 85)
        self.assertTrue(result['requirements_passed'])

    def test_hard_caps_use_minimum_and_require_evidence(self):
        r = filled_control()
        r['requirements'][0].update(status='fail', evidence='CONTROL: material pairing corruption.')
        r['requirements'][1].update(status='fail', evidence='CONTROL: required vector artifact absent.')
        result = score_review(r)
        self.assertEqual(result['raw_score'], 100)
        self.assertEqual(result['score'], 35)
        self.assertFalse(result['requirements_passed'])
        self.assertEqual(len(result['applied_caps']), 2)
        r['requirements'][0]['evidence'] = ''
        with self.assertRaises(ValueError): score_review(r)

    def test_each_unknown_channel_blocks_final_score(self):
        for section, field, value in [('ratings', 'level', None), ('requirements', 'status', 'unassessed'), ('observations', 'status', 'unassessed')]:
            with self.subTest(section=section):
                r = filled_control(); r[section][0][field] = value
                result = score_review(r)
                self.assertIsNone(result['score'])
                self.assertTrue(result['missing_items'])

    def test_known_missing_media_differs_from_unobserved(self):
        r = filled_control('R06', 'A')
        next(x for x in r['requirements'] if x['id'] == 'actual_video').update(status='fail', evidence='CONTROL: output.mp4 absent from submitted inventory.')
        next(x for x in r['observations'] if x['id'] == 'candidate_video').update(status='missing', evidence='CONTROL: confirmed absent file.')
        self.assertEqual(score_review(r)['score'], 0)
        next(x for x in r['observations'] if x['id'] == 'candidate_video')['status'] = 'unassessed'
        self.assertIsNone(score_review(r)['score'])

    def test_video_protocol_breach_is_not_a_comparable_run(self):
        r = filled_control('R06', 'A')
        self.assertTrue(score_review(r)['protocol_eligible'])
        next(x for x in r['requirements'] if x['id'] == 'mode_integrity').update(status='fail', evidence='CONTROL: candidate was given reference before the A run.')
        result = score_review(r)
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['protocol_eligible'])
        next(x for x in r['requirements'] if x['id'] == 'mode_integrity')['status'] = 'unassessed'
        self.assertIsNone(score_review(r)['protocol_eligible'])
        self.assertTrue(score_review(filled_control('R01'))['protocol_eligible'])

    def test_forged_total_is_ignored(self):
        r = filled_control(); r['score'] = -500; r['total'] = 9999
        self.assertEqual(score_review(r)['score'], 100)

    def test_invalid_ids_types_and_blank_evidence_rejected(self):
        mutations = [
            lambda r: r['ratings'].append(deepcopy(r['ratings'][0])),
            lambda r: r['ratings'].pop(),
            lambda r: r['ratings'][0].update(id='unknown'),
            lambda r: r['ratings'][0].update(level=True),
            lambda r: r['ratings'][0].update(level=2.5),
            lambda r: r['ratings'][0].update(level=float('nan')),
            lambda r: r['ratings'][0].update(level=float('inf')),
            lambda r: r['ratings'][0].update(level=10**1000),
            lambda r: r['ratings'][0].update(level=5),
            lambda r: r['ratings'][0].update(evidence='  '),
            lambda r: r['observations'][0].update(status='pass'),
            lambda r: r['requirements'][0].update(status='observed'),
            lambda r: r['requirements'][0].update(status=[]),
            lambda r: r['observations'][0].update(status={}),
            lambda r: r['observations'][0].update(artifact_sha256='not-a-hash'),
        ]
        for mutate in mutations:
            with self.subTest(mutate=repr(mutate)):
                r = filled_control(); mutate(r)
                with self.assertRaises(ValueError): score_review(r)

    def test_json_integer_values_normalize_to_integer_levels(self):
        for value in (-0.0, 0.0, 1.0, 2.0, 3.0, 4.0):
            r = filled_control(); r['ratings'][0]['level'] = value
            result = score_review(r)
            self.assertIs(type(result['dimension_scores'][0]['level']), int)
            expected = deepcopy(r); expected['ratings'][0]['level'] = int(value)
            self.assertEqual(result, score_review(expected))

    def test_version_hash_and_mode_mismatches_rejected(self):
        for key, value in [('benchmark_version', 'obsolete'), ('rubric_hash', '0'*64),
                           ('packet_hash', '0'*64), ('input_manifest_hash', '0'*64), ('mode', 'A')]:
            r = filled_control(); r[key] = value
            with self.assertRaises(ValueError): score_review(r)
        r = filled_control('R06', 'A'); r['mode'] = 'B'
        with self.assertRaises(ValueError): score_review(r)
        with self.assertRaises(ValueError): candidate_inputs('R06')
        with self.assertRaises(ValueError): blank_review('R06')
        with self.assertRaises(ValueError): rubric_spec('H01', 'A')

    def test_review_binds_candidate_prompt_and_mode_specific_input_bytes(self):
        from nrb_v2.packets import candidate, input_manifest
        for tid in SUBJECTIVE_IDS:
            for mode in ('A', 'B') if tid == 'R06' else (None,):
                review = filled_control(tid, mode)
                expected_packet = candidate(tid, 17)['packet_hash']
                expected_inputs = input_manifest(tid, 17, mode)['sha256']
                self.assertEqual(review['packet_hash'], expected_packet)
                self.assertEqual(review['input_manifest_hash'], expected_inputs)
                result = score_review(review)
                self.assertEqual(result['packet_hash'], expected_packet)
                self.assertEqual(result['input_manifest_hash'], expected_inputs)
                self.assertEqual(result['comparison_key']['input_manifest_hash'], expected_inputs)
                for field in ('packet_hash', 'input_manifest_hash'):
                    old = deepcopy(review); old.pop(field)
                    with self.assertRaises(ValueError): score_review(old)
        a = filled_control('R06', 'A'); b = filled_control('R06', 'B')
        self.assertNotEqual(a['input_manifest_hash'], b['input_manifest_hash'])
        a['input_manifest_hash'] = b['input_manifest_hash']
        with self.assertRaises(ValueError): score_review(a)

    def test_human_and_llm_authority_cannot_share_comparison_key(self):
        h = score_review(filled_control(kind='human'))
        m = score_review(filled_control(kind='llm_provisional'))
        self.assertEqual(h['score'], m['score'])
        self.assertNotEqual(h['comparison_key'], m['comparison_key'])
        self.assertEqual(m['completion_authority'], 'llm_provisional')
        another = filled_control(kind='human'); another['reviewer']['id'] = 'second-reviewer'
        self.assertNotEqual(h['comparison_key'], score_review(another)['comparison_key'])

    def test_reviewer_and_submission_identity_required(self):
        for field in ('reviewer', 'submission_id'):
            r = filled_control()
            if field == 'reviewer': r['reviewer']['id'] = ''
            else: r[field] = ''
            self.assertIsNone(score_review(r)['score'])

    def test_returned_specs_are_not_shared_mutable_authority(self):
        original = rubric_hash('R01')
        task = get_task('R01'); task['rubric'][0]['weight'] = 999
        inputs = candidate_inputs('R06', 'A'); inputs.append({'source':'bad','path':'reference.mp4'})
        self.assertEqual(rubric_hash('R01'), original)
        self.assertFalse(any(f['path'] == 'reference.mp4' for f in candidate_inputs('R06', 'A')))


if __name__ == '__main__':
    unittest.main()
