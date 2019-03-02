#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__: 'Patrick Wang'
__date__: '2019/2/28 14:52'

from scrapy.cmdline import execute
import sys
import os


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

execute(["scrapy", "crawl", "jobbole"])
