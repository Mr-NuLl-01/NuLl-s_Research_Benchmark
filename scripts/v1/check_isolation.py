#!/usr/bin/env python3
"""Build a real V1 Harbor candidate image and inspect its offline boundary.

The check uses only a C01 candidate packet and no oracle solution. It does not
call an agent/provider, validate live API host allowlists, or establish the
security of a raw host CLI. Separate-verifier permissions and all-task Harbor
execution are checked by adapters/v1/harbor_smoke.py. Missing Docker is a
nonzero infrastructure-unavailable outcome, not an isolation pass.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from nrb_v1.adapters import export_harbor
from nrb_v1.packets import candidate
from nrb_v1.provenance import identity, seal


class IsolationError(RuntimeError):pass


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_build_context(task_dir,*,seed=17,image='nrb-v1:local'):
    """Inspect the actual exported environment, failing closed on extra input."""
    task=Path(task_dir);environment=task/'environment'
    allowed={'Dockerfile','.dockerignore','packet/task.md'}
    actual=set();directories=set()
    for path in environment.rglob('*'):
        if path.is_symlink():raise IsolationError('Candidate build context contains a symlink')
        name=path.relative_to(environment).as_posix()
        if path.is_dir():directories.add(name)
        elif path.is_file():actual.add(name)
        else:raise IsolationError('Candidate build context contains a special filesystem entry')
    if actual!=allowed or directories!={'packet'}:
        raise IsolationError('Candidate build context has extra or missing files/directories')
    dockerfile=(environment/'Dockerfile').read_text(encoding='utf-8')
    lines=[line.strip() for line in dockerfile.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    copies=[line for line in lines if line.upper().startswith(('COPY ','ADD '))]
    if copies!=['COPY packet/ /app/']:
        raise IsolationError('Only the candidate packet may be copied into the candidate image')
    if [line for line in lines if line.upper().startswith('FROM ')]!=['FROM '+image]:
        raise IsolationError('Candidate Dockerfile base differs from the requested runtime image')
    if any(word in dockerfile.lower() for word in ('/grader','/solution','docker.sock','copy .','mount=')):
        raise IsolationError('Candidate Dockerfile references evaluator content or a host mount')
    if (environment/'.dockerignore').read_text(encoding='utf-8')!='*\n!Dockerfile\n!packet/\n!packet/**\n':
        raise IsolationError('Candidate dockerignore must whitelist only the packet')
    if (task/'solution').exists() or (task/'solution').is_symlink():
        raise IsolationError('Isolation export unexpectedly contains a reference solution directory')
    packet=candidate('C01',seed)
    digest=_sha(environment/'packet/task.md')
    if digest!=packet['packet_hash']:
        raise IsolationError('Exported task differs from the self-contained candidate prompt')
    config=(task/'task.toml').read_text(encoding='utf-8')
    if 'network_mode = "no-network"' not in config or 'environment_mode = "separate"' not in config:
        raise IsolationError('Harbor task must request offline agent execution and a separate verifier')
    return {'passed':True,'only_packet_copied':True,'reference_solution_not_exported':True,
            'expected_candidate_files':{'task.md':digest},
            'build_files':{name:_sha(environment/name) for name in sorted(actual)}}


PROBE=r'''
import hashlib,importlib.util,json,os,pathlib,socket,sys
root=pathlib.Path('/app');expected=json.loads(sys.argv[1])
forbidden=['/grader','/solution','/tests','/app/nrb','/app/nrb_v1','/app/.git','/app/solution','/app/tests',
 '/task/nrb','/task/nrb_v1','/task/.git','/repo','/workspace/NuLl-s_Research_Benchmark',
 '/root/NuLl-s_Research_Benchmark','/var/run/docker.sock','/run/docker.sock']
present=[p for p in forbidden if pathlib.Path(p).exists() or pathlib.Path(p).is_symlink()]
repo_names={'.git','nrb','nrb_v1','questions','validation','tests_v1','grader','solution','NuLl-s_Research_Benchmark'}
repository_entries=[]
for location in ('/app','/task','/workspace'):
 p=pathlib.Path(location)
 if p.is_dir():
  repository_entries.extend(str(q) for q in p.rglob('*') if q.name in repo_names)
actual=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())
symlinks=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_symlink())
unchanged=all((root/name).is_file() and not (root/name).is_symlink() and hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in expected.items())
interfaces=sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir())
external_socket_blocked=False
try:
 with socket.create_connection(('198.51.100.1',443),timeout=1):pass
except OSError:external_socket_blocked=True
importable={name:importlib.util.find_spec(name) is not None for name in ('nrb','nrb_v1')}
submission=root/'submission.json'
checks={'unprivileged_probe':os.getuid()==65534,'forbidden_paths_absent':not present,
 'repository_paths_absent':not repository_entries,'evaluator_packages_not_importable':not any(importable.values()),
 'only_candidate_files':actual==sorted([*expected,'submission.json']),
 'no_candidate_symlinks':not symlinks,'candidate_files_unchanged':unchanged,
 'blank_submission':submission.is_file() and submission.read_bytes()==b'',
 'loopback_only':interfaces==['lo'],'external_socket_blocked':external_socket_blocked}
print(json.dumps({'passed':all(checks.values()),'checks':checks,'uid':os.getuid(),
 'candidate_files':actual,'symlinks':symlinks,'present_forbidden_paths':present,
 'repository_entries':repository_entries,'importable_evaluator_packages':importable,'network_interfaces':interfaces}))
'''


def _command(argv,timeout,*,stdout_path=None,stderr_path=None):
    start=time.monotonic()
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    if stdout_path is not None:Path(stdout_path).write_text(p.stdout,encoding='utf-8')
    if stderr_path is not None:Path(stderr_path).write_text(p.stderr,encoding='utf-8')
    return {'exit_code':p.returncode,'wall_seconds':time.monotonic()-start,'stdout':p.stdout,'stderr':p.stderr}


def _image_metadata(data):
    # Avoid recording arbitrary image environment variables or credentials.
    return {key:data.get(key) for key in ('Id','RepoTags','RepoDigests','Created','Architecture','Os')}


def _inspect_image(docker,image):
    info=_command([docker,'image','inspect',image],30)
    if info['exit_code']:raise FileNotFoundError('Docker runtime image unavailable: '+image)
    values=json.loads(info['stdout'])
    if len(values)!=1:raise IsolationError('Expected a single inspected image')
    return _image_metadata(values[0])


def _container_boundary(settings):
    host=settings['HostConfig'];mounts=settings.get('Mounts') or []
    safe_mounts=all(m.get('Type')=='tmpfs' and m.get('Destination')=='/tmp' and m.get('Source') in (None,'') for m in mounts)
    checks={'network_none':host.get('NetworkMode')=='none','not_privileged':not host.get('Privileged'),
            'read_only_root':host.get('ReadonlyRootfs') is True,'no_host_bind_mounts':not host.get('Binds'),
            'no_host_mounts':safe_mounts,'capabilities_dropped':'ALL' in (host.get('CapDrop') or []),
            'no_new_privileges':any('no-new-privileges' in x for x in host.get('SecurityOpt') or []),
            'unprivileged_user':settings.get('Config',{}).get('User')=='65534:65534'}
    return {'passed':all(checks.values()),'checks':checks,'network_mode':host.get('NetworkMode'),
            'privileged':host.get('Privileged'),'root_readonly':host.get('ReadonlyRootfs'),
            'user':settings.get('Config',{}).get('User'),'bind_mounts':host.get('Binds'),'mounts':mounts}


def run(output,*,image='nrb-v1:local',seed=17,timeout=600):
    output=Path(output);materials=output.parent/(output.stem+'-materials')
    if output.exists() or output.is_symlink() or materials.exists() or materials.is_symlink():
        raise FileExistsError('Isolation report and material paths must be new')
    if timeout<=0:raise ValueError('timeout must be positive')
    materials.mkdir(parents=True)
    started=time.monotonic();evaluator=identity()
    report={'schema':'nrb-v1-candidate-isolation-check-v1','kind':'actual_offline_harbor_candidate_image_probe',
            'not_model_performance':True,'api_provider_calls':0,'evaluator_identity':evaluator,
            'started_utc':datetime.now(timezone.utc).isoformat(),'requested_base_image':image,'seed':seed,
            'scope':'C01 candidate image build context and actual disconnected runtime only; separate-verifier checks are a different CI gate.',
            'materials':str(materials),'runtime_status':'unavailable','passed':False,'checks':{}}
    docker=None;container=None;image_created=False
    candidate_image='nrb-v1-isolation-'+uuid.uuid4().hex
    try:
        exported=materials/'export'
        manifest=export_harbor(exported,selection='C01',seed=seed,image=image,agent_hosts='')
        task=exported/'c01'
        report['static_build_context']=check_build_context(task,seed=seed,image=image)
        report['checks']['no_oracle_export']=manifest.get('include_oracle') is False
        report['checks']['separate_verifier_export']=manifest.get('separate_verifier') is True
        report['checks']['offline_agent_export']=manifest.get('agent_hosts')==[]
        docker=shutil.which('docker')
        if not docker:raise FileNotFoundError('Docker executable is unavailable')
        version=_command([docker,'version','--format','{{json .}}'],30,
                         stdout_path=materials/'docker-version.json',stderr_path=materials/'docker-version-stderr.txt')
        if version['exit_code']:raise OSError('Docker daemon unavailable; inspect docker-version-stderr.txt')
        report['docker_version']=json.loads(version['stdout'])
        report['base_image']=_inspect_image(docker,image)
        build=_command([docker,'build','--pull=false','--tag',candidate_image,str(task/'environment')],timeout,
                       stdout_path=materials/'build-stdout.txt',stderr_path=materials/'build-stderr.txt')
        report['build']={k:v for k,v in build.items() if k not in ('stdout','stderr')}
        if build['exit_code']:raise IsolationError('Candidate image build failed; inspect build logs')
        image_created=True
        report['candidate_image']=_inspect_image(docker,candidate_image)
        report['checks']['base_image_unchanged']=_inspect_image(docker,image)['Id']==report['base_image']['Id']
        create=_command([docker,'create','--pull=never','--network','none','--read-only',
            '--tmpfs','/tmp:rw,noexec,nosuid,size=16777216','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1',
            '--user','65534:65534','--workdir','/app','--entrypoint','python',report['candidate_image']['Id'],
            '-I','-B','-c',PROBE,json.dumps(report['static_build_context']['expected_candidate_files'])],30)
        if create['exit_code']:raise IsolationError('Could not create candidate probe container: '+create['stderr'][-1000:])
        container=create['stdout'].strip()
        inspected=_command([docker,'inspect',container],30)
        if inspected['exit_code']:raise IsolationError('Could not inspect the actual probe boundary')
        settings=json.loads(inspected['stdout'])[0]
        report['container_boundary']=_container_boundary(settings)
        report['checks']['inspected_container_boundary']=report['container_boundary']['passed']
        if not report['container_boundary']['passed']:raise IsolationError('Unexpected networking, privileges, or mounts')
        executed=_command([docker,'start','--attach',container],30,
            stdout_path=materials/'probe-stdout.txt',stderr_path=materials/'probe-stderr.txt')
        report['probe_execution']={k:v for k,v in executed.items() if k not in ('stdout','stderr')}
        if executed['exit_code']:raise IsolationError('Actual candidate probe execution failed; inspect probe logs')
        probe=json.loads(executed['stdout'].strip())
        report.update(runtime_status='executed',runtime_probe=probe)
        report['checks']['actual_runtime_probe']=probe.get('passed') is True
        report['checks']['evaluator_unchanged']=identity()==evaluator
        report['passed']=all(report['checks'].values())
    except (FileNotFoundError,OSError) as exc:
        report.update(runtime_status='unavailable',error=type(exc).__name__+': '+str(exc))
    except (IsolationError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as exc:
        report.update(runtime_status='failed',error=type(exc).__name__+': '+str(exc))
    finally:
        cleanup=[]
        for target,argv in ([('container',[docker,'rm','--force',container])] if docker and container else [])+([('candidate_image',[docker,'image','rm','--force',candidate_image])] if docker and image_created else []):
            try:
                result=_command(argv,30)
                cleanup.append({'target':target,'exit_code':result['exit_code'],'stderr':result['stderr']})
            except (OSError,subprocess.SubprocessError) as exc:
                cleanup.append({'target':target,'error':type(exc).__name__+': '+str(exc)})
        report['cleanup']=cleanup
        if any(item.get('exit_code')!=0 for item in cleanup):report['passed']=False
    report['material_sha256']={p.relative_to(materials).as_posix():_sha(p) for p in sorted(materials.rglob('*')) if p.is_file() and not p.is_symlink()}
    report['wall_seconds']=time.monotonic()-started
    report['report_hash']=seal(report)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--image','--python-image',dest='image',default='nrb-v1:local')
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--timeout',type=float,default=600)
    args=parser.parse_args(argv)
    try:report=run(args.out,image=args.image,seed=args.seed,timeout=args.timeout)
    except (OSError,ValueError) as exc:
        print(json.dumps({'passed':False,'error':type(exc).__name__+': '+str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'passed':report['passed'],'runtime_status':report['runtime_status'],'report':str(args.out)}))
    return 0 if report['passed'] else 2


if __name__=='__main__':raise SystemExit(main())
