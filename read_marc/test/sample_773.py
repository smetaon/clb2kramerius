from pymarc import MARCReader
import random
from pandas import DataFrame

"""
Sample some random 773$q fields for testing purposes
"""

random.seed(2025)

max = 200
i = 0
data = []

for record in MARCReader(open('/home/clb/data/ucla_all_v4.mrc', 'rb')):
    if i == max:
        break

    pages = list()
    for item in record.get_fields('773'):
        for q in item.get_subfields('q'):
            if random.randint(0, 9) < 2:
                i += 1
                data.append([record['001'].value(), q])
df = DataFrame(data, columns=['id_001', '773q'])
with open('read_marc/test/', 'w') as f:
    df.to_csv(f, sep=';', index=False)
