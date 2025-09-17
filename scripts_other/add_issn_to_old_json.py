import csv
from DwnKramerius import load_periodical
import logging

logging.basicConfig(level=logging.INFO)

path = 'data/mzk_medium/'
with open(path+'mzk_medium.csv') as f:
    reader = csv.DictReader(f, delimiter=';')

    for line in reader:
        per_uuid = line['uuid']
        issn = line['issn']
        json_path = path+per_uuid+'.json'
        print(f'Processing {json_path}')
        per = load_periodical(json_path)
        per.issn = issn
        per.save(json_path)
        print('-'*15)
