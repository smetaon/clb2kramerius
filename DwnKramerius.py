import networkx as nx
import json
import logging
from enum import Enum
import requests as req


class Library(Enum):
    """Library identifier.

    Parameters
    ----------
    Enum : str
        Acronym of a library.
    """
    MZK = 'mzk'


class KramVer(Enum):
    """Kramerius (API) version.

    Parameters
    ----------
    Enum : str
        '7' or '5'
    """
    V7 = '7'
    V5 = '5'


class KramScraperBase():
    """Base class for a scraper which uses Kramerius API.


    Attributes
    ----------
    url : str
        Kramerius API URL. It should not end with `/`.

    sep : str
        Separator used in keys when downloading from Kramerius. By default `/`.

    INFO : str
        String to pass to API to receive info about Kramerius installation.

    VER : KramVer
        Kramerius version.


    Methods
    -------
    _check_url()
        Check that the API URL does not end with `/`.
        Also check that the request for INFO returns 200.

    get_response()
        Get response from a given URL.
        Throw an exception if the response is not ok.

    _check_version()
        Check that the version of API is correct.
    """
    INFO: str
    VER: KramVer

    def __init__(self, url: str, sep='/') -> None:
        self.url = url
        self.sep = sep
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
                f'API URL should not end with `/`, but `{self.url}`')

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
        Exception
            Response is not ok.
        """
        logging.debug(f'Trying url {url}')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0',
            'Content-Type': 'application/json'}
        resp = req.get(url, headers=headers)
        if not resp.ok:
            err_msg = f'Response from {url} is not ok'
            logging.warning(err_msg)
            raise Exception(err_msg)
        return resp

    def _check_version(self) -> None:
        """Check that the Kramerius API version is correct.

        Raises
        ------
        ValueError
            Kramerius API returns a version different from 5|7.x.x.
        """
        info = self.url + self.INFO
        resp = self.get_response(info)
        ver = resp.json()['version']
        if ver[0] == self.VER.value:
            logging.info(
                f'Scraper version ({self.VER}) matches Kramerius API version ({ver})')
        else:
            msg = f'Expected version {self.VER.value}.x.x, got {ver}'
            logging.warning(msg)
            raise ValueError(msg)


class KramScraperV7(KramScraperBase):
    """Scraper class for Kramerius version 7.

    Attributes
    ----------
    url, sep, INFO, VER
        See superclass.

    ITEMS, STRUCT, DETAILS : str
        Request URLs. For more detail, see
        https://k7.inovatika.dev/search/openapi/client/v7.0/index.html
        https://github.com/ceskaexpedice/kramerius/wiki/Kramerius-REST-API-verze-7.0
        https://github.com/ceskaexpedice/kramerius/blob/master/installation/solr-9.x/search/conf/managed-schema
        https://docs.google.com/spreadsheets/d/1DoDnSIGPqPnYbb0U2RSNLKm9eAY2FQNimJyTPeQsC2A/edit?gid=0#gid=0

    tree : nx.DiGraph()
        The tree of the digited periodical.
        Keys are made by concatenating volume/issue/page number.

    Methods
    -------
    _make_struct_url()
        Make a URL for a structure request.

    _make_detail_url()
        Make a URL for a detail request about a given UUID.

    find_children()
        Perform DFS to find children.

    return_tree()
        Return the downloaded tree.
        Intended to be passed to a Periodical object.

    _find_node_details()
        Return a model and a title of a UUID.
    """
    INFO = '/search/api/client/v7.0/info'
    ITEMS = '/search/api/client/v7.0/items/'
    STRUCT = '/info/structure'
    DETAILS = '/search/api/client/v7.0/search?fl=title.search,model&q=pid:'
    VER = KramVer.V7

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self._check_version()
        self.tree = nx.DiGraph()

    def _make_struct_url(self, uuid: str) -> str:
        return self.url+self.ITEMS+uuid+self.STRUCT

    def _make_detail_url(self, uuid: str) -> str:
        # quotes have to a part of the API request
        return self.url+self.DETAILS+f'"{uuid}"'

    def find_children(self, parent_uuid: str, model: str, par_id: str) -> None:
        """Perform DFS to find children.

        To find complete information in V7, we have to perform two steps.
        First, we perform a _structure_ request to find all children of a node.
        Then, we request details for each to node to fill in page and model.
        (In V5, we can do this by simply requesting _children_.)

        Parameters
        ----------
        parent_uuid : str
            UUID of a parent node.
        model : str
            Model paramater of the parent node.
        par_id : str
            Key to the parent node.
            Keys are made by concatenating volume/issue/page number.
        """
        if model == 'page':  # we could also check if it has no children
            return
        par_url = self._make_struct_url(parent_uuid)
        resp = self.get_response(par_url)
        children = resp.json()['children']['own']
        logging.info(
            f'Found {len(children)} children of {model} `{par_id}` ({parent_uuid})')
        for child in children:
            child_uuid = child['pid']
            child_model, child_title = self._find_node_details(child_uuid)
            child_id = par_id + self.sep + child_title

            self.tree.add_edge(par_id, child_id)
            self.tree.nodes[child_id]['model'] = child_model
            self.tree.nodes[child_id]['uuid'] = child_uuid

            logging.info(
                f"Adding edge between `{par_id}` and `{child_id}` ({model}--{child_model})")
            self.find_children(child_uuid, child_model, child_id)
        return

    def return_tree(self) -> nx.DiGraph:
        return self.tree

    def _find_node_details(self, uuid: str) -> tuple[str, str]:
        """Make a request for details about a UUID.

        Parameters
        ----------
        uuid : str
            UUID.

        Returns
        -------
        tuple[str, str]
            `model` and `title.search` parameters from Kramerius.
        """
        detail_url = self._make_detail_url(uuid)
        resp = self.get_response(detail_url)
        # this could vary from library to library
        model = resp.json()['response']['docs'][0]['model']
        title = resp.json()['response']['docs'][0]['title.search']
        return (model, title)


class KramScraperV5(KramScraperBase):
    ...
    INFO = '/search/api/v5.0/info'


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

    Methods
    -------
    _select_scraper():
        Select a Kramerius scraper.
    _check_url():
        Check if the `link_uuid` URL is correct.
    save_tree():
        Save only the tree to a JSON file.
    make_url():
        Generate a URL to a page/issue/volume.
    find_children():
        Perform DFS to find children.
    save():
        Save the object parameters to a JSON file.
        It can be loaded later with the function `load_periodical()`
    make_url():
        Generate a URL to user-friendly issue/volume/page.
    find_children():
        Download the tree from Kramerius.
    link():
        Link a 773q field to a UUID.
    _children_are_page():
        TODO: zdokumentovat, možná je k ničemu
    bfs():
        Not implemented yet.
    """

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
                 link_uuid='uuid'):
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

        self._check_url()

        logging.info(f"Loaded periodical {self}")

    def _select_scraper(self) -> None:
        """Select a Kramerius scraper based on version.

        Raises
        ------
        Exception
            Only V7 is supported
        """
        if self.kramerius_ver == KramVer.V7.value:
            self.scraper = KramScraperV7(self.api_url)
        else:
            raise Exception('Only V7 is supported')

    def _check_url(self):
        """Check if the URL format is correct.

        Raises
        ------
        ValueError
            URL should end with `/`
        """
        if self.url[-1] != '/':
            raise ValueError('URL should end with `/`.')

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
        """Save the object to path in JSON.

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

    def find_children(self) -> None:
        self._select_scraper()
        self.scraper.find_children(self.uuid, 'periodical', self.root)
        self.tree = self.scraper.return_tree()

    def link(self, volume: str | None, issue: str | None, page: str | None) -> str | None:
        """Make a URL to a page with a given path.

        Parameters
        ----------
        volume : str | None
            Volume of a periodical.
        issue : str | None
            Issue 
        page : str | None
            Page of a periodical.

        Returns
        -------
        str | None
            Link to a page or `None` if the path leads nowhere.
        """
        path_to_page = self.id_sep.join(
            filter(None, [self.root, volume, issue, page]))
        try:
            page_node = self.tree.nodes[path_to_page]
        except KeyError:
            path_to_issue = self.id_sep.join(filter(None, [self.root, volume]))
            # It can happen, that
            # a) We did not download issue number from Kramerius
            #   (that happens when there is only one issue in a volume)
            #   but it is present in the člb record.
            # TODO: what if there is no `issue` in člb record, but there is an issue number from Kramerius?
            # e.g. we have 773q '25<100' but from Kramerius we have '25/2/100'
            # this should only happen if the volume has one issue, so we can
            # check that volume has only one child and try path '25:{the only child of vol}<page'
            if self._children_are_page(path_to_issue):
                logging.info(
                    f'Node `{path_to_page}` not found, trying path without issue `{path_to_issue}`')
                return self.link(volume, None, page)
            logging.warning(f'Node `{path_to_page}` was not found!')
            return None
        else:
            page_url = self.make_url(page_node['uuid'])
            logging.info(f'Success! Node `{path_to_page}` found: {page_url}')
            return page_url

    def _children_are_page(self, node: str) -> bool:
        """Check wheter all children of a node have model `page`.

        Parameters
        ----------
        node : str
            A path to a node.

        Returns
        -------
        bool
            `True` if all children have model `page`, `False` otherwise
        """
        try:
            self.tree.nodes[node]
        except KeyError:
            return False
        for succ in self.tree.successors(node):
            if self.tree.nodes[succ]['model'] != 'page':
                return False
        return True

    def bfs(self):
        """
        Něco jako online verze find_children.
        DFS mi najde všechno, tohle by snad šlo udělat tak, aby to našlo jen co potřebuju.
        Tj. dostalo by to 773q z marcu a do šířky by to vyhledávalo.
        Tím bychom dostali z krameria jenom data o článcích, které jsou v člb.
        To by mohlo zrychlit proces stahování. Ale taky nemuselo.
        Taky hodně záleží na tom, jak dobře budu parsovat 773q.
        Je to k zvážení.
        """
        # TODO: implement (?)
        raise NotImplementedError


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
