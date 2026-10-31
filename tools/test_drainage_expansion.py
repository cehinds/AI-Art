import copy
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
import drainage_expansion as d

class DrainageTests(unittest.TestCase):
    def test_all_quarter_turns(self):
        self.assertEqual(d.rotate(['N','E'],90),['E','S'])
        self.assertEqual(d.rotate(['N','E','W'],270),['N','S','W'])
        for edges in d.EDGES.values():
            self.assertEqual(d.rotate(d.rotate(edges,90),270), d.rotate(edges,0))
        with self.assertRaises(ValueError): d.rotate(['N'],45)

    def test_connection_errors(self):
        p={'placements':[{'cell':[0,0],'shape':'straight','rotation_deg':90},{'cell':[1,0],'shape':'straight','rotation_deg':0}]}
        with self.assertRaisesRegex(ValueError,'Nonreciprocal'):d.validate_connections(p)
        p['placements'][1]['rotation_deg']=90
        d.validate_connections(p)
        p['open_boundaries']=[]
        with self.assertRaisesRegex(ValueError,'Open channel'):d.validate_connections(p)
        del p['open_boundaries']
        p['placements'][1]['cell']=[0,0]
        with self.assertRaisesRegex(ValueError,'Overlapping'):d.validate_connections(p)

    def test_alpha_cleanup_preserves_primary_and_rgb(self):
        image=Image.new('RGBA',(12,12),(30,90,100,0))
        for y in range(2,7):
            for x in range(2,7):image.putpixel((x,y),(30,90,100,254))
        image.putpixel((0,0),(30,90,100,8))
        for y in range(5):image.putpixel((9,y),(30,90,100,254)) # significant secondary component preserved
        image.putpixel((10,10),(30,90,100,254))
        image.putpixel((11,11),(30,90,100,254)) # diagonal8-connected pair
        clean,stats=d.clean_alpha(image)
        self.assertEqual(stats,{'alpha_below_threshold_pixels_removed':1,'secondary_components_removed':1,'secondary_component_pixels_removed':2,'retained_component_count':2})
        self.assertEqual(clean.getpixel((3,3)),image.getpixel((3,3)))
        self.assertEqual(clean.getpixel((10,10)),(30,90,100,0))
        self.assertEqual(clean.convert('RGB').tobytes(),image.convert('RGB').tobytes())

    def test_map_bounds(self):
        recipe={'placements':[{'shape':'straight','cell':[-1,0],'rotation_deg':0}],'cell_size_px':128,'canvas_px':[256,256],'background_rgba':[35,39,43,255]}
        with self.assertRaisesRegex(ValueError,'outside map'):d.render(Path('/tmp'),recipe)

    def test_explicit_background_and_asset_reference(self):
        recipe={'placements':[],'cell_size_px':16,'canvas_px':[32,32],'background_rgba':[10,80,90,77]}
        self.assertEqual(d.render(Path('/tmp'),recipe).getpixel((0,0)),(10,80,90,77))
        recipe['background_rgba']=[0,0,0,256]
        with self.assertRaisesRegex(ValueError,'RGBA bytes'):d.render(Path('/tmp'),recipe)
        recipe['background_rgba']=[10,80,90,77]
        recipe['placements']=[{'shape':'straight','cell':[0,0],'rotation_deg':0,'asset_id':'drainage-corner-top'}]
        with self.assertRaisesRegex(ValueError,'asset reference mismatch'):d.render(Path('/tmp'),recipe)

    def test_build_replay_hashes_and_references(self):
        # Synthetic input verifies crop mechanics only; production art comes from imagegen.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'source').mkdir()
            Image.new('RGBA',(12,12),(20,70,90,255)).save(root/'source/raw.png')
            (root/'source/prompt.txt').write_text('test fixture')
            recipe={'exports':[{'shape':s,'view':v,'source':'source/raw.png','crop':[0,0,12,12],'normalization':{'method':'nearest-width-centered-canvas','canvas_px':[32,32],'target_width_px':24,'alpha_threshold':16,'remove_secondary_components_max_px':4}} for s in d.EDGES for v in d.VIEWS]}
            d.write(root/'source/recipe.json',recipe)
            d.build(root)
            first={str(p.relative_to(root)):d.sha(p) for p in root.rglob('*') if p.is_file()}
            d.build(root)
            self.assertEqual(first,{str(p.relative_to(root)):d.sha(p) for p in root.rglob('*') if p.is_file()})
            self.assertEqual(d.check(root)['assets'],21)
            decisions=d.read(root/'review.json')
            decisions['root_approval']={'status':'approved-qualified','reviewer':'test fixture'}
            decisions['status']='qualified-pass'
            decisions['map_review']={'alignment_report_sha256':d.sha(root/'maps/alignment-report.json')}
            decisions['source_evidence']=[{'source_path':'source/raw.png','source_sha256':d.sha(root/'source/raw.png'),'contact_review_path':'previews/straight-contact.png','contact_sha256':d.sha(root/'previews/straight-contact.png')}]
            for record in decisions['records']:record['status']='qualified-pass'
            d.write(root/'source/review-decisions.json',decisions)
            d.build(root)
            self.assertEqual(d.read(root/'catalog.json')['status'],'qualified-reviewed')
            approved={str(p.relative_to(root)):d.sha(p) for p in root.rglob('*') if p.is_file()}
            d.build(root)
            self.assertEqual(approved,{str(p.relative_to(root)):d.sha(p) for p in root.rglob('*') if p.is_file()})
            decisions['records'][0]['sha256']='0'*64
            d.write(root/'source/review-decisions.json',decisions)
            with self.assertRaisesRegex(ValueError,'Stale'):d.build(root)
            self.assertEqual(approved['catalog.json'],d.sha(root/'catalog.json'))
            self.assertEqual(approved['drainage-channels-v1.zip'],d.sha(root/'drainage-channels-v1.zip'))
            decisions['records'][0]['sha256']=d.read(root/'review.json')['records'][0]['sha256']
            d.write(root/'source/review-decisions.json',decisions)
            for target,key in [(decisions['map_review'],'alignment_report_sha256'),(decisions['source_evidence'][0],'source_sha256'),(decisions['source_evidence'][0],'contact_sha256')]:
                good=target[key];target[key]='0'*64;d.write(root/'source/review-decisions.json',decisions)
                with self.assertRaisesRegex(ValueError,'[Rr]eview.*hash mismatch'):d.build(root)
                self.assertEqual(approved['catalog.json'],d.sha(root/'catalog.json'))
                self.assertEqual(approved['drainage-channels-v1.zip'],d.sha(root/'drainage-channels-v1.zip'))
                target[key]=good;d.write(root/'source/review-decisions.json',decisions)
            asset=json.loads((root/'catalog.json').read_text())['assets'][0]
            self.assertEqual(asset['placement']['support_tile_ids'],[d.SUPPORT])
            (root/asset['image']['path']).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'PNG hash mismatch'):d.check(root)

if __name__=='__main__':unittest.main()
