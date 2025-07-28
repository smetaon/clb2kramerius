import csv
from Parse773 import parse_location


def test_parse_location():
    with open('test/test_773.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row['issue'] == 'None':
                row['issue'] = None
            hand_parsed = (row['volume'], row['issue'], row['page'])
            assert parse_location(row['773q']) == hand_parsed
