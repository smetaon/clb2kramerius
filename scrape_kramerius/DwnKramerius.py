from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import networkx as nx
import json
import logging


def setup_driver(headless: bool = False) -> webdriver.Firefox:
    """    
    Setup the browser for scraping the digital library.

    Args:
        headless (bool): Headless or visible browser 

    Returns:
        webdriver.Firefox: A Selenium driver (browser)
    """
    options = Options()
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    return driver


def teardown(driver: webdriver.Firefox) -> None:
    """
    Quit the browser.

    Args:
        driver (webdriver.Firefox): A Selenium driver (browser)
    """
    driver.quit()


def read_metadata(driver: webdriver.Firefox) -> str:
    """
    Find and download the `children` metadata on a Kramerius website

    Args:
        driver (webdriver.Firefox): A Selenium driver (browser)

    Returns:
        str: The children metadata (usually JSON)
    """

    # Find the metadata button
    metadata_button_class_name = 'app-metadata-controls'
    WebDriverWait(driver, timeout=2).until(
        EC.presence_of_element_located((By.CLASS_NAME, metadata_button_class_name)))
    control_div = driver.find_element(
        by=By.CLASS_NAME, value=metadata_button_class_name)
    buttons = control_div.find_elements(by=By.TAG_NAME, value='mat-icon')
    # no useful identifier to identify this button 🙁
    metadata_button = buttons[-1]

    # Show the metadata overlay
    metadata_button.click()

    # Show the metadata selector
    mods_button_class_name = 'app-dialog-title'
    WebDriverWait(driver, timeout=2).until(
        EC.presence_of_element_located((By.CLASS_NAME, mods_button_class_name)))
    mods_button = driver.find_element(
        by=By.CLASS_NAME, value=mods_button_class_name)
    mods_button.click()

    dropdown_sel_class_name = 'app-dropdown-item'
    WebDriverWait(driver, timeout=2).until(
        EC.presence_of_element_located((By.CLASS_NAME, dropdown_sel_class_name)))
    dropdown_selectors = driver.find_elements(
        by=By.CLASS_NAME, value=dropdown_sel_class_name)
    # no useful identifier to identify this button 🙁
    children_button = dropdown_selectors[-2]

    # Show the children metadata
    children_button.click()
    code_tag_name = 'code'
    WebDriverWait(driver, timeout=2).until(
        EC.presence_of_element_located((By.TAG_NAME, code_tag_name)))
    children_metadata = driver.find_element(
        by=By.TAG_NAME, value=code_tag_name)
    return children_metadata.text


class Periodical:
    """
    Information about a periodical

    Attributes
    ---------
    name : str
        Name of a periodical
    uuid : str
        A unique identifier of a periodical from a digital library.
    library : str
        The library that digitized the periodical.
    kramerius_ver : str
        Kramerius version running in the library.
    url : str
        The base url of the library
    tree : networkx.DiGraph()
        The tree of the digited periodical.

        The layers of the tree are:
            periodical/volume (optional)/issue (optional)/page
        Keys are UUIDs.

    Methods
    -------
    save_tree: 
        Save the tree to a file
    make_url: 
        Generate a url to a unit (issue/volume)
    find_children: 
        Perform DFS to find UUIDs of children
    """

    # TODO: Možná nejsou atributy `library` a `kramerius_ver` vůbec nutné

    def __init__(self, name: str, uuid: str, library: str, kramerius_ver: str, url: str):
        self.name = name
        self.uuid = uuid
        self.library = library
        self.kramerius_ver = kramerius_ver
        self.url = url
        self.tree = nx.DiGraph()

        logging.info(f"Loaded periodical {self}")
        # Add root
        self.tree.add_node(self.uuid)
        self.tree.nodes[self.uuid]['model'] = 'periodical'
        self.tree.nodes[self.uuid]['n'] = -1

    def __str__(self) -> str:
        return f"{self.name} UUID={self.uuid}, lib={self.library}, url={self.url}, ver={self.kramerius_ver}"

    def save_tree(self, path: str) -> None:
        """
        Save tree to a JSON file.
        The format is `tree_data` from networkx. If the the graph/tree is not tree, the format is `node_link_data` and a warning

        Args:
            path (str): Path to a file to write to. It is rewritten on each save.
        """
        with open(path, 'w') as f:
            if not nx.is_tree(self.tree):
                logging.warning(
                    'Not a tree! Saving using `node_link_data` format')
                graph = nx.node_link_data(
                    self.tree, edges='edges')  # type: ignore
            else:
                graph = nx.tree_data(self.tree, root=self.uuid)
            json.dump(graph, f, indent='\t')

        logging.info(
            f'Nodes={self.tree.number_of_nodes()} Edges={self.tree.number_of_edges()}')
        logging.info(
            f"Tree saved to {path}")
        return

    def make_url(self, unit: str, uuid: str) -> str:
        """
        Generate a url to a unit (issue/volume)

        Args:
            unit (str): A "unit" in the tree (issue/volume/page)
            uuid (str): UUID of the unit

        Returns:
            str: A link to the unit on the Kramerius website
        """
        return self.url + unit + '/' + uuid

    def find_children(self, model: str, uuid: str, driver: webdriver.Firefox) -> None:
        """
        Perform a depth-first search to find UUIDs from metadata

        Args:
            model (str): A keyword from Kramerius, distinguishes periodicals / supplements / pages etc. We want to stop the recursion when we get to "page" 
            uuid (str): UUID of a unit
            driver (webdriver.Firefox) : A Selenium driver (browser)

        """
        if model == 'page':
            return
        if model in ['periodicalitem', 'supplement']:
            unit = 'view'
        else:
            unit = 'periodical'

        driver.get(self.make_url(unit, uuid))
        response = json.loads(read_metadata(driver))

        logging.info(
            f"Found {len(response['response']['docs'])} children of {model} {uuid}")

        for item in response['response']['docs']:
            child_model = item['model']
            child_uuid = item['pid']

            self.tree.add_edge(uuid, child_uuid)
            self.tree.nodes[child_uuid]['model'] = child_model
            self.tree.nodes[child_uuid]['n'] = item['title.search']

            logging.info(
                f"Adding edge between {uuid=} and {child_uuid=}, {model}--{child_model}")
            self.find_children(child_model, child_uuid, driver)
        return
