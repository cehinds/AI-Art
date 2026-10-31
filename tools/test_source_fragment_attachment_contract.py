"""Source reconstruction evidence must survive attachment checks byte-for-byte."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import asset_attachment_tags as tags


class SourceFragmentEvidenceTests(unittest.TestCase):
    def evidence(self):
        digest = 'a' * 64
        return {'schemaVersion': 1, 'canvas': [16, 16], 'source': 'source.png',
                'sourceSha256': digest,
                'representation': 'visible source fragments; occluded pixels are absent, not inferred',
                'layers': [{'id': 'wall-source', 'file': 'components/wall.png',
                            'componentSha256': 'b' * 64,
                            'provenance': {'kind': 'literal-source-pixels', 'sourceSha256': digest}},
                           {'id': 'occluded', 'visiblePixels': 0, 'visibility': 'fully occluded'}]}

    def test_check_and_apply_preserve_exact_evidence_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'assets'
            root.mkdir()
            (root / 'reusable-library.json').write_text(tags.encoded({'libraries': []}))
            evidence = root / 'manifest.json'
            raw = json.dumps(self.evidence(), separators=(',', ':')).encode()
            evidence.write_bytes(raw)
            tags.apply(root)
            self.assertEqual(evidence.read_bytes(), raw)
            self.assertEqual(tags.apply(root, check=True)['changed'], 0)
            self.assertEqual(tags.apply(root, check=True)['preserved_generation_documents'], 1)

    def test_ordinary_and_incomplete_manifests_remain_subject_to_enrichment(self):
        for mutate in (lambda d: d.pop('representation'),
                       lambda d: d['layers'][0]['provenance'].update(kind='inferred'),
                       lambda d: d['layers'][0].update(componentSha256='bad'),
                       lambda d: d['layers'][0]['provenance'].update(sourceSha256='c' * 64)):
            document = copy.deepcopy(self.evidence())
            mutate(document)
            self.assertFalse(tags.is_source_fragment_evidence(document))
            tags.enrich_document(document, 'gameplay')
            self.assertIn('attachment', document['layers'][0])


if __name__ == '__main__':
    unittest.main()
