from scrapy import Item, Field


class AmazonSpiderItem(Item):
    item_details = Field()
    stock_details = Field()


class ProductItem(Item):
    sold_by = Field()
    shipped_from = Field()
    price = Field()
    ratings_percentage = Field()
    number_of_feedback = Field()
    delivery_date = Field()
    stock_count = Field()
    stock_limit_indicator = Field()
    response_timestamp = Field()
