#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__: 'Patrick Wang'
__date__: '2019/3/12 13:48'
import requests
from scrapy.selector import Selector
import pymysql

conn = pymysql.connect(host='rdsv148e9hymz8rj85wqo.mysql.rds.aliyuncs.com', user='kadin008', passwd='Admin@2010', db='article_spider', charset='utf8')
cursor = conn.cursor()


def crawl_ips():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'}
    for i in range(3625):
        re = requests.get('https://www.xicidaili.com/nn/{0}'.format(i), headers=headers)

        selector = Selector(text=re.text)
        all_trs = selector.css('#ip_list tr')

        ip_list = []
        for tr in all_trs[1:]:
            speed_str = tr.css('.bar::attr(title)').extract()[0]
            if speed_str:
                speed = float(speed_str.split('秒')[0])
            all_texts = tr.css('td::text').extract()

            ip = all_texts[0]
            port = all_texts[1]
            proxy_type = all_texts[5]

            ip_list.append((ip, port, proxy_type, speed))

        for ip_info in ip_list:
            # if ip_info == "http":
                cursor.execute(
                    'INSERT INTO proxy_ip(ip,port,speed,proxy_type) VALUES("{0}","{1}",{2},"{3}") '
                    'ON DUPLICATE KEY UPDATE port=VALUES(port), speed=VALUES(speed), proxy_type=VALUES(proxy_type)'.format(
                        ip_info[0], ip_info[1], ip_info[3], ip_info[2]

                    )
                )
                conn.commit()


class GetIP(object):
    def delete_ip(self, ip):
        delete_sql = 'delete from proxy_ip where ip={0}'.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, ip, port, proxy_type):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/59.0.3071.115 Safari/537.36"}
        http_url = 'http://www.baidu.com'
        proxy_url = 'http://{0}:{1}'.format(ip, port)
        try:
            proxy_dict = {proxy_type: proxy_type + '://' + ip + ':' + port}
            response = requests.get(http_url, proxies=proxy_dict, headers=headers)
            return True
        except Exception as e :
            print('invalid ip and port')
            self.delete_ip(ip)
            return False
        else:
            if 200 <= response.status_code < 300:
                print('effective ip ')
                return True
            else:
                print('invalid ip and port')
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        random_sql = 'select ip, port, proxy_type from proxy_ip WHERE proxy_type = "http" order by RAND() limit 1'
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2]
            judge_re = self.judge_ip(ip, port, proxy_type)
            if judge_re:
                return '{0}://{1}:{2}'.format(proxy_type, ip, port)
            else:
                return self.get_random_ip()


# get_ip = GetIP()
# print(get_ip.get_random_ip())

if __name__ == '__main__':
    get_ip = GetIP()
    print(get_ip.get_random_ip())

