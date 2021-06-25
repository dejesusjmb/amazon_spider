from datetime import datetime

import scrapy
from scrapy import Request, FormRequest

from amazon_spider.items import AmazonSpiderItem


class AmazonSpider(scrapy.Spider):
    name = 'amazon'

    def __init__(self, **kwargs):
        base_url = {
            'us': 'https://www.amazon.com',
            'uk': 'https://www.amazon.co.uk'
        }
        self.base_url = base_url[kwargs['marketplace']]
        self.asin = kwargs['asin']
        super().__init__(**kwargs)

    def start_requests(self):
        meta = {'cookiejar': str(datetime.now()), 'asin': self.asin}

        yield Request(url=f'{self.base_url}/gp/cart/view.html?ref_=nav_cart',
                      meta=meta,
                      callback=self.handle_cart_page)

    def handle_cart_page(self, response):
        if response.meta.get('item'):
            yield AmazonSpiderItem(item_details=response.meta['item'], stock_details=response)

        if 'backlog_items' in response.meta and len(response.meta['backlog_items']) == 0:
            return

        url = f'{self.base_url}/gp/aod/ajax/ref=dp_aod_NEW_mbc?asin={self.asin}'
        yield Request(url=url,
                      meta=response.meta,
                      dont_filter=True,
                      callback=self.handle_item_page)

    def handle_item_page(self, response):
        backlog_items = response.meta.get('backlog_items')
        if backlog_items is None:
            backlog_items = response.xpath('//div[@id="aod-pinned-offer"]')
            backlog_items.extend(response.xpath('//div[@id="aod-offer"]'))

        item = backlog_items.pop(0)
        formdata = self._create_formdata(item)
        meta = dict(response.meta)
        meta['item'] = item
        meta['backlog_items'] = backlog_items

        yield FormRequest(url=f'{self.base_url}/gp/add-to-cart/html/ref=aod_dpdsk_new_1',
                          meta=meta,
                          formdata=formdata,
                          callback=self.handle_cart_page)

    def _create_formdata(self, item):
        names = ['session-id', 'qid', 'sr', 'signInToHUC', 'registryItemID.1', 'registryID.1',
                 'itemCount', 'offeringID.1', 'isAddon', f'metric-asin.{self.asin}']

        formdata = {
            name: item.xpath(f'.//form/input[@name="{name}"]/@value').extract_first() or ''
            for name in names
        }

        formdata.update({
            'quantity.1': '999',
            'submit.addToCart': 'Submit',
        })

        return formdata
