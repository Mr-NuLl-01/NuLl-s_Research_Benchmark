"""Optional V1.1 video bundles: explicit media inputs and manual-only evaluation.

No model API, video quality metric, candidate execution, or automatic score is used.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import shutil
import tempfile

from . import __version__
from .provenance import fingerprint

VIDEO_IDS = ('X04', 'X05')
TRACKS = {'X04': 'A', 'X05': 'B'}
SCENES = ((0, 1.5), (1.5, 4), (4, 5.5), (5.5, 7), (7, 8.5), (8.5, 10))


def data_root():
    root = Path(__file__).resolve().parents[1] / 'sources/v1.1/signal-in-motion'
    if not root.is_dir():
        import sys
        root = Path(sys.prefix) / 'share/null-research-benchmark/sources/v1.1/signal-in-motion'
    if not root.is_dir():
        raise ValueError('Video dataset is missing; install the full V1.1 package, including its binary assets.')
    return root


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _mapping(task_id):
    if task_id not in VIDEO_IDS:
        raise ValueError('Not a V1.1 video task: ' + task_id)
    letter = TRACKS[task_id]
    entries = [(f'tracks/{letter}/TASK.md', 'TASK.md'),
               (f'tracks/{letter}/COPY.txt', 'COPY.txt'),
               ('shared_assets/source.mp4', 'source.mp4'),
               ('shared_assets/soundtrack.wav', 'soundtrack.wav'),
               ('PACKAGE_LICENSE_STATUS.md', 'LICENSES/PACKAGE_LICENSE_STATUS.md'),
               ('LICENSE.txt', 'LICENSES/NRB-MIT-LICENSE.txt'),
               ('evaluator/run_record.template.json', 'RUN_RECORD.template.json')]
    root = data_root()
    for source, dest in [('shared_assets/fonts', 'assets'), ('shared_assets/LICENSES', 'LICENSES')]:
        for path in sorted((root / source).rglob('*')):
            if path.is_file():
                entries.append((path.relative_to(root).as_posix(), dest + '/' + path.relative_to(root / source).as_posix()))
    if task_id == 'X05':
        entries.append(('tracks/B/reference.mp4', 'reference.mp4'))
    return entries


def input_manifest(task_id, verify=False):
    root = data_root()
    manifest = _read(root / 'MATERIAL_MANIFEST.json')
    known = {x['path']: x for x in manifest['files']}
    files = []
    for source, target in _mapping(task_id):
        if source not in known:
            raise ValueError('Video input absent from material manifest: ' + source)
        expected = known[source]
        path = root / source
        if not path.is_file() or path.is_symlink() or path.stat().st_size != expected['bytes']:
            raise ValueError('Missing, unsupported or wrong-sized video input: ' + source)
        if verify and fingerprint(path.read_bytes()) != expected['sha256']:
            raise ValueError('Video material hash mismatch: ' + source)
        files.append({'path': target, 'bytes': expected['bytes'], 'sha256': expected['sha256']})
    files.sort(key=lambda x: x['path'])
    common = [x for x in files if x['path'] not in ('TASK.md', 'reference.mp4')]
    return {'schema': 'nrb-video-input-v1.1', 'benchmark_version': __version__,
            'task_id': task_id, 'track': TRACKS[task_id], 'files': files,
            'packet_hash': fingerprint(files), 'common_assets_sha256': fingerprint(common),
            'status': 'prepared_only_not_a_model_test'}


def task(task_id):
    root = data_root()
    rubric = _read(Path(__file__).with_name('video_rubrics.json'))[task_id]
    return {'id': task_id, 'title': ('SIGNAL IN MOTION: prompt-driven video design' if task_id == 'X04'
                                  else 'SIGNAL IN MOTION: reference video reconstruction'),
            'track': rubric['profile'], 'difficulty': 4, 'format': 'md', 'packet_kind': 'media_directory',
            'content': (root / f'tracks/{TRACKS[task_id]}/TASK.md').read_text(encoding='utf-8'),
            'capabilities': ['video', 'compositing', 'motion_design', 'typography'] + (['reference_reconstruction'] if task_id == 'X05' else []),
            'language': None, 'modality': ['text', 'video', 'audio', 'code'], 'time_budget_s': 3600,
            'required_artifacts': ['output.mp4', 'source.zip', 'README.md', 'LICENSES.md', 'run-record.json'],
            'optional_artifacts': [], 'modal_observation_artifacts': ['output.mp4'],
            'review_extension': 'signal_in_motion', 'rubric': rubric['rubric'],
            'essential': [
                {'id': 'video', 'requirement': 'A playable original 10-second video with all six specified scenes is delivered.'},
                {'id': 'source', 'requirement': 'The supplied actor footage is used continuously without invented action, looping or copied reference frames.'},
                {'id': 'depth', 'requirement': 'Orbit text and ribbon have observable behind/in-front depth changes, not only opacity changes.'},
                {'id': 'audio', 'requirement': 'The supplied soundtrack is included; actual output listening and audio checks are recorded separately from visual points.'},
                {'id': 'handoff', 'requirement': 'Editable project, reproduction instructions, factual run record and correct third-party attribution are delivered.'}]}


def candidate(task_id, seed=17):
    t = task(task_id)
    inputs = input_manifest(task_id, verify=True)
    return {'task_id': task_id, 'seed': seed, 'format': 'md', 'content': t['content'],
            'packet_hash': inputs['packet_hash'], 'packet_kind': 'media_directory',
            'input_manifest': inputs}


def generate_pack(task_id, dest, seed=17):
    """Copy an allowlisted bundle, hash-checking before and after. Never overwrite."""
    root = data_root().resolve()
    dest = Path(dest).absolute()
    if dest.exists() or dest.is_symlink():
        raise ValueError('Use a new candidate directory: ' + str(dest))
    if root == dest.resolve() or root in dest.resolve().parents:
        raise ValueError('Candidate directory must be outside the source dataset.')
    manifest = input_manifest(task_id, verify=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.nrb-video-', dir=dest.parent))
    try:
        expected = {x['path']: x for x in manifest['files']}
        for source, target in _mapping(task_id):
            out = staging / target
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / source, out)
            if fingerprint(out.read_bytes()) != expected[target]['sha256']:
                raise ValueError('Copied video input hash mismatch: ' + target)
        manifest = dict(manifest, seed=seed)
        (staging / 'INPUT_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # A destination appearing while files were copied must not be overwritten.
        if dest.exists() or dest.is_symlink():
            raise ValueError('Candidate directory appeared during export: ' + str(dest))
        staging.rename(dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def add_review_protocol(ledger):
    """Add blank evidence fields. This function asserts no media was observed."""
    task_id = ledger['task_id']
    inputs = input_manifest(task_id, verify=True)
    files = {x['path']: x for x in inputs['files']}
    output_sha = ledger['artifact_manifest'].get('output.mp4', {}).get('sha256')
    def obs(name, action, digest):
        return {'artifact': name, 'sha256': digest, 'action': action, 'performed': False, 'evidence': ''}
    observations = [obs('source.mp4', 'watched_full', files['source.mp4']['sha256']),
                    obs('output.mp4', 'listened_full', output_sha)]
    if task_id == 'X05':
        observations.append(obs('reference.mp4', 'watched_full', files['reference.mp4']['sha256']))
    ledger['media_review'] = {
        'schema': 'nrb-video-observation-v1.1', 'task_id': task_id,
        'input_packet_hash': inputs['packet_hash'],
        'audio_check': {'status': 'unassessed', 'evidence': '', 'expected_soundtrack_sha256': files['soundtrack.wav']['sha256']},
        'observations': observations,
        'scenes': [{'scene': n, 'interval_seconds': list(interval), 'observed': False,
                    'timecodes_seconds': [], 'evidence': ''} for n, interval in enumerate(SCENES, 1)],
        'protocol': 'Watch the full source and output, and the full reference for X05. Listen to the output. Record concrete timecoded scene findings, including orbit and ribbon depth changes. Probe data is technical evidence, not a visual-quality score. Audio has no extra visual-score weight.'}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _timecode(value, lo, hi):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and lo <= value <= hi
    except (OverflowError, TypeError):
        return False


def validate_media_review(ledger, review_directory):
    """Require honest observation records before a video review is finalized.

