# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import Field
import scrapy



class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # title = scrapy.Field()
    # news_script = scrapy.Field()
    # title_date = scrapy.Field()
    # reply = scrapy.Field()
    # user = scrapy.Field()
    # reply_pros = scrapy.Field()
    # reply_cons = scrapy.Field()
    # reply_date = scrapy.Field()
    # rereply = scrapy.Field()
    # rereply_date = scrapy.Field()
    # rereply_user = scrapy.Field()
    keyword = scrapy.Field()
    article = scrapy.Field()
    reply = scrapy.Field()
    rereply = scrapy.Field()

