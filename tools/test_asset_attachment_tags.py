"""Semantic attachment regressions: grounded surface distinctions and safe metadata."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import asset_attachment_tags as rules


class AttachmentRulesTests(unittest.TestCase):
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
        document={'characters':{'frames':{'carl':{'idle':{'x':5,'y':8,'width':40,'height':70,'anchor':{'x':1,'y':2}}}}}}
        rules.enrich_document(document,'gameplay');frame=document['characters']['frames']['carl']['idle']
        self.assertIn('attachment:floor',frame['tags']);self.assertNotIn('id',frame);self.assertEqual([frame[k] for k in ('x','y','width','height')],[5,8,40,70]);self.assertEqual(frame['anchor'],{'x':1,'y':2})
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
