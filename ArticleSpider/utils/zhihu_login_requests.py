#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__: 'Patrick Wang'
__date__: '2019/3/8 11:28'

import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')
try:
    session.cookies.load(ignore_discard=True)
except:
    print('cookie未能加载')

agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' \
        ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
header = {
    'HOST':  'www.zhihu.com',
    'Referer': 'https://www.zhihu.com',
    'User-Agent': agent
}


def is_login():
    inbox_url = 'https://www.zhihu.com/inbox'
    response = session.get(inbox_url, headers=header, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_xsrf():
    response = session.get('https://www.zhihu.com', headers=header)
    match_obj = re.match('.*naem="_xsrf" value="(.*?)"', response.text)
    if match_obj:
        return (match_obj.group(1))
    else:
        return ''


def get_index():
    response = session.get('https://www.zhihu.com', headers=header)
    with open('index_page.html', 'wb') as f:
        f.write(response.text.encode('utf-8'))
    print('OK')


def zhihu_login(account, password):
    if re.match('^1\d{10}', account):
        print('手机号码登录')
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            '_xsrf': get_xsrf(),
            'phone_num': account,
            'password': password
        }
        # response_text = session.post(post_url, data=post_data, headers=header)
        # session.cookies.save()
    else:
        if '@' in account:
            print('邮箱登录')
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                '_xsrf': get_xsrf(),
                'email': account,
                'password': password
            }
    response_text = session.post(post_url, data=post_data, headers=header)
    session.cookies.save()

# get_xsrf()
# zhihu_login('18930059946', 'Admin@2009')
get_index()