from DwnKramerius import KramAPIv7, Periodical
from Parse773 import parse_location, normalize
import logging
import csv
import json
import networkx as nx


logging.basicConfig(level=logging.INFO)

per = Periodical(
    name='frenstat',
    uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
    library='mzk',
    kramerius_ver='7',
    url='https://www.digitalniknihovna.cz/mzk',
    api_url='https://api.kramerius.mzk.cz'
)


per.build_clb_tree('data/marc_data/frenstat_marc.csv')
print(list(per.clb_tree.successors('root')))

per._select_KramAPI()
per.api.dfs_with_clb_tree(
    per.uuid, 'periodical', per.root, per.clb_tree, per.root)
per.tree = per.api.return_tree()
print(per.tree)
per.save('data/frenstat_clb_tree.json')

# per._select_scraper()

# vols, issues, pages = set(), set(), set()


# PATH = 'data/marc_data/narodopis_marc.csv'
# with open(PATH) as f:
#     reader = csv.DictReader(f, delimiter=';')
#     for row in reader:
#         for loc in row['location'].split(';'):
#             volume, issue, page = parse_location(loc)
#             if issue is None:
#                 issue = 'no_issue'.upper()

#             volume, issue, page = normalize(volume, issue, page)
#             vols.add(volume)
#             issues.add(issue)
#             pages.add(page)
# print(vols, issues, pages, sep='\n')

# per.scraper.dfs2(per.uuid, 'periodical', per.root, [vols, issues, pages], 0)
# per.tree = per.scraper.return_tree()

# per.save('data/narodopis_faster.json')


# 12m24,857s pro obyčejné dfs stahování všeho pro frenštát, Nodes=3242 Edges=3241
# 7m48,013s pro dfs stahování s využitím requests.Session()
# 5m17,567s pro dfs2 1236 nodes and 1235 edges
# když stahuju pouze člb přesně: 1m51,364s Nodes=133 Edges=132
