# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CoastdemoItem(scrapy.Item):
    type = scrapy.Field()
# 'A' apparel
# 'S' shoes
# 'B' bags
# 'J' jewelry
# 'R' accessories
    gender = scrapy.Field()
# 'F' female
# 'M' male
    designer = scrapy.Field()
    code = scrapy.Field()  # unique identifier from a retailer perspective
    name = scrapy.Field()  # short summary of the item
    description = scrapy.Field()  # fuller description and details of the item
    raw_color = scrapy.Field()  # best guess of what colour the item is (set to None if unidentifiable)
    image_urls = scrapy.Field()  # list of urls of large images representing the item
    price = scrapy.Field()  # full (non-discounted) price of the item  # Get items with prices from any other currency (USD or EUR)
    currency = scrapy.Field()  # price currency
    sale_discount = scrapy.Field()  # percentage discount for sale items where applicable
    stock_status = scrapy.Field()  # dictionary of sizes to stock status
# False - out of stock
# True - in stock
    skus = scrapy.Field()  # list of skus
    link = scrapy.Field()  # url of product page

