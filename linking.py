from DwnKramerius import Periodical, load_periodical
from Parse773 import parse_location, normalize, remove_leading_zeros
import csv
import logging

logging.basicConfig(level=logging.INFO)

path_to_periodical = 'data/narodopis_revue_session.json'
path_to_marc = 'data/marc_data/narodopis_marc.csv'

perio = load_periodical(path_to_periodical)

count, fail = 0, 0
with open(path_to_marc) as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        count += 1
        loc = row["location"].split(';')
        for item in loc:
            path = normalize(*parse_location(item))
            l = perio.link(*path)
            print(f"https://vufind.ucl.cas.cz/Record/{row['id']}", item, l)
            if l is None:
                fail += 1
print(f'Success rate {1-fail/count:.1%}')
