"""Synthetic regressions. These do not validate an actual ebook or model behaviour."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import date

PKG=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ebook_check', PKG/'scripts/ebook_check.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
AS_OF=date(2026,9,14)

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.m={
          'schema':'cometweb.ebook/v1',
          'publication':{'id':'fixture','title':'Synthetic validation fixture','language':'pl','edition':'1.0','revision':'1','as_of':'2026-09-14'},
          'scope':{'audience':'Test runner','outcome':'Exercise record checks, not factual validity','questions':[{'id':'Q1','question':'Is the synthetic record complete?','status':'covered','chapter_ids':['ch1'],'rationale':''}]},
          'chapters':[{'id':'ch1','title':'Test','outcome':'Exercise validation','question_ids':['Q1']}],
          'sources':[{'id':'S1','title':'Synthetic source fixture (not research)','source_type':'primary','origin':'fixture-origin','inspected':True,'accessed_on':'2026-09-14','url':'https://example.org/fixture'}],
          'claims':[{'id':'C1','text':'Synthetic record used only in software tests.','chapter_id':'ch1','kind':'fact','materiality':'material','conclusion':'supported','time_sensitive':False,
                     'evidence':[{'source_id':'S1','relation':'supports','locator':'Fixture section','explanation':'Synthetic relation for program regression only.'}],
                     'countercheck':{'performed':True,'checked_on':'2026-09-14','queries':['synthetic falsifier case'],'outcome':'This is a software test record, not external verification.','source_ids':['S1']}}],
          'files':{'manuscript':'manuscript.md','pdf':'ebook.pdf','deliverables':['manuscript.md','ebook.pdf']},
          'checks':[], 'visual':{}}
        (self.root/'manuscript.md').write_text('# Fixture\n<!-- chapter:ch1 -->\n<!-- claim:C1 -->\nSynthetic statement.[^S1]\n\n[^S1]: Synthetic source, https://example.org/fixture\n',encoding='utf-8')
        (self.root/'review.md').write_text('Synthetic review evidence: unit-test fixture only.\n',encoding='utf-8')
        self.rebind()

    def rebind(self, stage='manuscript'):
        fp=mod.fingerprints(self.m,self.root)
        checks=[]
        for level in mod.STAGES[:mod.STAGES.index(stage)+1]:
            for key in mod.CHECKS[level]:
                checks.append({'id':key,'status':'pass','reviewer':'synthetic-fixture','method':'self_review','checked_on':'2026-09-14',
                               'notes':'Synthetic check record; not actual review.', 'evidence_file':'review.md',
                               'evidence_sha256':mod.sha256_file(self.root/'review.md'),
                               'fingerprints':{k:fp[k] for k in mod.BINDINGS[level]}})
        self.m['checks']=checks

    def result(self,stage='research'):
        return mod.validate(self.m,self.root,stage,AS_OF)

    def assertBlocked(self,stage='research',code=None):
        try:
            result=self.result(stage)
        except mod.InputError:
            if code is not None: raise
            return
        self.assertEqual(result['result'],'BLOCKED',result)
        if code: self.assertIn(code,[x['code'] for x in result['blockers']])

    def pdf_fixture(self,pages=1):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.fail('Install approved test dependency pypdf; do not silently skip PDF coverage.')
        writer=PdfWriter()
        for _ in range(pages): writer.add_blank_page(width=100,height=100)
        with (self.root/'ebook.pdf').open('wb') as f: writer.write(f)
        (self.root/'page.png').write_bytes(b'\x89PNG\r\n\x1a\nsynthetic-hash-fixture-not-an-inspected-render')
        self.m['visual']={'renderer':'synthetic-test-fixture','pdf_sha256':mod.sha256_file(self.root/'ebook.pdf'),'page_count':pages,
           'pages':[{'page':n,'status':'pass','reviewer':'synthetic-fixture','inspected_on':'2026-09-14',
                     'notes':f'Synthetic page {n} record, not visual inspection.','render_path':'page.png',
                     'render_sha256':mod.sha256_file(self.root/'page.png')} for n in range(1,pages+1)]}
        self.rebind('release')

    def test_complete_research_records(self): self.assertEqual(self.result()['result'],'RECORDS_COMPLETE')
    def test_complete_manuscript_records(self): self.assertEqual(self.result('manuscript')['result'],'RECORDS_COMPLETE')
    def test_complete_release_records(self):
        self.pdf_fixture(); self.assertEqual(self.result('release')['result'],'RECORDS_COMPLETE')
    def test_missing_source(self): self.m['sources']=[]; self.assertBlocked()
    def test_duplicate_source_id(self): self.m['sources']*=2; self.assertBlocked(code='duplicate_id')
    def test_duplicate_claim_id(self): self.m['claims']*=2; self.assertBlocked(code='duplicate_id')
    def test_empty_claims(self): self.m['claims']=[]; self.assertBlocked(code='empty_claims')
    def test_unknown_source_edge(self): self.m['claims'][0]['evidence'][0]['source_id']='missing'; self.assertBlocked(code='unknown_source')
    def test_no_support(self): self.m['claims'][0]['evidence'][0]['relation']='context'; self.assertBlocked(code='missing_support')
    def test_discovery_is_not_evidence(self): self.m['sources'][0]['source_type']='discovery'; self.assertBlocked(code='inadmissible_source')
    def test_uninspected_source(self): self.m['sources'][0]['inspected']=False; self.assertBlocked(code='inadmissible_source')
    def test_unresolved_claim(self): self.m['claims'][0]['conclusion']='unresolved'; self.assertBlocked(code='claim_conclusion')
    def test_qualified_needs_qualification(self): self.m['claims'][0]['conclusion']='qualified'; self.assertBlocked(code='missing_text')
    def test_inference_cannot_be_fact_verified(self): self.m['claims'][0]['kind']='inference'; self.assertBlocked(code='claim_conclusion')
    def test_recommendation_needs_rationale(self):
        self.m['claims'][0].update(kind='recommendation',conclusion='recommended'); self.assertBlocked(code='missing_text')
    def test_synthetic_needs_visible_label(self):
        self.m['claims'][0].update(kind='synthetic',conclusion='illustrative'); self.assertBlocked(code='missing_text')
    def test_synthetic_no_support_allowed_when_labelled(self):
        self.m['claims'][0].update(kind='synthetic',conclusion='illustrative',display_label='Przykład syntetyczny',evidence=[])
        self.rebind(); self.assertEqual(self.result()['result'],'RECORDS_COMPLETE')
    def test_contradiction_requires_resolution(self):
        self.m['claims'][0]['evidence'].append({'source_id':'S1','relation':'contradicts','locator':'Other section','explanation':'Synthetic contradiction'})
        self.assertBlocked(code='unresolved_contradiction')
    def test_countercheck_missing(self): self.m['claims'][0].pop('countercheck'); self.assertBlocked(code='countercheck_missing')
    def test_countercheck_false(self): self.m['claims'][0]['countercheck']['performed']=False; self.assertBlocked(code='countercheck_missing')
    def test_countercheck_query_empty(self): self.m['claims'][0]['countercheck']['queries']=[]; self.assertBlocked(code='countercheck_empty')
    def test_countercheck_unknown_source(self): self.m['claims'][0]['countercheck']['source_ids']=['unknown']; self.assertBlocked(code='unknown_source')
    def test_stale_claim(self):
        self.m['claims'][0].update(time_sensitive=True,as_of='2026-09-01',review_by='2026-09-13',freshness_rationale='Fixture short-lived value')
        self.assertBlocked(code='stale_claim')
    def test_current_sensitive_claim(self):
        self.m['claims'][0].update(time_sensitive=True,as_of='2026-09-14',review_by='2026-09-15',freshness_rationale='Fixture short-lived value')
        self.rebind(); self.assertEqual(self.result()['result'],'RECORDS_COMPLETE')
    def test_future_access_date(self): self.m['sources'][0]['accessed_on']='2026-09-15'; self.assertBlocked(code='future_date')
    def test_invalid_calendar_date(self): self.m['sources'][0]['accessed_on']='2026-02-30'; self.assertBlocked(code='invalid_date')
    def test_open_question(self): self.m['scope']['questions'][0]['status']='open'; self.assertBlocked(code='open_question')
    def test_unknown_chapter(self): self.m['claims'][0]['chapter_id']='missing'; self.assertBlocked(code='unknown_chapter')
    def test_question_coverage_bidirectional(self): self.m['chapters'][0]['question_ids']=[]; self.assertBlocked(code='coverage_mismatch')
    def test_missing_review(self): self.m['checks']=[]; self.assertBlocked(code='missing_check')
    def test_not_run_is_not_pass(self): self.m['checks'][0]['status']='not_run'; self.assertBlocked(code='check_not_pass')
    def test_review_evidence_mutated(self): (self.root/'review.md').write_text('Changed'); self.assertBlocked(code='file_hash_mismatch')
    def test_ledger_mutation_invalidates_reviews(self): self.m['claims'][0]['text']='Changed meaning'; self.assertBlocked(code='stale_check')
    def test_manuscript_mutation_invalidates_reviews(self):
        with (self.root/'manuscript.md').open('a') as f: f.write('\nMore text.\n')
        self.assertBlocked('manuscript',code='stale_check')
    def test_missing_claim_marker(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text().replace('<!-- claim:C1 -->','')); self.assertBlocked('manuscript',code='missing_claim_anchor')
    def test_unknown_claim_marker(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\n<!-- claim:unknown -->'); self.assertBlocked('manuscript',code='unknown_claim_anchor')
    def test_missing_footnote(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text().split('[^S1]:')[0]); self.assertBlocked('manuscript',code='missing_footnote')
    def test_duplicate_footnote(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\n[^S1]: second definition\n'); self.assertBlocked('manuscript',code='duplicate_footnote')
    def test_unknown_footnote(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\nAnother.[^unknown]\n'); self.assertBlocked('manuscript',code='unknown_citation')
    def test_placeholder_blocks(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\n[UZUPEŁNIJ przykład]'); self.assertBlocked('manuscript',code='placeholder')
    def test_template_code_is_not_banned(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\nExample template syntax: `{{ user.name }}`\n')
        self.rebind(); self.assertEqual(self.result('manuscript')['result'],'RECORDS_COMPLETE')
    def test_code_fence_cannot_fake_claim_anchors(self):
        p=self.root/'manuscript.md'; p.write_text('```md\n'+p.read_text()+'\n```\n')
        self.assertBlocked('manuscript',code='missing_claim_anchor')
    def test_tilde_fence_cannot_fake_claim_anchors(self):
        p=self.root/'manuscript.md'; p.write_text('~~~md\n'+p.read_text()+'\n~~~\n')
        self.assertBlocked('manuscript',code='missing_claim_anchor')
    def test_inline_code_cannot_fake_citation(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text().replace('statement.[^S1]','statement.`[^S1]`'))
        self.assertBlocked('manuscript',code='uncited_support')
    def test_code_example_unknown_citation_ignored(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\n```md\nLiteral [^NOT_A_SOURCE]\n```\n')
        self.rebind(); self.assertEqual(self.result('manuscript')['result'],'RECORDS_COMPLETE')
    def test_unclosed_code_fence(self):
        p=self.root/'manuscript.md'; p.write_text(p.read_text()+'\n```python\nx=1\n')
        self.assertBlocked('manuscript',code='unclosed_code_fence')
    def test_citation_in_other_claim_not_enough(self):
        self.m['claims'].append({'id':'C2','text':'Illustrative exercise','chapter_id':'ch1','kind':'synthetic','materiality':'background','conclusion':'illustrative','time_sensitive':False,'display_label':'Przykład syntetyczny','evidence':[]})
        p=self.root/'manuscript.md'; p.write_text('# Test\n<!-- chapter:ch1 -->\n<!-- claim:C1 -->\nUncited statement.\n<!-- claim:C2 -->\nPrzykład syntetyczny.[^S1]\n\n[^S1]: Synthetic source\n')
        self.rebind(); self.assertBlocked('manuscript',code='uncited_claim_support')
    def test_shared_origin_is_not_independence(self):
        second=copy.deepcopy(self.m['sources'][0]); second['id']='S2'; self.m['sources'].append(second)
        edge=copy.deepcopy(self.m['claims'][0]['evidence'][0]);edge['source_id']='S2';self.m['claims'][0]['evidence'].append(edge)
        self.rebind(); self.assertEqual(self.result()['warnings'][0]['code'],'shared_origin')
    def test_countercheck_type_malformed(self): self.m['claims'][0]['countercheck']=[]; self.assertBlocked()
    def test_missing_artifact_record(self): self.m['sources'][0]['url']=''; self.assertBlocked(code='missing_source_location')
    def test_local_source_artifact_supported(self):
        self.m['sources'][0].update(url='',source_type='provided',artifact={'path':'review.md','sha256':mod.sha256_file(self.root/'review.md')})
        self.rebind();self.assertEqual(self.result()['result'],'RECORDS_COMPLETE')
    def test_missing_edition_not_silently_changed(self):
        self.m['publication']['edition']='';self.assertBlocked(code='missing_text')
    def test_review_future_date(self): self.m['checks'][0]['checked_on']='2026-09-15';self.assertBlocked(code='future_date')
    def test_malformed_pdf_is_input_error(self):
        (self.root/'ebook.pdf').write_bytes(b'not a PDF')
        with self.assertRaises(mod.InputError): self.result('release')
    def test_missing_pdf(self): self.assertBlocked('release',code='missing_pdf')
    def test_page_count_not_trusted(self): self.pdf_fixture(2); self.m['visual']['page_count']=1; self.assertBlocked('release',code='page_count_mismatch')
    def test_missing_page_review(self): self.pdf_fixture(2); self.m['visual']['pages'].pop(); self.assertBlocked('release',code='page_coverage')
    def test_duplicate_page_review(self): self.pdf_fixture(); self.m['visual']['pages']*=2; self.assertBlocked('release',code='page_coverage')
    def test_false_page_number_not_integer(self): self.pdf_fixture(); self.m['visual']['pages'][0]['page']=True; self.assertBlocked('release')
    def test_page_not_run(self): self.pdf_fixture(); self.m['visual']['pages'][0]['status']='not_run'; self.assertBlocked('release',code='page_not_pass')
    def test_page_image_changed(self): self.pdf_fixture(); (self.root/'page.png').write_bytes(b'changed'); self.assertBlocked('release',code='file_hash_mismatch')
    def test_pdf_hash_changed(self):
        self.pdf_fixture(); self.m['visual']['pdf_sha256']='0'*64; self.assertBlocked('release',code='pdf_hash_mismatch')
    def test_font_in_delivery_rejected(self):
        self.pdf_fixture(); (self.root/'font.TTF').write_bytes(b'not-font'); self.m['files']['deliverables'].append('font.TTF')
        self.assertBlocked('release',code='forbidden_deliverable')
    def test_path_traversal_rejected(self): self.m['files']['manuscript']='../escape.md'; self.assertBlocked('manuscript')
    def test_absolute_path_rejected(self): self.m['files']['manuscript']='/etc/passwd'; self.assertBlocked('manuscript')
    def test_symlink_escape_rejected(self):
        (self.root/'leak').symlink_to('/etc/passwd'); self.m['files']['manuscript']='leak'; self.assertBlocked('manuscript')
    def test_source_url_credentials_rejected(self): self.m['sources'][0]['url']='https://user:password@example.org'; self.assertBlocked(code='unsafe_source_url')
    def test_source_url_requires_supported_scheme(self): self.m['sources'][0]['url']='javascript:alert(1)'; self.assertBlocked(code='unsafe_source_url')
    def test_wrong_top_level_type(self):
        with self.assertRaises(mod.InputError): mod.validate([],self.root,'research',AS_OF)
    def test_boolean_sensitive_required(self): self.m['claims'][0]['time_sensitive']='false'; self.assertBlocked()
    def test_duplicate_json_keys_rejected(self):
        p=self.root/'bad.json'; p.write_text('{"schema":1,"schema":2}')
        with self.assertRaises(mod.InputError): mod.load_json(p)
    def test_nan_rejected(self):
        p=self.root/'bad.json'; p.write_text('{"x":NaN}')
        with self.assertRaises(mod.InputError): mod.load_json(p)
    def test_init_no_overwrite(self):
        p=self.root/'already'; p.mkdir(); (p/'sentinel').write_text('keep')
        with self.assertRaises(mod.InputError): mod.initialise(p)
        self.assertEqual((p/'sentinel').read_text(),'keep')
    def test_init_template_is_not_ready(self):
        p=self.root/'new'; mod.initialise(p); m=mod.load_json(p/'publication.json')
        self.assertEqual(mod.validate(m,p,'research',AS_OF)['result'],'BLOCKED')
    def test_fingerprints_dont_edit(self):
        before=copy.deepcopy(self.m); mod.fingerprints(self.m,self.root); self.assertEqual(before,self.m)
    def test_cli_valid_research(self):
        p=self.root/'publication.json'; p.write_text(json.dumps(self.m))
        out=subprocess.run([sys.executable,str(PKG/'scripts/ebook_check.py'),'validate',str(p),'--stage','research','--as-of','2026-09-14'],capture_output=True,text=True)
        self.assertEqual(out.returncode,0,out.stderr+out.stdout)
        self.assertEqual(json.loads(out.stdout)['result'],'RECORDS_COMPLETE')
    def test_cli_invalid_input_json(self):
        p=self.root/'publication.json'; p.write_text('[]')
        out=subprocess.run([sys.executable,str(PKG/'scripts/ebook_check.py'),'validate',str(p),'--stage','research'],capture_output=True,text=True)
        self.assertEqual(out.returncode,2); self.assertEqual(json.loads(out.stdout)['result'],'INPUT_ERROR')

class PackageTests(unittest.TestCase):
    def test_frontmatter(self):
        text=(PKG/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: ebook-publisher\n'))
        desc=text.split('description: ',1)[1].split('\n',1)[0]
        self.assertTrue(1 <= len(desc) <= 1024)
        self.assertLess(len(text.splitlines()),500)
    def test_all_main_relative_links_exist(self):
        import re
        for path in re.findall(r'\]\(([^)]+)\)',(PKG/'SKILL.md').read_text()):
            if '://' not in path: self.assertTrue((PKG/path).is_file(),path)
    def test_version_and_candidate_match(self):
        candidate=json.loads((PKG/'integration/registry-entry.json').read_text())
        self.assertEqual(candidate['version'],(PKG/'VERSION').read_text().strip())
        desc=(PKG/'SKILL.md').read_text().split('description: ',1)[1].split('\n',1)[0]
        self.assertEqual(desc,candidate['description'])
    def test_css_matches_state_tokens(self):
        tokens=json.loads((PKG/'assets/cometweb-tokens.json').read_text())
        css=(PKG/'assets/cometweb-print.css').read_text()
        for name,state in tokens['states'].items():
            rule=css.split('.status--'+name+' {',1)[1].split('}',1)[0]
            for key in ['text','fill','border']: self.assertIn(state[key],rule)
    def test_no_font_binaries(self):
        self.assertFalse([p for p in PKG.rglob('*') if p.suffix.lower() in {'.ttf','.otf','.woff','.woff2'}])
    def test_behaviour_cases_not_fabricated_results(self):
        data=json.loads((PKG/'evaluation/cases.json').read_text())
        self.assertEqual(data['execution_status'],'NOT_RUN_WITH_MODEL')
        ids=[c['id'] for c in data['cases']]; self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),15)
        for case in data['cases']: self.assertTrue(case['must'])
    def test_icons_are_well_formed(self):
        import xml.etree.ElementTree as ET
        root=ET.parse(PKG/'assets/status-icons.svg').getroot()
        self.assertEqual(len(list(root)),7)

if __name__=='__main__': unittest.main()
