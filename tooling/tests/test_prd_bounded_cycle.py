"""A broken cycle diagnostic must not turn malformed PRD into an infinite loop."""
import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_cycle_validation_terminates_when_cycle_diagnostic_guard_is_removed(tmp_path):
    source = ROOT / 'skills/brief-architect/scripts/kernel.py'
    tree = ast.parse(source.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == 'not ready':
            node.test = ast.Constant(False)
    mutant = tmp_path / 'kernel.py'
    mutant.write_text(ast.unparse(ast.fix_missing_locations(tree)))
    cases = json.loads((ROOT / 'skills/brief-architect/evals/cases.json').read_text())
    case = next(c['input'] for c in cases if c['id'] == 'prd-dependency-cycle')
    request = tmp_path / 'brief.json'
    request.write_text(json.dumps(case))
    script = ('import json,runpy,sys; k=runpy.run_path(sys.argv[1]); '
              'print(json.dumps(k["readiness"](json.load(open(sys.argv[2])))))')
    try:
        result = subprocess.run([sys.executable, '-c', script, str(mutant), str(request)],
                                capture_output=True, text=True, timeout=2, check=True)
    except subprocess.TimeoutExpired:
        outcome = 'TIMEOUT'
    else:
        outcome = json.loads(result.stdout)['status']
    assert outcome == 'INVALID'
