# -*- coding: utf-8 -*-
import scrapy
import re
import json
import datetime
try:
    import urlparse as parse
except:
    from urllib import parse
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhiHuQuestionItem, ZhiHuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&" \
                       "include=data%5B%2A%5D.is_normal" \
                       "%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%" \
                       "2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2" \
                       "Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2" \
                       "Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2" \
                       "Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2" \
                       "Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&" \
                       "limit={1}&offset={2}"


    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \
            ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': agent
    }

    def parse(self, response):
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.seartswith('https') else False, all_urls)
        for url in all_urls:
            print(url)
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', url)
            if match_obj:
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        if 'QusetionHeader-title' in response.text:
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', response.url)
            if match_obj:
                question_id = int(match_obj.group(2))
            item_loader = ItemLoader(item=ZhiHuQuestionItem(), response=response)
            item_loader.add_css('title', 'h1.QusetionHeader-title::text')
            item_loader.add_css('content', '.QusetionHeader-detail')
            item_loader.add_value('url', response.url)
            item_loader.add_value('zhihu_id', question_id)
            item_loader.add_css('answer_num', '.List-headerText span::text')
            item_loader.add_css('comments_num', '.QusetionHeader-actions button::text')
            item_loader.add_css('watch_user_num', '.NumberBoard-value::text')
            item_loader.add_css('topics', '.NumberBoard-topics .Popover div::text')

            question_item = item_loader.load_item()

        else:
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', response.url)
            if match_obj:
                question_id = int(match_obj.group(2))
            item_loader = ItemLoader(item=ZhiHuQuestionItem(), response=response)
            # item_loader.add_css('title', '.zh-qusetion-title h2 a::text')
            item_loader.add_xpath('title', '//*[@class="zh-qusetion-title"]/h2/a/text() |'
                                           ' //*[@class="zh-qusetion-title"]/h2/span/text()')
            item_loader.add_css('content', '#zh-qusetion-detail')
            item_loader.add_value('url', response.url)
            item_loader.add_value('zhihu_id', question_id)
            item_loader.add_css('answer_num', '#zh-question-answer-num::text')
            item_loader.add_css('comments_num', '#zh-question-meta-wrap a[name="addcomment"]::text')
            # item_loader.add_css('watch_user_num', '#zh-question-side-header-wrap::text')
            item_loader.add_xpath('watch_user_num', '//*[@id="zh-question-side-header-wrap"]/text()|'
                                                    '//*[@class="zh-question-followers-sidebar"]/div/a/strong/text()')
            item_loader.add_css('topics', '.zm-tag-editor-labels a::text')

            question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhiHuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/login/phone_num', headers=self.headers, callback=self.login)]

    def login(self, response):
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = (match_obj.group(1))

        if xsrf:
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                '_xsrf': xsrf,
                'phone_num': '',
                'password': ''
            }
            return [scrapy.FormRequest(
                url=post_url,
                formdata=post_data,
                headers=self.headers,
                callback=self.check_login
            )]

    def check_login(self, response):
        text_json = json.load(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)
        pass
