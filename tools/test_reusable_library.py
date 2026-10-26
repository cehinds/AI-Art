#!/usr/bin/env python3
"""Small deterministic fixtures for generic native extraction and archive closure."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
from build_pocket_reusable import Builder, image_bytes, json_bytes
from build_reusable_library import BookBuilder, GameplayBuilder, region_asset, registry
from package_pocket_reusable import plan
from validate_pocket_reusable import validate, view_set_approved, check_asset_geometry, render
from render_art_remix import render as render_remix, eligible
from asset_attachment_tags import enrich_library


class LibraryTests(unittest.TestCase):
    def test_composition_reference_does_not_replace_decomposed_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);assets=root/'assets';(root/'tools').mkdir()
            for folder in ('dungeon-stone','room-kit/concept'):
                (assets/folder).mkdir(parents=True)
                for suffix in 'abcd':
                    Image.new('RGBA',(2,2),(40,50,60,255)).save(assets/folder/f'stone-{suffix}.png')
            (assets/'house').mkdir()
            source=Image.new('RGBA',(20,20),(30,40,50,255))
            source.putpixel((0,0),(13,27,39,0))
            source.save(assets/'house/carl.png')
            regions=[{'id':'house--carl','label':'Room illustration','rect':[0,0,20,20],
                      'kind':'composition','physical':False,'reusable':False,'reconstruction_placement':False},
                     {'id':'house--carl--furnishing','label':'Furnishing occurrence','rect':[5,5,8,8],
                      'kind':'reconstruction_patch','physical':True,'reusable':False}]
            (root/'tools/all_asset_scene_regions.json').write_text(json.dumps(
                {'sources':[{'path':'house/carl.png','regions':regions}]}))
            with patch('build_reusable_library.ROOT',root),patch('build_reusable_library.ASSETS',assets):
                b=GameplayBuilder();outputs=b.build()
            index=json.loads(outputs['reusable/index.json'])
            entries={a['id']:a for a in index['assets']}
            room_map=next(m for m in index['maps'] if m['id']=='atlas-house--carl')
            document=json.loads(outputs[room_map['file']])
            placed={layer['asset_id'] for layer in document['layers']}
            self.assertNotIn('house--carl',placed)
            self.assertIn('house--carl--furnishing',placed)
            self.assertFalse(entries['house--carl']['views']['applicable'])
            self.assertFalse(entries['house--carl']['reconstruction']['placement'])
            for relative,raw in outputs.items():
                destination=b.pack/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            recreated=render(b.pack,document,entries)
            self.assertEqual(recreated.tobytes(),source.tobytes())

    def test_book_sample_preserves_edges_and_excludes_manual_transitions(self):
        with tempfile.TemporaryDirectory() as directory:
            b=self.fixture(Path(directory));b.normalized=[]
            for name,join,color in [('floor','join.floor',(90,40,20,255)),('transition','join.manual',(20,90,40,255))]:
                path=name+'.png';b.outputs[path]=image_bytes(Image.new('RGBA',(128,128),color))
                b.normalized.append({'id':name,'name':name,'kind':'tile','category':'ground',
                    'tags':['starter-dungeon'],'image':b.image_info(path),
                    'edges':{side:[join,'visual.starter-dungeon'] for side in ('north','east','south','west')},
                    'procedural':{'placement':{'points':[[0,0],[128,0],[128,128],[0,128]]}}})
            BookBuilder.add_procedural(b)
            recipe=json.loads(b.outputs['reusable/procedural/sample.json'])
            used={cell['asset_id'] for cell in recipe['cells'] if cell['walkable']}
            self.assertEqual(used,{'floor--surface'})
            self.assertEqual(b.assets['transition--surface']['edges'],b.normalized[1]['edges'])
            self.assertEqual(b.assets['transition--surface']['procedural']['connections'],[])
            first=dict(b.outputs);BookBuilder.add_procedural(b)
            self.assertEqual(b.outputs,first)

    def fixture(self, root):
        b=Builder.__new__(Builder)
        b.pack=root;b.outputs={};b.assets={};b.residuals={};b.maps=[];b.pixel_inventory={}
        b.manifest={'id':'fixture'};b.existing_index={}
        source=Image.new('RGBA',(20,20),(30,30,30,255))
        for x in range(6,14):
            for y in range(6,14):source.putpixel((x,y),(230,40,60,255))
        source.putpixel((0,0),(13,27,39,0))
        b.outputs['source.png']=image_bytes(source)
        return b

    def test_staged_mask_exact_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);b=self.fixture(root)
            asset=region_asset(b,'source.png',{'id':'glyph','label':'Glyph','rect':[0,0,20,20],
                'kind':'ui','physical':False,'mask':{'method':'border-color-distance','distance_threshold':45}},'fixture')
            b.metadata(asset);b.map_from_source('source','Source','source.png',[(asset,0,0)],'atlas')
            for residual in b.residuals.values():b.metadata(residual)
            index={'schema_version':1,'assets':list(b.assets.values()),'maps':b.maps,'view_sets':[],'procedural':{}}
            enrich_library(root,index)
            b.outputs['reusable/index.json']=json_bytes(index)
            b.finalize_outputs()
            first=dict(b.outputs);b.finalize_outputs()
            self.assertEqual(b.outputs,first)
            for path,raw in b.outputs.items():
                destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            report=validate(root)
            self.assertEqual(report['maps_pixel_exact'],1)
            self.assertEqual(report['maps'][0]['differing_pixels'],0)
            overlay=Image.open(root/asset['image']['path']).convert('RGBA')
            self.assertEqual(overlay.getpixel((7,7)),(230,40,60,255))
            self.assertEqual(overlay.getpixel((1,1)),(0,0,0,0))

    def test_region_bounds_fail_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            b=self.fixture(Path(directory));before=set(b.outputs)
            with self.assertRaisesRegex(ValueError,'bounds'):
                region_asset(b,'source.png',{'id':'bad','label':'Bad','rect':[19,0,2,2],'kind':'ui'},'fixture')
            self.assertEqual(set(b.outputs),before)

    def test_archive_includes_canonical_and_surface_companions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);b=self.fixture(root)
            records=[]
            for i,identity in enumerate(('native','normalized','surface')):
                a=region_asset(b,'source.png',{'id':identity,'label':identity,'rect':[i,0,5,5],'kind':'ui','physical':False},'fixture')
                if identity!='normalized':a['canonical_asset_id']='normalized'
                b.metadata(a);records.append(a)
            b.map_from_source('source','Source','source.png',[(records[0],0,0)],'atlas')
            for a in b.residuals.values():b.metadata(a)
            b.outputs['manifest.json']=json_bytes({'assets':[]})
            b.outputs['README.md']=b'Fixture\n'
            b.outputs['reusable/index.json']=json_bytes({'assets':list(b.assets.values()),'maps':b.maps,'view_sets':[]})
            for path,raw in b.outputs.items():
                destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            contents=plan(root,['source'])
            exported=json.loads(contents['library/reusable/index.json'])
            self.assertTrue({'native','normalized','surface'} <= {a['id'] for a in exported['assets']})
            for a in exported['assets']:
                self.assertIn('library/'+a['image']['path'],contents)
                self.assertIn('library/'+a['metadata_path'],contents)

    def test_pending_geometry_is_not_complete(self):
        self.assertFalse(view_set_approved({'complete':True,'geometry_qa':{'status':'pending-correction'}}))
        self.assertFalse(view_set_approved({'complete':False,'geometry_qa':{'status':'passed'}}))
        self.assertTrue(view_set_approved({'complete':True,'geometry_qa':{'status':'passed'}}))

    def test_principal_view_calibration_cannot_squeeze_axes_to_fit(self):
        with tempfile.TemporaryDirectory() as directory:
            asset={'id':'wall.top','view':'top','anchor_px':[4,4],
                'provenance':{'method':'generated','source_cell_calibration':[0.4,0.55]}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            with self.assertRaisesRegex(ValueError,'Anisotropic'):
                check_asset_geometry(Path(directory),asset,image,{})
            asset['provenance']['source_cell_calibration']=[0.4,0.4]
            self.assertEqual(check_asset_geometry(Path(directory),asset,image,{}),(0,0,8,8))
            asset['provenance']['source_cell_calibration']=[float('nan'),0.4]
            with self.assertRaisesRegex(ValueError,'Malformed'):
                check_asset_geometry(Path(directory),asset,image,{})

    def test_mixed_renderer_odd_center_rotation_and_trusted_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);libraries=[]
            for name,color in [('one',(255,0,0,255)),('two',(0,255,0,255))]:
                pack=root/name;pack.mkdir()
                source=Image.new('RGBA',(3,5),(0,0,0,0));source.putpixel((0,0),color)
                (pack/'sprite.png').write_bytes(image_bytes(source))
                b=self.fixture(pack)
                asset={'id':'sprite','kind':'ui','image':b.image_info('sprite.png'),'view':'source'}
                (pack/'index.json').write_bytes(json_bytes({'assets':[asset]}))
                libraries.append({'id':name,'base':name,'index':name+'/index.json'})
            (root/'reusable-library.json').write_bytes(json_bytes({'libraries':libraries}))
            document={'schema_version':2,'kind':'semantic-remix','canvas':{'width':12,'height':12},
                'dependencies':[{'library_id':name,'art_commit':'a'*40} for name in ('one','two')],
                'placements':[{'library_id':name,'asset_id':'sprite','path':'sprite.png','x':x,'y':5,'rotation_deg':90,'scale':1,'anchor':'center'} for name,x in [('one',5),('two',8)]]}
            rendered=render_remix(root,document,'a'*40)
            self.assertEqual(rendered.getpixel((6,4)),(255,0,0,255))
            self.assertEqual(rendered.getpixel((9,4)),(0,255,0,255))
            with self.assertRaisesRegex(ValueError,'revision mismatch'):render_remix(root,document,'b'*40)
            document['placements'][0]['path']='../sprite.png'
            with self.assertRaisesRegex(ValueError,'trusted asset metadata'):render_remix(root,document,'a'*40)

    def test_registry_is_seven_distinct_contained_libraries(self):
        rows=registry()['libraries']
        self.assertEqual(len(rows),7)
        self.assertEqual(len({r['id'] for r in rows}),7)
        for row in rows:
            self.assertNotIn('..',Path(row['index']).parts)
            self.assertTrue(row['index'].startswith(row['base']+'/'))

    def test_remix_principal_leaf_requires_canonical_direction_reference(self):
        parent={'id':'object','kind':'reconstruction_patch','reusable':False}
        leaf={'id':'object.top','object_id':'object','view':'top','kind':'sprite','reusable':True}
        catalog={'object':parent,'object.top':leaf}
        self.assertFalse(eligible(leaf,catalog))
        self.assertTrue(eligible(leaf,catalog,[{'object_id':'object','views':{'top':'object.top'}}]))
        self.assertFalse(eligible(leaf,catalog,[{'object_id':'object','views':{'front':'object.top'}}]))
        parent['views']={'top':{'asset_id':'object.top'}}
        self.assertTrue(eligible(leaf,catalog))
        self.assertFalse(eligible({**leaf,'object_id':'missing'},catalog))
        self.assertFalse(eligible({**leaf,'reusable':False},catalog))

    def test_animation_poses_keep_separate_roots_but_share_camera_aliases(self):
        from unittest.mock import patch
        from build_reusable_library import GameplayBuilder
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'directional').mkdir()
            frame={'x':0,'y':0,'width':8,'height':8}
            manifest={'characters':{'hero':{'file':'hero.png','frames':{
                direction:{pose:frame for pose in ('idle','walk1')} for direction in ('se','sw')}}}}
            (root/'directional/manifest.json').write_text(json.dumps(manifest))
            with patch('build_reusable_library.ASSETS',root):
                rows=GameplayBuilder.__new__(GameplayBuilder).automatic_regions('directional/hero.png',Image.new('RGBA',(8,8)))
            self.assertEqual([r['id'] for r in rows if r['physical']],['directional--hero','directional--hero--se--walk1'])
            self.assertEqual(rows[2]['canonical_asset_id'],rows[0]['id'])
            self.assertEqual(rows[3]['canonical_asset_id'],rows[1]['id'])
            self.assertEqual(rows[3]['pose'],'walk1')

    def test_book_contact_cards_are_exact_nonphysical_presentation_patches(self):
        from register_existing_derivatives import register_existing_derivatives
        from validate_pocket_reusable import render
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'book-tiles/fixture';root.mkdir(parents=True)
            b=self.fixture(root);(root/'kit').mkdir()
            (root/'kit/manifest.json').write_text(json.dumps({'assets':[{'id':'one'}]}))
            source=Image.new('RGBA',(768,640),(13,27,39,255))
            source.putpixel((0,0),(17,29,41,0))
            source.save(root/'kit/contact-sheet.png')
            register_existing_derivatives(b)
            for a in b.residuals.values():b.metadata(a)
            for path,raw in b.outputs.items():
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            document=json.loads(b.outputs[b.maps[0]['file']])
            self.assertEqual(render(root,document,b.assets).tobytes(),source.tobytes())
            card=b.assets['diagnostic--kit--contact-sheet--card-001']
            self.assertFalse(card['reusable'])
            self.assertFalse(card['views']['applicable'])
            self.assertEqual(card['canonical_asset_id'],'one')


if __name__=='__main__':unittest.main()
