import logging
from DwnKramerius import Periodical
from enum import Enum, auto
import csv
from Parse773 import parse_location, normalize
from dataclasses import dataclass, field
import networkx as nx


class ErrorCodes(Enum):
    """Error codes for processing records.

    Parameters
    ----------
    TO_PROCESS
        Record is to be linked (by the `link` function).
        Default for records read from csv file with marc records.
    SUCCESS
        The `link` function was successful at matching 773q and the relevant path in the downloaded tree.
    TO_DIAGNOSE
        The `link` function was unsuccessful at matching 773q and the relevant path in the downloaded tree.
        The record is to be diagnosed why the matching failed (by the `diagnose_fail` function).
    PAGE_NOT_DIGI
        Page is not digitized.
    VOL_NOT_DIGI
        Volume is not digitized.
    ISSUE_NOT_DIGI
        Volume is not digitized.
    NONSTANDARD_773
        Nonstandard format of the 773q field.
    MISSING_PAGE
        Page number was not found in the 773q field.
    MISSING_ISSUE
        Issue number was not found in the 773q field. 
    MISSING_VOL
        Volume number was not found in the 773q field. 
    MISSING_MULTIPLE
        More than one part of 773q is missing.

    """
    TO_LINK = auto()
    SUCCESS = auto()
    TO_DIAGNOSE = auto()

    PAGE_NOT_DIGI = auto()
    VOL_NOT_DIGI = auto()
    ISSUE_NOT_DIGI = auto()

    NONSTANDARD_773 = auto()  # TODO: implement (?)
    WRONG_773 = auto()  # TODO: potřebuju???

    MISSING_PAGE = auto()
    MISSING_ISSUE = auto()
    MISSING_VOL = auto()
    MISSING_MULTIPLE = auto()


@dataclass
class Record:
    """A single record from MARC.

    Attributes
    -----------
    id : str
        Record identifer, field `001` in marc.
    raw_loc : str
        Location in a periodical, field `773q` in marc.
    error_code : ErrorCodes
        Error code assigned to this record.
    link : str
        URL to digitized version.
    volume : str | None
        Volume number, parsed from `raw_loc`.
    issue : str | None
        Issue number, parsed from `raw_loc`.
    page : str | None
        Page number, parsed from `raw_loc`.
    """
    id: str
    raw_loc: str
    error_code: ErrorCodes = ErrorCodes.TO_LINK
    link: str | None = None

    volume: str | None = field(init=False)
    issue: str | None = field(init=False)
    page: str | None = field(init=False)

    def __post_init__(self) -> None:
        self.volume, self.issue, self.page = normalize(
            *parse_location(self.raw_loc))


