import networkx as nx
import json
import logging
from enum import Enum
import requests as req
from requests.adapters import HTTPAdapter, Retry
import Parse773
import csv
from tqdm import tqdm


class Library(Enum):
    """Library identifier.

    Parameters
    ----------
    Enum : str
        Acronym of a library.
    """
    MZK = 'mzk'
    NKP = 'nkp'


class KramVer(Enum):
    """Kramerius (API) version.

    Parameters
    ----------
    Enum : str
        '7' or '5'
    """
    V7 = '7'
    V5 = '5'


class KramAPIBase():
    """Base class for Kramerius API.


    Attributes
    ----------
    url : str
        Kramerius API URL. It should not end with `/`.

    sep : str
        Separator used in keys when downloading from Kramerius. By default `/`.

    tree : nx.DiGraph()
        The tree of the digited periodical.
        Keys are made by concatenating volume/issue/page number.

    INFO : str
        String to pass to API to receive info about Kramerius installation.

    VER : KramVer
        Kramerius version. So far, 5 and 7.   

    vols_to_dw : int
        Number of volumes to download.
        To be used in a simple progress bar.

    progress_bar : tdqm()
        Progress bar object.
    """
    INFO: str
    VER: KramVer
    vols_to_dwn: int = 0

    def __init__(self, url: str, sep='/') -> None:
        self.url = url
        self.sep = sep
        self.tree = nx.DiGraph()
        self.session = req.Session()
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status#server_error_responses
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        # https://stackoverflow.com/questions/23267409/how-to-implement-retry-mechanism-into-python-requests-library
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self._check_version()
        self._check_url()

    def _check_url(self):
        """Check that API URL is correct and functional.

        Raises
        ------
        ValueError
            The API URL should not end with `/`.
        ValueError
            The request for INFO is not OK.
        """
        if self.url[-1] == '/':
            raise ValueError(
                f'API URL should not end with `/` `{self.url}`')

        info = self.url+self.INFO
        resp = req.get(info)
        if resp.ok:
            logging.info(f'Received correct response from `{info}`')
        else:
            err_msg = f'Response from `{info}` is not ok'
            logging.warning(err_msg)
            raise ValueError(err_msg)

    def get_response(self, url: str) -> req.Response:
        """Return response from a request.

        Parameters
        ----------
        url : str
            URL to API.

        Returns
        -------
        req.Response
            Response object.

        Raises
        ------
        req.exceptions.ConnectionError
            Response raises ConnectionError.

        req.exceptions.Timeout
            Connection times out.
        """
        logging.debug(f'Trying url {url}')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0',
            'Content-Type': 'application/json'}
        try:
            resp = self.session.get(url, headers=headers, timeout=40)
            resp.raise_for_status()
        # todo: místo SystemExit nějaká jiná exception
        except req.HTTPError as err:
            logging.error(err)
            raise SystemExit(err)
        except req.exceptions.ConnectionError as err:
            logging.error(err)
            raise SystemExit(err)
        except req.exceptions.Timeout as err:
            logging.error(err)
            raise SystemExit(err)

        return resp

    def _check_version(self) -> None:
        """Check that the Kramerius API version is correct.

        Raises
        ------
        ValueError
            Kramerius API returns a version different from [57].x.x.
        """
        info = self.url + self.INFO
        resp = self.session.get(info)
        if not resp.ok:
            # if the versions do not match, we use wrong urls, we expect 404 to be returned
            err_msg = f'Kramerius API version probably does not match the set version ({self.VER.value}). Response code {resp.status_code}.'
            logging.error(err_msg)
            raise SystemExit(err_msg)

        ver = resp.json()['version']
        if ver[0] == self.VER.value:
            logging.info(
                f'Set API version ({self.VER}) matches Kramerius API version ({ver})')
        else:
            msg = f'Expected version {self.VER.value}.x.x, got {ver}'
            logging.error(msg)
            raise ValueError(msg)

    def _find_children(self, uuid: str):
        raise NotImplementedError("Subclass needs to define this.")

    def _find_node_details(self, node):
        raise NotImplementedError("Subclass needs to define this.")

    def dfs(self, parent_uuid: str, model: str, par_id: str, prog_bar: bool) -> None:
        """Perform DFS to find children.

        Kramerius versions differ in requests and responses to 
        find children and details.

        In V5, it is enough to send a request for _children_.
        Each child has information about `model` and page number.

        In V7, we have to first send a request for a list of children.
        Then, we have to ask for details of each child.

        Parameters
        ----------
        parent_uuid : str
            UUID of the parent node.
        model : str
            `model` parameter of the parent node.
        par_id : str
            Key to the parent node.
            Keys are made by concatenating volume/issue/page number.
        """
        children = self._find_children(parent_uuid)

        if len(children) == 0:
            return  # we could also check that model == 'page' or 'article'

        logging.info(
            f'Found {len(children)} children of {model} `{par_id}` ({parent_uuid})')
        for child in children:
            child_uuid = child['pid']
            child_model, child_title = self._find_node_details(child)
            child_id = par_id + self.sep + child_title

            self.tree.add_edge(par_id, child_id)
            self.tree.nodes[child_id]['model'] = child_model
            self.tree.nodes[child_id]['uuid'] = child_uuid

            logging.info(
                f"Adding edge between `{par_id}` and `{child_id}` ({model}--{child_model})")

            self.dfs(child_uuid, child_model, child_id, prog_bar)
            if prog_bar and child_model == 'periodicalvolume':
                self.progress_bar.update(1)
        return

    def dfs_with_clb_tree(self, parent_uuid: str, model: str, par_id: str, clb_tree: nx.DiGraph, clb_node) -> None:
        # todo: complete implementation
        raise NotImplementedError
        children = self._find_children(parent_uuid)

        if len(children) == 0:
            return  # we could also check that model == 'page'

        clb_succ = set(clb_tree.successors(clb_node))
        for child in children:
            child_uuid = child['pid']
            child_model, child_title = self._find_node_details(child)
            child_id = par_id + self.sep + child_title
            # TODO: vyřešit, když chybí issue
            if child_id in clb_succ:

                self.tree.add_edge(par_id, child_id)
                self.tree.nodes[child_id]['model'] = child_model
                self.tree.nodes[child_id]['uuid'] = child_uuid

                logging.info(
                    f"Adding edge between `{par_id}` and `{child_id}` ({model}--{child_model})")
                self.dfs_with_clb_tree(
                    child_uuid, child_model, child_id, clb_tree, child_id)

    def return_tree(self) -> nx.DiGraph:
        """Return the downloaded tree.
        Intended to be passed to a `Periodical` object. 

        Returns
        -------
        nx.DiGraph
            The downloaded tree.
        """
        return self.tree

    def count_vols_to_dwn(self, uuid: str) -> None:
        """Number of volumes (= children of periodical/root) to be downloaded.

        Parameters
        ----------
        uuid : str
            UUID of a unit, usually a periodical.
        """
        vols_to_dwn = len(self._find_children(uuid))
        logging.info(f'Found {vols_to_dwn} volumes to download')
        self.vols_to_dwn = vols_to_dwn

    def create_progress_bar(self, desc: str) -> None:
        """Create a `tqdm` progress bar.

        Raises
        ------
        ValueError
            There are no volumes to download.
        """
        if self.vols_to_dwn == 0:
            raise ValueError(
                'Zero volumes to download. Call `count_vols_to_dwn` first.')

        self.progress_bar = tqdm(desc=desc,
                                 total=self.vols_to_dwn,
                                 bar_format="{l_bar}{bar:20} [{n_fmt}/{total_fmt} volumes]")


