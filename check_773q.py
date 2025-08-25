from Parse773 import check_format
import csv
from pandas import DataFrame

path_to_marc = 'data/marc_data/all_marc.csv'
data = []

with open(path_to_marc) as f:
    i = 0
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        loc = row["location"].split(';')
        for item in loc:
            standard = check_format(item)
            if standard:
                # print(row['id'], item)
                # i += 1
                tpl = (row['periodical'], 1, 0)
            else:
                tpl = (row['periodical'], 0, 1)
            data.append(tpl)
# print(f'# of nonstandard: {i}')

df = DataFrame(data, columns=['periodical', 'standard', 'nonstandard'])
print(df)

out = df.groupby(['periodical']).sum()
print(out)
with open('data/out.txt', 'w') as f:
    out.to_csv(f)
