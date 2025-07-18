import DwnKramerius as dwn

frenstat = dwn.Periodical(
    uuid='uuid:a6e39600-4d55-11e5-8851-005056827e51',
    library='mzk',
    kramerius_ver='v7',
    url='https://www.digitalniknihovna.cz/mzk/',
)

driver = dwn.setup_driver(headless=True)

frenstat.find_children('', frenstat.uuid, driver, 0)
frenstat.save_tree(
    '/home/clb/dev/link_kramerius/kramerius_dwn_data/frenstat_complete.json')

dwn.teardown(driver)
