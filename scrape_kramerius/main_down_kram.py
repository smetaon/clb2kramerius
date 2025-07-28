import DwnKramerius as dwn
import logging
import datetime
now = datetime.datetime.now()
timestamp = now.strftime(r"%m%d%H%M%S")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler(
                            f'kramerius_dwn_data/logs/frenstat_{timestamp}.log', mode='w'),
                        logging.StreamHandler()
                    ])

per = dwn.Periodical(
    name='Hlasy muzea a archivu ve Frenštátě pod Radhoštěm',
    uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
    library='mzk',
    kramerius_ver='v7',
    url='https://www.digitalniknihovna.cz/mzk/',
)

# per = dwn.Periodical(
#     name='Ibero-Americana Pragensia',
#     uuid='uuid:72c440c0-ae90-11eb-94e5-005056827e52',
#     library='mzk',
#     kramerius_ver='v7',
#     url='https://www.digitalniknihovna.cz/mzk/',
# )

# per = dwn.Periodical(
#     name='Národopisná revue',
#     uuid='uuid:6d522af0-fd50-11e4-92a1-5ef3fc9bb22f',
#     library='mzk',
#     kramerius_ver='v7',
#     url='https://www.digitalniknihovna.cz/mzk/'
# )


driver = dwn.setup_driver(headless=False)
per.find_children('periodical', per.uuid, per.root, driver)
per.save_tree(
    f'/home/clb/dev/link_kramerius/kramerius_dwn_data/frenstat_new_{timestamp}.json')

dwn.teardown(driver)
