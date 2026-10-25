#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),{check}=require('./core.cjs');
const file=path.resolve(__dirname,'../../Assets/Art/Production/procedural-tiles.json');
const [first,direction,second]=process.argv.slice(2),catalog=JSON.parse(fs.readFileSync(file)),a=catalog.tiles.find(a=>a.id===first),b=catalog.tiles.find(a=>a.id===second);
if(!a||!b){console.error('Usage: node Tools/procedural-tiles/check.cjs <tile-id> <north|east|south|west> <neighbor-id>');process.exitCode=2}else{const result=check(a,direction,b,catalog.policy);console.log(JSON.stringify(result,null,2));if(!result.match)process.exitCode=1}
