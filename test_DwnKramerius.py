from DwnKramerius import Periodical, KramScraperV5, KramScraperV7
import logging
# TODO: potřebuje to nějaké testy pro scrapery, ne????
logging.basicConfig(level=logging.INFO)


def test_KramScraperV5_find_children():
    # https://kramerius5.nkp.cz/periodical/uuid:ae747548-435d-11dd-b505-00145e5790ea
    scrpr = KramScraperV5('https://kramerius5.nkp.cz')
    expected = [{'pid': 'uuid:af139b19-435d-11dd-b505-00145e5790ea', 'model': 'periodicalvolume', 'details': {'volumeNumber': '1', 'year': '1862'}}, {'pid': 'uuid:af14104a-435d-11dd-b505-00145e5790ea', 'model': 'periodicalvolume', 'details': {'volumeNumber': '2', 'year': '1863'}},
                {'pid': 'uuid:af14104c-435d-11dd-b505-00145e5790ea', 'model': 'periodicalvolume', 'details': {'volumeNumber': '4', 'year': '1864'}}, {'pid': 'uuid:af14375e-435d-11dd-b505-00145e5790ea', 'model': 'periodicalvolume', 'details': {'volumeNumber': '6', 'year': '1865'}}]
    assert scrpr._find_children(
        'uuid:ae747548-435d-11dd-b505-00145e5790ea') == expected


def test_KramScraperV5_find_node_details():
    # https://kramerius5.nkp.cz/periodical/uuid:af14375e-435d-11dd-b505-00145e5790ea
    scrpr = KramScraperV5('https://kramerius5.nkp.cz')
    node = {
        'pid': 'uuid:af14375e-435d-11dd-b505-00145e5790ea',
        'model': 'periodicalvolume',
        'details': {
            "volumeNumber": "6",
            "year": "1865"
        }
    }
    assert scrpr._find_node_details(node) == ('periodicalvolume', '6')


def test_KramScraperV7_find_children():
    # https://www.digitalniknihovna.cz/mzk/periodical/uuid:d9408d50-56d4-11e5-9a33-5ef3fc9ae867
    scrpr = KramScraperV7('https://api.kramerius.mzk.cz')
    children = scrpr._find_children(
        'uuid:d9408d50-56d4-11e5-9a33-5ef3fc9ae867')
    expected = [{'pid': 'uuid:40288e00-56e4-11e5-b7d6-5ef3fc9bb22f', 'relation': 'hasIntCompPart'}, {'pid': 'uuid:a158b831-56df-11e5-b7d6-5ef3fc9bb22f', 'relation': 'hasItem'},
                {'pid': 'uuid:6c855dc0-56e4-11e5-b7d6-5ef3fc9bb22f', 'relation': 'hasItem'}, {'pid': 'uuid:9ca50940-56e1-11e5-b7d6-5ef3fc9bb22f', 'relation': 'hasItem'}]
    assert children == expected
