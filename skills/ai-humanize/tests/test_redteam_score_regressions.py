"""Saved synthetic texts exercise the real scorer and guard, not model quality."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('candidate_redteam', ROOT/'scripts/redteam_score.py')
SCORER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORER)


class ScorerRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'scripts').mkdir(); (self.root/'evaluation').mkdir()
        shutil.copyfile(ROOT/'scripts/rewrite_guard.py', self.root/'scripts/rewrite_guard.py')
        self.outputs = self.root/'outputs'; self.outputs.mkdir()
        self.cases = [dict(id='case-one', language='en', request='Rewrite faithfully.', mode_expectation='light', source='The beta does not support SSO.', protected=['SSO'], manual_checks=['Keep negation and scope.'])]
        self.manifest = self.root/'evaluation/redteam-cases.json'
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.cases), encoding='utf-8')

    def run_scorer(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(SCORER, 'ROOT', self.root), patch.object(sys, 'argv', ['redteam_score.py', str(self.outputs), '--json']), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = SCORER.main()
        return code, json.loads(out.getvalue()) if out.getvalue().strip() else None, err.getvalue()

    def output(self, text=None):
        (self.outputs/'case-one.txt').write_text(self.cases[0]['source'] if text is None else text, encoding='utf-8')

    def test_all_outputs_missing_blocks(self):
        code, result, _ = self.run_scorer(); self.assertEqual(code, 1)
        self.assertEqual(result[0]['status'], 'missing_output')

    def test_one_missing_among_otherwise_good_outputs_blocks(self):
        self.cases.append({**self.cases[0], 'id':'case-two'}); self.save(); self.output()
        self.assertEqual(self.run_scorer()[0], 1)

    def test_empty_output_blocks(self):
        self.output(''); self.assertEqual(self.run_scorer()[0], 1)

    def test_whitespace_only_output_blocks(self):
        self.cases[0]['source']='prosty tekst'; self.cases[0]['protected']=[]; self.save()
        self.output(' \n\t '); code, result, _ = self.run_scorer()
        self.assertEqual(code, 1); self.assertEqual(result[0]['status'], 'invalid_output')

    def test_negation_risk_requires_review(self):
        self.output('The beta supports SSO.')
        code, result, _ = self.run_scorer(); self.assertEqual(code, 1)
        self.assertEqual(result[0]['status'], 'review')

    def test_modality_risk_requires_review(self):
        self.cases[0]['source']='It may work.';self.cases[0]['protected']=[];self.save()
        self.output('It must work.'); self.assertEqual(self.run_scorer()[0], 1)

    def test_unchanged_is_automated_only(self):
        self.output(); code, result, _ = self.run_scorer(); self.assertEqual(code, 0)
        self.assertEqual(result[0]['status'], 'automated_pass')
        self.assertEqual(result[0]['manual_review'], 'not_performed')
        self.assertEqual(result[0]['semantic_equivalence'], 'not_verified')

    def test_result_binds_output_and_source_bytes(self):
        self.output(); _, result, _ = self.run_scorer()
        self.assertEqual(result[0]['output_sha256'], hashlib.sha256((self.outputs/'case-one.txt').read_bytes()).hexdigest())
        self.assertEqual(result[0]['source_sha256'], hashlib.sha256(self.cases[0]['source'].encode()).hexdigest())

    def test_result_is_reproducible(self):
        self.output(); self.assertEqual(self.run_scorer(), self.run_scorer())

    def test_literal_claim_flag_is_not_declared_proof(self):
        self.cases[0]['source']='This is not undetectable.';self.cases[0]['protected']=[];self.save();self.output()
        code,result,_=self.run_scorer();self.assertEqual(code,1)
        self.assertIn('undetectable',result[0]['provenance_string_flags'])
        self.assertEqual(result[0]['claim_assessment'], 'heuristic_only')

    def test_empty_manifest_is_invalid(self):
        self.cases=[];self.save();self.assertEqual(self.run_scorer()[0],2)

    def test_duplicate_cases_are_invalid(self):
        self.cases.append(dict(self.cases[0]));self.save();self.output()
        self.assertEqual(self.run_scorer()[0],2)

    def test_duplicate_json_keys_are_invalid(self):
        self.manifest.write_text('[{"id":"case-one","id":"case-two"}]')
        self.assertEqual(self.run_scorer()[0],2)

    def test_parent_escape_is_invalid(self):
        self.cases[0]['id']='../outside';self.save()
        self.assertEqual(self.run_scorer()[0],2)

    def test_bad_source_type_is_invalid(self):
        self.cases[0]['source']=12;self.save();self.output('text')
        self.assertEqual(self.run_scorer()[0],2)

    def test_missing_manual_checks_is_invalid(self):
        del self.cases[0]['manual_checks'];self.save();self.output()
        self.assertEqual(self.run_scorer()[0],2)

    def test_invalid_json_is_redacted(self):
        self.manifest.write_text('DO_NOT_ECHO_INVALID_MANIFEST')
        code,_,err=self.run_scorer();self.assertEqual(code,2)
        self.assertNotIn('DO_NOT_ECHO_INVALID_MANIFEST',err)

    def test_unknown_output_case_is_invalid(self):
        self.output();(self.outputs/'unknown-case.txt').write_text('x')
        self.assertEqual(self.run_scorer()[0],2)

    def test_symlink_output_is_not_read(self):
        target=self.root/'outside.txt';target.write_text(self.cases[0]['source'])
        (self.outputs/'case-one.txt').symlink_to(target)
        code,result,_=self.run_scorer();self.assertEqual(code,1)
        self.assertEqual(result[0]['status'],'invalid_output')

    def test_symlink_root_is_invalid(self):
        alias=self.root/'alias';alias.symlink_to(self.outputs,target_is_directory=True);self.outputs=alias
        self.assertEqual(self.run_scorer()[0],2)

    def test_non_utf8_output_is_invalid(self):
        (self.outputs/'case-one.txt').write_bytes(b'\xff')
        self.assertEqual(self.run_scorer()[0],1)

    def test_oversized_output_is_invalid(self):
        (self.outputs/'case-one.txt').write_bytes(b'x'*(2*1024*1024+1))
        self.assertEqual(self.run_scorer()[0],1)


if __name__=='__main__':
    unittest.main()
