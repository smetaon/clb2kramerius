from DwnKramerius import load_periodical
from Linker import Kram2CLB
import logging

FORMAT = "[%(asctime)s %(funcName)s():]%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)

path_to_periodical = 'data/debug/frenstat.json'
path_to_marc = 'data/marc_data/frenstat_marc.csv'

perio = load_periodical(path_to_periodical)
linker = Kram2CLB(perio, path_to_marc)
linker.link()
succ_rate = linker.success_rate()
print(f'Succes rate {succ_rate:.1%}')
linker.diagnose_fails()
linker.fix_errors()
linker.link()
succ_rate = linker.success_rate()
print(f'Succes rate {succ_rate:.1%}')
