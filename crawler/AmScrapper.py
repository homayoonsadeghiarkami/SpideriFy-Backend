from asyncio.events import get_event_loop
from ssl import HAS_NEVER_CHECK_COMMON_NAME
import user_agent
import httpx
import asyncio
from selectorlib import Extractor
import json
import csv


class AmScrapper:
    """
    Scrapper Class for Amazon WebSite
    ================================
    Attributes:
    -----------
    * BASE_HEADER
    * NORMALIZED_DATA
    * Product class
    * Review class

    """

    BASE_HEADER = {
        'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image\
        /webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    NORMALIZED_DATA: dict = dict

    class Product:
        """
        Configuration class for Product data
        ++++++++++++++++++++++++++++++++++++
        Attributes:
        +++++++++++
        * URL
        * PRODUCT_EXTRACTOR_OBJ
        * NORMALIZED_PRODUCT_DATA
        """
        URL: str = str
        PRODUCT_EXTRACTOR_OBJ = Extractor.from_yaml_file(
            'crawler/pro-selectors.yml')
        NORMALIZED_PRODUCT_DATA: dict = {}

    class Review:
        """
        Configuration class for Review data
        ++++++++++++++++++++++++++++++++++++
        Attributes:
        +++++++++++
        * URL
        * NORMALIZED_REVIEW_DATA
        * REVIEW_COUNTS
        * REVIEW_EXTRACTOR_OBJ

        """
        URL: str = str
        NORMALIZED_REVIEW_DATA: dict = {}
        REVIEW_COUNTS: int = 0
        REVIEW_EXTRACTOR_OBJ = Extractor.from_yaml_file(
            'crawler/rev-selectors.yml')

    def __init__(self, all_review_url, product_url, headers):
        self.Review.URL = all_review_url
        self.Product.URL = product_url
        if headers is not None:
            self.BASE_HEADER = headers

    def generate_header(self) -> dict:
        """
        This func get the BASE_HEADER and add random user-agent key generated by generate_header package
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Return dict
        """
        # log generating random header user-agent
        n_header = self.BASE_HEADER.copy()
        n_header['user-agent'] = user_agent.generate_user_agent()
        return n_header

    async def requester(self, url: str):
        """
        Return the response of GET request or in case of failure return None
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        This func request the page using GET method with the help of httpx and asyncio
        Parameters
        ++++++++++
        * url : str

        """
        # log : Downloading page URL : url
        async with httpx.AsyncClient() as requester:
            response = await requester.get(url, params=self.generate_header())
        if response.status_code != httpx.codes.OK:
            # log failed to download the page(url)
            if response.status_code >= 500:
                pass
                # log Page was blocked by Amazon.
                # Please try using better proxies.
            return None

        return response

    async def extract_review(self, max_reviews: int) -> bool:
        """
        Return False if Data could not extracted Return True
        if required Data has been extracted
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        This func calls the requester and receive the data, then normalize
        the data and store it in Review class
        Parameters
        ++++++++++
        * max_reviews : int

        """
        # log starting review extraction
        # log creating all URLs (Reviews)
        urls = [
            self.Review.URL+f"&pageNumber={i}" for i in range(1, (max_reviews//10)+1)]
        # log creating event loop (Reviews)
        tasks = []
        for link in urls:
            tasks.append(self.requester(link))
        # log waiting for loop to complete (Reviews)
        data = await asyncio.gather(*tasks, return_exceptions=True)
        # log  closing loop (Reviews)

        if data is None:
            # log stoping review extractor
            return False
        # log extracting data... (Reviews)
        # loop over all scaped pages
        for review_page in data:
            if review_page is None:
                continue

            extracted_page = self.Review.REVIEW_EXTRACTOR_OBJ.extract(
                review_page.text)
            if not "PRODUCT_NAME" in self.Review.NORMALIZED_REVIEW_DATA.keys():
                self.Review.NORMALIZED_REVIEW_DATA = {
                    "PRODUCT_NAME": extracted_page["product_title"],
                    "ALL_REVIEW_URL": self.Review.URL
                }
            # loop over all reviews in each page
            for reviews in extracted_page["reviews"]:
                self.Review.REVIEW_COUNTS += 1
                self.Review.NORMALIZED_REVIEW_DATA[f"REVIEW #{self.Review.REVIEW_COUNTS}"] \
                    = await self.normalize_review(reviews)
        self.Review.NORMALIZED_REVIEW_DATA["REVIEW_COUNTS"] = self.Review.REVIEW_COUNTS
        return True

    async def extract_product(self) -> bool:
        """
        Return False if Data could not extracted Return True
        if required Data has been extracted
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        This func calls the requester and receive the data, then normalize
        the data and store it in Product class
        """
        # log start product extraction
        data = await self.requester(self.Product.URL)
        if data is None:
            # Log stoping product extractor
            return False
        # log extracting data ...(product)
        extracted_page = self.Product.PRODUCT_EXTRACTOR_OBJ.extract(data.text)
        self.Product.NORMALIZED_PRODUCT_DATA["PRICE"] = extracted_page["price"]
        self.Product.NORMALIZED_PRODUCT_DATA["PRODUCT_URL"] = self.Product.URL
        self.Product.NORMALIZED_PRODUCT_DATA["RATING"] = extracted_page["rating"]
        self.Product.NORMALIZED_PRODUCT_DATA["PRODUCT_DESCRIPTION"] \
            = extracted_page["product_description"]
        return True

    async def normalize_review(self, review: dict) -> dict:
        """
        Special func for cleaning and normalizing each review dict
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        This func is called in 'extract_review' func for extraction of reviews
        Parameters
        ++++++++++
        review : dict
        """
        review["rating"] = float(review["rating"][:3])
        del review["images"]
        review["verified"] = True\
            if review["verified"] == "Verified Purchase" else False
        return review

    async def extraction_wrapper(self, max_reviews) -> bool:
        """
        This Func creates two tasks of review extraction and \
            product extraction and start the event loop
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++\
            +++++++++++++++++++++++++++++++++++++++++
        Return True if extraction was successful else False
        Parameters
        ++++++++++
        max_reviews : int
        """
        # log starting event loop of Product and Review extraction  (extraction_wrapper)
        results = await asyncio.gather(
            self.extract_review(max_reviews), self.extract_product())
        # log checking the extraction results
        # this part check for result of each extractor func, if all returned True the
        # NORMALIZED_DATA will be created of merging two gathered data.
        if results[0] and results[1]:
            self.NORMALIZED_DATA = {**self.Review.NORMALIZED_REVIEW_DATA,
                                    **self.Product.NORMALIZED_PRODUCT_DATA}
            return True
        return False

    def scrap(self, export_type='json', max_reviews: int = 30):
        """
        Calls The extractor func and exporter func
        -------------------------------------------
        Parameters
        ++++++++++
        * export_type='json'
        * max_reviews : int = 30
        """
        # log scrapper has started
        result = asyncio.run(self.extraction_wrapper(max_reviews))
        if result:
            return getattr(self, export_type)()
        else:
            return None

    def json(self):
        """
        Dumps the data and return a json object
        +++++++++++++++++++++++++++++++++++++++
        """
        # log dumping json
        return json.dumps(self.NORMALIZED_DATA)

    def csv_file(self) -> str:
        """
        Export the data to a csv file and return the path directed to it
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        """
        # log exporting csv file
        with open("/fixtures/Scraped-data.csv", 'w', newline='') as writefile:
            csv_writer = csv.writer(writefile, delimiter=',')
            for reviews in self.NORMALIZED_DATA.items():
                csv_writer.writerow([reviews[0], reviews[1]])
        return "/fixtures/Scraped-data.csv"

    def dict(self) -> dict:
        """
        Return the data itself
        ++++++++++++++++++++++
        """
        # log exporting dictionary obj
        return self.NORMALIZED_DATA

    def json_file(self) -> str:
        """
        Export the data to a json file and return the path directed to it
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        """
        # log exporting json file
        with open("crawler\\fixtures\\Scraped-data2.json", 'w') as writfile:
            json.dump(self.NORMALIZED_DATA, writfile)
        return "crawler\\fixtures\\Scraped-data.json"


if __name__ == '__main__':
    testScraper = AmScrapper(
        all_review_url="https://www.amazon.com/HP-Business-Dual-core-Bluetooth-Legendary/product-reviews/B07VMDCLXV/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
        product_url="https://www.amazon.com/HP-Business-Dual-core-Bluetooth-Legendary/dp/B07VMDCLXV", headers=None)
    print(testScraper.scrap('json_file'))
