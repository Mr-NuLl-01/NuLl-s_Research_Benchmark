"""Offline delivery-chain check only: deliberately scores zero, no AI model."""
import json
from pathlib import Path

manifest = json.loads(Path("packet_manifest.json").read_text(encoding="utf-8"))
print(json.dumps({"task_id": manifest["task_id"], "answer": {}, "artifacts": {}}))
