from amazon_spider.spiders.amazon import AmazonSpider


class AmazonUKSpider(AmazonSpider):
    name = 'amazon_uk'

    def __init__(self, **kwargs):
        kwargs['base_url'] = 'https://www.amazon.co.uk'
        super().__init__(**kwargs)
