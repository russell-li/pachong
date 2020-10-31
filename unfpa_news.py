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
    assert(splash:wait(2))
    return {html=splash:html(),
    url=splash:url()
    }
end
"""


class NewsSpider(scrapy.Spider):
    name = 'unfpa_news'
    allowed_domains = ['unfpa.org']
    start_urls = ['https://www.unfpa.org/news']

    def start_requests(self):
        for start_url in self.start_urls:
            yield SplashRequest(start_url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': unep_homepage_script, 'timeout': 3600})

    def homepage_parse(self, response):
        articles = response.xpath('//*[@id="listing-page-template"]/div/div/div/div/div/div[2]/div')
        for article in articles:
            article_url = 'https://www.unfpa.org/' + \
                          article.xpath('.//div[@class="right"]/div/a/@href').extract_first().strip()
            article_title = article.xpath('.//div[@class="right"]/div/a/text()').extract_first().strip()
            article_date = article.xpath('.//div[@class="left"]/span/text()').extract_first().strip()
            article_abstract = article.xpath('.//div[@class="right"]/text()').extract()[1].strip()
            # print('+' * 20)
            # print(article_abstract)

            yield SplashRequest(article_url, callback=self.article_parse, endpoint='execute',
                                args={'lua_source': unep_article_script, 'timeout': 3600, },
                                meta={'abstract': article_abstract,
                                      'title': article_title, 'date': article_date})

    def article_parse(self, response):
        item = ScrapysplashnewsItem()
        item['title'] = response.meta['title']
        item['organization'] = 'United Nations'
        item['issueAgency'] = 'United Nations Population Fund'
        item['url'] = response.data['url']
        item['crawlTime'] = str(datetime.datetime.now().date())

        article_detail = ''
        # print('=' * 20)
        # print(response.data['html'])
        article_units = etree.HTML(response.data['html']).xpath('//*[@id="news-detail-page-template"]/'
                                                                'div[1]/div[1]/div/div/div/div/div/div/div[4]/div/*')
        # print('=' * 20)
        # print(len(article_units))
        for article_unit in article_units:
            article_unit_parts = article_unit.xpath('.//text()')
            for article_unit_part in article_unit_parts:
                sentence = article_unit_part.strip()
                if sentence:
                    article_detail += sentence + ' '
            article_detail += '\n'
        item['detail'] = article_detail
        item['issueTime'] = response.meta['date']
        item['abstract'] = response.meta['abstract']

        yield item
