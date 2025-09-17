from pymarc import MARCReader
import logging
import re
import pandas as pd

"""Retrieve useful data from Database of Recorded Periodicals.
    (https://clb.ucl.cas.cz/en/database/database-of-recorded-periodicals/)
    
    The source mrc file was provided by V. Malínek.
"""


def get_title(record) -> str:
    title = record['245']['a']
    # clean tail
    title = re.sub(r'[:\. \ =]*$', '', title)
    return title.strip()


def get_issn(record) -> str | None:
    try:
        return record['022']['a']
    except KeyError:
        return None


def get_id(record) -> str:
    return record['001'].value()


def get_digi(record) -> str | None:
    lst = []
    for field in record.get_fields('856'):
        url = field['u']
        lst.append(url)
    if len(lst) > 0:
        return ';'.join(lst)
    else:
        return None


if __name__ == '__main__':
    # WARNING:pymarc:more than 2 indicators found: b'  SE'
    logging.basicConfig(level=logging.ERROR)

    PATH = 'data/marc_files/dtbz_excerp_per.mrc'
    reader = MARCReader(open(PATH, 'rb'))

    data = []
    for record in reader:
        rec = {}
        rec['id'] = get_id(record)
        rec['title'] = get_title(record)
        rec['issn'] = get_issn(record)
        rec['digi'] = get_digi(record)

        data.append(rec)
    df = pd.DataFrame(data)

    # remove samizdat and online
    df = df[~df['title'].str.contains('online|samizdat', case=False)]

    df.sort_values(by='title').to_csv(
        'data/excerp_per.csv', index=False, sep=';')
