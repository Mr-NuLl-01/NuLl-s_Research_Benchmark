#!/usr/bin/env python3
"""Probe the actual V2 Docker execution path using an already-built image.

Runs one P01 reference, one deliberately wrong P01 candidate, and one small
auditable isolation probe through the same executor used by V2 grading.
No image build, model/provider call, broad filesystem scan, or full-suite rerun.
Missing Docker or image is unavailable and exits nonzero, never an isolation pass.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nrb_v1.execution import execute
from nrb_v1.provenance import fingerprint
from nrb_v2 import __version__
from nrb_v2.grading import grade, identity, validate_report
from nrb_v2.registry import module


PROBE = r'''
import errno
import importlib.util
import os
from pathlib import Path
import socket
import sys

def solve(problem):
    nonce = problem['nonce']
    imports = {name: importlib.util.find_spec(name) is not None
               for name in ('nrb', 'nrb_v1', 'nrb_v2')}
    # Only known boundary paths are inspected; no recursive host/image search.
    forbidden = ('/task/nrb_v1', '/task/nrb_v2', '/task/.git', '/grader',
                 '/solution', '/repo', '/var/run/docker.sock', '/run/docker.sock')
    present, absent, denied = [], [], []
    for name in forbidden:
        try:
            Path(name).lstat()
        except PermissionError:
            denied.append(name)
        except FileNotFoundError:
            absent.append(name)
        else:
            present.append(name)
    files = sorted(p.name for p in Path('/task').iterdir())
    symlinks = [p.name for p in Path('/task').iterdir() if p.is_symlink()]
    mounts = {}
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        before, after = line.split(' - ', 1)
        fields = before.split()
        if fields[4] in ('/', '/task', '/tmp'):
            mounts[fields[4]] = {'options': fields[5].split(','),
                                 'filesystem': after.split()[0]}
    proc = {}
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith(('NoNewPrivs:', 'CapEff:')):
            key, value = line.split(':', 1)
            proc[key] = value.strip()
    writes = {}
    for label, directory in [('root', '/'), ('candidate', '/task'), ('temporary', '/tmp')]:
        path = Path(directory) / ('nrb-boundary-' + nonce)
        try:
            with path.open('x', encoding='utf-8') as stream:
                stream.write('controlled-probe')
        except OSError as exc:
            writes[label] = {'written': False, 'errno': exc.errno, 'error': type(exc).__name__}
        else:
            writes[label] = {'written': True, 'errno': None, 'error': None}
            path.unlink()
    interfaces = sorted(p.name for p in Path('/sys/class/net').iterdir())
    blocked, network_errno = False, None
    try:
        # TEST-NET-2 is reserved for documentation, not a real service. No data
        # are sent; in a no-network container connect fails with no route.
        with socket.create_connection(('198.51.100.1', 443), timeout=1):
            pass
    except OSError as exc:
        blocked, network_errno = True, exc.errno
    checks = {
        'nonroot_uid_gid': os.getuid() == 65534 and os.geteuid() == 65534 and os.getgid() == 65534,
        'evaluator_not_importable': not any(imports.values()),
        'known_evaluator_and_socket_paths_absent': not present,
        'candidate_mount_only_solution_and_driver': files == ['_driver_nrb.py', 'solution.py'] and not symlinks,
        'root_mount_read_only': 'ro' in mounts.get('/', {}).get('options', []),
        'candidate_mount_read_only': 'ro' in mounts.get('/task', {}).get('options', []),
        'root_write_blocked': writes['root']['written'] is False,
        'candidate_write_blocked': writes['candidate']['written'] is False,
        'temporary_write_allowed': writes['temporary']['written'] is True,
        'no_new_privileges': proc.get('NoNewPrivs') == '1',
        'effective_capabilities_empty': int(proc.get('CapEff', '1'), 16) == 0,
        'loopback_only': interfaces == ['lo'],
        'external_connect_has_no_route': blocked and network_errno in (errno.ENETUNREACH, errno.EHOSTUNREACH),
    }
    return {'nonce': nonce, 'checks': checks, 'uid': os.getuid(), 'gid': os.getgid(),
            'python': sys.version, 'imports': imports, 'candidate_files': files,
            'candidate_symlinks': symlinks, 'present_forbidden_paths': present,
            'absent_forbidden_paths': absent, 'denied_forbidden_paths': denied,
            'mounts': mounts, 'process_security': proc, 'writes': writes,
            'network_interfaces': interfaces, 'connect_errno': network_errno}
'''

PROBE_CHECKS = {
    'nonroot_uid_gid', 'evaluator_not_importable', 'known_evaluator_and_socket_paths_absent',
    'candidate_mount_only_solution_and_driver', 'root_mount_read_only', 'candidate_mount_read_only',
    'root_write_blocked', 'candidate_write_blocked', 'temporary_write_allowed', 'no_new_privileges',
    'effective_capabilities_empty', 'loopback_only', 'external_connect_has_no_route',
}


def _command(argv, timeout=20):
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        raise OSError('Docker command failed: ' + completed.stderr[-1000:].strip())
    return completed.stdout


def run(output, *, image='nrb-v2-python:local', timeout=120):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError('Choose a new evidence filename; existing evidence is never overwritten')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError('timeout must be finite and in (0,3600]')
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    evaluator = identity()
    evidence = {
        'schema': 'nrb-v2-docker-check-v1', 'benchmark_version': __version__,
        'kind': 'actual_candidate_runtime_probe', 'not_model_performance': True,
        'api_provider_calls': 0, 'created_at': datetime.now(timezone.utc).isoformat(),
        'evaluator_identity': evaluator, 'requested_image': image,
        'runtime_status': 'unavailable', 'passed': False, 'checks': {}, 'controls': [],
        'probe_source_sha256': fingerprint(PROBE.encode('utf-8')),
        'scope': 'Observed container boundary for the current image and host via the production V2 executor; not a proof against kernel exploits, arbitrary image contents, or malicious score-report forgery.',
    }
    try:
        docker = shutil.which('docker')
        if docker is None:
            raise FileNotFoundError('Docker executable unavailable; build and start the CI runtime first')
        evidence['docker_server_version'] = _command([docker, 'version', '--format', '{{.Server.Version}}']).strip()
        inspected = json.loads(_command([docker, 'image', 'inspect', image]))
        if not isinstance(inspected, list) or len(inspected) != 1:
            raise ValueError('Expected exactly one runtime image')
        actual = inspected[0]
        # Deliberately exclude arbitrary image environment variables and labels.
        evidence['actual_image'] = {key: actual.get(key) for key in ('Id', 'RepoTags', 'RepoDigests', 'Created', 'Architecture', 'Os')}
        image_id = actual['Id']
        if not isinstance(image_id, str) or not image_id.startswith('sha256:'):
            raise ValueError('Image inspection did not return an immutable Docker image ID')
        nonce = uuid.uuid4().hex
        probe = execute(SimpleNamespace(TASK={'language': 'python'}),
                        {'task_id': 'CONTROL-ISOLATION', 'artifacts': {'solution.py': PROBE}, 'answer': {}},
                        [{'input': {'nonce': nonce}}], backend='docker', timeout=timeout, image=image_id)
        evidence['probe_execution'] = {key: value for key, value in probe.items() if key != 'records'}
        if probe.get('status') == 'unavailable':
            raise OSError(probe.get('error', 'Candidate runtime unavailable'))
        evidence['runtime_status'] = 'executed'
        records = probe.get('records', [])
        value = records[0].get('value') if len(records) == 1 and records[0].get('ok') is True else None
        evidence['probe_output'] = value
        evidence['checks']['probe_executed_by_production_executor'] = probe.get('status') == 'executed' and probe.get('backend') == 'docker'
        evidence['checks']['probe_image_matches_inspected_image'] = probe.get('image_id') == image_id
        evidence['checks']['probe_nonce_roundtrip'] = isinstance(value, dict) and value.get('nonce') == nonce
        reported_checks = value.get('checks', {}) if isinstance(value, dict) else {}
        evidence['checks']['all_boundary_observations_pass'] = (set(reported_checks) == PROBE_CHECKS and
                                                               all(type(v) is bool and v for v in reported_checks.values()))
        for label, submission in [
            ('reference', dict(module('P01').reference_submission(17), task_id='P01')),
            ('wrong_empty_output', {'task_id': 'P01', 'artifacts': {'solution.py': 'def solve(problem): return {}\n'}, 'answer': {}}),
        ]:
            report = grade('P01', submission, seed=17, backend='docker', timeout=timeout, image=image_id)
            validate_report(report)
            controls = {
                'executed': report['execution']['status'] == 'executed',
                'image_matches': report['execution'].get('image_id') == image_id,
                'evaluator_matches': report['evaluator_fingerprint'] == evaluator['evaluator_fingerprint'],
                'no_manual_review': report['manual_review_required'] is False,
                'expected_score': report['score'] == 100 if label == 'reference' else
                                  report['score'] is not None and report['score'] < 100,
                'expected_completion': report['status'] == ('passed' if label == 'reference' else 'failed'),
            }
            evidence['controls'].append({'task_id': 'P01', 'label': label, 'not_model_performance': True,
                                         'checks': controls, 'passed': all(controls.values()), 'report': report})
        evidence['checks']['reference_and_wrong_candidate_observed'] = len(evidence['controls']) == 2 and all(c['passed'] for c in evidence['controls'])
        evidence['checks']['evaluator_source_unchanged'] = identity()['evaluator_fingerprint'] == evaluator['evaluator_fingerprint']
        evidence['passed'] = all(evidence['checks'].values())
        if not evidence['passed']:
            evidence['runtime_status'] = 'failed'
    except (OSError, FileNotFoundError) as exc:
        evidence.update(runtime_status='unavailable', error=type(exc).__name__ + ': ' + str(exc)[:2000])
    except (ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        evidence.update(runtime_status='failed', error=type(exc).__name__ + ': ' + str(exc)[:2000])
    evidence['wall_seconds'] = time.monotonic() - started
    evidence['report_hash'] = fingerprint(evidence)
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--image', default='nrb-v2-python:local')
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args(argv)
    try:
        result = run(args.out, image=args.image, timeout=args.timeout)
    except (OSError, ValueError) as exc:
        print(json.dumps({'passed': False, 'error': type(exc).__name__ + ': ' + str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({'passed': result['passed'], 'runtime_status': result['runtime_status'], 'evidence': str(args.out)}))
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
