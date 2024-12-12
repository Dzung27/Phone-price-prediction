import scrapy
import logging

class SmallGsmSpider(scrapy.Spider):
    name = "small_gsm"
    allowed_domains = ["gsmarena.com"]
    start_urls = ["https://www.gsmarena.com/microsoft-phones-64.php"]

    def parse(self, response):
        # Log the proxy used for this request
        proxy = response.meta.get('proxy', 'No Proxy')
        logging.info(f"Request made with proxy: {proxy}")

        # Extract phone names and URLs, but don't follow the URLs
        phones = response.xpath('//div[@class="makers"]/ul/li')
        for phone in phones:
            name = phone.xpath('.//span/text()').get()
            link = phone.xpath('./a/@href').get()
            full_link = response.urljoin(link)

            # Yield the title and URL without following the link
            yield {
                'name': name,
                'url': full_link
            }

        # Jump to next page if available
        next_page = response.xpath('//a[@class="prevnextbutton"]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse)
