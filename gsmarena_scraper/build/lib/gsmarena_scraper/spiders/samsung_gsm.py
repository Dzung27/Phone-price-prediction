import scrapy
import logging

class SamsungGsmSpider(scrapy.Spider):
    name = "samsung_gsm"
    allowed_domains = ["gsmarena.com"]
    start_urls = ["https://www.gsmarena.com/xiaomi-phones-80.php"]
    failed_urls_file = "failed_pages.txt"

    def __init__(self, *args, **kwargs):
        super(SamsungGsmSpider,self).__init__(*args, **kwargs)
        self.failed_urls = set()
        with open(self.failed_urls_file, 'w') as f:
            f.write("")
    def parse(self, response):
        # Log the proxy used for this request
        proxy = response.meta.get('proxy', 'No Proxy')
        logging.info(f"Request made with proxy: {proxy}")

        phones = response.xpath('//div[@class="makers"]/ul/li')
        for phone in phones:
            name = phone.xpath('.//span/text()').get()
            link = phone.xpath('./a/@href').get()
            full_link = response.urljoin(link)
            yield scrapy.Request(url=full_link,
                                 callback=self.parse_product,
                                 meta={'name': name, 'link': full_link},
                                 errback=self.errback_parse_product)
        # Jump to next page
        next_page = response.xpath('//a[@class="prevnextbutton"]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse)
    def parse_product(self, response):
        try:
            name = response.meta['name']
            link = response.meta['link']
            specifications = {}
            for table in response.xpath('//div[@id="specs-list"]//table'):
                # Extract the category name (e.g., "Network", "Launch")
                category = table.xpath('.//th[1]/text()').get()
                if category:
                    category = category.strip()
                else:
                    category = "Uncategorized"

                # Initialize a dictionary to hold each specification for the category
                category_specs = {}

                # Loop through each row in the table to get the specification details
                for row in table.xpath('.//tr'):
                    # Get the specification name and value
                    spec_name = row.xpath('.//td[@class="ttl"]/a/text()').get()
                    spec_value = row.xpath('.//td[@class="nfo"]//text()').get()

                    # Only add valid specs (avoid empty rows)
                    if spec_name and spec_value:
                        category_specs[spec_name.strip()] = spec_value.strip()

                    # Add the category and its specs to the main specifications dictionary
                if category_specs:
                    specifications[category] = category_specs

                    # Yield the final structured data
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
        #Log failed URL
        request = failure.request
        logging.error(f"Failed to fetch {request.url}: {failure.value}")
        self.failed_urls.add(request.url)

        # Append to failed_pages.txt instantly
        with open(self.failed_urls_file, 'a') as f:
            f.write(f"{request.url}\n")


    def closed(self, reason):
        # Write all failed URLs to the failed_urls_file when the spider is closed
        if self.failed_urls:
            with open(self.failed_urls_file, 'a') as f:
                for url in self.failed_urls:
                    f.write(f"{url}\n")
        logging.info(f"Spider closed: {reason}. Failed URLs written to {self.failed_urls_file}")

