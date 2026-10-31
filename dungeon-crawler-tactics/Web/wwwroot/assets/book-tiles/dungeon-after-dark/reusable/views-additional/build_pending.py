"""Extract every retained atlas not yet reflected in set-index.json."""
import json, os
from pathlib import Path
from build_batch import process_batch
OUT=Path(__file__).resolve().parent
specs=json.loads((OUT/'batch-specs.json').read_text())
state_path=OUT/'run-state.json'
state=json.loads(state_path.read_text())
completed=set(state.get('completed_batch_ids',[]))
for spec in specs:
    if spec['batch_id'] in completed or not (OUT/spec['raw']).exists():
        continue
    process_batch(spec)
    completed.add(spec['batch_id'])
    state.update({'completed_batch_ids':sorted(completed),'completed_batches':len(completed),'completed_objects':sum(len(s['objects']) for s in specs if s['batch_id'] in completed),'pending_geometry_review_count':sum(len(x['objects']) for x in specs if x['batch_id'] in completed)-state.get('geometry_approved_count',0),'pending_batches':[s['batch_id'] for s in specs if s['batch_id'] not in completed],'status':'in progress'})
    tmp=state_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,state_path)
