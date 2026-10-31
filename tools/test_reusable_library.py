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
from validate_pocket_reusable import (validate, view_set_approved, check_asset_geometry,
    crop_alpha_bounds_xyxy, validate_normalization_records, normalization_input_group,
    per_view_normalization_basis, affine_calibration_basis, retained_snapshot_basis,
    _check_executed_replay_binding, render, digest)
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
            usage=json.loads(contents['usage.json'])
            self.assertEqual(usage['catalog_root'],'library/')
            self.assertIn('render_pocket_map.py',usage['commands']['render_map'])
            self.assertNotIn('READ-ME.txt',contents)
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

    def test_declared_xywh_crop_bounds_are_validated_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGBA',(20,20),(1,2,3,255)).save(root/'atlas.png')
            asset={'id':'object.top','view':'top','anchor_px':[4,4],
                'provenance':{'source_atlas':'atlas.png','crop_bounds_px':{
                    'coordinate_format':'xywh','alpha_bounds_global':[2,3,4,5]}}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            self.assertEqual(crop_alpha_bounds_xyxy(asset['provenance']['crop_bounds_px'],'fixture'),[2,3,6,8])
            self.assertEqual(check_asset_geometry(root,asset,image,{}),(0,0,8,8))
            asset['provenance']['crop_bounds_px']['alpha_bounds_global']=[18,3,4,5]
            with self.assertRaisesRegex(ValueError,'outside image'):
                check_asset_geometry(root,asset,image,{})

    def test_legacy_alpha_bounds_remain_xyxy_and_unknown_format_fails(self):
        self.assertEqual(crop_alpha_bounds_xyxy({'alpha_bounds_global':[2,3,6,8]},'fixture'),[2,3,6,8])
        with self.assertRaisesRegex(ValueError,'Unknown alpha-bounds coordinate format'):
            crop_alpha_bounds_xyxy({'coordinate_format':'guess','alpha_bounds_global':[2,3,6,8]},'fixture')

    def test_source_rect_uses_declared_scene_when_source_image_is_a_crop(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGBA',(6,4),(1,2,3,255)).save(root/'crop.png')
            Image.new('RGBA',(20,20),(4,5,6,255)).save(root/'scene.png')
            scene_hash=hashlib.sha256((root/'scene.png').read_bytes()).hexdigest()
            asset={'id':'crop.top','view':'top','anchor_px':[4,4],
                'provenance':{'source_image':'crop.png','source_scene':'scene.png',
                    'source_scene_sha256':scene_hash,
                    'source_rect':[10,11,6,4]}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            self.assertEqual(check_asset_geometry(root,asset,image,{}),(0,0,8,8))
            asset['provenance']['source_scene_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'source_rect image hash mismatch'):
                check_asset_geometry(root,asset,image,{})
            asset['provenance']['source_scene_sha256']=scene_hash
            asset['provenance']['source_rect']=[18,11,6,4]
            with self.assertRaisesRegex(ValueError,'source_rect'):
                check_asset_geometry(root,asset,image,{})

    def test_dict_source_rect_honors_explicit_image_and_coordinate_format(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGBA',(6,4),(1,2,3,255)).save(root/'crop.png')
            Image.new('RGBA',(20,20),(4,5,6,255)).save(root/'atlas.png')
            atlas_hash=hashlib.sha256((root/'atlas.png').read_bytes()).hexdigest()
            asset={'id':'crop.left','view':'left','anchor_px':[4,4], 'provenance':{
                'source_image':'crop.png','source_rect_image':'atlas.png',
                'source_rect_image_sha256':atlas_hash,'source_rect':{
                    'source_size':[20,20],'coordinate_format':'xyxy','alpha_bounds':[10,11,16,15]}}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            self.assertEqual(check_asset_geometry(root,asset,image,{}),(0,0,8,8))
            asset['provenance']['source_rect']['alpha_bounds']=[10,11,17,21]
            with self.assertRaisesRegex(ValueError,'source_rect/alpha_bounds'):
                check_asset_geometry(root,asset,image,{})

    def test_external_source_rect_requires_hash_bound_dimensions(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGBA',(6,4),(1,2,3,255)).save(root/'crop.png')
            raw=b'outside-pack-atlas';source_hash=hashlib.sha256(raw).hexdigest()
            asset={'id':'crop.rear','view':'rear','anchor_px':[4,4], 'provenance':{
                'source_image':'crop.png','source_rect_image':'raw/atlas.png',
                'source_rect_image_sha256':source_hash,'source_rect_coordinate_format':'xyxy',
                'source_rect':[10,11,16,15]}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            external={'raw/atlas.png':{'path':'raw/atlas.png','sha256':source_hash,'size_px':[20,20]}}
            self.assertEqual(check_asset_geometry(root,asset,image,{},external),(0,0,8,8))
            with self.assertRaisesRegex(ValueError,'Missing source_rect image'):
                check_asset_geometry(root,asset,image,{},{})
            external['raw/atlas.png']['size_px']=[12,12]
            with self.assertRaisesRegex(ValueError,'outside image'):
                check_asset_geometry(root,asset,image,{},external)

    def test_historical_list_normalization_is_validated_explicitly(self):
        record={'view':'front','candidate_path':'raw/front.png','candidate_sha256':'a'*64,
            'raw_bbox':[2,3,12,23],'raw_dimensions':[10,20],'render_size':[5,10],
            'uniform_scale':0.5,'threshold_alpha':16,'anchor_px':[128,248]}
        validate_normalization_records([record],(20,30),'fixture')
        malformed={**record,'raw_dimensions':[10,19]}
        with self.assertRaisesRegex(ValueError,'raw dimensions disagree'):
            validate_normalization_records([malformed],(20,30),'fixture')

    def test_adapter_extractor_atlas_is_hash_bound_crop_coordinate_source(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGBA',(20,10),(1,2,3,255)).save(root/'direct.png')
            Image.new('RGBA',(30,30),(4,5,6,255)).save(root/'extractor.png')
            direct_hash=hashlib.sha256((root/'direct.png').read_bytes()).hexdigest()
            extractor_hash=hashlib.sha256((root/'extractor.png').read_bytes()).hexdigest()
            asset={'id':'adapter.top','view':'top','anchor_px':[4,4], 'provenance':{
                'source_atlas':'direct.png','source_atlas_sha256':direct_hash,
                'normalization_adapter':{'extractor_atlas':'extractor.png','extractor_sha256':extractor_hash},
                'crop_bounds_px':{'alpha_bounds_global':[22,5,28,28]}}}
            image=Image.new('RGBA',(8,8),(100,100,100,255))
            self.assertEqual(check_asset_geometry(root,asset,image,{}),(0,0,8,8))
            asset['provenance']['normalization_adapter']['extractor_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'adapter atlas hash mismatch'):
                check_asset_geometry(root,asset,image,{})
            asset['provenance']['normalization_adapter']['extractor_sha256']=extractor_hash
            asset['provenance']['crop_bounds_px']['alpha_bounds_global']=[29,5,38,28]
            with self.assertRaisesRegex(ValueError,'alpha_bounds_global'):
                check_asset_geometry(root,asset,image,{})

    def test_supported_local_cell_normalization_group_is_strict(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);Image.new('RGBA',(30,30)).save(root/'atlas.png')
            atlas_hash=hashlib.sha256((root/'atlas.png').read_bytes()).hexdigest()
            group={'schema_version':1,'method':'process_object_local_cells_shared_scale',
                'recipe_id':'object-local-cell-alpha-components-shared-scale-v1',
                'source_atlas':'atlas.png','source_atlas_sha256':atlas_hash,
                'cell_grid':{'columns':6,'rows':6,'row_index':2,'cell_size_px':[256,171]},
                'alpha_threshold_exclusive':32,'component_connectivity':4,'minimum_component_area_px':24,
                'edge_touch_margin_px':1,
                'component_selection':'non-edge-touching-at-least-1-percent-largest-fallback-largest',
                'cell_calibration':[1.0,1.0],
                'shared_scale_formula':'204/max-width-or-height-of-all-six-extracted-cells-after-calibration',
                'resampling':'nearest'}
            provenance={'generated_atlas':'atlas.png','generated_atlas_sha256':atlas_hash,
                'source_cell_calibration':[1.0,1.0],'normalization':{'input_group':group}}
            self.assertIsNotNone(normalization_input_group(root,provenance,{},'fixture'))
            provenance['source_cell_calibration']=[0.5,1.0]
            with self.assertRaisesRegex(ValueError,'calibration'):
                normalization_input_group(root,provenance,{},'fixture')

    def test_per_view_scale_policy_requires_exact_bound_recipe_cell(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=Image.new('RGBA',(2,2),(1,2,3,255));source.save(root/'source.png')
            atlas=Image.new('RGBA',(4,4),(4,5,6,255));atlas.save(root/'atlas.png')
            output=Image.new('RGBA',(8,8),(7,8,9,255));output.save(root/'output.png')
            (root/'producer.json').write_text(json.dumps({'purpose':'source-bound output recipe'}))
            sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
            recipe={'records':[{'object_id':'object','view':'front','scale':0.5,
                'source_path':'source.png','source_sha256':sha('source.png'),
                'atlas_path':'atlas.png','atlas_sha256':sha('atlas.png'),
                'active_output_sha256':sha('output.png'),
                'active_output_rgba_sha256':digest(output),
                'crop_bounds_xyxy':[0,0,4,4],'resized_dimensions_px':[2,2],
                'projection_scale':1,'replay_status':'exact-output-hash-match',
                'verification_basis':'producer-recorded-output',
                'original_recipe_path':'producer.json','original_recipe_sha256':sha('producer.json'),
                'original_recipe_output_sha256':sha('output.png'),'original_recipe_output_match':True}]}
            (root/'recipe.json').write_text(json.dumps(recipe))
            recipe_hash=sha('recipe.json')
            asset={'id':'object.front','object_id':'object','view':'front',
                'image':{'path':'output.png','sha256':sha('output.png')},'provenance':{
                    'source_image':'source.png','source_sha256':sha('source.png'),
                    'generated_atlas':'atlas.png','generated_atlas_sha256':sha('atlas.png'),
                    'crop_bounds_px':{'alpha_bounds_global':[0,0,4,4],
                        'resized_bounds_px':[2,2]},
                    'normalization':{'scale':0.5,'scale_policy':'per-view-uniform',
                        'scale_evidence':{'schema_version':1,'method':'verified-per-view-isotropic-v1',
                            'recipe_path':'recipe.json','recipe_sha256':recipe_hash,
                            'object_id':'object','view':'front','source_path':'source.png',
                            'source_sha256':sha('source.png'),'atlas_path':'atlas.png',
                            'atlas_sha256':sha('atlas.png'),'active_output_sha256':sha('output.png'),
                            'active_output_rgba_sha256':digest(output),'crop_bounds_xyxy':[0,0,4,4],
                            'resized_dimensions_px':[2,2],'scale':0.5,'projection_scale':1,
                            'verification_basis':'producer-recorded-output'}}}}
            basis=per_view_normalization_basis(root,asset,asset['provenance'],
                asset['provenance']['normalization'],'object/front',{})
            self.assertEqual(basis,('verified-per-view-scale',recipe_hash,'object','front'))
            evidence=asset['provenance']['normalization']['scale_evidence']
            recipe['records'][0]['replay_status']='not-replayed'
            (root/'recipe.json').write_text(json.dumps(recipe));recipe_hash=sha('recipe.json')
            evidence['recipe_sha256']=recipe_hash
            evidence['method']='reviewed-current-output-isotropic-v1'
            evidence['replay_status']='not-replayed'
            evidence['verification_basis']='reviewed-current-output'
            review={'object_id':'object','view':'front','status':'approved'}
            (root/'review.json').write_text(json.dumps(review));review_hash=sha('review.json')
            evidence['review_record_path']='review.json';evidence['review_record_sha256']=review_hash
            recipe['records'][0].update({'verification_basis':'reviewed-current-output',
                'replay_status':'not-replayed','review_record_path':'review.json',
                'review_record_sha256':review_hash})
            (root/'recipe.json').write_text(json.dumps(recipe));recipe_hash=sha('recipe.json')
            evidence['recipe_sha256']=recipe_hash
            self.assertEqual(per_view_normalization_basis(root,asset,asset['provenance'],
                asset['provenance']['normalization'],'object/front',{}),
                ('verified-per-view-scale',recipe_hash,'object','front'))
            evidence['replay_status']='replayed'
            with self.assertRaisesRegex(ValueError,'Unclear non-replayed scale evidence status'):
                per_view_normalization_basis(root,asset,asset['provenance'],
                    asset['provenance']['normalization'],'object/front',{})
            evidence['method']='verified-per-view-isotropic-v1';evidence.pop('replay_status')
            evidence['verification_basis']='producer-recorded-output';evidence.pop('review_record_path');evidence.pop('review_record_sha256')
            recipe['records'][0].update({'verification_basis':'producer-recorded-output',
                'replay_status':'exact-output-hash-match'})
            recipe['records'][0].pop('review_record_path');recipe['records'][0].pop('review_record_sha256')
            (root/'recipe.json').write_text(json.dumps(recipe));recipe_hash=sha('recipe.json')
            evidence['recipe_sha256']=recipe_hash
            asset['provenance']['normalization']['scale']=0.51
            with self.assertRaisesRegex(ValueError,'scale is not bound by the recipe'):
                per_view_normalization_basis(root,asset,asset['provenance'],
                    asset['provenance']['normalization'],'object/front',{})

    def test_reviewed_affine_projection_requires_hash_bound_recipe_and_review(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=Image.new('RGBA',(10,10),(1,2,3,255));source.save(root/'source.png')
            atlas=Image.new('RGBA',(10,10),(4,5,6,255));atlas.save(root/'atlas.png')
            output=Image.new('RGBA',(8,6),(7,8,9,255));output.save(root/'output.png')
            review={'status':'approved'};(root/'review.json').write_text(json.dumps(review))
            sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
            evidence={'schema_version':1,'method':'reviewed-axis-affine-v1',
                'object_id':'fixture','view':'front','recipe_path':'recipe.json','recipe_sha256':'',
                'source_path':'source.png','source_sha256':sha('source.png'),
                'atlas_path':'atlas.png','atlas_sha256':sha('atlas.png'),
                'active_output_sha256':sha('output.png'),'active_output_rgba_sha256':digest(output),
                'crop_bounds_xyxy':[0,0,10,10],'resized_dimensions_px':[8,6],
                'scale_x':0.8,'scale_y':0.6,'target_dimensions_px':[8,6],
                'review_record_path':'review.json','review_record_sha256':sha('review.json'),
                'review_status':'approved'}
            recipe={'records':[dict({k:v for k,v in evidence.items()
                if k not in {'recipe_path','recipe_sha256'} })]}
            (root/'recipe.json').write_text(json.dumps(recipe));evidence['recipe_sha256']=sha('recipe.json')
            asset={'id':'fixture.front','object_id':'fixture','view':'front',
                'image':{'path':'output.png','sha256':sha('output.png')},'provenance':{
                    'source_image':'source.png','source_sha256':sha('source.png'),
                    'source_atlas':'atlas.png','source_atlas_sha256':sha('atlas.png'),
                    'source_cell_calibration':[0.8,0.6],
                    'crop_bounds_px':{'alpha_bounds_global':[0,0,10,10],
                        'resized_bounds_px':[8,6]},
                    'normalization':{'resized_dimensions_px':[8,6],
                        'calibration_evidence':evidence}}}
            basis=affine_calibration_basis(root,asset,asset['provenance'],
                asset['provenance']['normalization'],'fixture/front',{})
            self.assertEqual(basis,('reviewed-axis-affine',evidence['recipe_sha256'],'fixture','front'))
            asset['provenance']['normalization']['calibration_evidence']['scale_y']=0.7
            with self.assertRaisesRegex(ValueError,'disagrees with source cell calibration'):
                affine_calibration_basis(root,asset,asset['provenance'],
                    asset['provenance']['normalization'],'fixture/front',{})

    def test_retained_snapshot_is_exact_and_separate_from_output(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            output=Image.new('RGBA',(4,4),(9,8,7,255));output.save(root/'output.png')
            output_hash=hashlib.sha256((root/'output.png').read_bytes()).hexdigest()
            rgba=digest(output)
            output.save(root/'retained.png')
            record={'object_id':'fixture','view':'top','snapshot_path':'retained.png',
                'snapshot_sha256':output_hash,'snapshot_rgba_sha256':rgba,
                'active_output_path':'output.png','active_output_sha256':output_hash,
                'active_output_rgba_sha256':rgba,'dimensions_px':[4,4],
                'claim':'Exact retained approved output.','existing_explanation':'Historical transform is unrecoverable.'}
            (root/'manifest.json').write_text(json.dumps({'records':[record]}))
            manifest_sha=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
            asset={'id':'fixture.top','object_id':'fixture','view':'top',
                'image':{'path':'output.png','sha256':output_hash}}
            normalization={'retained_snapshot_evidence':{'schema_version':1,
                'method':'verified-retained-snapshot-v1','manifest_path':'manifest.json',
                'manifest_sha256':manifest_sha,'object_id':'fixture','view':'top'}}
            basis=retained_snapshot_basis(root,asset,normalization,'fixture/top',{})
            self.assertEqual(basis,('verified-retained-snapshot',manifest_sha,'fixture','top'))
            record['snapshot_path']='output.png'
            (root/'manifest.json').write_text(json.dumps({'records':[record]}))
            normalization['retained_snapshot_evidence']['manifest_sha256']=hashlib.sha256(
                (root/'manifest.json').read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'must be distinct'):
                retained_snapshot_basis(root,asset,normalization,'fixture/top',{})

    def test_execution_report_requires_matching_atlas_crop_and_dual_output_hashes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            atlas=Image.new('RGBA',(8,8),(1,2,3,255));atlas.save(root/'atlas.png')
            output=Image.new('RGBA',(2,1),(8,9,10,255));output.save(root/'output.png')
            sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
            rgba=digest(output)
            resolution={'processed':1,'expected':1,'count':1,'failures':[],
                'resolutions':[{'id':'fixture.front','view':'front','source_atlas':'atlas.png',
                    'source_atlas_sha256':sha('atlas.png'),'decoded_bounds_xyxy':[1,2,5,4]}]}
            output_receipt={'outputs':[{'id':'fixture.front','sha256':sha('output.png'),
                'rgba_sha256':rgba}]}
            (root/'resolution.json').write_text(json.dumps(resolution))
            (root/'outputs.json').write_text(json.dumps(output_receipt))
            asset={'id':'fixture.front','object_id':'fixture','view':'front'}
            evidence={'execution_report_path':'resolution.json',
                'execution_report_sha256':sha('resolution.json'),
                'output_report_path':'outputs.json','output_report_sha256':sha('outputs.json'),
                'atlas_path':'atlas.png','atlas_sha256':sha('atlas.png'),
                'crop_bounds_xyxy':[1,2,5,4],'active_output_sha256':sha('output.png'),
                'active_output_rgba_sha256':rgba}
            _check_executed_replay_binding(root,evidence,asset,{},'fixture/front')
            evidence['active_output_rgba_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'output hash mismatch'):
                _check_executed_replay_binding(root,evidence,asset,{},'fixture/front')

    def test_per_view_quarter_turn_swaps_only_scaled_axis_dimensions(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=Image.new('RGBA',(4,2),(1,2,3,255));source.save(root/'source.png')
            atlas=Image.new('RGBA',(4,2),(4,5,6,255));atlas.save(root/'atlas.png')
            output=Image.new('RGBA',(1,2),(7,8,9,255));output.save(root/'output.png')
            (root/'producer.json').write_text('{"producer":"test"}')
            sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
            row={'object_id':'fixture','view':'front','scale':0.5,'projection_scale':1,
                'source_path':'source.png','source_sha256':sha('source.png'),
                'atlas_path':'atlas.png','atlas_sha256':sha('atlas.png'),
                'active_output_sha256':sha('output.png'),'active_output_rgba_sha256':digest(output),
                'crop_bounds_xyxy':[0,0,4,2],'resized_dimensions_px':[1,2],
                'verification_basis':'producer-recorded-output','original_recipe_path':'producer.json',
                'original_recipe_sha256':sha('producer.json'),'original_recipe_output_sha256':sha('output.png'),
                'original_recipe_output_match':True,'orientation_correction_degrees':90}
            (root/'proof.json').write_text(json.dumps({'records':[row]}));proof_hash=sha('proof.json')
            ev={k:row[k] for k in ('object_id','view','source_path','source_sha256','atlas_path',
                'atlas_sha256','active_output_sha256','active_output_rgba_sha256','crop_bounds_xyxy',
                'resized_dimensions_px','scale','projection_scale','verification_basis',
                'orientation_correction_degrees')}
            ev.update({'schema_version':1,'method':'verified-per-view-isotropic-v1',
                'recipe_path':'proof.json','recipe_sha256':proof_hash})
            asset={'id':'fixture.front','object_id':'fixture','view':'front',
                'image':{'path':'output.png','sha256':sha('output.png')},'provenance':{
                    'source_image':'source.png','source_sha256':sha('source.png'),
                    'generated_atlas':'atlas.png','generated_atlas_sha256':sha('atlas.png'),
                    'crop_bounds_px':{'alpha_bounds_global':[0,0,4,2],
                        'resized_bounds_px':[1,2],'orientation_correction_degrees':90},
                    'normalization':{'scale':0.5,'scale_policy':'per-view-uniform',
                        'scale_evidence':ev}}}
            self.assertEqual(per_view_normalization_basis(root,asset,asset['provenance'],
                asset['provenance']['normalization'],'fixture/front',{}),
                ('verified-per-view-scale',proof_hash,'fixture','front'))

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
