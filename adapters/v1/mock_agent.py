"""Empty file-only CLI mock for plumbing checks; never a model result."""
import json
from pathlib import Path
import re
import sys
path=Path(sys.argv[1])
text=path.read_text(encoding="utf-8")
match=re.search(r"\b([CRX]\d{2})\b",text)
if not match:raise ValueError("Task ID missing")
Path("submission.json").write_text(json.dumps({"task_id":match.group(1),"artifacts":{},"answer":{}})+"\n")
