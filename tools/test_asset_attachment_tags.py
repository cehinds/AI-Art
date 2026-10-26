"""Semantic attachment regressions: grounded surface distinctions and safe metadata."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from PIL import Image
import asset_attachment_tags as rules


class AttachmentRulesTests(unittest.TestCase):
    def test_generation_recipe_hashes_survive_asset_tagging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'assets';pack=root/'book-tiles/pocket-dungeon'
            workspace=pack/'reusable/views-additional'
            raw=workspace/'raw/candidates';raw.mkdir(parents=True)
            leaf={'id':'stone-floor.front','object_id':'stone-floor','view':'front',
                  'kind':'tile','category':'ground','tags':[],
                  'image':{'path':'reusable/views-additional/images/stone-floor.front.png'},
                  'metadata_path':'reusable/views-additional/images/stone-floor.front.json'}
            index={'assets':[leaf]}
            (pack/'reusable/index.json').write_text(json.dumps(index))
            (workspace/'set-index.json').write_text(json.dumps(index))
            (root/'reusable-library.json').write_text(json.dumps({'libraries':[{
                'id':'pocket-books','base':'book-tiles/pocket-dungeon',
                'index':'book-tiles/pocket-dungeon/reusable/index.json'}]}))
            recipe=b'{"source": "raw.png", "crop": [1, 2, 3, 4]}\n'
            digest=hashlib.sha256(recipe).hexdigest()
            evidence={raw/'normalization-recipe.json':recipe,
                      raw/'candidate-index.json':json.dumps({'recipe_sha256':digest}).encode(),
                      workspace/'replay-baseline.json':b'{"snapshot_sha256":"frozen"}\n'}
            for path,data in evidence.items():path.write_bytes(data)
            result=rules.apply(root)
            self.assertEqual(result['preserved_generation_documents'],3)
            for path,data in evidence.items():self.assertEqual(path.read_bytes(),data)
            self.assertEqual(hashlib.sha256((raw/'normalization-recipe.json').read_bytes()).hexdigest(),
                             json.loads((raw/'candidate-index.json').read_text())['recipe_sha256'])
            for path in (pack/leaf['metadata_path'],workspace/'set-index.json'):
                data=json.loads(path.read_text());asset=data['assets'][0] if 'assets' in data else data
                self.assertIn('surface:floor',asset['tags'])
                self.assertIn('attachment',asset)
            self.assertEqual(rules.apply(root,check=True)['changed'],0)

    def asset(self, ident, **extra):
        value={'id':ident,'kind':'sprite','category':'prop','tags':[],**extra}
        index={'assets':[value]};rules.enrich_library(Path('/fixture/assets/style-packs/pocket-dungeon'),index)
        return value

    def test_surface_and_object_classification(self):
        cases=[
            ('studio-stage-panel-floor',{'kind':'tile','category':'ground'},'world','provider',[],['surface:floor']),
            ('circuit-control-panel',{'views':{'applicable':True}},'world','object',['surface:floor'],[]),
            ('inventory-panel',{'kind':'ui','category':'ui'},'screen','screen',[],['surface:screen']),
            ('wall-torch',{},'world','object',['surface:wall'],[]),
            ('standing-torch',{},'world','object',['surface:floor'],[]),
            ('ceiling-lamp',{},'world','object',['surface:ceiling'],[]),
            ('door',{},'world','object',['surface:doorway'],[]),
            ('doorway-frame',{'category':'terrain'},'world','provider',['surface:floor'],['surface:doorway']),
            ('wooden-chest',{},'world','object',['surface:floor'],[]),
        ]
        for ident,extra,space,role,any_,provides in cases:
            with self.subTest(ident=ident):
                obj=self.asset(ident,**extra);a=obj['attachment'];self.assertEqual((a['space'],a['role'],a['requires']['any'],a['provides']),(space,role,any_,provides))
        self.assertIn('material:wood',self.asset('wooden-chest')['tags'])
        self.assertIn('attachment:wall',self.asset('wall-torch')['tags'])

    def test_boat_matches_water_never_lava(self):
        boat=self.asset('wooden-boat');water=self.asset('water-floor',kind='tile',category='ground');lava=self.asset('lava-floor',kind='tile',category='ground')
        self.assertTrue(rules.matches(water['tags'],boat['attachment']['requires']))
        self.assertFalse(rules.matches(lava['tags'],boat['attachment']['requires']))
        self.assertEqual(lava['attachment']['provides'],['surface:lava'])

    def test_authored_wall_mount_takes_precedence_over_hanging_name(self):
        tool=self.asset('house-crafting-hanging-implement',tags=['wall-mounted'])
        self.assertEqual(tool['attachment']['requires']['any'],['surface:wall'])
        self.assertNotIn('attachment:ceiling',tool['tags'])
        self.assertEqual(tool['attachment']['role'],'object')
        self.assertEqual(tool['attachment']['provides'],[])
        lantern=self.asset('hanging-lantern')
        self.assertEqual(lantern['attachment']['requires']['any'],['surface:ceiling'])

    def test_wall_fixtures_never_advertise_structural_wall(self):
        for name in ('Framed wall picture','Gold wall curtain rod','Hanging metal tool'):
            with self.subTest(name=name):
                obj=self.asset('fixture',name=name,tags=['wall-mounted'])
                self.assertEqual(obj['attachment']['requires']['any'],['surface:wall'])
                self.assertEqual(obj['attachment']['provides'],[])
        wall=self.asset('wall-shell',category='wall')
        self.assertEqual(wall['attachment']['provides'],['surface:wall'])

    def test_support_furniture_noun_not_location_or_modifier(self):
        for name in ('Desk candle','Tabletop monitor','Book on desk','Single tabletop candlestick',
                     'Jar on workbench','Gold vessel beside table','Desk candle and books'):
            with self.subTest(name=name):
                obj=self.asset('small-prop',name=name,tags=['tabletop'])
                self.assertEqual(obj['attachment']['role'],'object')
                self.assertEqual(obj['attachment']['provides'],[])
                self.assertEqual(obj['attachment']['requires']['any'],['surface:tabletop'])
        for name in ('Table with books','Wooden workbench','Small side table Front','Desk with monitor',
                     'Guide desk and chairs'):
            with self.subTest(name=name):
                obj=self.asset('furniture',name=name)
                self.assertEqual(obj['attachment']['provides'],['surface:tabletop'])
                self.assertEqual(obj['attachment']['requires']['any'],['surface:floor'])

    def reviewed_table_proxy(self,pack,approved=True):
        from view_review_contract import file_evidence,canonical_primary,statistics,reference,encoded,VIEWS
        (pack/'reusable').mkdir(parents=True)
        assets=[]
        for view in ('source',*VIEWS):
            ident='scene-table' if view=='source' else 'scene-table.'+view
            filename=ident+'.png';Image.new('RGBA',(3,3),(40,50,60,255)).save(pack/filename)
            image={**file_evidence(pack,filename),'width':3,'height':3}
            assets.append({'id':ident,'object_id':'scene-table','name':'Wooden table',
                'kind':'reconstruction_patch' if view=='source' else 'sprite','category':'prop',
                'view':view,'reusable':view!='source','tags':[],
                'views':{'applicable':True,'complete':approved},'image':image,
                'provenance':{'source_image':'scene-table.png'}})
        group={'object_id':'scene-table','complete':approved,
               'views':{v:'scene-table.'+v for v in VIEWS}}
        index={'assets':assets,'view_sets':[group]};rules.enrich_library(pack,index)
        source=file_evidence(pack,'scene-table.png')
        record={'object_id':'scene-table','complete':approved,'status':'passed' if approved else 'needs-correction',
            'source':source,'primary_source':canonical_primary(pack,'scene-table',{a['id']:a for a in assets},group),
            'views':{v:{'asset_id':'scene-table.'+v,**file_evidence(pack,'scene-table.'+v+'.png')} for v in VIEWS},
            'review':{'reviewer':'page_inventory','status':'pass','reviewed_at':'2026-10-26T00:00:00+00:00',
                      'source_evidence':{'method':'direct-reviewed-source','reviewed_reference':source}}}
        report={'schema_version':1,'path_base':'library-root','scope':'reusable-gameplay',
                'sets':[record],'statistics':statistics([record])}
        (pack/'reusable/view-review.json').write_bytes(encoded(report));index['view_review']=reference(report)
        return index

    def test_proxy_provider_requires_current_independent_source_and_six_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack=Path(tmp)/'assets/reusable-gameplay';index=self.reviewed_table_proxy(pack)
            library=({'id':'gameplay'},pack,pack/'reusable/index.json',index)
            central=rules.central_rules([library]);self.assertEqual(len(central['tiles']),1)
            tile=central['tiles'][0]
            self.assertEqual((tile['id'],tile['asset_id'],tile['canonical_asset_id']),
                             ('gameplay::scene-table','scene-table.front','scene-table'))
            self.assertNotIn('reconstruction',tile['tags'])
            # Canonical ID lets source and all six views exclude only themselves.
            self.assertEqual(tile['id'],'gameplay::'+index['assets'][1]['object_id'])
            unreviewed=copy.deepcopy(index);unreviewed.pop('view_review')
            self.assertEqual(rules.central_rules([({**library[0]},pack,library[2],unreviewed)])['tiles'],[])
            Image.new('RGBA',(3,3),(1,2,3,255)).save(pack/'scene-table.right.png')
            with self.assertRaisesRegex(ValueError,'Stale view-review file hash'):
                rules.central_rules([library])

    def test_unapproved_or_orphan_proxy_never_becomes_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack=Path(tmp)/'assets/reusable-gameplay';index=self.reviewed_table_proxy(pack,False)
            self.assertEqual(rules.central_rules([({'id':'gameplay'},pack,pack/'index.json',index)])['tiles'],[])
            other=Path(tmp)/'other/assets/reusable-gameplay';index=self.reviewed_table_proxy(other)
            index['view_sets'][0]['views']['front']='scene-table.rear'
            with self.assertRaisesRegex(ValueError,'View-review leaf differs'):
                rules.central_rules([({'id':'gameplay'},other,other/'index.json',index)])

    def test_location_names_do_not_turn_solid_supports_into_water(self):
        crate=self.asset('crate')
        for name in ('Palace paving floor','Wet palace paving floor','Riverbank stone floor',
                     'River palace stone floor','River bridge floor'):
            with self.subTest(name=name):
                floor=self.asset('hunting-river-'+name.lower().replace(' ','-'),
                                 name=name,kind='tile',category='ground',tags=['hunting-river'])
                self.assertEqual(floor['attachment']['provides'],['surface:floor'])
                self.assertNotIn('hazard:water',floor['tags'])
                self.assertTrue(rules.matches(floor['tags'],crate['attachment']['requires']))
        water=self.asset('hunting-river-river-water-floor',name='River water floor',kind='tile',category='ground')
        self.assertEqual(water['attachment']['provides'],['surface:water'])
        self.assertFalse(rules.matches(water['tags'],crate['attachment']['requires']))
        wall=self.asset('hunting-river-river-palace-wall',name='River palace wall',category='wall')
        self.assertNotIn('hazard:water',wall['tags'])
        self.assertNotIn('hazard:water',self.asset('water-bottle')['tags'])
        self.assertNotIn('hazard:pit',self.asset('pit-boss',category='actor')['tags'])

    def test_source_map_reference_does_not_require_a_world_support_tile(self):
        doc = {'maps': [{'id': 'atlas-safe-room', 'kind': 'atlas',
                         'file': 'reusable/maps/atlas-safe-room.json',
                         'source': 'reusable/sources/safe-room.png'}]}
        rules.enrich_document(doc, 'gameplay')
        ref = doc['maps'][0]
        self.assertEqual(ref['attachment']['space'], 'reconstruction')
        self.assertFalse(any(ref['attachment']['requires'].values()))
        self.assertNotIn('attachment:floor', ref['tags'])
        before = copy.deepcopy(doc)
        rules.enrich_document(doc, 'gameplay')
        self.assertEqual(doc, before)

    def test_portable_items_and_actors_use_appropriate_additional_supports(self):
        table=self.asset('wooden-table');stairs=self.asset('stone-stairs',kind='tile',category='stairs',procedural={'walkable':True})
        potion=self.asset('healing-potion',category='consumable');actor=self.asset('hero',category='actor');bed=self.asset('wooden-bed')
        self.assertTrue(rules.matches(table['tags'],potion['attachment']['requires']))
        self.assertTrue(rules.matches(stairs['tags'],actor['attachment']['requires']))
        self.assertFalse(rules.matches(stairs['tags'],bed['attachment']['requires']))
        self.assertFalse(rules.matches(table['tags'],bed['attachment']['requires']))
        blocked=self.asset('stone-stairs',kind='tile',category='stairs',procedural={'walkable':False})
        self.assertFalse(rules.matches(blocked['tags'],actor['attachment']['requires']))
        self.assertEqual(self.asset('weapon-rack',category='equipment')['attachment']['requires']['any'],['surface:floor'])

    def test_floor_threshold_frame_and_loose_door_have_distinct_support_roles(self):
        floor=self.asset('stone-floor',kind='tile',category='ground')
        frame=self.asset('stone-doorway-frame',category='door');door=self.asset('wooden-door',category='door')
        threshold=self.asset('doorway-threshold-floor',kind='tile',category='ground')
        self.assertTrue(rules.matches(floor['tags'],frame['attachment']['requires']))
        self.assertTrue(rules.matches(frame['tags'],door['attachment']['requires']))
        self.assertFalse(any(threshold['attachment']['requires'].values()))

    def test_matcher_any_all_none(self):
        match={'any':['surface:floor','surface:wall'],'all':['material:stone'],'none':['hazard:lava']}
        self.assertTrue(rules.matches(['surface:floor','material:stone'],match))
        for tags in [['surface:floor'],['material:stone'],['surface:floor','material:stone','hazard:lava']]:self.assertFalse(rules.matches(tags,match))

    def test_floor_exclusions_preserve_wall_mount_support(self):
        crate=self.asset('wooden-crate');torch=self.asset('wall-torch')
        for ident,extra in [('void-floor',{}),('pit-floor',{}),('chasm-floor',{}),('stone-floor',{'procedural':{'walkable':False}})]:
            tile=self.asset(ident,kind='tile',category='ground',**extra)
            self.assertFalse(rules.matches(tile['tags'],crate['attachment']['requires']))
        wall=self.asset('stone-wall',kind='tile',category='wall',procedural={'walkable':False})
        self.assertTrue(rules.matches(wall['tags'],torch['attachment']['requires']))
        self.assertFalse(wall['procedural']['walkable'])

    def test_legacy_archive_refresh_changes_only_json_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'assets';pack=root/'style-packs/test';folder=pack/'collections/a';folder.mkdir(parents=True)
            metadata=b'{"tags":["new"]}';(folder/'manifest.json').write_bytes(metadata)
            path=folder/'a.zip'
            with ZipFile(path,'w') as z:z.writestr('collections/a/manifest.json',b'{}');z.writestr('components/original.png',b'original-png-bytes')
            self.assertEqual(rules.refresh_legacy_archives(root)['json_members'],1)
            with ZipFile(path) as z:self.assertEqual(z.read('collections/a/manifest.json'),metadata);self.assertEqual(z.read('components/original.png'),b'original-png-bytes')
            self.assertEqual(rules.refresh_legacy_archives(root,check=True)['archives'],0)

    def test_parent_view_inherits_without_conflicting_generated_role(self):
        index={'assets':[{'id':'stone-floor','kind':'tile','category':'ground','view':'source','object_id':'stone-floor','tags':[]},{'id':'stone-floor.front','kind':'sprite','category':'prop','view':'front','object_id':'stone-floor','tags':[]}]}
        rules.enrich_library(Path('/fixture/assets/style-packs/pocket-dungeon'),index);child=index['assets'][1]
        self.assertIn('role:provider',child['tags']);self.assertNotIn('role:object',child['tags']);self.assertEqual(child['attachment']['inherited_from'],'stone-floor')
        first=copy.deepcopy(index);rules.enrich_library(Path('/fixture/assets/style-packs/pocket-dungeon'),index);self.assertEqual(first,index)

    def test_preserves_authoritative_namespaced_tags_and_gameplay_fields(self):
        obj=self.asset('chest',tags=['material:obsidian','environment:authored'],procedural={'eligible':False,'walkable':False},footprint_tiles=[2,3])
        self.assertIn('material:obsidian',obj['tags']);self.assertIn('environment:authored',obj['tags']);self.assertEqual(obj['footprint_tiles'],[2,3]);self.assertEqual(obj['procedural'],{'eligible':False,'walkable':False})

    def test_patch_never_becomes_provider(self):
        obj=self.asset('wall-floor-patch',kind='reconstruction_patch',reusable=False)
        self.assertEqual(obj['attachment']['space'],'reconstruction');self.assertIsNone(obj['attachment']['compatibility_group']);self.assertEqual(obj['attachment']['provides'],[])

    def test_clean_proxy_does_not_inherit_baked_patch_placement_exclusion(self):
        index={'assets':[{'id':'scene-chest','name':'Wooden chest','kind':'reconstruction_patch','category':'reconstruction','reusable':False,'view':'source','tags':[]}, {'id':'scene-chest.front','kind':'sprite','category':'prop','reusable':True,'object_id':'scene-chest','view':'front','tags':[]}]}
        pack=Path('/fixture/assets/style-packs/pocket-dungeon');rules.enrich_library(pack,index)
        self.assertEqual(index['assets'][0]['attachment']['space'],'reconstruction');proxy=index['assets'][1]
        self.assertEqual(proxy['attachment']['space'],'world');self.assertIn('attachment:floor',proxy['tags']);self.assertEqual(proxy['attachment']['inferred_proxy_for'],'scene-chest')
        first=copy.deepcopy(index);rules.enrich_library(pack,index);self.assertEqual(first,index)

    def test_copied_source_tags_do_not_mark_clean_views_as_reconstruction(self):
        pack=Path('/fixture/assets/reusable-gameplay')
        parent={'id':'house-bed','name':'Wooden bed','kind':'reconstruction_patch',
                'category':'prop','reusable':False,'view':'source','tags':['bedroom']}
        index={'assets':[parent]};rules.enrich_library(pack,index)
        # Actual generators copy tags, but do not copy attachment_generated_tags.
        child={'id':'house-bed.front','kind':'sprite','category':'prop',
               'reusable':True,'object_id':'house-bed','view':'front',
               'tags':parent['tags']+['inferred-view','material:obsidian']}
        index['assets'].append(child);rules.enrich_library(pack,index)
        self.assertEqual(child['attachment']['space'],'world')
        self.assertEqual(child['attachment']['requires']['any'],['surface:floor'])
        self.assertEqual([t for t in child['tags'] if t.startswith('role:')],['role:object'])
        self.assertIn('bedroom',child['tags']);self.assertIn('material:obsidian',child['tags'])
        self.assertEqual(parent['attachment']['space'],'reconstruction')
        first=copy.deepcopy(index);rules.enrich_library(pack,index);self.assertEqual(first,index)

    def test_central_references_self_exclusion_missing_reason_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'assets';pack=root/'style-packs/pocket-dungeon';(pack/'reusable').mkdir(parents=True)
            assets=[self.asset('floor',kind='tile',category='ground'),self.asset('chandelier'),self.asset('self-support',tags=['surface:floor']),self.asset('other-support',tags=['surface:floor'])]
            for a in assets:a['metadata_path']='reusable/'+a['id']+'.json';a['view']='source'
            # A multi-surface authored provider cannot target itself.
            assets[2]['kind']='tile';assets[2]['category']='wall'
            assets[3]['kind']='tile';assets[3]['category']='wall'
            (pack/'reusable/index.json').write_text(json.dumps({'assets':assets}));(root/'reusable-library.json').write_text(json.dumps({'schema_version':1,'libraries':[{'id':'pocket','base':'style-packs/pocket-dungeon','index':'style-packs/pocket-dungeon/reusable/index.json'}]}))
            rules.apply(root);self.assertEqual(rules.apply(root,check=True)['changed'],0)
            doc=json.loads((root/'attachment-rules.json').read_text());tiles={t['id'] for t in doc['tiles']}
            for group in doc['groups']:
                self.assertTrue(set(group['tile_ids'])<=tiles)
                if not group['tile_ids']:self.assertIn('No registered provider',group['reason'])
            enriched=json.loads((pack/'reusable/index.json').read_text())['assets']
            queried=enriched[2];group=next(g for g in doc['groups'] if g['id']==queried['attachment']['compatibility_group'])
            self.assertTrue(queried['attachment']['exclude_self'])
            self.assertEqual(queried['attachment']['compatibility_group'],enriched[3]['attachment']['compatibility_group'])
            # The shared JSON includes all candidates; a query removes ONLY
            # its canonical identity, retaining other compatible providers.
            candidates=set(group['tile_ids'])-{'pocket::'+queried['id']}
            self.assertNotIn('pocket::self-support',candidates)
            self.assertIn('pocket::other-support',candidates)
            self.assertIn('pocket::floor',candidates)
            self.assertIn('queried asset',doc['semantics']['exclude_self'])

    def test_cross_style_support_is_available_with_visual_preference(self):
        libraries=[]
        for style,ident,asset in [('pocket-dungeon','pocket',self.asset('crate')),('ink-and-lanterns','ink',self.asset('stone-floor',kind='tile',category='ground'))]:
            pack=Path('/fixture/assets/style-packs')/style;index={'assets':[asset]};rules.enrich_library(pack,index);libraries.append(({'id':ident},pack,pack/'reusable/index.json',index))
        central=rules.central_rules(libraries);group=next(g for g in central['groups'] if g['style']=='pocket-dungeon')
        self.assertIn('ink::stone-floor',group['tile_ids']);self.assertEqual(group['preferred_tile_ids'],[])

    def test_anonymous_atlas_frames_tagged_without_geometry_or_id_changes(self):
        rectangle={'x':2,'y':3,'width':30,'height':60}
        document={'characters':{'frames':{'carl':{'idle':{'x':5,'y':8,'width':40,'height':70,
            'anchor':{'x':1,'y':2},'bounds':copy.deepcopy(rectangle),
            'provenance':{'frames':{'reference':copy.deepcopy(rectangle)}}}}}}}
        rules.enrich_document(document,'gameplay');frame=document['characters']['frames']['carl']['idle']
        self.assertIn('attachment:floor',frame['tags']);self.assertNotIn('id',frame);self.assertEqual([frame[k] for k in ('x','y','width','height')],[5,8,40,70]);self.assertEqual(frame['anchor'],{'x':1,'y':2})
        self.assertEqual(frame['bounds'],rectangle)
        self.assertEqual(frame['provenance'],{'frames':{'reference':rectangle}})
        first=copy.deepcopy(document);rules.enrich_document(document,'gameplay');self.assertEqual(first,document)

    def test_anonymous_file_records_are_tagged_without_touching_provenance(self):
        document={'sprites':{'hoarder':{'file':'hoarder.png','frameWidth':64,'frames':4,
            'anchor':{'x':32,'y':60},'provenance':{'file':'raw.png'}},
            'bench':{'file':'bench.png','frameWidth':128}},
            'icons':{'heart':{'file':'heart.png'}},'tiles':{'stone':{'file':'stone.png','role':'ground',
                'edges':{'north':['join.manual']}}},'source':{'sprites':{'reference':{'file':'reference.png'}}}}
        rules.enrich_document(document,'gameplay');sprite=document['sprites']['hoarder']
        self.assertIn('attachment:stairs',sprite['tags']);self.assertNotIn('id',sprite)
        self.assertEqual((sprite['frameWidth'],sprite['frames'],sprite['anchor']),(64,4,{'x':32,'y':60}))
        self.assertEqual(sprite['provenance'],{'file':'raw.png'})
        self.assertEqual(document['sprites']['bench']['attachment']['requires']['any'],['surface:floor'])
        self.assertEqual(document['source'],{'sprites':{'reference':{'file':'reference.png'}}})
        self.assertEqual(document['icons']['heart']['attachment']['space'],'screen')
        self.assertIn('surface:floor',document['tiles']['stone']['tags'])
        self.assertEqual(document['tiles']['stone']['edges'],{'north':['join.manual']})
        first=copy.deepcopy(document);rules.enrich_document(document,'gameplay');self.assertEqual(first,document)


if __name__=='__main__':unittest.main()
