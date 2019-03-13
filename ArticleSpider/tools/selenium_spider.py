#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__: 'Patrick Wang'
__date__: '2019/3/13 11:24'

from selenium import webdriver


browser = webdriver.Chrome(executable_path='E:/git/chromedriver_win32 (3)/chromedriver.exe')

browser.get('https://www.zhihu.com/signup?next=%2F')
browser.find_element_by_css_selector('.SignContainer-switch span').click()
browser.find_element_by_css_selector('.Login-content .SignFlow-account .SignFlow-accountInputContainer div input[name="username"]').send_keys('18930059946')
browser.find_element_by_css_selector('.Login-content .SignFlow-password  .SignFlowInput div input[name="password"]').send_keys('Admin@2009')
browser.find_element_by_css_selector('.Login-content button.SignFlow-submitButton').click()
# print(browser.page_source)

# 设置chromederiver设置不加载图片
# chrome_opt = webdriver.ChromeOptions()
# prefs = {'profile.managed_default_content_settings.images': 2}
# chrome_opt.add_experimental_option('prefs', prefs)
# browser = webdriver.Chrome(executable_path='E:/git/chromedriver_win32 (1)/chromedriver.exe', chrome_options=chrome_opt)
# browser.get("https://www.taobao.com")

# phantomjs ，无界面的浏览器， 在多进程的情况下phantomjs性能会下降很严重
# browser = webdriver.PhantomJS(executable_path='E:/git/phantomjs-2.1.1-windows/phantomjs-2.1.1-windows/bin/phantomjs.exe')
# browser.get('https://detail.tmall.com/item.htm?spm=a230r.1.14.1.585a778fknWw3c&id=575984231019&ns=1&abbucket=16&sku_properties=10004:653780895;5919063:6536025')
# print(browser.page_source)
# browser.quit()

