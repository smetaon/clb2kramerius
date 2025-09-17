import json
from DwnKramerius import load_periodical
import os

tmp = 'data/debug/tmp.json'
dir = 'data/mzk_medium/'
lst = []
for root, dirs, files in os.walk(dir):
    for file in files:
        if file.endswith('.json'):
            lst.append(os.path.join(root, file))

for item in lst:

    with open(item) as f:
        perio = json.load(f)
    print(f'Processing {item}')

    perio['per_uuid'] = perio['uuid']
    del perio['uuid']
    perio['root_id'] = perio['root']
    del perio['root']
    perio['issn'] = 'todo'

    with open(tmp, 'w') as out:
        json.dump(perio, out, indent='\t', ensure_ascii=False)
    print('Dumped tmp')

    new_perio = load_periodical(tmp)
    new_perio.save(item)
    print(f'Saving to {item}')
    print('-'*15)
    os.remove(tmp)
