#!/usr/bin/env python3
"""Execute all V1 references and scientific wrong candidates in real Docker.

This is a CI regression check of repository-authored code, not model
performance. It never calls a provider. Missing Docker/image/runtime evidence
is an infrastructure failure, never a successful or silently skipped check.
Build environments/v1/Dockerfile separately before invoking this script.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from nrb_v1.grading import grade
from nrb_v1.provenance import identity, seal
from nrb_v1.registry import CODING_IDS, module


SCIENTIFIC_MUTANTS={
    'C03':('arithmetic_interface',),
    'C04':('amplitude_as_power',),
    'C06':('central_drift',),
    'C07':('conditional_information',),
    'C08':('arithmetic_interface',),
    'C09':('wrong_poisson_mesh_scale',),
    'C10':('lagged_reaction_transfer','relative_sigma_covariance'),
}


RUNTIME_PROBE=r'''
import importlib.metadata,json,os,platform,subprocess,sys
packages={}
for name in ('numpy','scipy','matplotlib','Pillow','CairoSVG'):
    try:packages[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:packages[name]=None
p=subprocess.run(['gfortran','--version'],text=True,capture_output=True,check=True)
print(json.dumps({'python':sys.version,'platform':platform.platform(),'uid':os.getuid(),
                 'gfortran':p.stdout.splitlines()[0],'packages':packages}))
'''


def _command(argv,timeout):
    start=time.monotonic()
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    return {'argv':argv,'exit_code':p.returncode,'wall_seconds':time.monotonic()-start,
            'stdout':p.stdout,'stderr':p.stderr}


def _image_metadata(image):
    # Deliberately omit image environment variables from the report.
    return {key:image.get(key) for key in ('Id','RepoTags','RepoDigests','Created','Architecture','Os')}


def _scientific_outcome(report,kind,image_id,evaluator):
    checks={
        'actual_docker_execution':report.get('execution',{}).get('status')=='executed',
        'backend_is_docker':report.get('execution',{}).get('backend')=='docker',
        'actual_image_matches':report.get('execution',{}).get('image_id')==image_id,
        'all_70_automatic_points_scored':report.get('auto_scored_max')==70,
        'evaluator_matches':report.get('evaluator_identity')==evaluator,
        'manual_score_unassigned':report.get('total') is None and report.get('review_points') is None,
    }
    if kind=='reference':
        checks.update(reference_70=report.get('auto_points')==70,
                      no_critical_failure=not report.get('critical_failures'),
                      manual_review_still_pending=report.get('completion_status')=='pending_review')
    else:
        checks.update(scientific_points_lost=0<report.get('auto_points',0)<70,
                      critical_failure_recorded=bool(report.get('critical_failures')),
                      failed_completion=report.get('completion_status')=='failed',
                      no_compile_failure=not any('CompileError' in c.get('detail','') for c in report.get('checks',[])))
    return checks


def run(output,*,image='nrb-v1:local',seed=17,timeout=120):
    output=Path(output)
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    if timeout<=0:raise ValueError('timeout must be positive')
    output.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();evaluator=identity()
    report={'schema':'nrb-v1-docker-check-v1','kind':'actual_docker_reference_and_scientific_controls',
            'not_model_performance':True,'api_provider_calls':0,'evaluator_identity':evaluator,
            'started_utc':datetime.now(timezone.utc).isoformat(),'requested_image':image,'seed':seed,
            'scope':'Repository references and deliberately wrong scientific candidates only; automatic70, manual30 remains unassessed.',
            'runtime_status':'unavailable','passed':False,'entries':[],'checks':{}}
    try:
        docker=shutil.which('docker')
        if not docker:raise FileNotFoundError('Docker executable is unavailable')
        version=_command([docker,'version','--format','{{json .}}'],30)
        report['docker_version_command']=version
        if version['exit_code']:raise OSError('Docker daemon unavailable')
        report['docker_version']=json.loads(version['stdout'])
        inspected=_command([docker,'image','inspect',image],30)
        if inspected['exit_code']:raise FileNotFoundError('V1 Docker image unavailable; build environments/v1/Dockerfile first')
        data=json.loads(inspected['stdout'])
        if len(data)!=1:raise ValueError('Expected exactly one Docker image')
        report['actual_image']=_image_metadata(data[0]);image_id=data[0]['Id']
        probe=_command([docker,'run','--rm','--pull=never','--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64',
            '--memory','512m','--cpus','1','--user','65534:65534',
            '--tmpfs','/tmp:rw,noexec,nosuid,size=16777216','--entrypoint','python',image_id,
            '-I','-B','-c',RUNTIME_PROBE],30)
        report['runtime_probe_command']=probe
        if probe['exit_code']:raise RuntimeError('Actual Docker Python/Fortran runtime probe failed')
        report['runtime']=json.loads(probe['stdout'])
        report['checks']['unprivileged_runtime']=report['runtime'].get('uid')==65534
        report['checks']['fortran_compiler_recorded']=bool(report['runtime'].get('gfortran'))
        report['runtime_status']='executed'
        plans=[(tid,'reference','reference') for tid in CODING_IDS]
        plans += [(tid,'scientific_mutant',label) for tid,labels in SCIENTIFIC_MUTANTS.items() for label in labels]
        for tid,kind,label in plans:
            entry={'task_id':tid,'kind':kind,'label':label,'passed':False}
            try:
                task=module(tid)
                submission=task.reference_submission(seed) if kind=='reference' else task.mutants(seed)[label]
                result=grade(tid,submission,seed,backend='docker',timeout=timeout,image=image_id)
                entry['report']=result
                entry['checks']=_scientific_outcome(result,kind,image_id,evaluator)
                entry['passed']=all(entry['checks'].values())
            except (OSError,RuntimeError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as exc:
                entry['error']=type(exc).__name__+': '+str(exc)
            report['entries'].append(entry)
        report['checks'].update(all_ten_references_executed=sum(e['kind']=='reference' for e in report['entries'])==10,
            all_selected_controls_executed=sum(e['kind']=='scientific_mutant' for e in report['entries'])==sum(map(len,SCIENTIFIC_MUTANTS.values())),
            all_expected_scientific_outcomes=all(e['passed'] for e in report['entries']),
            evaluator_unchanged=identity()==evaluator)
        report['passed']=all(report['checks'].values())
    except (FileNotFoundError,OSError) as exc:
        report.update(runtime_status='unavailable',error=type(exc).__name__+': '+str(exc))
    except (RuntimeError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as exc:
        report.update(runtime_status='failed',error=type(exc).__name__+': '+str(exc))
    report['wall_seconds']=time.monotonic()-started
    report['report_hash']=seal(report)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--image',default='nrb-v1:local')
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--timeout',type=float,default=120)
    args=parser.parse_args(argv)
    try:report=run(args.out,image=args.image,seed=args.seed,timeout=args.timeout)
    except (OSError,ValueError) as exc:
        print(json.dumps({'passed':False,'error':type(exc).__name__+': '+str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'passed':report['passed'],'runtime_status':report['runtime_status'],
                      'entries':len(report['entries']),'report':str(args.out)}))
    return 0 if report['passed'] else 2


if __name__=='__main__':raise SystemExit(main())
