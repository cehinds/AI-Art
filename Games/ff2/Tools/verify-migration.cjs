'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const record = JSON.parse(fs.readFileSync(path.join(root, 'Docs/FF2ArtMigration.json'), 'utf8'));
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
const sourceIndex = process.argv.indexOf('--source');
const source = sourceIndex < 0 ? null : process.argv[sourceIndex + 1];
if (sourceIndex >= 0 && !source) throw Error('--source needs a repository path');
const gitTree = process.argv.includes('--git') ? new Map(
  execFileSync('git', ['ls-tree', '-r', '-z', 'HEAD'], { cwd: root, maxBuffer: 16 * 1024 * 1024 })
    .toString().split('\0').filter(Boolean).map(line => {
      const tab = line.indexOf('\t');
      return [line.slice(tab + 1), line.slice(0, tab).split(' ')[2]];
    })
) : null;
const expected = new Set();
for (const item of record.files) {
  if (expected.has(item.path)) throw Error('Duplicate migration path: ' + item.path);
  expected.add(item.path);
  const bytes = fs.readFileSync(path.join(root, item.path));
  if (bytes.length !== item.bytes || digest(bytes) !== item.sha256) throw Error('Destination mismatch: ' + item.path);
  if (source && digest(fs.readFileSync(path.join(source, item.path))) !== item.sha256) throw Error('Source changed: ' + item.path);
  if (gitTree) {
    const blob = crypto.createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
    if (gitTree.get(item.path) !== blob) throw Error('Committed bytes mismatch: ' + item.path);
  }
}
function walk(folder) {
  return fs.readdirSync(folder, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(folder, entry.name);
    return entry.isDirectory() ? walk(file) : [file];
  });
}
for (const base of [root, ...(source ? [source] : [])]) {
  for (const relative of record.movedRoots) {
    const actual = walk(path.join(base, relative));
    for (const file of actual) {
      const name = path.relative(base, file).split(path.sep).join('/');
      if (!expected.has(name)) throw Error('Unrecorded art file: ' + name);
    }
    const count = record.files.filter(item => item.path.startsWith(relative + '/')).length;
    if (actual.length !== count) throw Error('Art directory file count mismatch: ' + relative);
  }
}
console.log(`PASS: ${record.files.length} migration files match SHA-256${source ? ', source bytes and directory counts' : ''}${gitTree ? ', and committed Git blobs' : ''}.`);
