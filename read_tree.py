from DwnKramerius import Periodical, load_periodical
import csv

frenstat = load_periodical(
    'kramerius_dwn_data/frenstat_object_0728114733.json')


with open('read_marc/marc_data/frenstat_marc.csv') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        loc = row["location"].split(';')
        print(loc)
