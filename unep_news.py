import scrapy
from scrapy_splash import SplashRequest
from scrapysplashNews.items import ScrapysplashnewsItem
import datetime
from lxml import etree


unep_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 10
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""

unep_article_script = """
function main(splash, args)
    splash.resource_timeout = 10
    splash.images_enabled = false
    splash:go(args.url)
    return {html=splash:html(),
    url=splash:url()
    }
end
"""


class NewsSpider(scrapy.Spider):
    name = 'unep_news'
    allowed_domains = ['unep.org']
    start_urls = ['https://www.unep.org/resources?f%5B0%5D=category%3A451&keywords=']

    def start_requests(self):
        for start_url in self.start_urls:
            url = start_url + '&page=0'
            yield SplashRequest(url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': unep_homepage_script, 'timeout': 3600})

    def homepage_parse(self, response):
        articles = response.xpath('//*[@id="block-unep-3spot-content"]/div[2]/'
                                  'div/div/div[2]/div/div[@class="views-row"]')
        for article in articles:
            article_url = 'https://www.unep.org/' + \
                          article.xpath('.//div[@class="result_item_title"]/h5/a/@href').extract_first().strip()
            article_title = article.xpath('.//div[@class="result_item_title"]/h5/a/text()').extract_first().strip()
            article_date = article.xpath('.//span[@class="date"]/text()').extract_first().strip()
            article_abstract = article.xpath('.//div[@class="result_item_summary"]/p/text()').extract_first().strip()

            yield SplashRequest(article_url, callback=self.article_parse, endpoint='execute',
                                args={'lua_source': unep_article_script, 'timeout': 3600, },
                                meta={'abstract': article_abstract,
                                      'title': article_title, 'date': article_date})

    def article_parse(self, response):
        item = ScrapysplashnewsItem()
        item['title'] = response.meta['title']
        item['organization'] = 'United Nations'
        item['issueAgency'] = 'Environment Programme'
        item['url'] = response.data['url']
        item['crawlTime'] = str(datetime.datetime.now().date())

        article_detail = ''
        article_units = etree.HTML(response.data['html']).xpath('//*[@id="ThisOne"]/div/div/div/div/div/div/*')
        for article_unit in article_units:
            article_unit_parts = article_unit.xpath('.//text()')
            for article_unit_part in article_unit_parts:
                sentence = article_unit_part.strip()
                if sentence:
                    article_detail += sentence
            article_detail += '\n'
        item['detail'] = article_detail
        item['issueTime'] = response.meta['date']
        item['abstract'] = response.meta['abstract']

        yield item
