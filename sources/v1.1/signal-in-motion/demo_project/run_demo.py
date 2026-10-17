"""Rebuild the author demonstration from the exact public benchmark MP4.

Run after installing requirements.txt and FFmpeg. This is author implementation,
not candidate input. New material uses the repository MIT license; third-party terms remain.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
SHARED = ROOT.parent / "shared_assets"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = SHARED / "source.mp4"
    if not source.is_file():
        raise FileNotFoundError(f"Missing shared benchmark source: {source}")
    assets = ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    inputs = list((SHARED / "fonts").glob("*.ttf"))
    inputs.append(SHARED / "LICENSES" / "DejaVu-LICENSE.txt")
    if len(inputs) < 3:
        raise FileNotFoundError("The two shared fonts and their license are required.")
    for item in inputs:
        output = assets / item.name
        if output.exists() and digest(output) != digest(item):
            raise RuntimeError(f"A modified local asset already exists: {output}; move it aside before rebuilding.")
        if not output.exists():
            shutil.copy2(item, output)
    subprocess.run([sys.executable, str(ROOT / "source" / "prepare_assets.py"), "--source", str(source)], check=True)
    subprocess.run([sys.executable, str(ROOT / "source" / "render.py")], check=True)
    print(f"Rebuilt author video: {ROOT / 'reference.mp4'}")
    print("The supplied evaluation reference at tracks/B/reference.mp4 was not changed.")
    supplied_audio = SHARED / "soundtrack.wav"
    if supplied_audio.is_file():
        print("Soundtrack identical:", digest(supplied_audio) == digest(assets / "soundtrack.wav"))


if __name__ == "__main__":
    main()
