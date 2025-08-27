from DwnKramerius import Periodical, load_periodical
import logging
import datetime
import csv
import time


def main_mass():
    log_formatter = logging.Formatter(
        '%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    root_logger = logging.getLogger()
    log_lvl = logging.INFO
    root_logger.setLevel(log_lvl)

    prog_bar = True
    if not prog_bar:
        console_log = logging.StreamHandler()
        console_log.setFormatter(log_formatter)
        console_log.setLevel(log_lvl)
        root_logger.addHandler(console_log)

    PATH = 'data/mzk_medium/mzk_medium.csv'
    with open(PATH) as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            now = datetime.datetime.now()
            timestamp = now.strftime(r"%m%d%H%M%S")
            log_title = row['uuid']
            log_path = f'data/mzk_medium/logs/{log_title}_{timestamp}.log'

            text_log = logging.FileHandler(log_path, mode='w')
            text_log.setFormatter(log_formatter)
            text_log.setLevel(log_lvl)
            root_logger.addHandler(text_log)

            per = Periodical(
                name=row['title'],
                uuid=row['uuid'],
                library='mzk',
                kramerius_ver='7',
                url='https://www.digitalniknihovna.cz/mzk',
                api_url='https://api.kramerius.mzk.cz'
            )

            per.complete_download(prog_bar)
            per.save(f'data/mzk_medium/{log_title}.json')

            root_logger.removeHandler(text_log)


def main_single():
    prog_bar = True
    if not prog_bar:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    per = Periodical(
        name='frenštát',
        uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
        library='mzk',
        kramerius_ver='7',
        url='https://www.digitalniknihovna.cz/mzk',
        api_url='https://api.kramerius.mzk.cz'
    )

    per.complete_download(prog_bar)


if __name__ == '__main__':
    main_mass()
    # start = time.time()
    # main_single()
    # print(time.time()-start)
