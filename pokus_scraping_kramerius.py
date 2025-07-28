import requests
import json


class PageInKrameriusMZK:
    """
    Works for Kramerius v7 (MZK) (v5 uses xml)
    """

    def __init__(self, url: str) -> None:
        self.url = url
        page = requests.get(self.url)
        self.data = json.loads(page.text)
        self.assoc_uuids = self._get_assoc_uuids()

    def _get_assoc_uuids(self) -> dict:
        """Extract UUIDs associated with a page (= ancestors).

        Returns:
            dict: UUIDs of page (stránka), issue (číslo), volume (ročník), periodical (periodikum) 
        """
        own_pid_path = self.data['response']['docs'][0]['own_pid_path']
        paths_list = own_pid_path.split('/')
        return {'page': paths_list[3],
                'issue': paths_list[2],
                'volume': paths_list[1],
                'periodical': paths_list[0]
                }

    def assoc_uuids_url(self) -> dict:
        """Generate clickable url to associated UUIDs

        Returns:
            dict: links to page, issue, volume, periodical
        """
        url_periodical = 'https://www.digitalniknihovna.cz/mzk/periodical/'
        url_view = 'https://www.digitalniknihovna.cz/mzk/view/'
        return {
            'page': f'{url_view}{self.assoc_uuids["issue"]}?page={self.assoc_uuids["page"]}',
            'issue': f'{url_view}{self.assoc_uuids["issue"]}',
            'volume': url_periodical + self.assoc_uuids["volume"],
            'periodical': url_periodical + self.assoc_uuids["periodical"]
        }


# Literární noviny
p1 = PageInKrameriusMZK(
    r'https://api.kramerius.mzk.cz/search/api/client/v7.0/search?q=pid:%22uuid:34c6a6b0-1933-11e7-8a18-5ef3fc9ae867%22')
print(p1.assoc_uuids_url())

# Hlasy muzea a archivu ve Frenštátě pod Radhoštěm
p2 = PageInKrameriusMZK(
    r'https://api.kramerius.mzk.cz/search/api/client/v7.0/search?q=pid:%22uuid:aac87ca0-57ae-11e5-81eb-001018b5eb5c%22')
print(p2.assoc_uuids_url())
