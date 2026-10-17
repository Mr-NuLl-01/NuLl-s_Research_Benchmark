"""Verify frozen legacy prompts and V1.1 source bytes; never run a model."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nrb_v1.packets import candidate
from nrb_v1.provenance import fingerprint
from nrb_v1.video import data_root, VIDEO_IDS, input_manifest


def main():
    legacy = [*(f'C{i:02}' for i in range(1, 11)), *(f'R{i:02}' for i in range(1, 7)), 'X01', 'X02', 'X03']
    for tid in legacy:
        packet = candidate(tid, 17)
        path = ROOT / 'tasks/v1.0' / (tid + '.' + packet['format'])
        if path.read_bytes() != packet['content'].encode('utf-8'):
            raise ValueError('Legacy frozen task changed: ' + tid)
    root = data_root()
    if (ROOT/'nrb_v1/video_rubrics.json').read_bytes() != (root/'evaluator/nrb_rubrics.json').read_bytes():
        raise ValueError('Public rubric copy differs from authoritative evaluator rubric')
    manifest = json.loads((root / 'MATERIAL_MANIFEST.json').read_text())
    listed = {x['path'] for x in manifest['files']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name != 'MATERIAL_MANIFEST.json'}
    if listed != actual:
        raise ValueError('Material manifest file set differs')
    for item in manifest['files']:
        path = root / item['path']
        if path.is_symlink() or path.stat().st_size != item['bytes'] or fingerprint(path.read_bytes()) != item['sha256']:
            raise ValueError('Material mismatch: ' + item['path'])
    bundles = [input_manifest(tid, verify=True) for tid in VIDEO_IDS]
    if bundles[0]['common_assets_sha256'] != bundles[1]['common_assets_sha256']:
        raise ValueError('A/B common input assets differ')
    if bundles[0]['packet_hash'] == bundles[1]['packet_hash']:
        raise ValueError('A/B full input bundles must differ')
    for tid in VIDEO_IDS:
        if (ROOT / 'tasks/v1.1' / (tid + '.md')).read_bytes() != candidate(tid)['content'].encode('utf-8'):
            raise ValueError('Frozen V1.1 instructions differ: ' + tid)
    print(json.dumps({'passed': True, 'legacy_frozen_tasks': len(legacy), 'verified_material_files': len(listed),
                      'new_media_tasks': list(VIDEO_IDS), 'model_calls': 0, 'not_model_performance': True}))


if __name__ == '__main__':
    main()
