import pandas as pd

records = pd.read_csv(
    '/home/clb/dev/link_kramerius/data/uuid_nk_clb.csv', sep=';')

kram_insts = pd.read_csv(
    '/home/clb/dev/link_kramerius/data/match_periodicals/kram_inst_details.csv', sep=';')
print(records.head())
kram_insts = kram_insts.set_index('domain')
print(kram_insts)
joined = records.join(kram_insts, on='url')
print(joined)
with open('/home/clb/dev/link_kramerius/data/records.csv', 'w') as out:
    joined.to_csv(out, sep=';', index=False)