A missing audio stream may be recorded as missing, with a failed audio gate, while
visual observations remain assessable. Unavailable viewing leaves the review open.
"""
    output = [o for o in ledger.get('observations', []) if isinstance(o, dict) and o.get('artifact') == 'output.mp4']
    output_sha = ledger['artifact_manifest'].get('output.mp4', {}).get('sha256')
    if (len(output) != 1 or output[0].get('action') != 'watched' or output[0].get('performed') is not True
            or not output_sha or output[0].get('sha256') != output_sha or not _text(output[0].get('evidence'))):
        raise ValueError('Actual output video watching is required before any visual score is finalized')
    expected = {'task_id': ledger['task_id'], 'artifact_manifest': ledger['artifact_manifest']}
    add_review_protocol(expected)
    expected = expected['media_review']
    # Evidence must bind the evaluator files actually supplied beside the ledger,
    # not merely the unchanged originals in the repository.
    input_root = Path(review_directory) / 'inputs'
    if input_root.is_symlink() or not input_root.is_dir():
        raise ValueError('Video review input directory is missing or is a symlink')
    expected_inputs = dict(input_manifest(ledger['task_id'], verify=True), seed=ledger['seed'])
    manifest_path = input_root / 'INPUT_MANIFEST.json'
    if manifest_path.is_symlink() or not manifest_path.is_file() or _read(manifest_path) != expected_inputs:
        raise ValueError('Video review input manifest changed')
    expected_names = {x['path'] for x in expected_inputs['files']} | {'INPUT_MANIFEST.json'}
    actual_names = set()
    for item in input_root.rglob('*'):
        if item.is_symlink():
            raise ValueError('Symlink in video review inputs')
        if item.is_file(): actual_names.add(item.relative_to(input_root).as_posix())
    if actual_names != expected_names:
        raise ValueError('Video review input file set changed')
    for item in expected_inputs['files']:
        file = input_root / item['path']
        if file.stat().st_size != item['bytes'] or fingerprint(file.read_bytes()) != item['sha256']:
            raise ValueError('Video review input bytes changed: ' + item['path'])
    review = ledger.get('media_review')
    if not isinstance(review, dict):
        raise ValueError('Video media_review is required; generate a fresh evaluation skeleton.')
    for key in ('schema', 'task_id', 'input_packet_hash'):
        if review.get(key) != expected[key]:
            raise ValueError('Video observation protocol binding differs: ' + key)
    audio = review.get('audio_check', {})
    if audio.get('expected_soundtrack_sha256') != expected['audio_check']['expected_soundtrack_sha256']:
        raise ValueError('Soundtrack hash binding differs')
    if audio.get('status') not in ('present', 'missing') or not _text(audio.get('evidence')):
        raise ValueError('Record observed soundtrack status and evidence; unassessed audio is not finalized')
    gates = {x['id']: x['outcome'] for x in ledger.get('essential_review', [])}
    if audio['status'] == 'missing' and gates.get('audio') != 'fail':
        raise ValueError('Missing soundtrack requires a failed audio core requirement')
    observations = review.get('observations', [])
    if not isinstance(observations, list) or len(observations) != len(expected['observations']):
        raise ValueError('Video source/reference/listening observations missing or duplicated')
    for actual, exp in zip(observations, expected['observations']):
        if not isinstance(actual, dict) or any(actual.get(k) != exp[k] for k in ('artifact', 'sha256', 'action')):
            raise ValueError('Video observation artifact/action/hash binding differs')
        if type(actual.get('performed')) is not bool or not _text(actual.get('evidence')):
            raise ValueError('Video observations require a boolean and concrete evidence')
        allowed_missing_audio = actual['action'] == 'listened_full' and audio['status'] == 'missing'
        if not actual['performed'] and not allowed_missing_audio:
            raise ValueError('Actual source/reference playback and output listening are required')
        if actual['performed'] and not actual['sha256']:
            raise ValueError('Cannot observe absent output bytes')
    scenes = review.get('scenes', [])
    if not isinstance(scenes, list) or len(scenes) != 6:
        raise ValueError('All six scene observations are required')
    for row, exp in zip(scenes, expected['scenes']):
        if not isinstance(row, dict) or type(row.get('scene')) is not int or row.get('scene') != exp['scene'] or row.get('interval_seconds') != exp['interval_seconds']:
            raise ValueError('Scene identity/interval changed')
        if row.get('observed') is not True or not _text(row.get('evidence')):
            raise ValueError('Each scene needs actual observation and concrete findings')
        times = row.get('timecodes_seconds')
        lo, hi = exp['interval_seconds']
        if not isinstance(times, list) or not times or any(not _timecode(x, lo, hi) for x in times):
            raise ValueError('Scene timecodes must be finite measured seconds within its interval')


def evaluate_skeleton(task_id, submission, dest, seed=17):
    if task_id not in VIDEO_IDS:
        raise ValueError('evaluate-skeleton is for X04/X05; use review-packet for legacy tasks')
    from .grading import review_packet
    # Use no execution. Subjective scores and all observations remain unassessed.
    result = review_packet(task_id, submission, dest, seed, backend='none')
    dest = Path(dest)
    # Evaluator input directory is explicitly separate from submitted artifacts.
    (dest / 'video-rubric.md').write_text((data_root() / 'evaluator/rubric.md').read_text(encoding='utf-8'), encoding='utf-8')
    return dict(result, scoring='manual_only_100', model_run_performed=False,
                input_directory=str(dest / 'inputs'))
