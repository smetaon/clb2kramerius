import csv
from Parse773 import parse_location, replace_separators, remove_leading_zeros


def test_parse_location():
    with open('test_data/test_parsing.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            parsed = parse_location(row['773q'])
            vol, issue, page = (str(i) for i in parsed)
            hand_parsed = (row['volume'], row['issue'], row['page'])
            assert (vol, issue, page) == hand_parsed


def test_replace_separators():
    with open('test_data/test_replace_separators.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            hand_parsed = (row['hand_vol'],
                           row['hand_issue'],
                           row['hand_page'])
            vol_iss_pg = (row['vol'], row['issue'], row['page'])
            assert replace_separators(*vol_iss_pg) == hand_parsed


def test_remove_leading_zeros():
    with open('test_data/test_remove_leading_zeros.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            hand_parsed = (row['hand_vol'],
                           row['hand_issue'],
                           row['hand_page'])
            vol_iss_pg = (row['vol'], row['issue'], row['page'])
            assert remove_leading_zeros(*vol_iss_pg) == hand_parsed
