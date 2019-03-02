# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader
import datetime


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        # 1.获取文章列表页中的文章url并交给scrapy下载后并进行解析
        # 2.获取下一页的UTL并交给scrapy进行下载 下载完成后交给parse

        # 解析列表页中的所有文章url并交给scrapy下载后并进行解析
        post_nodes = response.css('#archive.grid-8 .floated-thumb .post-thumb a')
        for post_node in post_nodes:
            image_url = post_node.css('img::attr(src)').extract_first("")
            post_url = post_node.css('::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={'front_image_url': image_url}, callback=self.parse_datail)

        # 提取下一页并交个scrapy进行下载
        next_url = response.css('.next.page-numbers::attr(href)').extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_datail(self, response):
        article_item = JobBoleArticleItem()
        # # 使用xpath方式爬取内容
        # # 标题
        # title = response.xpath('//*[@id="post-114610"]/div[1]/h1/text()').extract()[0]
        #
        # # 时间
        # create_date = response.xpath('//*[@id="post-114610"]/div[2]/p/text()').extract()[0].strip().replace(' ·', '')
        # tag_list = response.xpath('//*[@id="post-114610"]/div[2]/p/a/text()').extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith('评论')]
        # tags = ','.join(tag_list)
        #
        # # 点赞数
        # praise_nums = int(response.xpath('//*[@id="post-114610"]/div[3]/div[3]/span[1]/h10/text()').extract()[0])
        #
        # # 收藏数
        # fav_nums = response.xpath('//*[@id="post-114610"]/div[3]/div[3]/span[2]/text()').extract()[0]
        # match_re = re.match('.*?(\d+).*', fav_nums)
        # if match_re:
        #     fav_nums = match_re.group(1)
        # else:
        #     fav_nums = 0
        #
        # # 评论数
        # comment_nums = response.xpath('//*[@id="post-114610"]/div[3]/div[3]/a/span/text()').extract()[0]
        # match_re = re.match('.*?(\d+).*', comment_nums)
        # if match_re:
        #     comment_nums = match_re.group(1)
        # else:
        #     comment_nums = 0
        #
        # # 正文
        # cotent = response.xpath('//*[@id="post-114610"]/div[3]').extract()[0]

        # 使用css方式爬取内容
        # 图片获取
        front_image_url = response.meta.get('front_image_url', '')

        # 标题
        title = response.css('.entry-header h1::text').extract()[0]

        # 时间
        create_date = response.css('.entry-meta p::text').extract()[0].strip().replace(' ·', '')
        tag_list = response.css('.entry-meta a::text').extract()
        tag_list = [element for element in tag_list if not element.strip().endswith('评论')]
        tags = ','.join(tag_list)

        # 点赞数
        praise_nums = int(response.css('.vote-post-up h10::text').extract()[0])
        if praise_nums:
            praise_nums = praise_nums
        else:
            praise_nums = 0

        # 收藏数
        fav_nums = response.css('.bookmark-btn::text').extract()[0]
        match_re = re.match('.*?(\d+).*', fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0

        # 评论数
        comment_nums = response.css('a[href="#article-comment"] span::text').extract_first("")
        match_re = re.match('.*?(\d+).*', comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        # 正文
        content = response.css('div.entry').extract()[0]

        article_item['url_object_id'] = get_md5(response.url)
        article_item['title'] = title
        try:
            create_date = datetime.datetime.strftime(create_date, '%Y/%m/%d').date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item['create_date'] = create_date
        article_item['url'] = response.url
        article_item['front_image_url'] = [front_image_url]
        article_item['praise_nums'] = praise_nums
        article_item['fav_nums'] = fav_nums
        article_item['comment_nums'] = comment_nums
        article_item['tags'] = tags
        article_item['content'] = content

        item_loader = ItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css('')

        yield article_item

