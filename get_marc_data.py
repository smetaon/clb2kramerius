from pymarc import MARCReader
from pandas import DataFrame
"""
Save a periodical from marc to a smaller csv
"""

data = []
reader = MARCReader(open('/home/clb/data/ucla_all_v4.mrc', 'rb'))
my_per_title = 'Hlasy Muzea a archivu ve Frenštátě pod Radhoštěm'
i = 0
for record in reader:
    for field in record.get_fields('773'):  # type: ignore
        per_title = field.get_subfields('t')  # assuming only one title
        if len(per_title) > 0:
            per_title = per_title[0]
        location = field.get_subfields('q')  # can be a list
        if per_title == my_per_title:
            data.append([record.get('001').value(),  # type: ignore
                         per_title,
                         ';'.join(location)])
            i += 1
            print(i)

df = DataFrame(data, columns=['id', 'periodical', 'location'])
with open('read_marc/marc_data/frenstat_marc.csv', 'w') as f:
    df.to_csv(f, sep=';', index=False)
