from crawler.AmScrapper import AmScrapper
from urllib.parse import urlparse


class AmazonSpider:
    """
    Main Spider Class for Amazon WebSite
    ====================================
    This class is resposible for calling Scraper, Sentiment Analyzer and Summarizer Components and URL validation Checking


    """

    class AmSpiderConfig:
        """
        This is the Confiuration Class of Amazon Spider
        +++++++++++++++++++++++++++++++++++++++++++++++

        Attributes
        ++++++++++
            * url
            * AmScrapper
            * SentimentAnalyzer
            * Summerizer
            * raw_data
            * AMAZON_DOMAINS
        """

        AM_SCRAPER = None
        AMAZON_DOMAINS = ["amazon.com.br", "amazon.ca", "amazon.com.mx", "amazon.com",
                          "amazon.cn", "amazon.in", "amazon.co.jp", "amazon.sg",
                          "amazon.com.tr", "amazon.ae", "amazon.sa", "amazon.fr",
                          "amazon.de", "amazon.it", "amazon.nl", "amazon.pl",
                          "amazon.es", "amazon.se", "amazon.co.uk", "amazon.com.au"]
        URL = str
        RAW_DATA = dict

    def __init__(self, url):
        self.AmSpiderConfig.URL = url

    def run_spider(self):
        """
        Run the Spider by calling url checkers and the other main components
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        """
        if self.url_validatior(url=None):
            self.AmSpiderConfig.RAW_DATA = self.call_scraper(
                self.url_normalizer(None))
            if self.AmSpiderConfig.RAW_DATA == None:
                # log stopping Amazon spider
                return None

    def url_validator(self, url=AmSpiderConfig.URL):
        """
        Checks the URL to belong to Amazon
        ++++++++++++++++++++++++++++++++++
        """
        url_obj = urlparse(url)
        domain_name = str(url_obj.netloc)[4:]
        if domain_name in self.AmSpiderConfig.AMAZON_DOMAINS:
            return True
        else:
            return False

    def url_normalizer(self, url: str = AmSpiderConfig.URL):
        """
        Generates the 'all review' URL of the entered link
        ++++++++++++++++++++++++++++++++++++++++++++++++++
        """
        if url.find("all_reviews") > 0:
            return url
        obj = urlparse(url)
        parts = obj.path.split('/')
        review_url = obj.scheme + "://" + obj.netloc + "/" + \
            parts[1] + "/product-reviews/" + parts[3] + \
            "/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        return review_url

    def call_scraper(self, normalized_url: str):
        """
        Creates a AmScrapper instance and calls the scrap function
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        """
        self.AmSpiderConfig.AM_SCRAPER = AmScrapper(normalized_url)
        return self.AmSpiderConfig.AM_SCRAPER.scrap('dict')

    def call_sentiment_analyzer(self):
        pass

    def call_summarizer(self):
        pass
