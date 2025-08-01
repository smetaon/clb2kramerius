from DwnKramerius import Periodical
import logging
import datetime
import csv

# PATH = 'data/mzk_small.csv'
# with open(PATH) as f:
#     reader = csv.DictReader(f, delimiter=';')
#     for row in reader:
#         now = datetime.datetime.now()
#         timestamp = now.strftime(r"%m%d%H%M%S")

#         log_title = row['title'].replace(' ', '')[:7]
#         logging.basicConfig(level=logging.INFO,
#                             format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
#                             handlers=[
#                                 logging.FileHandler(
#                                     f'data/logs/{log_title}_{timestamp}.log', mode='w'),
#                                 logging.StreamHandler()
#                             ])
#         per = Periodical(
#             name=row['title'],
#             uuid=row['uuid'],
#             library='mzk',
#             kramerius_ver='7',
#             url='https://www.digitalniknihovna.cz/mzk/',
#             api_url='https://api.kramerius.mzk.cz'
#         )


logging.basicConfig(level=logging.INFO)
per = Periodical(
    'ibero',
    'uuid:72c440c0-ae90-11eb-94e5-005056827e52',
    'mzk',
    '7',
    'https://www.digitalniknihovna.cz/mzk/',
    'https://api.kramerius.mzk.cz',
)
# per.find_children()
# per.save('data/ibero_api.json')
