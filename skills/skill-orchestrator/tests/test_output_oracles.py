import importlib.util
from pathlib import Path
import pytest
p=Path(__file__).resolve().parents[1]/'scripts/output_oracles.py'
spec=importlib.util.spec_from_file_location('oracle_test',p);O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)

@pytest.mark.parametrize('text,expected,ok',[('37','37',True),('-37','37',False),('−37','-37',True),('+37','37',True),('37.0','37',True),('37 apples','37',False),('29+8=37','37',False),('1e3','1000',False),('NaN','37',False),('Infinity','37',False),('١','1',False),(' 0 ','0',True),('0.1','0.1',True),('0.10000000000000001','0.1',False)])
def test_signed_numeric_oracle(text,expected,ok):assert O.exact_number(text,expected) is ok
