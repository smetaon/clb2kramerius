import DwnKramerius as dwn
import logging
import datetime
import csv

PATH = 'data/mzk_small.csv'
with open(PATH) as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        now = datetime.datetime.now()
        timestamp = now.strftime(r"%m%d%H%M%S")

        log_title = row['title'].replace(' ', '')[:7]
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                            handlers=[
                                logging.FileHandler(
                                    f'data/logs/{log_title}_{timestamp}.log', mode='w'),
                                logging.StreamHandler()
                            ])
        per = dwn.Periodical(
            name=row['title'],
            uuid=row['uuid'],
            library='mzk',
            kramerius_ver='v7',
            url='https://www.digitalniknihovna.cz/mzk/'
        )

        driver = dwn.setup_driver(headless=True)
        per.find_children('periodical', per.uuid, per.root, driver)
        per.save(f'data/{log_title}_{timestamp}.json')

        dwn.teardown(driver)
