import re


def parse_location(loc: str) -> tuple[str | None, str | None, str | None]:
    """Parse subfield 773$q.

    Format is volume:issue<page.

    BUT
    Issue does not have to be present (eg. 35<66 = vol 35 page 66).
    All three numbers can be in parentheses (eg. [1]:[5]<[112]).
    Issues can have more than one number (eg. 1:5/6<45 or 1:01/02<12) (but numbers appear to be consitently separated with `/`).
    Pages can be roman numerals (eg. 25:187<xii).

    Parameters
    ----------
    loc : str
        773$q value

    Returns
    -------
    tuple[str | None, str | None, str | None]
        volume, issue, page
    """
    capture_volume = r'^([\[\d\]\ ]+)[:<]'
    capture_issue = r':([\[\d/\]]+)<'
    capture_page = r'<([\[ixv\d\]]+)$'

    vol_match = re.search(capture_volume, loc)
    issue_match = re.search(capture_issue, loc)
    page_match = re.search(capture_page, loc, re.IGNORECASE)

    vol = vol_match[1] if vol_match is not None else None
    issue = issue_match[1] if issue_match is not None else None
    page = page_match[1] if page_match is not None else None

    return (vol, issue, page)


def normalize(vol: str | None, issue: str | None, page: str | None) -> tuple[str | None, str | None, str | None]:
    raise NotImplementedError


def replace_separators(vol: str | None, issue: str | None, page: str | None) -> tuple[str | None, str | None, str | None]:
    """Replace `/` with `-` in an issue number.

    Kramerius uses `-` as a separator for issues with more than one number, eg. https://www.digitalniknihovna.cz/mzk/view/uuid:e62bcfd1-5796-11e5-bf4b-005056827e51 is `1-2`.
    ČLB uses `/` for the same purpose.

    Parameters
    ----------
    vol : str | None
        _description_
    issue : str | None
        _description_
    page : str | None
        _description_

    Returns
    -------
    tuple[str | None, str | None, str | None]
        _description_

    """
    if issue is not None:
        issue = re.sub('/', '-', issue)

    return (vol, issue, page)


def remove_leading_zeros():
    raise NotImplementedError


def remove_brackets():
    raise NotImplementedError
