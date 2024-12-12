import scrapy
import logging


class ScraperGSM(scrapy.Spider):
    # Scrape Urls for each phone brand
    name = "scraper_gsm"
    allowed_domains = ["gsmarena.com"]
    start_urls = ["https://www.gsmarena.com/makers.php3"]

    def parse(self, response):
        # Extract each brand link from the main makers page
        brands = response.xpath('//div[@class="st-text"]/table//td/a')
        for brand in brands:
            brand_name = brand.xpath('.//text()').get()
            brand_link = brand.xpath('.//@href').get()
            full_brand_link = response.urljoin(brand_link)
            yield scrapy.Request(url=full_brand_link,
                                 callback=self.parse_brand,
                                 meta={'brand_name': brand_name})

    def parse_brand(self, response):
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
                                 meta={'brand_name': response.meta['brand_name'], 'name': name, 'link': full_link},
                                 errback=self.errback_parse_product)

        # Follow pagination if there’s a next page
        next_page = response.xpath('//a[@class="pages-next"]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse_brand, meta=response.meta)

    def parse_product(self, response):
        try:
            name = response.meta['name']
            brand_name = response.meta['brand_name']
            link = response.meta['link']
            specifications = {}

            for table in response.xpath('//div[@id="specs-list"]//table'):
                category = table.xpath('.//th[1]/text()').get()
                category = category.strip() if category else "Uncategorized"
                category_specs = {}

                for row in table.xpath('.//tr'):
                    spec_name = row.xpath('.//td[@class="ttl"]/a/text()').get()
                    spec_value = row.xpath('.//td[@class="nfo"]//text()').get()
                    if spec_name and spec_value:
                        category_specs[spec_name.strip()] = spec_value.strip()

                if category_specs:
                    specifications[category] = category_specs

            yield {
                'brand': brand_name,
                'name': name,
                'link': link,
                'specifications': specifications
            }
        except Exception as e:
            logging.error(f"Error parsing product {name}: {e}")
            yield {
                'brand': response.meta['brand_name'],
                'name': name,
                'link': link,
                'error': str(e)
            }

    def errback_parse_product(self, failure):
        request = failure.request
        logging.error(f"Failed to fetch {request.url}: {failure.value}")

    def closed(self, reason):
        logging.info(f"Spider closed: {reason}.")
