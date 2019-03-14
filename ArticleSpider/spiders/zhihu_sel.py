# -*- coding: utf-8 -*-
import scrapy
import time
import pickle
import base64
import datetime
import json
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from mouse import move, click
from zheye import zheye
from scrapy.loader import ItemLoader
from ArticleSpider.tools.yundama_requests import YDMHttp
from ArticleSpider.items import ZhiHuQuestionItem, ZhiHuAnswerItem
try:
    import urlparse as parse
except:
    from urllib import parse


class ZhihuSelSpider(scrapy.Spider):
    name = 'zhihu_sel'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': agent
    }

    custom_settings = {
        "COOKIES_ENABLED": True
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
            item_loader.add_xpath('title', '//*[@id="zh-qusetion-title"]/h2/a/text() |'
                                           ' //*[@id="zh-qusetion-title"]/h2/span/text()')
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
        chrome_option = Options()
        chrome_option.add_argument('--disable-extensions')
        chrome_option.add_experimental_option('debuggerAddress', '127.0.0.1:9222/json')
        browser = webdriver.Chrome(executable_path='E:/git/chromedriver_win32 (3)/chromedriver.exe', chrome_options=chrome_option)
        # browser = webdriver.Chrome(executable_path='E:/git/chromedriver_win32 (3)/chromedriver.exe')

        try:
            browser.maximize_window()  # 将窗口最大化防止定位错误
        except:
            pass
        browser.get("https://www.zhihu.com/signin")
        browser.find_element_by_css_selector('.SignFlow-account input').send_keys(Keys.CONTROL + 'a')
        browser.find_element_by_css_selector('.SignFlow-account input').send_keys('18930059946')
        browser.find_element_by_css_selector('.SignFlow-password input').send_keys(Keys.CONTROL + 'a')
        browser.find_element_by_css_selector('.SignFlow-password input').send_keys('Admin@2019')
        # browser.find_element_by_css_selector('.Button.SignFlow-submitButton').click()
        time.sleep(3)
        move(902, 599)
        click()
        time.sleep(10)
        login_success = False
        while not login_success:
            try:
                notify_ele = browser.find_element_by_class_name('Popover PushNotifications AppHeader-notifications')
                login_success = True
            except:
                pass
            try:
                # 查询是否有英文验证码
                english_captcha_element = browser.find_element_by_class_name('Captcha-englishImg')
            except:
                english_captcha_element = None
            try:
                # 查询是否有中文验证码
                chinese_captcha_element = browser.find_element_by_class_name('Captcha-chineseImg')
            except:
                chinese_captcha_element = None

            if chinese_captcha_element:
                ele_postion = chinese_captcha_element.location
                x_relative = ele_postion['x']
                y_relative = ele_postion['y']
                browser_navigation_panel_height = browser.execute_script(
                    'return window.outerHeight - window.innerHeight;')

                """ 
                保存图片 1. 通过保存base64编码 2. 通过crop方法
                """
                # 1. 通过保存base64编码
                base64_text = chinese_captcha_element.get_attribute("src")
                code = base64_text.replace('data:image/jpg;base64,', '').replace('%0A', '')

                fh = open("yzm_cn.jpeg", "wb")
                fh.write(base64.b64decode(code))
                fh.close()

                z = zheye()
                positions = z.Recognize("yzm_cn.jpeg")

                last_postion = []
                if len(positions) == 2:
                    if positions[0][1] > positions[1][1]:
                        last_postion.append([positions[1][1], positions[1][0]])
                        last_postion.append([positions[0][1], positions[0][0]])
                    else:
                        last_postion.append([positions[0][1], positions[0][0]])
                        last_postion.append([positions[1][1], positions[1][0]])

                    first_point = [int(last_postion[0][0] / 2), int(last_postion[0][1] / 2)]
                    second_point = [int(last_postion[1][0] / 2), int(last_postion[1][1] / 2)]
                    move((x_relative + first_point[0]), y_relative + browser_navigation_panel_height + first_point[1])
                    click()
                    move((x_relative + second_point[0]), y_relative + browser_navigation_panel_height + second_point[1])
                    click()
                else:
                    last_postion.append([positions[0][1], positions[0][0]])
                    first_point = [int(last_postion[0][0] / 2), int(last_postion[0][1] / 2)]
                    move((x_relative + first_point[0]), y_relative + browser_navigation_panel_height + first_point[1])
                    click()

                browser.find_element_by_css_selector('.SignFlow-account input').send_keys(Keys.CONTROL + 'a')
                browser.find_element_by_css_selector('.SignFlow-account input').send_keys('18930059946')
                browser.find_element_by_css_selector('.SignFlow-password input').send_keys(Keys.CONTROL + 'a')
                browser.find_element_by_css_selector('.SignFlow-password input').send_keys('Admin@2009')
                # browser.find_element_by_css_selector('.Button.SignFlow-submitButton').click()
                time.sleep(3)
                move(836, 634)
                click()

            if english_captcha_element:
                base64_text = english_captcha_element.get_attribute("src")

                code = base64_text.replace('data:image/jpg;base64,', '').replace('%0A', '')
                # print code
                fh = open("yzm_en.jpeg", "wb")
                fh.write(base64.b64decode(code))
                fh.close()

                yundama = YDMHttp("Patrick_Wang", "A100s200", 7107, "f8ecb1a73b115d41f7a2526fd1d8d5a8")
                code = yundama.decode("yzm_en.jpeg", 5000, 60)
                while True:
                    if code == "":
                        code = yundama.decode("yzm_en.jpeg", 5000, 60)
                    else:
                        break

                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[2]/div[1]/form/div[3]/div/div/div[1]/input').send_keys(code)

                browser.find_element_by_css_selector('.SignFlow-account input').send_keys(Keys.CONTROL + 'a')
                browser.find_element_by_css_selector('.SignFlow-account input').send_keys('18930059946')
                browser.find_element_by_css_selector('.SignFlow-password input').send_keys(Keys.CONTROL + 'a')
                browser.find_element_by_css_selector('.SignFlow-password input').send_keys('Admin@2009')
                # submit_ele = browser.find_element_by_css_selector(".Button.SignFlow-submitButton")
                # browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
                move(836, 634)
                click()

            time.sleep(10)
            try:
                Cookies = browser.get_cookies()
                print(Cookies)
                cookie_dict = {}

                for cookie in Cookies:
                    # 写入文件
                    # 此处大家修改一下自己文件的所在路径
                    f = open('./ArticleSpider/cookies/' + cookie['name'] + '.zhihu', 'wb')
                    pickle.dump(cookie, f)
                    f.close()
                    cookie_dict[cookie['name']] = cookie['value']
                browser.close()
                return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]
            except:
                pass







