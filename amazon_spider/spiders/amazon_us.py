from amazon_spider.spiders.amazon import AmazonSpider


class AmazonUSSpider(AmazonSpider):
    name = 'amazon_us'

    def __init__(self, **kwargs):
        kwargs['base_url'] = 'https://www.amazon.com'
        super().__init__(**kwargs)
