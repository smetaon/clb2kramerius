from clb2kramerius.DwnKramerius import Periodical, load_periodical
import logging
import datetime
import time
import os
import pandas as pd


def main_single():
    prog_bar = False
    if not prog_bar:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    per = Periodical(
        name='frenstat_test',
        per_uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
        library='mzk',
        kramerius_ver='7',
        url='https://www.digitalniknihovna.cz/mzk',
        api_url='https://api.kramerius.mzk.cz',
        issn='',
        ccnb=''
    )

    # per = Periodical(
    #     name='slansky obzor_test',
    #     per_uuid='uuid:597d4560-66fb-11de-ad0b-000d606f5dc6',
    #     library='nkp',
    #     kramerius_ver='5',
    #     url='https://kramerius5.nkp.cz',
    #     api_url='https://kramerius5.nkp.cz',
    #     issn='',
    #     ccnb=''
    # )

    per.download(prog_bar, save_part=True)
    # per.save(f'data/debug/{per.name}')


if __name__ == '__main__':
    # start = time.time()
    main_single()
    # print(f'it took {time.time()-start:.1f} sec')
