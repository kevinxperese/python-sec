import requests
import xml.etree.ElementTree as ET

from typing import List
from typing import Union
from datetime import date

from pysec.parser import EDGARParser

# https://www.sec.gov/cgi-bin/srch-edgar?text=form-type%3D%2810-q*+OR+10-k*%29&first=2020&last=2020

class EDGARQuery():

    def __init__(self):
        """Initalizes the EDGAR Client with the different endpoints used."""        

        # base URL for the SEC EDGAR browser
        self.sec_url = "https://www.sec.gov"
        self.sec_archive = "https://www.sec.gov/Archives/edgar/data"
        self.sec_cgi_endpoint = "https://www.sec.gov/cgi-bin"
        self.browse_service = "https://www.sec.gov/cgi-bin/browse-edgar"
        self.search_service = 'srch-edgar'
        self.cik_lookup = 'cik_lookup'
        self.mutal_fund_search = 'series'

        self.parser_client = EDGARParser()

    def company_directories(self, cik: str) -> dict:
        """Grabs all the filing directories for a company.

        Overview:
        ----
        Companies often file many SEC disclosures, so this endpoint
        makes grabbing all the endpoints associated with a company
        easy, by only requiring the CIK number.

        Arguments:
        ----
        cik {str} -- The company CIK number, defined by the SEC.

        Returns:
        ----
        dict -- A Dictionary containing the directory filings path.

        Usage:
        ----
            >>> edgar_client = EDGARQuery()
            >>> company_filings = edgar_client.company_directories(cik='1265107')
            [
                {
                    'last-modified': '2019-07-02 12:27:42',
                    'name': '000000000019010655',
                    'size': '',
                    'type': 'folder.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000000000019010655/index.json'
                },
                {
                    'last-modified': '2019-07-01 17:17:26',
                    'name': '000110465919038688',
                    'size': '',
                    'type': 'folder.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000110465919038688/index.json'
                }
            ]
        """

        # Build the URL.
        url = self.sec_archive + "/{cik_number}/index.json".format(
            cik_number=cik
        )

        cleaned_directories = []
        directories = requests.get(url=url).json()

        # Loop through each item.
        for directory in directories['directory']['item']:

            # Create the URL.
            directory['url'] = self.sec_archive + "/{cik_number}/{directory_id}/index.json".format(
                cik_number=cik,
                directory_id=directory['name']
            )

            directory['filing_id'] = directory.pop('name')
            directory['last_modified'] = directory.pop('last-modified')

            cleaned_directories.append(directory)

        return cleaned_directories

    def company_directory(self, cik: str, filing_id: str) -> dict:
        """Grabs all the items from a specific filing.

        Overview:
        ----
        The SEC organizes filings by CIK number which represent a single
        entity. Each entity can have multiple filings, which is identified
        by a filing ID. That filing can contain multiple items in it.

        This endpoint will return all the items from a specific filing that
        belongs to a single company.

        Arguments:
        ----
        cik {str} -- The company CIK number, defined by the SEC.

        filing_id {str} -- The ID of filing to pull.

        Returns:
        ----
        dict -- A Dictionary containing the filing items.

        Usage:
        ----
            >>> edgar_client = EDGARQuery()
            >>> company_filings = edgar_client.company_directory(cik='1265107', filing_id='000110465919038688')
            [
                {
                    'item_id': '0001104659-19-038688.txt',
                    'last_modified': '2019-07-01 17:17:26',
                    'size': '',
                    'type': 'text.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000110465919038688/0001104659-19-038688.txt'
                },
                {
                    'item_id': 'a19-12321_2425.htm',
                    'last_modified': '2019-07-01 17:17:26',
                    'size': '37553',
                    'type': 'text.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000110465919038688/a19-12321_2425.htm'
                }
            ]
        """

        url = self.sec_archive + "/{cik_number}/{filing_number}/index.json".format(
            cik_number=cik,
            filing_number=filing_id
        )

        cleaned_items = []
        directory = requests.get(url=url).json()

        for item in directory['directory']['item']:

            item['url'] = self.sec_archive + "/{cik_number}/{directory_id}/{file_id}".format(
                cik_number=cik,
                directory_id=filing_id,
                file_id=item['name']
            )

            item['item_id'] = item.pop('name')
            item['last_modified'] = item.pop('last-modified')
            cleaned_items.append(item)

        return cleaned_items

    def company_filings_by_type(self, cik: str, filing_type: str) -> List[dict]:
        """Returns all the filings of certain type for a particular company.

        Arguments:
        ----
        cik {str} -- The company CIK Number.

        filing_type {str} -- The filing type ID.


        Returns:
        ----
        dict -- A Dictionary containing the filing items.

        Usage:
        ----
            >>> edgar_client = EDGARQuery()
            >>> company_filings = edgar_client.company_directory(cik='1265107', filing_id='000110465919038688')
            [
                {
                    'item_id': '0001104659-19-038688.txt',
                    'last_modified': '2019-07-01 17:17:26',
                    'size': '',
                    'type': 'text.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000110465919038688/0001104659-19-038688.txt'
                },
                {
                    'item_id': 'a19-12321_2425.htm',
                    'last_modified': '2019-07-01 17:17:26',
                    'size': '37553',
                    'type': 'text.gif',
                    'url': 'https://www.sec.gov/Archives/edgar/data/1265107/000110465919038688/a19-12321_2425.htm'
                }
            ]
        """

        # define the endpoint to do filing searches.
        url = self.browse_service

        # Set the params
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': filing_type,
            'output': 'atom'
        }

        # Grab the response.
        response = requests.get(url=url, params=params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def companies_by_state(self, state: str, num_of_companies: int = None) -> List[dict]:
        """Returns all the companies that fall under a given state.

        Arguments:
        ----
        state {str} -- [description]

        Returns:
        ----
        List[dict] -- [description]
        """

        # define the arguments of the request
        search_sic_params = {
            'State': state,
            'Count': '100',
            'action': 'getcompany',
            'output': 'atom'
        }

        response = requests.get(
            url=self.browse_service,
            params=search_sic_params
        )

        # Parse the entries.
        entries = self.parser_client.parse_entries(
            entries_text=response.text,
            num_of_items=num_of_companies
        )

        return entries

    def companies_by_country(self, country: str, num_of_companies: int = None) -> List[dict]:
        """Grabs all the companies that fall under a particular country code.

        Arguments:
        ----
        country {str} -- The country code.

        Keyword Arguments:
        ----
        num_of_companies {int} -- If you would like to limit the number of results, then
            specify the number of companies you want back. (default: {None})

        Returns:
        ----
        List[dict] -- A list of Entry resources.
        """

        # define the arguments of the request
        search_sic_params = {
            'Country': country,
            'Count': '100',
            'action': 'getcompany',
            'output': 'atom'
        }

        # Grab the Response.
        response = requests.get(
            url=self.browse_service,
            params=search_sic_params
        )

        # Parse the entries.
        entries = self.parser_client.parse_entries(
            entries_text=response.text,
            num_of_items=num_of_companies
        )

        return entries

    def companies_by_sic(self, sic_code: str, num_of_companies: int = None) -> List[dict]:
        """Grabs all companies with a certain SIC code.

        Returns all companies, that fall under a particular SIC code. The information returned
        by this endpoint depends on the infromation available on the company.

        Arguments:
        ----
        sic_code {str} -- The SIC code for a particular Industry.

        Keyword Arguments:
        ----
        num_of_companies {int} -- If you would like to limit the number of results, then
            specify the number of companies you want back. (default: {None})

        Returns:
        ----
            list[dict] -- A list of companies with the following attributes:

            [
                {
                    "state": "MN",
                    "cik": "0000066740",
                    "last-date": "",
                    "name": "3M CO",
                    "sic-code": "3841",
                    "id": "urn:tag:www.sec.gov:cik=0000066740",
                    "href": "URL",
                    "type": "html",
                    "summary": "<strong>CIK:</strong> 0000066740, <strong>State:</strong> MN",
                    "title": "3M CO",
                    "updated": "2020-04-05T15:21:24-04:00",
                    "atom_owner_only": "URL",
                    "atom_owner_exclude": "URL",
                    "atom_owner_include": "URL",
                    "html_owner_only": "URL",
                    "html_owner_exclude": "URL",
                    "html_owner_include": "URL",
                    "atom_owner_only_filtered_date": "URL",
                    "atom_owner_exclude_filtered_date": "URL",
                    "atom_owner_include_filtered_date": "URL",
                    "html_owner_only_filtered_date": "URL",
                    "html_owner_exclude_filtered_date": "URL",
                    "html_owner_include_filtered_date": "URL",
                }
            ]
        """
        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_sic_params = {
            'Count': '100',
            'SIC': sic_code,
            'Count': '100',
            'action': 'getcompany',
            'output': 'atom'
        }

        # Make the response.
        response = requests.get(
            url=self.browse_service,
            params=search_sic_params
        )

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def ownership_filings_by_cik(self, cik: str, before: Union[str, date] = None, after: Union[str, date] = None) -> List[dict]:
        """Returns all the ownership filings for a given CIK number in a given date range.

        Arguments:
        ----
        cik {str} -- The CIK number of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'CIK': cik,
            'Count': '100',
            'myowner': 'only',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def non_ownership_filings_by_cik(self, cik: str, before: str = None, after: str = None) -> List[dict]:
        """Returns all the non-ownership filings for a given CIK number in a given date range.

        Arguments:
        ----
        cik {str} -- The CIK number of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'CIK': cik,
            'Count': '100',
            'myowner': 'exclude',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def all_filings_by_cik(self, cik: str, before: str = None, after: str = None) -> List[dict]:
        """Returns all the filings (ownership and non-ownership) for a given CIK number in a given date range.

        Arguments:
        ----
        cik {str} -- The CIK number of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'CIK': cik,
            'Count': '100',
            'myowner': 'include',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def ownership_filings_by_company_name(self, company_name: str, before: str = None, after: str = None) -> List[dict]:
        """Returns all the filings ownership for a given company in a given date range.

        Arguments:
        ----
        company_name {str} -- The name of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'company': company_name,
            'Count': '100',
            'myowner': 'only',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def non_ownership_filings_by_company_name(self, company_name: str, before: str = None, after: str = None) -> List[dict]:
        """Returns all the filings non-ownership for a given company in a given date range.

        Arguments:
        ----
        company_name {str} -- The name of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'company': company_name,
            'Count': '100',
            'myowner': 'exclude',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        print(response.url)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries

    def all_filings_by_company_name(self, company_name: str, before: str = None, after: str = None) -> List[dict]:
        """Returns all the filings (ownership and non-ownership) for a given company in a given date range.

        Arguments:
        ----
        company_name {str} -- The name of the company to be queried.

        Keyword Arguments:
        ----
        before {Union[str, date]} -- Represents filings that you want before a certain
            date. For example, "2019-12-01" means return all the filings BEFORE
            Decemeber 1, 2019. (default: {None})

        after {Union[str, date]} -- Represents filings that you want after a certain
            date. For example, "2019-12-01" means return all the filings AFTER 
            Decemeber 1, 2019. (default: {None})

        Returns:
        ----
        List[dict] -- A list of ownership filings.
        """

        # define the endpoint to do filing searches.
        browse_edgar = r"https://www.sec.gov/cgi-bin/browse-edgar"

        # define the arguments of the request
        search_params = {
            'company': company_name,
            'Count': '100',
            'myowner': 'include',
            'action': 'getcompany',
            'output': 'atom',
            'datea': after,
            'dateb': before
        }

        # Make the response.
        response = requests.get(url=self.browse_service, params=search_params)

        # Parse the entries.
        entries = self.parser_client.parse_entries(entries_text=response.text)

        return entries
