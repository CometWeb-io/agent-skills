import subprocess
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("text,signal", [('{'+'"a":1,"a":2'+'}',"duplicate JSON key"),('{"a":NaN}',"non-finite JSON number"),('{"a":Infinity}',"non-finite JSON number")])
def test_ambiguous_or_nonfinite_json_rejected(tmp_path,text,signal):
    path=tmp_path/"report.json";path.write_text(text)
    script=ROOT/"scripts"/"validate_report.py"
    run=subprocess.run([sys.executable,str(script),str(path)],capture_output=True,text=True,timeout=15)
    assert run.returncode != 0
    assert signal in run.stdout+run.stderr
    assert "Traceback" not in run.stderr
