#!/usr/bin/env python3
"""Assemble a reviewer delivery from the exact already-published grader ZIP.

No API credentials, model results, screenshots or original video bytes are
included. The grader and candidate bytes must match the published manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from package_v2_release import archive, ROOT, __version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-packages', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.base_packages / 'package-manifest.json').read_text())
    artifacts = {item['name']: item for item in manifest['artifacts']}
    files = {}
    for suffix, folder in [('python-candidates', 'candidates'), ('python-grader', 'grader')]:
        name = 'NRB-v' + __version__ + '-' + suffix + '.zip'
        path = args.base_packages / name
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == artifacts[name]['sha256'], name
        with zipfile.ZipFile(path) as source:
            assert source.testzip() is None
            for entry in source.infolist():
                parts = Path(entry.filename).parts
                assert len(parts) >= 2 and '..' not in parts and not Path(entry.filename).is_absolute()
                files[folder + '/' + '/'.join(parts[1:])] = source.read(entry)
    for directory in ('docs/v2.0', 'validation/v2.0-rc.1', 'web'):
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for directory in ('scripts/v2', 'tests_v2'):
        for path in sorted((ROOT / directory).glob('*.py')):
            files['grader/' + path.relative_to(ROOT).as_posix()] = path.read_bytes()
    files['LICENSE'] = (ROOT / 'LICENSE').read_bytes()
    status = json.loads((ROOT / 'docs/v2.0/release-status.json').read_text())
    files['START-HERE.md'] = f'''# NRB V2 第一轮完整交付

版本 {__version__}。本包供评测者使用。已开放8道Python，其余12题为第二轮计划。

## 先做一次评分

1. 只把 `candidates/P01.md` 等所选单题交给模型，使用新会话。
2. 把完整源码保存到 `grader/submissions/P01/solution.py` 等对应文件夹。
3. 首次进入 `grader/`，运行 Build-Environment 脚本构建Docker镜像。
4. 运行 Grade-Results 脚本，打开新生成的 results 目录里的 index.html。
5. 将单题JSON导入私有网页，核验后保存模型和运行条件。

Windows使用.cmd，macOS使用.command，Linux使用.sh。宿主需要Python3.11+和Docker；包内README有完整说明。不要把grader目录交给候选，它包含参考与检查逻辑。

## 内容

- candidates：8道可直接提供给模型的单题文件。
- grader：完整离线评分器、固定环境、启动脚本和提交文件夹；附维护者回归及独立科学核对脚本。
- docs/v2.0：设计、使用、验证、Drive资源与第二轮接续说明。
- validation/v2.0-rc.1：实际本地和GitHub CI证据，不是模型成绩。
- web：与已发布第5版匹配的网页源码镜像，保留旧21题材料。

实现提交：{status['github']['implementation_commit']}

网站：{status['site']['url']}

下载目录：{status['drive_folder']}

V2 CI：{status['github']['v2_workflow']['url']}

原视频文件仍从Drive单独下载；本包不重复包含大体积媒体。完整Git历史与旧框架适配器从GitHub获取。本包没有真实模型排名，旧分数不能混入V2。
'''.encode('utf-8')
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    result = archive(output, 'NRB-v' + __version__ + '-round1', files)
    output.with_suffix('.manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
