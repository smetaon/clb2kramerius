from DwnKramerius import Periodical, load_periodical
import logging
import datetime
import time
import pandas as pd


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
        csv = pd.read_csv(f, delimiter=';', keep_default_na=False)
    csv_copy = csv.copy()

    for row in csv.itertuples():
        if row.downloaded == 'F':
            now = datetime.datetime.now()
            timestamp = now.strftime(r"%m%d%H%M%S")
            log_title = row.uuid
            log_path = f'data/mzk_medium/logs/{log_title}_{timestamp}.log'

            text_log = logging.FileHandler(log_path, mode='w')
            text_log.setFormatter(log_formatter)
            text_log.setLevel(log_lvl)
            root_logger.addHandler(text_log)

            per = Periodical(
                name=str(row.title),
                uuid=str(row.uuid),
                library='mzk',
                kramerius_ver='7',
                url='https://www.digitalniknihovna.cz/mzk',
                api_url='https://api.kramerius.mzk.cz'
            )

            per.complete_download(prog_bar, save_part=True)
            per.save(f'data/mzk_medium/{log_title}.json')

            root_logger.removeHandler(text_log)
            csv_copy.at[row.Index, 'downloaded'] = 'T'
            with open(PATH, 'w') as out:
                csv_copy.to_csv(out, sep=';', index=False)
        else:
            print(f'Skipping {row.title}')


def main_single():
    prog_bar = False
    if not prog_bar:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    # per = Periodical(
    #     name='frenstat',
    #     uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
    #     library='mzk',
    #     kramerius_ver='7',
    #     url='https://www.digitalniknihovna.cz/mzk',
    #     api_url='https://api.kramerius.mzk.cz'
    # )

    per = Periodical(
        name='slansky obzor',
        uuid='uuid:597d4560-66fb-11de-ad0b-000d606f5dc6',
        library='nkp',
        kramerius_ver='5',
        url='https://kramerius5.nkp.cz',
        api_url='https://kramerius5.nkp.cz'
    )

    per.complete_download(prog_bar, save_part=True)
    # per.save(f'data/debug/{per.name}')


if __name__ == '__main__':
    # main_mass()
    start = time.time()
    main_single()
    print(f'it took {time.time()-start:.1f} sec')
