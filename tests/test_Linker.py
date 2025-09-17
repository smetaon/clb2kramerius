from clb2kramerius.Linker import Kram2CLB, ErrorCodes
from clb2kramerius.DwnKramerius import load_periodical


def test_diagnose_773q():
    perio = load_periodical('test_data/frenstat_test.json')
    linker = Kram2CLB(perio, 'test_data/frenstat_marc.csv')
    linker.link()
    linker._diagnose_773q()
    expected = [ErrorCodes.MISSING_ISSUE,
                ErrorCodes.MISSING_PAGE,
                ErrorCodes.MISSING_ISSUE,
                ErrorCodes.MISSING_MULTIPLE]
    for f, err in zip(linker.return_fails(), expected):
        assert f.error_code is err
