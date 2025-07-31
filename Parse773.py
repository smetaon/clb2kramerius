import re


def standardize_loc(loc: str) -> str:
    """Complete field 773q in a way that it is always in the form
    `volume:issue<page`.

    This facilitates future parsing.

    Sometimes, 773q in marc misses issue or page, eg. 1<3 or 1:5.
    Fix this by attaching the appropriate symbol, eg. 1<3: or 1<:5.

    Parameters
    ----------
    loc : str
        Raw 773q from marc.

    Returns
    -------
    str
        773q field in the form `volume:issue<page`.
    """
    PAGE_SEP_CHAR = '<'
    ISSUE_SEP_CHAR = ':'
    issue_sep = re.search(ISSUE_SEP_CHAR, loc)
    page_sep = re.search(PAGE_SEP_CHAR, loc)

    if issue_sep is None and page_sep is None:
        return loc+ISSUE_SEP_CHAR+PAGE_SEP_CHAR
    if issue_sep is None:
        return re.sub(PAGE_SEP_CHAR, ISSUE_SEP_CHAR+PAGE_SEP_CHAR, loc)
    if page_sep is None:
        return loc+PAGE_SEP_CHAR
    return loc


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
    fixed_loc = standardize_loc(loc)
    capture_volume = r'^(.+):'
    capture_issue = r':(.+)<'
    capture_page = r'<(.+)$'

    vol_match = re.search(capture_volume, fixed_loc)
    issue_match = re.search(capture_issue, fixed_loc)
    page_match = re.search(capture_page, fixed_loc, re.IGNORECASE)

    vol = vol_match[1] if vol_match is not None else None
    issue = issue_match[1] if issue_match is not None else None
    page = page_match[1] if page_match is not None else None

    return (vol, issue, page)


def replace_separators(vol: str | None, issue: str | None, page: str | None) -> tuple[str | None, str | None, str | None]:
    """Replace `/` with `-` in an issue number.

    Kramerius uses `-` as a separator for issues with more than one number, eg. https://www.digitalniknihovna.cz/mzk/view/uuid:e62bcfd1-5796-11e5-bf4b-005056827e51 is `1-2`.
    ČLB uses `/` for the same purpose.

    Parameters
    ----------
    vol : str | None
        Volume.
    issue : str | None
        Issue.
    page : str | None
        Page.

    Returns
    -------
    tuple[str | None, str | None, str | None]
        Volume Issue Page

    """
    if issue is not None:
        issue = re.sub('/', '-', issue)

    return (vol, issue, page)


def remove_leading_zeros(vol: str | None, issue: str | None, page: str | None) -> tuple[str | None, str | None, str | None]:
    """Remove leading zeros sometimes found in `issue` string.

    Parameters
    ----------
    vol : str | None
        Volume.
    issue : str | None
        Issue.
    page : str | None
        Page

    Returns
    -------
    tuple[str | None, str | None, str | None]
        Volume, issue, page.
    """
    if issue is not None:
        match = re.findall(r'(\d+)', issue)
        trimmed = []
        # remove leading zeros
        for num in match:
            trimmed.append(re.sub(r'^0+', '', num))

        # place numbers with removed zeros back to the original string
        for orig, new in zip(match, trimmed):
            issue = re.sub(orig, new, issue)

    return (vol, issue, page)


def remove_brackets():
    raise NotImplementedError


def normalize(vol: str | None, issue: str | None, page: str | None) -> tuple[str | None, str | None, str | None]:
    normalized = remove_leading_zeros(vol, issue, page)
    normalized = replace_separators(*normalized)

    return normalized
