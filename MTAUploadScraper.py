import os
from random_user_agent.user_agent import UserAgent
import requests
from bs4 import BeautifulSoup
import logging
from multiprocessing import Pool
import re
import urllib.parse

class MTAUploadScraper():
    def __init__(self, debug=False):
        self.url = "https://mtaupload.com/maplist/?cp="
        self.debug = debug
        self.user_agent = UserAgent()
        self.logger = logging.getLogger(__name__)
        self.unreachable_links = []

        self.page_count = self.debug and 1 or (self._get_page_count() or 1)

    def _ensure_savedir(self) -> None:
        try:
            os.makedirs("maps")
        except FileExistsError:
            pass

    def _fetch_data(self, url) -> requests.Response:
        headers = {
            'User-Agent': self.user_agent.get_random_user_agent()
        }
        self.logger.debug(f"Using user agent: {headers['User-Agent']}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response

    def _get_page_count(self) -> int | None:
        try:
            response = self._fetch_data(f"{self.url}1")
            soup = BeautifulSoup(response.content, 'html.parser')
            page_numbers = soup.find_all(class_='page-numbers')

            return int(page_numbers[-2].text)
        except Exception as e:
            self.logger.error(e)
            return None
    
    def _add_prefix_brackets(self, slug, file_name):
        # Extracting prefix from slug
        match = re.match(r'^([a-zA-Z]+)-', slug)
        if match:
            prefix = match.group(1)
            # Adding brackets around prefix in filename
            new_file_name = re.sub(r'^' + re.escape(prefix), '[' + prefix.upper() + ']', file_name, count=1)
            new_file_name = re.sub(r'^' + re.escape(prefix.upper()), '[' + prefix.upper() + ']', new_file_name, count=1)
            return new_file_name
        else:
            return file_name
        
    def _process_map(self, index) -> None:
        link = self.download_links[index]

        try:
            response = self._fetch_data(link['data-downloadurl'])
            slug = link['data-downloadurl'].split('/')[-2]

            disposition = response.headers['content-disposition']
            file_name = urllib.parse.unquote(re.findall("filename=(.+)", disposition)[0].strip('"'))

            fixed_file_name = self._add_prefix_brackets(slug, file_name)

            with open(f"maps/{fixed_file_name}", 'wb') as f:
                f.write(response.content)

            self.logger.info(f"Downloaded {fixed_file_name}")
        except requests.exceptions.RequestException as e:
            self.unreachable_links.append(link['data-downloadurl'])
            self.logger.error(f"Failed to download {link['data-downloadurl']}")
        except Exception as e:
            self.logger.error(e)
        
    def _process_links(self) -> None:
        pool = Pool()
        pool.map(self._process_map, range(len(self.download_links)))
        pool.close()
        pool.join()
        
    def process(self) -> None:
        self._ensure_savedir()

        self.logger.info(f"Pages to process: {self.page_count}")
        for i in range(1, self.page_count + 1):
            self.logger.info(f"Processing page {i}")
            try:
                response = self._fetch_data(f"{self.url}{i}")
                soup = BeautifulSoup(response.content, 'html.parser')

                self.download_links = soup.find_all('a', attrs={'data-downloadurl': True})
                self._process_links()
            except Exception as e:
                self.logger.error(e)
                continue

        if len(self.unreachable_links) > 0:
            with open("unreachable_links.txt", 'w') as f:
                for link in self.unreachable_links:
                    f.write(link + '\n')

        self.logger.info("Done")