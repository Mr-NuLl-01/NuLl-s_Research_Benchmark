"""Integrity tests for offline scientific materials, not tests of candidate answers."""
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from xml.etree import ElementTree as ET

from nrb_v1.research import tasks

ROOT = Path(__file__).resolve().parents[1]


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources=[]
        self.tags=[]
        self.text=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        self.tags.append((tag,attrs))
        if tag in {'img','script','iframe','audio','video','source','link','object','embed'}:
            for key in ('src','href','data','poster','srcset'):
                if key in attrs:self.resources.append((tag,key,attrs[key]))
    def handle_data(self,data):
        self.text.append(data)


class ResearchPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks=tasks()
        cls.by_id={t['id']:t for t in cls.tasks}

    def test_required_and_optional_tracks_are_distinct(self):
        self.assertEqual([t['id'] for t in self.tasks if t['track']=='research'],[f'R{i:02d}' for i in range(1,7)])
        self.assertEqual([t['id'] for t in self.tasks if t['track']=='optional'],['X01','X02','X03'])
        for tid in ['X01','X02','X03']:
            self.assertIn('excluded from the enabled-track denominator',self.by_id[tid]['content'])
            self.assertIn('unavailable',self.by_id[tid]['content'])

    def test_manual_rubrics_have_explicit_weights_anchors_and_gates(self):
        for task in self.tasks:
            with self.subTest(task=task['id']):
                self.assertEqual(sum(c['weight'] for c in task['rubric']),100)
                self.assertGreaterEqual(len(task['rubric']),5)
                self.assertGreaterEqual(len(task['essential']),3)
                self.assertTrue(task['required_artifacts'])
                self.assertTrue(task['capabilities'])
                for criterion in task['rubric']:
                    self.assertEqual(set(criterion['anchors']),{'0','2','4'})
                    self.assertTrue(all(len(s)>30 for s in criterion['anchors'].values()))
                    # Evaluator anchors must not leak into self-contained candidate file.
                    for anchor in criterion['anchors'].values():
                        self.assertNotIn(anchor,task['content'])

    def test_artifact_contracts_use_concrete_names_and_observable_outputs(self):
        for task in self.tasks:
            with self.subTest(task=task['id']):
                for name in task['required_artifacts']:
                    self.assertNotRegex(name,r'\s|[()]')
                self.assertTrue(set(task['modal_observation_artifacts']).issubset(task['required_artifacts']))
                self.assertFalse(set(task['optional_artifacts']) & set(task['required_artifacts']))
        self.assertIn('source.zip',self.by_id['R01']['required_artifacts'])
        self.assertIn('captions.srt',self.by_id['X02']['required_artifacts'])
        self.assertEqual(self.by_id['X03']['optional_artifacts'],['listening-preview.mp3'])

    def test_each_candidate_is_one_small_offline_html(self):
        for task in self.tasks:
            with self.subTest(task=task['id']):
                content=task['content']
                self.assertEqual(task['format'],'html')
                self.assertTrue(content.startswith('<!doctype html>'))
                self.assertLess(len(content.encode('utf-8')),3_000_000)
                p=ResourceParser();p.feed(content)
                for tag,key,url in p.resources:
                    self.assertTrue(url.startswith('data:') or url.startswith('#'),(task['id'],tag,key,url[:100]))
                    if url.startswith('data:image/png;base64,'):
                        self.assertTrue(base64.b64decode(url.split(',',1)[1]).startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertFalse(any(tag in {'script','iframe','object','embed'} for tag,_ in p.tags))
                self.assertNotRegex(content,r'url\([\s\'"]*https?://')
                self.assertNotIn('answer_key',content.lower())

    def test_actual_reference_images_and_readable_papers_are_supplied(self):
        r01=ResourceParser();r01.feed(self.by_id['R01']['content'])
        self.assertEqual(sum(tag=='img' for tag,_ in r01.tags),3)
        for tid in ['R05','R06']:
            p=ResourceParser();p.feed(self.by_id[tid]['content'])
            text=' '.join(p.text)
            self.assertEqual(sum(tag=='img' for tag,_ in p.tags),17)
            self.assertGreater(len(text.split()),17000)
            for required in ['943 articles were screened','Analyses were completed on the remaining 631','Defining colour spaces','Rule 10: Get the Right Tool','10.1371/journal.pbio.1002128','10.1371/journal.pcbi.1003833','10.1038/s41467-020-19160-7']:
                self.assertIn(required,text)

    def test_figure_writing_task_contains_real_svg_and_underlying_tables(self):
        content=self.by_id['R04']['content']
        svg=re.search(r'(<svg\b.*?</svg>)',content,re.S).group(1)
        root=ET.fromstring(svg)
        ns={'s':'http://www.w3.org/2000/svg'}
        self.assertGreaterEqual(len(root.findall('.//s:text',ns)),12)
        self.assertIn('paired.csv',content)
        self.assertIn('transient.csv',content)
        self.assertIn('Mean ± SD',content)
        self.assertIn('benchmark-created synthetic',content.lower())

    def test_source_license_and_byte_provenance(self):
        source_root=ROOT/'sources'/'v1'
        manifest=json.loads((source_root/'manifest.json').read_text())
        licenses={a['id']:a['license'] for a in manifest['articles']}
        self.assertEqual(licenses,{'P1':'CC BY 4.0','P2':'CC0 1.0 public domain dedication','P3':'CC BY 4.0'})
        for a in manifest['articles']:
            self.assertTrue(a['license_statement'])
            self.assertTrue(a['supplied_scope'])
            self.assertTrue(a['doi'])
        for asset in manifest['assets']:
            path=source_root/asset['path']
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_size,asset['bytes'],asset['path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'],asset['path'])
        self.assertTrue((source_root/'weissgerber2015-s1.docx').is_file())
        self.assertIn('Methods',(source_root/'weissgerber2015-s1.txt').read_text())


if __name__=='__main__':
    unittest.main()