class KramAPIv7(KramAPIBase):
    """Class for Kramerius API version 7.

    Attributes
    ----------
    url, sep, tree, INFO, VER
        See superclass.

    ITEMS, STRUCT, DETAILS : str
        Request URLs. For more details, see
        https://k7.inovatika.dev/search/openapi/client/v7.0/index.html
        https://github.com/ceskaexpedice/kramerius/wiki/Kramerius-REST-API-verze-7.0
        https://github.com/ceskaexpedice/kramerius/blob/master/installation/solr-9.x/search/conf/managed-schema
        https://docs.google.com/spreadsheets/d/1DoDnSIGPqPnYbb0U2RSNLKm9eAY2FQNimJyTPeQsC2A/edit?gid=0#gid=0

    """
    CHILDREN = '/search/api/client/v7.0/search?fl=pid,model,title.search&q=own_parent.pid:'
    VER = KramVer.V7

    def __init__(self, url: str, sep='/') -> None:
        super().__init__(url, sep)

    def _make_children_url(self, uuid: str) -> str:
        """Create URL for a request for children.

        The maximal number of returned children is 4 000 (default by Kramerius).

        Parameters
        ----------
        uuid : str
            UUID.

        Returns
        -------
        str
            Link to a children request.
        """
        # quotes have to a part of the URL
        return self.url+self.CHILDREN+f'"{uuid}"&rows=4000&sort=rels_ext_index.sort asc'

    def _find_children(self, uuid: str) -> list[dict[str, str]]:
        """Find children of a given UUID (JSON request).

        The maximal number of returned children is 4 000 (default by Kramerius).

        Parameters
        ----------
        uuid : str
            UUID.

        Returns
        -------
        list[dict[str, str]]
            List of dictionaries in the form
            `{'pid':___, 'model':___, 'title.search':___}`
        """
        req_url = self._make_children_url(uuid)
        resp = self.get_response(req_url)
        children = resp.json()['response']['docs']
        if len(children) == 4_000:
            logging.warning(
                'Maximal number of rows in a response reached (4 000)')
        return children

    def _find_node_details(self, node: dict[str, str]) -> tuple[str, str]:
        """Make a request for details about a UUID.

        Parameters
        ----------
        node : dict[str, str]
            A node in the format `{'pid':___, 'model':___, 'title.search':___}`

        Returns
        -------
        tuple[str, str]
            `model` and `title.search` parameters from Kramerius.
        """
        try:
            title = node['title.search']
        except KeyError:
            default_tit_search = 'no_title_search'
            logging.warning(
                f'No `title.search` parameter found, using `{default_tit_search}` ({node["pid"]})')
            title = default_tit_search

        return (node['model'], title)


