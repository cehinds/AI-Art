'use strict';
module.exports=(markdown,report)=>{
 const families=report.campaign.groups.filter(g=>['effects','effect-family'].includes(g.group)),familyCount=families.reduce((n,g)=>n+g.owners,0),frameCount=families.reduce((n,g)=>n+g.pngs,0);
 const spells=`Spell visual families: **${report.spells.learnableCandidateFamilies} / ${report.spells.learnableExpected} learnable spells** and **${report.spells.specialMappedCandidateFamilies} / ${report.spells.specialExpected} Special/item/monster entries** are explicitly mapped to **${familyCount} exported families (${frameCount} frames)**. Mappings distinguish direct visual families, translation aliases (Scourge to poison, Break to stone), and shared visual families. Reuse is recorded in Tools/campaign-art/spell-effect-mapping.json and Review/campaign/coverage.json; it does not establish original animation, level variants, reverse effects or spell behavior. [Original spell catalog](https://guides.gamercorner.net/ffii/spells/).

`;
 const caveats=`## Known candidate limitations

[Independent contact-sheet visual QA](CampaignVisualQA.md) found subtle walking on robe/skirt/cape and rear-view NPC poses, inconsistent overhead versus side/three-quarter transport orientations, compressed thin equipment details, and subtle thunder/haste/drain changes. Native 24 × 32 party battle bodies vary in visible size because long weapons participate in each owner's shared scale. Registration and in-game readability need approval. The 16 status icons are optional modern readability candidates, not original FFII icon reproductions, and have no original-UI wiring approval.

The delivery includes 20 NPC owners with eight declared directional idle/step states each, four transports with four directions, eight equipment families with two poses, 16 prop states, 16 world markers, 16 item icons, and 16 status icons. Counts describe selected candidates rather than an audited original map/event inventory.

`;
 return markdown.replace('## Reproduce and review\n',spells+'## Reproduce and review\n').replace('ArtSource/Campaign/{party,world,enemies}/sheets.json','ArtSource/Campaign/**/sheets.json').replace('## Remaining approval and coverage work\n',caveats+'## Remaining approval and coverage work\n');
};
