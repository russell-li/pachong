import scrapy
from scrapy_splash import SplashRequest
from scrapysplashNews.items import ScrapysplashnewsItem
import datetime
from lxml import etree
import re


geo_homepage_script = """
function main(splash, args)
    splash.resource_timeout = 15
    splash.images_enabled = false
    assert(splash:go(args.url))
    return splash:html()
end
"""

geo_article_script = """
function main(splash, args)
    splash.resource_timeout = 15
    splash.images_enabled = false
    splash:go(args.url)
    splash:wait(5)
    return {html=splash:html(),
    url=splash:url()
    }
end
"""


class NewsSpider(scrapy.Spider):
    name = 'geo_news'
    allowed_domains = ['earthobservations.org']
    start_urls = ['https://www.earthobservations.org/articles.php']

    def start_requests(self):
        for start_url in self.start_urls:
            yield SplashRequest(start_url, callback=self.homepage_parse, endpoint='execute',
                                args={'lua_source': geo_homepage_script, 'timeout': 3600})

    def homepage_parse(self, response):
        articles = response.xpath('/html/body/div[6]/div[2]/div/div[position() < 9]')
        for article in articles:
            article_url = 'https://www.earthobservations.org/' + article.xpath('./a/@href').extract_first().strip()
            article_title = article.xpath('./a/div/p/text()').extract_first().strip()
            # article_date = article.xpath('.//div[contains(@class, "news-summary-listing")]/strong/span/text()').extract_first().strip()
            # article_date = self.parse_issueTime_raw(article_date)
            # article_abstract = article.xpath('.//div[contains(@class, "news-summary-listing")]/text()').extract()[2].replace('-', ' ').replace('\n', ' ').strip()
            # print('+' * 20)
            # print(article_abstract)

            yield SplashRequest(article_url, callback=self.article_parse, endpoint='execute',
                                args={'lua_source': geo_article_script, 'timeout': 3600, },
                                meta={'title': article_title})

    def article_parse(self, response):
        item = ScrapysplashnewsItem()
        item['title'] = response.meta['title']
        item['organization'] = 'Fields of science and technology cooperation'
        item['issueAgency'] = 'Earth observation organization'
        item['url'] = response.data['url']
        item['crawlTime'] = str(datetime.datetime.now().date())

        article_detail = ''
        # print('=' * 20)
        # print(response.data['html'])
        # detail_id = re.search('-(\d{5})$', response.data['url'], re.S).group(1)
        # print('=' * 20)
        # print(detail_id)
        # two conditions: article, geo_blog
        if 'article' in response.data['url']:
            article_units = etree.HTML(response.data['html']).xpath('/html/body/div[6]/div[2]/div/*[position()>3]')
            item['issueTime'] = response.xpath('/html/body/div[6]/div[2]/div/*[3]/text()').extract_first().split('/')[-1].strip()
        else:
            article_units = etree.HTML(response.data['html']).xpath('/html/body/div[7]/div[2]/div/*[position()>3]')
            item['issueTime'] = response.xpath('/html/body/div[7]/div[2]/div/*[3]/text()').extract_first().split('/')[-1].strip()

        # print('=' * 20)
        # print(len(article_units))
        for article_unit in article_units:
            article_unit_parts = article_unit.xpath('.//text()')
            if ''.join(article_unit_parts).strip() == '':
                continue
            for article_unit_part in article_unit_parts:
                sentence = article_unit_part.strip()
                if sentence:
                    article_detail += sentence + ' '
            article_detail += '\n'
        item['detail'] = article_detail
        item['abstract'] = article_detail[:100]

        yield item

    def parse_issueTime_raw(self, issueTime_raw):

        day, month, year = issueTime_raw.split('-')
        mapping = {
            'Jan': 'January',
            'Feb': 'February',
            'Mar': 'March',
            'Apr': 'April',
            'May': 'May',
            'Jun': 'June',
            'Jul': 'July',
            'Aug': 'August',
            'Sep': 'September',
            'Oct': 'October',
            'Nov': 'November',
            'Dec': 'December',
        }

        return ' '.join([day, mapping[month], year])