class Kram2CLB:
    """Links downloaded periodicals from Kramerius to records in člb.

    Attributes:
    -----------
    records : list[Record]
        A list of records read from `marc_path` file.
    tree : nx.DiGraph
        The tree of the digited periodical.
    root_id : str
        Root identifier, by default `root`.
    id_sep : str
        Separator used in keys in the tree, by default `/`.
    name : str
        Name of a periodical.
    issn : str | None
        ISSN of the periodical, if it is available.
    url : str
        The base URL of the library.
    link_uuid : str
        Part of URL linking to a particular UUID, by default `uuid`.
    """

    def __init__(self, perio: Periodical, marc_path: str) -> None:
        self.records: list[Record] = list()

        self.tree: nx.DiGraph = perio.tree
        self.root_id: str = perio.root_id
        self.id_sep: str = perio.id_sep
        self.name: str = perio.name
        self.issn: str | None = perio.issn
        self.url: str = perio.url
        self.link_uuid: str = perio.link_uuid

        self.load_marc(marc_path)

    def load_marc(self, path: str):
        """Load marc records from a csv to `self.records`.

        Parameters
        ----------
        path : str
            Path to csv file with marc records.
        """
        # so far, we only support handmade csv with records from a single periodical
        # TODO: full support (ie. match periodicals 😬)
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for line in reader:
                id = line['id']
                for raw_loc in line["location"].split(';'):
                    self.records.append(Record(id, raw_loc))

    def make_url(self, uuid: str) -> str:
        """Generate a URL to issue/volume/page.

        Parameters
        ----------
        uuid : str
            UUID of the unit.

        Returns
        -------
        str
            A link to the unit on the Kramerius website.
        """
        return self.url+'/'+self.link_uuid+'/'+uuid

    def return_successes(self) -> list[Record]:
        """Return records with SUCCESS error code.

        Returns
        -------
        list[Record]
            Records with SUCCESS error code.
        """
        return self._filter_error_codes(ErrorCodes.SUCCESS)

    def return_fails(self) -> list[Record]:
        """Return records with unsuccessful linking.

        Returns
        -------
        list[Record]
            Records with error code other than SUCCESS or TO_LINK.
        """
        fails = filter(lambda rec: rec.error_code is not
                       ErrorCodes.SUCCESS and rec.error_code is not ErrorCodes.TO_LINK, self.records)
        return list(fails)

    def to_csv(self):
        raise NotImplementedError

    def diagnose_fails(self):
        """Diagnose why linking failed.
        """
        self._diagnose_773q()
        return

    def normalize_tree(self):
        # normalizuj strom třeba tak, aby odstranil závorky a názvech atd.
        raise NotImplementedError

    def success_rate(self) -> float:
        """Return linking success rate.

        Returns
        -------
        float
            Linking success rate.
        """
        return len(self.return_successes())/len(self.records)

    def fix_errors(self) -> None:
        """Fix failed matches based on their error code.
        """
        self._fix_missing_issue()

    def _make_path_to_node(self, lst: list[str | None]) -> str:
        """Make path to a node by concatenating root, volume, issue, page numbers.

        Parameters
        ----------
        lst : list[str  |  None]
            Root, volume, issue, page (anything can be omitted).

        Returns
        -------
        str
            Path to a node.
        """
        path = self.id_sep.join(filter(None, lst))
        return path

    def _link(self, path: str) -> str | None:
        """Try making a URL to a given path.

        Parameters
        ----------
        path : str
            Path to a node.

        Returns
        -------
        str | None
            URL to a unit or `None` if the path leads nowhere.
        """
        try:
            page_node = self.tree.nodes[path]
        except KeyError:
            return None
        else:
            page_url = self.make_url(page_node['uuid'])
            return page_url

    def link(self):
        """Try linking records with code `TO_LINK`.
        """
        to_process = self._filter_error_codes(ErrorCodes.TO_LINK)
        for rec in to_process:
            path_to_page = self._make_path_to_node(
                [self.root_id, rec.volume, rec.issue, rec.page])
            link_to_page = self._link(path_to_page)
            if link_to_page is not None:
                logging.info(f'{rec.id} `{path_to_page}` --> `{link_to_page}`')
                rec.error_code = ErrorCodes.SUCCESS
                rec.link = link_to_page
            else:
                logging.info(f'{rec.id} `{path_to_page}` not found')
                rec.error_code = ErrorCodes.TO_DIAGNOSE

    def _diagnose_773q(self) -> None:
        """Look for inconsitencies in the 773q field.
        """
        fails = self.return_fails()
        for rec in fails:
            nones = filter(lambda x: x is None, [
                           rec.volume, rec.issue, rec.page])
            if len(list(nones)) > 1:
                rec.error_code = ErrorCodes.MISSING_MULTIPLE
                continue

            if rec.volume is None:
                rec.error_code = ErrorCodes.MISSING_VOL
            if rec.issue is None:
                rec.error_code = ErrorCodes.MISSING_ISSUE
            if rec.page is None:
                rec.error_code = ErrorCodes.MISSING_PAGE
        return

    def _filter_error_codes(self, err_code: ErrorCodes) -> list[Record]:
        """Filter `records` based on an error code.

        Parameters
        ----------
        err_code : ErrorCodes
            Error code used for filtering.

        Returns
        -------
        list[Record]
            List of Records with error code matching the provided `err_code`.
        """
        filtered = filter(lambda rec: rec.error_code is err_code, self.records)
        return list(filtered)

    def _fix_missing_issue(self) -> None:
        """Try fixing records that have a missing issue number.
        """
        wrong_issues = self._filter_error_codes(ErrorCodes.MISSING_ISSUE)
        for rec in wrong_issues:
            if self._volume_has_one_issue(rec.volume):
                new_issue = self._find_only_child_of_vol(rec.volume)
                logging.info(
                    f'Volume `{rec.volume}` has only one issue: `{new_issue}`, using it as a new issue')
                rec.issue = new_issue
                rec.error_code = ErrorCodes.TO_LINK
            else:
                logging.info(
                    f'Volume `{rec.volume}` has more than one child, unable to fix.')
        return

    def _volume_has_one_issue(self, volume: str | None) -> bool:
        """Check that given volume has only one child (= one issue).

        Parameters
        ----------
        volume : str | None
            Volume number (not a path).

        Returns
        -------
        bool
            `True` if volume has one child, `False` otherwise.
        """
        path_to_vol = self._make_path_to_node([self.root_id, volume])
        try:
            self.tree.nodes[path_to_vol]
        except KeyError:
            return False
        children = list(self.tree.successors(path_to_vol))
        return True if len(children) == 1 else False

    def _find_only_child_of_vol(self, volume: str | None) -> str:
        """Find issue number of an issue that is the only child of a volume.

        Parameters
        ----------
        volume : str | None
            Volume number (not a path).

        Returns
        -------
        str
            Issue number (not a path).

        Raises
        ------
        ValueError
            Volume has more than one child.
        """
        path_to_vol = self._make_path_to_node([self.root_id, volume])
        children = list(self.tree.successors(path_to_vol))
        if len(children) != 1:
            raise ValueError('More than one child!')
        issue_path = children[0]
        issue = issue_path.split('/')[-1]
        return issue
