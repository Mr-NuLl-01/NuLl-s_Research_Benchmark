"""Media input/review-contract tests. Synthetic fixtures are NOT model scores."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nrb_v1.adapters import run_command
from nrb_v1.cli import main
from nrb_v1.grading import attach_review, grade, review_packet, summarize
from nrb_v1.packets import candidate, freeze, public_metadata
from nrb_v1.provenance import fingerprint, identity, seal
from nrb_v1.registry import ids, spec
from nrb_v1.video import add_review_protocol, data_root, evaluate_skeleton, generate_pack, input_manifest, validate_media_review

ROOT = Path(__file__).resolve().parents[1]


def synthetic_submission(tid='X04'):
    return {'task_id': tid, 'artifacts': {p: 'synthetic contract fixture, not real media' for p in spec(tid)['required_artifacts']}, 'answer': {}}


def reviewed_fixture(ledger):
    """Populate a synthetic validator fixture, never an actual model review."""
    value = copy.deepcopy(ledger)
    value['reviewer'].update(type='human', id='synthetic-contract-fixture')
    for item in value['criteria']:
        item.update(score=4, evidence='synthetic fixture only', rationale='validator positive control')
    for item in value['essential_review']:
        item.update(outcome='pass', evidence='synthetic fixture only', rationale='validator positive control')
    for item in value['observations'] + value['media_review']['observations']:
        item.update(performed=True, evidence='synthetic fixture only; no real viewing asserted')
    value['media_review']['audio_check'].update(status='present', evidence='synthetic fixture only')
    for item in value['media_review']['scenes']:
        item.update(observed=True, timecodes_seconds=[sum(item['interval_seconds'])/2], evidence='synthetic fixture only')
    return value


class VideoV11Tests(unittest.TestCase):
    def test_registry_appends_ids_and_preserves_required_tracks(self):
        self.assertEqual(ids('video'), ['X04', 'X05'])
        self.assertEqual(ids('optional'), ['X01', 'X02', 'X03', 'X04', 'X05'])
        self.assertEqual(len(ids('required')), 16)
        self.assertEqual(len(ids('all')), 21)
        self.assertEqual(spec('X02')['track'], 'optional')
        for tid, profile in [('X04', 'optional_video_a'), ('X05', 'optional_video_b')]:
            task = spec(tid)
            self.assertEqual(task['track'], profile)
            self.assertEqual(sum(x['weight'] for x in task['rubric']), 100)
            self.assertEqual(task['modal_observation_artifacts'], ['output.mp4'])

    def test_legacy_frozen_bytes_and_material_manifest(self):
        proc = subprocess.run([sys.executable, str(ROOT/'scripts/v1/check_v11_materials.py')], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)['passed'])

    def test_media_metadata_binds_whole_directory_not_prompt_only(self):
        for tid in ids('video'):
            packet = candidate(tid)
            self.assertNotEqual(packet['packet_hash'], fingerprint(packet['content'].encode()))
            self.assertEqual(packet['packet_hash'], input_manifest(tid)['packet_hash'])
            self.assertEqual(public_metadata(tid)['file'], tid+'/TASK.md')
            self.assertEqual(public_metadata(tid)['packet_kind'], 'media_directory')

    def test_generated_packs_are_isolated_and_share_exact_common_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            a = generate_pack('X04', Path(temp)/'A')
            b = generate_pack('X05', Path(temp)/'B')
            self.assertEqual(a['common_assets_sha256'], b['common_assets_sha256'])
            self.assertNotEqual(a['packet_hash'], b['packet_hash'])
            self.assertFalse((Path(temp)/'A/reference.mp4').exists())
            self.assertTrue((Path(temp)/'B/reference.mp4').is_file())
            for folder, manifest in [('A', a), ('B', b)]:
                actual = {p.relative_to(Path(temp)/folder).as_posix() for p in (Path(temp)/folder).rglob('*') if p.is_file()}
                self.assertEqual(actual, {x['path'] for x in manifest['files']} | {'INPUT_MANIFEST.json'})
                self.assertFalse(any('demo_project' in x or 'reference_qa' in x or 'rubric' in x for x in actual))
                for item in manifest['files']:
                    self.assertEqual(fingerprint((Path(temp)/folder/item['path']).read_bytes()), item['sha256'])

    def test_pack_refuses_existing_destination_and_wrong_task(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): generate_pack('X04', temp)
            with self.assertRaises(ValueError): generate_pack('X02', Path(temp)/'out')
            with self.assertRaises(ValueError): generate_pack('X04', data_root()/'nested-test-never-created')

    def test_hash_corruption_is_detected_before_copy(self):
        actual = fingerprint
        with tempfile.TemporaryDirectory() as temp, patch('nrb_v1.video.fingerprint', side_effect=lambda value: '0'*64 if isinstance(value, bytes) else actual(value)):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): generate_pack('X04', Path(temp)/'out')
            self.assertFalse((Path(temp)/'out').exists())

    def test_plain_grade_is_manual_and_unassessed(self):
        for tid in ids('video'):
            report = grade(tid, synthetic_submission(tid), backend='none')
            self.assertEqual(report['auto_max'], 0)
            self.assertIsNone(report['auto_points'])
            self.assertIsNone(report['total'])
            self.assertIsNone(report['review_points'])
            self.assertEqual(report['completion_status'], 'pending_review')

    def test_skeleton_contains_inputs_and_false_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'review'
            result = evaluate_skeleton('X05', synthetic_submission('X05'), dest)
            self.assertFalse(result['model_run_performed'])
            self.assertTrue((dest/'inputs/reference.mp4').is_file())
            ledger = json.loads((dest/'review.json').read_text())
            self.assertTrue(all(x['score'] is None for x in ledger['criteria']))
            self.assertTrue(all(x['performed'] is False for x in ledger['media_review']['observations']))
            self.assertTrue(all(x['observed'] is False for x in ledger['media_review']['scenes']))
            with self.assertRaises(ValueError): attach_review(synthetic_submission('X05'), dest/'review.json')

    def test_reference_listening_scene_and_hash_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            review_packet('X05', synthetic_submission('X05'), Path(temp)/'review', backend='none')
            ledger = reviewed_fixture(json.loads((Path(temp)/'review/review.json').read_text()))
            validate_media_review(ledger, Path(temp)/'review')
            changes = [
                lambda x: x.pop('media_review'),
                lambda x: x['media_review']['observations'][-1].update(performed=False),
                lambda x: x['media_review']['observations'][1].update(performed=False),
                lambda x: x['media_review']['observations'][0].update(sha256='0'*64),
                lambda x: x['media_review']['scenes'][0].update(timecodes_seconds=[True]),
                lambda x: x['media_review']['scenes'][0].update(timecodes_seconds=[float('nan')]),
                lambda x: x['media_review']['scenes'][0].update(timecodes_seconds=[10**400]),
                lambda x: x['media_review']['scenes'][0].update(scene=True),
                lambda x: x['media_review']['scenes'][0].update(timecodes_seconds=[8]),
                lambda x: x['media_review']['scenes'][1].update(observed=False),
                lambda x: x['media_review']['scenes'][2].update(evidence=''),
                lambda x: x['media_review']['audio_check'].update(status='missing'),
            ]
            for change in changes:
                altered = copy.deepcopy(ledger); change(altered)
                with self.subTest(change=change), self.assertRaises(ValueError): validate_media_review(altered, Path(temp)/'review')

    def test_actual_evaluator_input_bytes_and_symlinks_are_checked(self):
        for filename in ('source.mp4', 'reference.mp4', 'soundtrack.wav'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)/'review'
                submission = synthetic_submission('X05')
                evaluate_skeleton('X05', submission, dest)
                ledger = reviewed_fixture(json.loads((dest/'review.json').read_text()))
                (dest/'review.json').write_text(json.dumps(ledger))
                target = dest/'inputs'/filename
                with target.open('r+b') as stream:
                    first = stream.read(1); stream.seek(0); stream.write(bytes([first[0] ^ 1]))
                with self.assertRaisesRegex(ValueError, 'input bytes changed'):
                    attach_review(submission, dest/'review.json')
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'review'
            submission=synthetic_submission()
            review_packet('X04', submission, dest, backend='none')
            ledger=reviewed_fixture(json.loads((dest/'review.json').read_text()))
            (dest/'review.json').write_text(json.dumps(ledger))
            (dest/'inputs/source.mp4').unlink()
            (dest/'inputs/source.mp4').symlink_to(data_root()/'shared_assets/source.mp4')
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                attach_review(submission, dest/'review.json')

    def test_failed_gates_never_allow_unwatched_visual_credit(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'review'
            submission = synthetic_submission()
            review_packet('X04', submission, dest, backend='none')
            ledger = reviewed_fixture(json.loads((dest/'review.json').read_text()))
            for gate in ledger['essential_review']: gate['outcome'] = 'fail'
            ledger['observations'][0]['performed'] = False
            (dest/'review.json').write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError, 'output video watching'):
                attach_review(submission, dest/'review.json')

    def test_missing_audio_is_separate_failed_gate_not_new_score_weight(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'review'
            submission = synthetic_submission()
            review_packet('X04', submission, dest, backend='none')
            ledger = reviewed_fixture(json.loads((dest/'review.json').read_text()))
            ledger['media_review']['audio_check'].update(status='missing', evidence='synthetic missing-stream fixture')
            ledger['media_review']['observations'][1]['performed'] = False
            next(x for x in ledger['essential_review'] if x['id']=='audio')['outcome']='fail'
            (dest/'review.json').write_text(json.dumps(ledger))
            report = attach_review(submission, dest/'review.json')
            self.assertEqual(report['total'], 100)
            self.assertEqual(report['completion_status'], 'failed')
            self.assertFalse(report['quality_qualified'])

    def test_video_profiles_never_combine_with_each_other_or_science(self):
        reports = []
        with tempfile.TemporaryDirectory() as temp:
            for tid in ids('video'):
                dest = Path(temp)/tid
                submission = synthetic_submission(tid)
                review_packet(tid, submission, dest, backend='none')
                ledger = reviewed_fixture(json.loads((dest/'review.json').read_text()))
                if tid == 'X05':
                    for item in ledger['criteria']: item['score'] = 0
                (dest/'review.json').write_text(json.dumps(ledger))
                reports.append(attach_review(submission, dest/'review.json'))
        summary = summarize(reports, 'video')
        self.assertEqual(set(summary['profiles']), {'optional_video_a', 'optional_video_b'})
        self.assertEqual(summary['profiles']['optional_video_a']['mean_total'], 100)
        self.assertEqual(summary['profiles']['optional_video_b']['mean_total'], 0)
        self.assertIsNone(summary['mean_total'])
        self.assertTrue(all(x['automatic_mean_of_70'] is None for x in summary['profiles'].values()))

    def test_external_rubric_is_identity_bound_and_mixed_hashes_rejected(self):
        from nrb_v1 import provenance
        rubric_path = ROOT/'nrb_v1/video_rubrics.json'
        original = Path.read_bytes
        baseline = identity()
        with patch.object(Path, 'read_bytes', lambda path: original(path)+b' ' if path==rubric_path else original(path)):
            self.assertNotEqual(identity()['evaluator_digest'], baseline['evaluator_digest'])
        first=grade('X04',synthetic_submission(),seed=17,backend='none')
        second=grade('X04',synthetic_submission(),seed=18,backend='none')
        second['rubric_hash']='0'*64
        second['report_hash']=seal(second)
        with self.assertRaisesRegex(ValueError, 'per-task rubric'):
            summarize([first,second], 'X04')

    def test_text_only_adapter_rejects_video_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'should-not-exist'
            with self.assertRaisesRegex(ValueError, 'complete media bundles'):
                run_command([sys.executable, '-c', 'pass'], dest, 'X04')
            self.assertFalse(dest.exists())

    def test_cli_generate_and_evaluate_skeleton_interfaces(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch('builtins.print'):
                self.assertEqual(main(['generate-pack','--task','X04','--dest',str(root/'input')]),0)
                submission=root/'submission.json';submission.write_text(json.dumps(synthetic_submission()))
                self.assertEqual(main(['evaluate-skeleton','--task','X04','--submission',str(submission),'--dest',str(root/'review')]),0)
            self.assertTrue((root/'input/INPUT_MANIFEST.json').is_file())
            self.assertTrue((root/'review/review.json').is_file())

    def test_files_export_contains_real_media_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'export'
            manifest=freeze(dest, 'X04')
            self.assertEqual(manifest['tasks'][0]['file'],'X04/TASK.md')
            self.assertTrue((dest/'X04/source.mp4').is_file())
            self.assertFalse((dest/'X04.md').exists())


if __name__ == '__main__': unittest.main()
