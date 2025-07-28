from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import networkx as nx
import json
import logging


def setup_driver(headless: bool = False) -> webdriver.Firefox:
    """Setup the browser for scraping the digital library.

    Parameters
    ----------
    headless : bool, optional
        Headless or visible browser, by default False.

    Returns
    -------
    webdriver.Firefox
        A Selenium driver (browser).
    """
    options = Options()
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    return driver


def teardown(driver: webdriver.Firefox) -> None:
    """Quit the Selenium browser.


    Parameters
    ----------
    driver : webdriver.Firefox
        A Selenium driver (browser).
    """
    driver.quit()


def read_metadata(driver: webdriver.Firefox) -> str:
    """Find and download the `children` metadata on a Kramerius website.

    Parameters
    ----------
    driver : webdriver.Firefox
        A Selenium driver (browser).

    Returns
    -------
    str
        The children metadata (usually JSON).
    """
    wait = WebDriverWait(driver, timeout=5)

    # Find the metadata button
    metadata_button_class_name = 'app-metadata-controls'
    wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, metadata_button_class_name)))
    control_div = driver.find_element(
        by=By.CLASS_NAME, value=metadata_button_class_name)
    buttons = control_div.find_elements(by=By.TAG_NAME, value='mat-icon')
    # no useful identifier to identify this button 🙁
    metadata_button = buttons[-1]

    # Show the metadata overlay
    metadata_button.click()

    # Show the metadata selector
    mods_button_class_name = 'app-dialog-title'
    wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, mods_button_class_name)))
    mods_button = driver.find_element(
        by=By.CLASS_NAME, value=mods_button_class_name)
    mods_button.click()

    dropdown_sel_class_name = 'app-dropdown-item'
    wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, dropdown_sel_class_name)))
    dropdown_selectors = driver.find_elements(
        by=By.CLASS_NAME, value=dropdown_sel_class_name)
    # no useful identifier to identify this button 🙁
    children_button = dropdown_selectors[-2]

    # Show the children metadata
    children_button.click()
    code_tag_name = 'code'
    wait.until(EC.presence_of_element_located((By.TAG_NAME, code_tag_name)))
    children_metadata = driver.find_element(
        by=By.TAG_NAME, value=code_tag_name)
    return children_metadata.text


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
        The base url of the library. Use URL with '/' at the end.
    tree : networkx.DiGraph
        The tree of the digited periodical.

        The layers of the tree are:
            periodical/volume (optional)/issue (optional)/page
        Keys are made by concatenating volume/issue/page number.
    id_sep : str
        Separator used in keys in the tree, by default '/'.
    root : str
        Root ID, by default 'root'.
    link_uuid : str
        Part of URL linking to a particular UUID, by default 'uuid'.

    Methods
    -------
    save_tree:
        Save the tree to a JSON file.
    make_url:
        Generate a URL to a page/issue/volume.
    find_children:
        Perform DFS to find children.
    _check_url:
        Check if the `link_uuid` URL is correct
    save:
        Save the object to a JSON file.
    """

    def __init__(self, name: str, uuid: str, library: str, kramerius_ver: str, url: str, tree=nx.DiGraph(), id_sep='/', root='root', link_uuid='uuid'):
        self.name = name
        self.uuid = uuid
        self.library = library
        self.kramerius_ver = kramerius_ver
        self.url = url
        self.tree = tree
        self.id_sep = id_sep
        self.root = root
        self.link_uuid = link_uuid

        self._check_url()

        logging.info(f"Loaded periodical {self}")
        if self.tree.number_of_nodes == 0:
            # Add a root
            self.tree.add_node(self.root)
            self.tree.nodes[self.root]['model'] = 'periodical'
            self.tree.nodes[self.root]['uuid'] = self.uuid

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
        return f"{self.name} UUID={self.uuid}, lib={self.library}, url={self.url}, ver={self.kramerius_ver}"

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
            'tree': graph,
            'id_sep': self.id_sep,
            'root': self.root,
            'link_uuid': self.link_uuid
        }
        with open(path, 'w') as f:
            json.dump(params, f, indent='\t')
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
        return self.url + self.link_uuid + '/' + uuid

    def find_children(self, model: str, uuid: str, par_id: str, driver: webdriver.Firefox) -> None:
        """Perform a depth-first search to find UUIDs from metadata.

        Parameters
        ----------
        model : str
            A keyword from Kramerius, distinguishes periodicals / supplements / pages etc. We want to stop the recursion when we get to `page`.
        uuid : str
            UUID of a unit.
        par_id : str
            Parent ID, follows the tree structure.
        driver : webdriver.Firefox
            A Selenium driver (browser)
        """
        if model == 'page':
            return

        logging.debug(f'Visiting {self.make_url(uuid)}')
        driver.get(self.make_url(uuid))
        response = json.loads(read_metadata(driver))

        # TODO: parser JSON; verze krameria (resp. MZK a NKP) se liší strukturou vráceného JSONu
        logging.info(
            f"Found {len(response['response']['docs'])} children of {model} `{par_id}`")

        for item in response['response']['docs']:
            child_model = item['model']
            child_uuid = item['pid']
            child_n = item['title.search']  # volume or issue or page number
            child_id = par_id + self.id_sep + child_n

            self.tree.add_edge(par_id, child_id)
            self.tree.nodes[child_id]['model'] = child_model
            self.tree.nodes[child_id]['uuid'] = child_uuid

            logging.info(
                f"Adding edge between `{par_id}` and `{child_id}` ({model}--{child_model})")
            self.find_children(child_model, child_uuid, child_id, driver)
        return

    def link(self, volume: str | None, issue: str | None, page: str | None) -> str | None:
        """Make a URL to a page with given path.

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
            [self.root, volume, issue, page])  # type: ignore
        try:
            page_node = self.tree.nodes[path_to_page]
        except KeyError:
            logging.warning(f'Node `{path_to_page}` was not found!')
            return None
        else:
            return self.make_url(page_node['uuid'])

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
