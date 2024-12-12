import scrapy
import json
import logging
import os
class PhoneGsmSpider(scrapy.Spider):
    # Scrape specific phone given phone brand url "phone_brand.json"
    name = "phone_gsm"
    allowed_domains = ["gsmarena.com"]
    failed_urls_file = "failed_pages.txt"
    url_file = os.path.join(os.path.dirname(__file__), '..', 'phone_url', 'samsung.json')

    def __init__(self, start_index=0, end_index=None, *args, **kwargs):
        super(PhoneGsmSpider, self).__init__(*args, **kwargs)

        # Load the list of URLs from the JSON file
        with open(self.url_file, 'r') as f:
            self.phones = json.load(f)

        # Set the range for scraping
        self.start_index = int(start_index)
        self.end_index = int(end_index) if end_index is not None else len(self.phones)

        # Set to store failed URLs for later logging
        self.failed_urls = set()

    def start_requests(self):
        for phone in self.phones[self.start_index:self.end_index]:
            url = phone['url']
            name = phone['name']
            yield scrapy.Request(url=url,
                                 callback=self.parse_product,
                                 meta={'name': name, 'link': url},
                                 errback=self.errback_parse_product)

    def parse_product(self, response):
        try:
            name = response.meta['name']
            link = response.meta['link']
            specifications = {}

            for table in response.xpath('//div[@id="specs-list"]//table'):
                category = table.xpath('.//th[1]/text()').get(default="Uncategorized").strip()
                category_specs = {}

                for row in table.xpath('.//tr'):
                    spec_name = row.xpath('.//td[@class="ttl"]/a/text()').get()
                    spec_value = row.xpath('.//td[@class="nfo"]//text()').get()
                    if spec_name and spec_value:
                        category_specs[spec_name.strip()] = spec_value.strip()

                if category_specs:
                    specifications[category] = category_specs

            yield {
                'name': name,
                'link': link,
                'specifications': specifications
            }
        except Exception as e:
            logging.error(f"Error parsing product {response.meta['name']}: {e}")
            yield {
                'name': response.meta['name'],
                'link': response.meta['link'],
                'error': str(e)
            }

    def errback_parse_product(self, failure):
        request = failure.request
        logging.error(f"Failed to fetch {request.url}: {failure.value}")
        self.failed_urls.add(request.url)

        with open(self.failed_urls_file, 'a') as f:
            f.write(f"{request.url}\n")

    def closed(self, reason):
        if self.failed_urls:
            with open(self.failed_urls_file, 'a') as f:
                for url in self.failed_urls:
                    f.write(f"{url}\n")
        logging.info(f"Spider closed: {reason}. Failed URLs written to {self.failed_urls_file}")