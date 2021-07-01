import re
import logging
from datetime import datetime

from scrapy import Spider, Request, FormRequest

from amazon_spider.items import AmazonSpiderItem


class AmazonSpider(Spider):
    def __init__(self, **kwargs):
        self.base_url = kwargs['base_url']
        self.asin = kwargs['asin']

        self.number_of_vendors = 10
        self.items = []
        self.max_item_count = 0
        self.backlog_items = []
        super().__init__(**kwargs)

    def start_requests(self):
        yield Request(url='http://checkip.amazonaws.com/',
                      callback=self.handle_amazon_page)

        meta = {'cookiejar': str(datetime.now()), 'asin': self.asin}
        yield Request(url=f'{self.base_url}/gp/cart/view.html?ref_=nav_cart',
                      meta=meta,
                      dont_filter=True,
                      callback=self.handle_initial_page)

    def handle_amazon_page(self, response):
        logging.info(f'IP Address: {response.text}')

    def handle_initial_page(self, response):
        url = (f'{self.base_url}/gp/aod/ajax/ref=dp_aod_NEW_mbc?asin={self.asin}'
               f'&m=&qid=&smid=&sourcecustomerorglistid=&sourcecustomerorglistitemid='
               f'&sr=&pc=dp&filters=%257B%2522all%2522%253Atrue%252C%2522new%2522%253Atrue%257D')
        yield Request(url=url,
                      meta=response.meta,
                      dont_filter=True,
                      callback=self.handle_item_page)

    def handle_item_page(self, response):
        self.backlog_items = response.xpath('//div[@id="aod-pinned-offer"]')
        self.backlog_items.extend(response.xpath('//div[@id="aod-offer"]'))
        self.max_item_count = len(self.backlog_items)
        sessions = (self.number_of_vendors
                    if self.max_item_count >= self.number_of_vendors
                    else self.max_item_count)

        for i in range(sessions):
            meta = {'cookiejar': str(i) + str(datetime.now()),
                    'asin': self.asin,
                    'index': i}
            yield Request(url=f'{self.base_url}/gp/cart/view.html?ref_=nav_cart',
                          meta=meta,
                          dont_filter=True,
                          callback=self.handle_add_to_cart_page)

    def handle_add_to_cart_page(self, response):
        item = self.backlog_items[int(response.meta['index'])]
        formdata = self._create_formdata(item)
        formdata['session-id'] = self.get_session_id(response)
        meta = dict(response.meta)
        meta['item'] = item

        yield FormRequest(url=f'{self.base_url}/gp/add-to-cart/html/ref=aod_dpdsk_new_1',
                          meta=meta,
                          formdata=formdata,
                          dont_filter=True,
                          callback=self.handle_cart_page)

    def get_session_id(self, response):
        cookie = str(response.headers['Set-Cookie'], response.headers.encoding)
        return re.findall('session-id=(.+?);', cookie)[0]

    def handle_cart_page(self, response):
        item = {
            'item_details': response.meta['item'],
            'stock_details': response,
            'index': response.meta['index']
        }
        self.items.append(item)

        if len(self.items) >= self.number_of_vendors or len(self.items) == self.max_item_count:
            self.items = sorted(self.items, key=lambda data: data['index'])
            for item in self.items:
                yield AmazonSpiderItem(item_details=item['item_details'],
                                       stock_details=item['stock_details'])

    def _create_formdata(self, item):
        names = ['qid', 'sr', 'signInToHUC', 'registryItemID.1', 'registryID.1',
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