class KramAPIv5(KramAPIBase):
    """Class for Kramerius API version 5.

    Attributes
    ----------
    url, sep, tree, INFO, VER
        See superclass.

    ITEM, CHILDREN : str
        Request URLs. For more detail, see
        https://github.com/ceskaexpedice/kramerius/wiki/ClientAPIDEV

    """

    INFO = '/search/api/v5.0/info'
    ITEM = '/search/api/v5.0/item/'
    CHILDREN = '/children'
    VER = KramVer.V5
    MODEL_TITLE_DICT = {
        # model : title
        # TODO: podpora pro `article` (eg. https://vufind.ucl.cas.cz/Record/002973863)
        'periodicalvolume': 'volumeNumber',
        'periodicalitem': 'partNumber',
        'page': 'pagenumber'
    }

    def __init__(self, url: str, sep='/') -> None:
        super().__init__(url, sep)

    def _make_children_url(self, uuid: str) -> str:
        """Create URL for a children request.

        Parameters
        ----------
        uuid : str
            UUID.

        Returns
        -------
        str
            Link to a children request.
        """
        return self.url+self.ITEM+uuid+self.CHILDREN

    def _find_children(self, uuid: str) -> list[dict]:
        """Find children of a given UUID (JSON request).

        Parameters
        ----------
        uuid : str
            UUIS

        Returns
        -------
        list[dict]
            List of children in format
            `{'pid':___, 'model':___, 'details':{'volumeNumber':___, 'year':___}}`
        """
        url = self._make_children_url(uuid)
        resp = self.get_response(url)
        lst = []
        if len(resp.json()) == 0:
            return lst  # empty
        for child in resp.json():
            if child['model'] in self.MODEL_TITLE_DICT:
                d = {
                    'pid': child['pid'],
                    'model': child['model'],
                    'details': child['details']
                }
                # do not include `internalpart` etc (see eg. https://ndk.cz/periodical/uuid:f037984f-200b-402d-94c3-8df539168e78)
                lst.append(d)
        return lst

    def _find_node_details(self, node: dict) -> tuple[str, str]:
        """Return a model and a title of a UUID.

        Parameters
        ----------
        node : dict
            Node as returned by API.
            It has the following structure.
            `{'pid':___, 'model'___, 'details':{'volumeNumber':___, 'year': ___}}`


        Returns
        -------
        tuple[str, str]
            Model, title (= page/issue/volume number).
        """
        model = node['model']
        details = node['details']
        if model not in self.MODEL_TITLE_DICT:
            # asi to bude chtít udělat nějaké uuid pro tenhle případ, abych vždycyky měl strom
            return (model, 'n_not_found')

        title = details[self.MODEL_TITLE_DICT[model]].strip()
        return (model, title)


