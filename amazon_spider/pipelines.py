from datetime import datetime

import re

from amazon_spider.items import ProductItem
from amazon_spider.utils import recursive_compress


class AmazonSpiderPipeline:
    def process_item(self, item, spider):
        document = {'response_timestamp': str(datetime.now())}
        if self.check_if_no_stock(item['stock_details']):
            document.update(self.get_empty_item())
            return ProductItem(**document)

        document.update(self.extract_item_details(item['item_details']))
        document.update(self.extract_stock_details(item['stock_details']))
        document = recursive_compress(document)
        return ProductItem(**document)

    def extract_item_details(self, item_details):
        sold_by = self.extract_sold_by(item_details)
        shipped_from = self.extract_shipped_from(item_details)
        price = self.extract_price(item_details)
        delivery_date = self.extract_delivery_date(item_details)
        ratings_percentage, number_of_feedback = self.extract_ratings(item_details, sold_by)

        item_details = {
            'sold_by': sold_by,
            'shipped_from': shipped_from,
            'price': price,
            'ratings_percentage': ratings_percentage,
            'number_of_feedback': number_of_feedback,
            'delivery_date': delivery_date
        }

        return item_details

    def extract_stock_details(self, stock_details):
        xpath = '//p[contains(text(), "Your Update Failed")]/text()'
        update_failed = stock_details.xpath(xpath).extract_first()
        if update_failed:
            raise Exception('Update Failed!')

        alert = stock_details.xpath('.//div[@id="huc-v2-message-group"]//p/text()').extract()
        stock_count, stock_limit_indicator = self.extract_stock_details_from_alert(alert)

        stock_details = {
            'stock_count': stock_count,
            'stock_limit_indicator': stock_limit_indicator
        }

        return stock_details

    def check_if_no_stock(self, stock_details):
        xpath = './/span/text()[contains(., "There are no items to add to your cart")]'
        return stock_details.xpath(xpath).extract_first()

    def extract_sold_by(self, item_details):
        a_sold_by = item_details.xpath('.//div[@id="aod-offer-soldBy"]//a/text()').extract_first()
        span_sold_by = item_details.xpath('.//div[@id="aod-offer-soldBy"]//span/text()').extract()
        return a_sold_by or span_sold_by[-1]

    def extract_shipped_from(self, item_details):
        xpath = './/div[@id="aod-offer-shipsFrom"]//span[@class="a-size-small a-color-base"]/text()'
        return item_details.xpath(xpath).extract_first()

    def extract_price(self, item_details):
        return item_details.xpath('.//span[@class="a-offscreen"]/text()').extract_first()

    def extract_delivery_date(self, item_details):
        us_date = item_details.xpath('.//div[@id="delivery-message"]/b/text()').extract_first()
        uk_date = item_details.xpath('.//div[@id="ddmDeliveryMessage"]//b/text()').extract_first()
        return us_date or uk_date

    def extract_ratings(self, item_details, sold_by):
        ratings = item_details.xpath(
            './/span[@id="seller-rating-count-{iter}"]/span/text()').extract()
        if ratings:
            ratings_percentage = ratings[1].split()[0]
            number_of_feedback = ratings[0]
        else:
            ratings_percentage = ''
            number_of_feedback = item_details.xpath(
                './/span[@id="aod-asin-reviews-count-title"]/text()').extract_first()

        number_of_feedback = (re.findall(r'\d+,*\d+', number_of_feedback)[0]
                              if number_of_feedback else '')

        if not ratings_percentage and 'amazon' in sold_by.lower():
            ratings_percentage = '100%'

        return ratings_percentage, number_of_feedback

    def get_empty_item(self):
        item = {
            'sold_by': '',
            'shipped_from': '',
            'price': '',
            'ratings_percentage': '',
            'number_of_feedback': '',
            'delivery_date': '',
            'stock_count': 0,
            'stock_limit_indicator': False
        }
        return item

    def extract_stock_details_from_alert(self, alert):
        if alert:
            stock_count = re.findall(r'than the (\d+) available from the seller', alert[1])
            limit_count = re.findall(r'this seller has a limit of (\d+) per customer', alert[1])

            if stock_count:
                stock_count = stock_count[0]
                stock_limit_indicator = False
            elif limit_count:
                stock_count = limit_count[0]
                stock_limit_indicator = True
            else:
                raise Exception('Both stock count and limit count are zero!')
        else:
            stock_count = 999
            stock_limit_indicator = False

        return stock_count, stock_limit_indicator
