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


def get_773(record) -> list[tuple[str, str]] | list[None]:
    # https://www.loc.gov/marc/bibliographic/bd773.html
    lst = []
    for field in record.get_fields('773'):
        per_title_lst = field.get_subfields('t')  # assuming only one title
        per_title = per_title_lst[0] if len(per_title_lst) > 0 else ''
        location = field.get_subfields('q')  # can be a list
        lst.append((per_title, ';'.join(location)))
    return lst


def get_record_id(record) -> str:
    return record.get('001').value()


def create_record(record_id, list_773, list_856):
    # i only care about the first one rn
    if len(list_773) > 0:
        per = list_773[0][0]
        loc = list_773[0][1]
    else:
        per, loc = None, None

    if len(list_856) > 0:
        status = list_856[0][1]
        # link = list_856[0][0]
    else:
        status = None

    return (record_id, per, loc, status)


def rec_has_773q(record_id, per, loc, status) -> bool:
    return loc is not None and len(loc) > 0


if __name__ == "__main__":
    data = []
    reader = MARCReader(open('/home/clb/data/ucla_all_v4.mrc', 'rb'))
    total_records = 2_359_694  # for ucla_all_v4.mrc

    with tqdm(total=total_records) as pbar:
        for record in tqdm(reader):
            rec_id = get_record_id(record)
            lst_856 = get_856(record)
            lst_773 = get_773(record)
            rec = create_record(rec_id, lst_773, lst_856)
            if rec_has_773q(*rec):
                data.append(rec)
            pbar.update(1)
    cols = ['id', 'periodical', 'location', 'is_digitized']
    df = DataFrame(data, columns=cols)
    with open('data/marc_data/all_marc_v2.csv', 'w') as f:
        df.to_csv(f, sep=';', index=False)
