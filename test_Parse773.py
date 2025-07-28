import csv
from Parse773 import parse_location, replace_separators


def test_parse_location():
    with open('test_data/test_parsing.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row['issue'] == 'None':
                row['issue'] = None
            hand_parsed = (row['volume'], row['issue'], row['page'])
            assert parse_location(row['773q']) == hand_parsed


def test_replace_separators():
    with open('test_data/test_replace_separators.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            hand_parsed = (row['hand_vol'],
                           row['hand_issue'],
                           row['hand_page'])
            vol_iss_pg = (row['vol'], row['issue'], row['page'])
            assert replace_separators(*vol_iss_pg) == hand_parsed
