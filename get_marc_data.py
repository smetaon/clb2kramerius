from pymarc import MARCReader
from pandas import DataFrame
import re
from tqdm import tqdm
"""
Save a periodical from marc to a smaller csv
"""


def get_856(record) -> list[tuple[str, str]] | list[None]:
    # https://www.loc.gov/marc/bibliographic/bd856.html
    lst = []
    for field in record.get_fields('856'):
        url = ';'.join(field.get_subfields('u'))
        link_text = ';'.join(field.get_subfields('y'))
        lst.append((url, link_text))
    return lst


def get_773(record) -> list[tuple[str, str, str | None]] | list[None]:
    # title; 773q; issn
    # https://www.loc.gov/marc/bibliographic/bd773.html
    lst = []
    for field in record.get_fields('773'):
        per_title_lst = field.get_subfields('t')  # assuming only one title
        per_title = per_title_lst[0] if len(per_title_lst) > 0 else ''
        location = field.get_subfields('q')  # can be a list
        issn = field.get_subfields('x')  # can be a list
        lst.append((per_title, ';'.join(location), ';'.join(issn)))
    return lst


def get_rec_creation_year(record) -> str | None:
    # první CAT je datum založení záznamu
    cats = record.get_fields('CAT')
    if len(cats) > 1:
        first_cat = cats[0]
        date = first_cat.get_subfields('c')[0]
        return date[:4]
    else:
        return None


def get_rec_publish_year(record) -> str:
    # rok vydání
    field = record.get('008')
    val = field.value()
    return val[7:11]


def get_record_id(record) -> str:
    return record.get('001').value()


def create_record(record_id, list_773, list_856, pub_year, rec_create_year) -> dict:
    # i only care about the first one rn
    d = dict()
    d['id'] = record_id
    if len(list_773) > 0:
        d['periodical'] = list_773[0][0].lower().strip()
        d['location'] = list_773[0][1]
        d['issn'] = list_773[0][2]
    else:
        d['periodical'], d['location'], d['issn'] = None, None, None

    if len(list_856) > 0:
        d['digi'] = list_856[0][1]
        d['link'] = list_856[0][0]
    else:
        d['digi'] = None
        d['link'] = None
    d['pub_year'] = pub_year
    d['create_year'] = rec_create_year

    return d


def rec_has_773q(loc) -> bool:
    return loc is not None and len(loc) > 0


def is_serial(record) -> bool:
    return record.leader[7] == 'b'


if __name__ == "__main__":
    data = []
    reader = MARCReader(open('/home/clb/data/ucla_all_v4.mrc', 'rb'))
    total_records = 2_359_694  # for ucla_all_v4.mrc

    with tqdm(total=total_records, disable=False) as pbar:
        for record in reader:
            rec_id = get_record_id(record)
            lst_856 = get_856(record)
            lst_773 = get_773(record)
            publish_year = get_rec_publish_year(record)
            rec_create_year = get_rec_creation_year(record)

            rec = create_record(rec_id, lst_773, lst_856,
                                publish_year, rec_create_year)

            if is_serial(record) and rec_has_773q(rec['location']):
                data.append(rec)
            pbar.update(1)

    df = DataFrame(data)
    with open('data/marc_data/all_marc_v2.csv', 'w') as f:
        df.to_csv(f, sep=';', index=False)
