#!/usr/bin/env python3
"""Capture the current countercheck execution; output goes outside frozen runs."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, required=True)
args = parser.parse_args()
out = args.output_dir.resolve()
out.mkdir(parents=True, exist_ok=True)
command = ['bash', str(RUN/'commands.sh')]
env = dict(os.environ, OUT=str(out))
start = time.monotonic()
with (out/'execution.log').open('w') as stream:
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
report = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
              baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              command=['bash', str((RUN/'commands.sh').relative_to(ROOT))],
              graphs_root=os.environ.get('GRAPHS_ROOT'), output_dir=str(out),
              exit_code=result.returncode, elapsed_seconds=round(time.monotonic()-start,3),
              python=sys.version, platform=platform.platform(), machine=platform.machine(),
              compiler=subprocess.check_output([os.environ.get('CXX','c++'),'--version'],text=True),
              binaries_tracked=False, exhaustive_search_executed=False)
(out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'environment.txt').write_text('\n'.join(f'{key}: {value}' for key,value in report.items())+'\n')
print(json.dumps(report,indent=2))
sys.exit(result.returncode)
