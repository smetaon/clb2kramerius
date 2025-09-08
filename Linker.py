import logging
from DwnKramerius import Periodical
from enum import Enum, auto
import csv
from Parse773 import parse_location, normalize
from collections import namedtuple


class ErrorCodes(Enum):

    PAGE_NOT_DIGI = auto()
    VOL_NOT_DIGI = auto()
    ISSUE_NOT_DIGI = auto()

    NONSTANDARD_773 = auto()
    WRONG_773 = auto()


class Kram2CLB:
    def __init__(self, perio: Periodical, marc_path: str) -> None:
        self.to_proc = set()
        self.success = set()
        self.fail = set()

        self.tree = perio.tree
        self.root_id = perio.root_id
        self.id_sep = perio.id_sep
        self.name = perio.name
        self.issn = perio.issn
        self.url = perio.url
        self.link_uuid = perio.link_uuid

        self.load_marc(marc_path)

    def _add_to_succ(self):
        # remove from to_proc, add to success
        raise NotImplementedError

    def _add_to_fail(self):
        # remove from to_proc, add to fail
        raise NotImplementedError

    def load_marc(self, path: str):
        # load 773q records from csv
        # so far, we only support handmade csv with records from a single periodical
        # TODO: full support (ie. match periodicals 😬)
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for line in reader:
                id = line['id']
                for raw_loc in line["location"].split(';'):
                    Tpl = namedtuple('record', ['id', 'raw_loc'])
                    self.to_proc.add(Tpl(id, raw_loc))

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

    def to_csv(self):
        raise NotImplementedError

    def diagnose_fails(self):
        raise NotImplementedError

    def normalize_tree(self):
        # normalizuj strom třeba tak, aby odstranil závorky a názvech atd.
        raise NotImplementedError

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
        iter_copy = self.to_proc.copy()
        for id, loc in iter_copy:
            volume, issue, page = normalize(*parse_location(loc))
            path_to_page = self._make_path_to_node(
                [self.root_id, volume, issue, page])
            link_to_page = self._link(path_to_page)
            if link_to_page is not None:
                logging.info(f'{id} `{path_to_page}` --> `{link_to_page}`')
            else:
                logging.info(f'{id} `{path_to_page}` not found')

        # # It can happen that there is no `issue` in člb record, but there is an issue number from Kramerius.
        # # E.g. we have 773q '25<100' but from Kramerius we have '25/2/100'.
        # # This should only happen if the volume has one issue, so we can
        # # check that volume has only one child and try path '25:{the only child of vol}<page'
        # if self._volume_has_one_issue(volume):
        #     new_issue = self._find_only_child_of_vol(volume)
        #     new_path_to_page = self._make_path_to_node(
        #         [self.root_id, volume, new_issue, page])
        #     logging.info(
        #         f'Node `{path_to_page}` not found, but it has only one child. Trying path with the one child `{new_path_to_page}`')
        #     link_to_page = self._link(new_path_to_page)

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