class Periodical:
    """Information about a periodical

    Attributes
    ---------
    name : str
        Name of a periodical.
    uuid : str
        A unique identifier of a periodical from a digital library.
    library : str
        The library that digitized the periodical.
    kramerius_ver : str
        Kramerius version running in the library.
    url : str
        The base URL of the library. Do not use URL with '/' at the end.
    api_url : str
        The Kramerius API URL. Do not use URL with '/' at the end.
    tree : networkx.DiGraph
        The tree of the digited periodical.
        Keys are made by concatenating volume/issue/page number.
    id_sep : str
        Separator used in keys in the tree, by default '/'.
    root : str
        Root ID, by default 'root'.
    link_uuid : str
        Part of URL linking to a particular UUID, by default 'uuid'.
    max_depth : int
        Maximum depth of the downloaded tree (zero-based counting), by default 3.
    """
    # TODO: uložit ISSN, pokud je dostupné (z Krameria snad ano)

    def __init__(self,
                 name: str,
                 uuid: str,
                 library: str,
                 kramerius_ver: str,
                 url: str,
                 api_url: str,
                 tree=nx.DiGraph(),
                 id_sep='/',
                 root='root',
                 link_uuid='uuid',
                 clb_tree=nx.DiGraph(),  # todo: document
                 max_depth=3
                 ):
        self.name = name
        self.uuid = uuid
        self.library = library
        self.kramerius_ver = kramerius_ver
        self.url = url
        self.api_url = api_url
        self.tree = tree
        self.id_sep = id_sep
        self.root = root
        self.link_uuid = link_uuid
        self.clb_tree = clb_tree
        self.max_depth = max_depth

        self._check_url()

        logging.info(f"Loaded periodical {self}")

    def _select_KramAPI(self) -> None:
        """Select a Kramerius API version.

        Raises
        ------
        Exception
            Only V7 and V5 is supported
        """
        if self.kramerius_ver == KramVer.V7.value:
            self.api = KramAPIv7(self.api_url)
        elif self.kramerius_ver == KramVer.V5.value:
            self.api = KramAPIv5(self.api_url)
        else:
            raise Exception('Only V7 and V5 is supported')

    def _check_url(self):
        """Check if the URL format is correct.

        Raises
        ------
        ValueError
            URL should not end with `/`
        """
        if self.url[-1] == '/':
            raise ValueError('URL should not end with `/`.')

    def __str__(self) -> str:
        return f"{self.name} UUID={self.uuid}, lib={self.library}, url={self.url}, ver={self.kramerius_ver}, api_url={self.api_url}"

    def save_tree(self, path: str) -> None:
        """Save the tree to a JSON file.
        The format is `tree_data` from networkx. If the the graph/tree is not tree, the format is `node_link_data` and a warning is logged.

        Parameters
        ----------
        path : str
            Path to a file to write to. It is rewritten on each save.
        """
        with open(path, 'w') as f:
            if not nx.is_tree(self.tree):
                logging.warning(
                    'Not a tree! Saving using `node_link_data` format')
                graph = nx.node_link_data(
                    self.tree, edges='edges')  # type: ignore
            else:
                graph = nx.tree_data(self.tree, root=self.root)
            json.dump(graph, f, indent='\t')

        logging.info(
            f'Nodes={self.tree.number_of_nodes()} Edges={self.tree.number_of_edges()}')
        logging.info(
            f"Tree saved to {path}")
        return

    def save(self, path: str) -> None:
        """Save the object parameters to path in JSON.

        Parameters
        ----------
        path : str
            Path to save location.
        """
        if not nx.is_tree(self.tree):
            logging.warning(
                'Not a tree! Saving using `node_link_data` format')
            graph = nx.node_link_data(
                self.tree, edges='edges')  # type: ignore
        else:
            graph = nx.tree_data(self.tree, root=self.root)
        logging.info(
            f'Nodes={self.tree.number_of_nodes()} Edges={self.tree.number_of_edges()}')

        params = {
            'name': self.name,
            'uuid': self.uuid,
            'library': self.library,
            'kramerius_ver': self.kramerius_ver,
            'url': self.url,
            'api_url': self.api_url,
            'tree': graph,
            'id_sep': self.id_sep,
            'root': self.root,
            'link_uuid': self.link_uuid
        }
        with open(path, 'w') as f:
            json.dump(params, f, indent='\t', ensure_ascii=False)
        logging.info(f'Saved to {path}')
        return

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

    def complete_download(self, prog_bar: bool) -> None:
        """Use depth-first search to find children starting 
        from UUID of a periodical.
        """
        self._select_KramAPI()
        if prog_bar:
            self.api.count_vols_to_dwn(self.uuid)
            self.api.create_progress_bar(self.name)

        self.api.dfs(self.uuid, 'periodical', self.root, prog_bar)

        self.tree = self.api.return_tree()
        self.check_tree_depth()

    def check_tree_depth(self) -> None:
        """Check that the downloaded tree is not too deep.

        We expect at most four layers: periodical -- volume -- issue -- page/article.

        Raises
        ------
        ValueError
            Tree is too deep
        """
        if len(self.tree) <= 2:
            raise ValueError('No tree to check!')
        try:
            self._check_tree_depth(self.root, self.max_depth, 0)
        except ValueError:
            logging.warning('Tree is too deep!')
        return

    def _check_tree_depth(self, node: str, max_depth: int, depth: int) -> None:
        """Use dfs to check that the downloaded tree is not too deep.


        Parameters
        ----------
        node : str
            Node ID.
        max_depth : int
            Maximum tree depth.
        depth : int
            Current depth.

        Raises
        ------
        ValueError
            Tree is too deep (`depth` > `max_depth`).
        """
        children = list(self.tree.successors(node))
        if depth > max_depth:
            raise ValueError(f'Tree is too deep ({depth=} > {max_depth=})')

        if len(children) == 0:
            return

        for item in children:
            self._check_tree_depth(item, max_depth, depth+1)
        return

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

    def link(self, volume: str | None, issue: str | None, page: str | None) -> str | None:
        """Try making a URL to a given page.

        Parameters
        ----------
        volume : str | None
            Volume number.
        issue : str | None
            Issue number.
        page : str | None
            Page number.

        Returns
        -------
        str | None
            Link to a page or `None` if the path leads nowhere.
        """
        # todo: asi by bylo lepší hodit záznamy, ke kterým jsem okamžitě nenašel uuid do nějakého seznamu
        # a tenhle seznam projet nějakou fcí, která to zkusí znova nalinkovat a diagnostikovat proč první linkování nevyšlo
        # prostě tu funkci rozsekat
        path_to_page = self._make_path_to_node(
            [self.root, volume, issue, page])
        link_to_page = self._link(path_to_page)

        # It can happen that there is no `issue` in člb record, but there is an issue number from Kramerius.
        # E.g. we have 773q '25<100' but from Kramerius we have '25/2/100'.
        # This should only happen if the volume has one issue, so we can
        # check that volume has only one child and try path '25:{the only child of vol}<page'
        if self._volume_has_one_issue(volume):
            new_issue = self._find_only_child_of_vol(volume)
            new_path_to_page = self._make_path_to_node(
                [self.root, volume, new_issue, page])
            logging.info(
                f'Node `{path_to_page}` not found, but it has only one child. Trying path with the one child `{new_path_to_page}`')
            link_to_page = self._link(new_path_to_page)
        if link_to_page is None:
            logging.warning(f'🔴 Node `{path_to_page}` was not found!')
            return None
        else:
            logging.info(f'🟢 Node `{path_to_page}` found: {link_to_page}')
            return link_to_page

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
        path_to_vol = self._make_path_to_node([self.root, volume])
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
        path_to_vol = self._make_path_to_node([self.root, volume])
        children = list(self.tree.successors(path_to_vol))
        if len(children) != 1:
            raise ValueError('More than one child!')
        issue_path = children[0]
        issue = issue_path.split('/')[-1]
        return issue

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

    def build_clb_tree(self, path: str) -> None:
        """Build a ČLB tree from MARC 773q records.

        Keys are made by concatenating volume/issue/page.

        Parameters
        ----------
        path : str
            Path to a CSV file with 773q records.
        """
        # todo: uložit tenhle strom do jsonu
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                for loc in row['location'].split(';'):
                    volume, issue, page = Parse773.parse_location(loc)
                    if issue is None:
                        issue = 'no_issue'.upper()  # TODO: unify
                    # modify records HERE
                    vol_iss_pg = Parse773.normalize(volume, issue, page)
                    self._add_clb_record(*vol_iss_pg)
        logging.info(
            f'Built ČLB tree with Nodes={self.clb_tree.number_of_nodes()}, Edges={self.clb_tree.number_of_edges()}')
        return

    def _add_clb_record(self, volume: str | None, issue: str | None, page: str | None) -> None:
        """Add a ČLB MARC record to a ČLB tree.

        Parameters
        ----------
        volume : str | None
            Volume number.
        issue : str | None
            Issue number.
        page : str | None
            Page number.

        Raises
        ------
        ValueError
            All inputs should be `str`, not `None`.
        """
        # issue should not be be None, but something that identifies vols without issue
        if None in [volume, issue, page]:
            raise ValueError(
                f'There should be no `None`! {volume=}, {issue=}, {page=}')
        l = [self.root, volume, issue, page]
        for i in range(1, len(l)):
            parent = self._make_path_to_node(l[:i])
            child = self._make_path_to_node(l[:i+1])
            self.clb_tree.add_edge(parent, child)
            self.clb_tree.nodes[child]['number'] = l[i]
            logging.info(f'Adding edge to ČLB tree: `{parent}`--`{child}`')
        return


def load_periodical(path: str) -> Periodical:
    """Load class `Periodical` from JSON.

    Parameters
    ----------
    path : str
        Path to a JSON file.

    Returns
    -------
    Periodical
        Periodical class.
    """
    with open(path) as f:
        json_per = json.load(f)
    json_per['tree'] = nx.tree_graph(json_per['tree'])
    per = Periodical(**json_per)
    return per
