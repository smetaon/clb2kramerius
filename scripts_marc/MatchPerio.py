import pandas as pd


def pair_issn(lib: pd.DataFrame, marc: pd.DataFrame) -> pd.DataFrame:
    lib = lib.dropna(ignore_index=True)
    marc = marc.dropna(ignore_index=True)

    marc = marc.set_index('issn')
    lib = lib.set_index('issn')
    joined = lib.join(marc, how='outer')
    return joined


def prep_df(df: pd.DataFrame, cols: list[str], col_title_name: dict[str, str]) -> pd.DataFrame:
    df = df[cols]
    df = df.drop_duplicates(ignore_index=True)
    df = df.rename(columns=col_title_name)
    return df


def issn(df: pd.DataFrame, sort_by_col: str, no_issn_file: str, has_issn_file: str):
    has_issn = df[df['issn'].notnull()]
    no_issn = df[df['issn'].isnull()]

    with open(f'data/match_periodicals/{has_issn_file}.csv', 'w') as f1:
        has_issn.sort_values(by=sort_by_col).to_csv(f1, sep=DELIM, index=False)

    with open(f'data/match_periodicals/{no_issn_file}.csv', 'w') as f2:
        no_issn.sort_values(by=sort_by_col).to_csv(f2, sep=DELIM, index=False)


def get_kramerius_instances(df: pd.DataFrame, col_domains: str, file: str):
    krams = df.sort_values(by=col_domains)
    krams = krams[col_domains]
    krams = krams.str.strip()
    krams = krams.drop_duplicates(ignore_index=True)
    with open(f'data/match_periodicals/{file}.csv', 'w') as f:
        krams.to_csv(f, sep=DELIM, index=False)


PATH_DIGI_LIB = 'data/records.csv'
PATH_MARC = 'data/marc_data/all_marc.csv'
DELIM = ';'

with open(PATH_DIGI_LIB) as f:
    digi_lib_df = pd.read_csv(f, delimiter=DELIM, dtype=str)
with open(PATH_MARC) as f:
    marc_df = pd.read_csv(f, delimiter=DELIM, dtype=str)


digi_lib_df = prep_df(digi_lib_df,
                      ['title', 'issn', 'uuid', 'url'],
                      {'title': 'digi_lib_title'})

marc_df = prep_df(marc_df,
                  ['periodical', 'issn'],
                  {'periodical': 'marc_title'})


print(marc_df)

# get_kramerius_instances(digi_lib_df, 'url', 'kram_instances')

# issn(digi_lib_df,
#      sort_by_col='digi_lib_title',
#      no_issn_file='kram_no_issn',
#      has_issn_file='kram_has_issn')

# issn(marc_df,
#      sort_by_col='marc_title',
#      no_issn_file='clb_no_issn',
#      has_issn_file='clb_has_issn')


joined = pair_issn(digi_lib_df, marc_df)
print(joined)

with open('data/match_periodicals/joined_per_all.csv', 'w') as out:
    joined.to_csv(out, sep=DELIM)
