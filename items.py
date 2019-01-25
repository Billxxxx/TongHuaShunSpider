# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Company(scrapy.Item):
    # 股票代码
    share_id = scrapy.Field()
    # 公司简称
    nick_name = scrapy.Field()
    # 公司全称
    name = scrapy.Field()
    # 营收
    revenue = scrapy.Field()
    # 年份
    year = scrapy.Field()
    # 总市值
    market_value = scrapy.Field()
    # 建立时间
    start_time = scrapy.Field()
    # 上市时间
    market_time = scrapy.Field()
