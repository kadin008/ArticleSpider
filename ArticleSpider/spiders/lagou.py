# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ArticleSpider.items import LagouJobItemLoader, LagouJobItem
from ArticleSpider.utils.common import get_md5

from datetime import datetime


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    rules = (
        Rule(LinkExtractor(allow=(r'zhaoping/.*',)), follow=True),
        Rule(LinkExtractor(allow=(r'gongsi/j\d+.html',)), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_item', follow=True),
    )

    # def parse_start_url(self, response):
    #     return []
    #
    # def process_results(self, response, results):
    #     return results

    def parse_item(self, response):
        item_logder = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_logder.add_css('title', '.job-name::attr(title)')
        item_logder.add_value('url', response.url)
        item_logder.add_value('url_object_id', get_md5(response.url))
        item_logder.add_css('salary', '.job_request .salary::text')
        item_logder.add_xpath('job_city', '//*[@class="job_request"]/p/span[2]/text()')
        item_logder.add_xpath('work_years', '//*[@class="job_request"]/p/span[3]/text()')
        item_logder.add_xpath('degree_need', '//*[@class="job_request"]/p/span[4]/text()')
        item_logder.add_xpath('job_type', '//*[@class="job_request"]/p/span[5]/text()')
        item_logder.add_css('tags', '.position-label li::text')
        item_logder.add_css('publish_time', '.publish_time::text')
        item_logder.add_css('job_advantage', '.job-advantage p::text')
        item_logder.add_css('job_desc', '.job_bt div')
        item_logder.add_css('job_addr', '.work_addr')
        item_logder.add_css('company_name', '#job_company dt a img::attr(alt)')
        item_logder.add_css('company_url', '#job_company dt a::attr(href)')
        item_logder.add_value('crawl_time', datetime.now())

        job_item = item_logder.load_item()

        return job_item
