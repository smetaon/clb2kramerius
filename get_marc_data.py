from pymarc import MARCReader
from pandas import DataFrame
import re
"""
Save a periodical from marc to a smaller csv
"""

data = []
reader = MARCReader(open('/home/clb/data/ucla_all_v4.mrc', 'rb'))
# my_per_title = 'Národopisná revue'
i = 0
for record in reader:
    for field in record.get_fields('773'):  # type: ignore
        per_title_lst = field.get_subfields('t')  # assuming only one title
        per_title = per_title_lst[0] if len(per_title_lst) > 0 else ''
        location = field.get_subfields('q')  # can be a list
        # if re.search(my_per_title, per_title, re.IGNORECASE) is not None:
        if len(location) > 0:
            data.append([record.get('001').value(),  # type: ignore
                        per_title,
                        ';'.join(location)])
        i += 1
        if i % 1_000 == 0:
            print(i)

df = DataFrame(data, columns=['id', 'periodical', 'location'])
with open('data/marc_data/all_marc.csv', 'w') as f:
    df.to_csv(f, sep=';', index=False)
