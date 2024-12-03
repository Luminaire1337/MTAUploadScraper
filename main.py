import logging
import sys
from MTAUploadScraper import MTAUploadScraper

if __name__ == "__main__":
    sys.setrecursionlimit(10**6)
    logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%d/%b/%Y %H:%M:%S",
            stream=sys.stdout)

    scraper = MTAUploadScraper()
    scraper.process()