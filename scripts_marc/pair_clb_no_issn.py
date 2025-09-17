import pandas as pd

# máme dva soubory: záznamy z člb s issn a záznamy bez issn
# ne všem záznamům bez issn skutečně nenáleží žádné issn
# podle jména zkusíme napárovat a odstranit ze souboru bez issn
# periodika, která ve skutečnosti mají issn

no_issn = pd.read_csv(
    '/home/clb/dev/link_kramerius/data/match_periodicals/clb_no_issn_shorter.csv', sep=';')
has_issn = pd.read_csv(
    '/home/clb/dev/link_kramerius/data/match_periodicals/clb_has_issn.csv', sep=';')

no_issn = no_issn.set_index('marc_title')
has_issn = has_issn.set_index('marc_title')
joined = has_issn.join(no_issn, how='outer', rsuffix='_r')

joined.to_csv(
    '/home/clb/dev/link_kramerius/data/match_periodicals/clb_joined.csv', sep=';')
