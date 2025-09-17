import csv
from ..DwnKramerius import Periodical, load_periodical

PATH_JSON = 'data/done/mzk/'
with open('data/ccnb_mzk_med.csv') as f:
    reader = csv.DictReader(f, delimiter=';')
    for line in reader:
        uuid = line['uuid']
        per = load_periodical(PATH_JSON+uuid+'.json')
        print(uuid, per.name)

        per.ccnb = line['ccnb'].strip()
        print(per.ccnb)
        # per.save(PATH_JSON+uuid+'.json')
        print('-'*15)
