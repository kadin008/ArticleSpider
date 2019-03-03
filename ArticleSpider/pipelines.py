# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
import codecs
import json
import pymysql
import pymysql.cursors


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


# 自定义json文件的导出
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class MysqlPipeline(object):
    def __init__(self):
        self.conn = pymysql.connect('rdsv148e9hymz8rj85wqo.mysql.rds.aliyuncs.com', 'kadin008', 'Admin@2010',
                                    'article_spider', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """ INSERT INTO jobbole_article ( title, create_date, url, url_object_id, front_image_url, comment_nums, fav_nums, praise_nums, tags, content ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
        self.cursor.execute(insert_sql, (item['title'], item['create_date'], item['url'], item['url_object_id'], item['front_image_url'], item['comment_nums'], item['fav_nums'], item['praise_nums'], item['tags'], item['content']))
        self.conn.commit()


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)

    def handle_error(self, failure):
        print(failure)

    def do_insert(self, cursor, item):
        insert_sql = """ INSERT INTO jobbole_article ( title, create_date, url, url_object_id, front_image_url, comment_nums, fav_nums, praise_nums, tags, content, front_image_path ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
        cursor.execute(insert_sql, (item['title'], item['create_date'], item['url'], item['url_object_id'], item['front_image_url'], item['comment_nums'], item['fav_nums'], item['praise_nums'], item['tags'], item['content'], item["front_image_path"]))


# 调用scrapy提供的json export导出json 文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path

        return item
