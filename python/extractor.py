#!/usr/bin/env python
import re

class HtmlExtractor(object):
    '''
    * 主题型网页正文抽取，比较适合于新闻和Blog的正文抽取.<br />
    * 主题型网页正文抽取，比较适合于新闻和Blog的正文抽取.<br />
    * 采用《基于行块分布函数的通用网页正文抽取》的算法，该算法时间复杂度为线性，
    * 不需要建立DOM树，且不依赖HTML标签。<br />
    * 首先将网页正文抽取问题转化为求页面的行块分布函数，这种方法不用建立Dom树，
    * 不被病态HTML所累（事实上与HTML标签完全无关）。
    * 通过在线性时间内建立的行块分布函数图，直接准确定位网页正文。
    * 采用《基于行块分布函数的通用网页正文抽取》的算法，该算法时间复杂度为线性，
    * 不需要建立DOM树，且不依赖HTML标签。<br />
    * 首先将网页正文抽取问题转化为求页面的行块分布函数，这种方法不用建立Dom树，
    * 不被病态HTML所累（事实上与HTML标签完全无关）。
    * 通过在线性时间内建立的行块分布函数图，直接准确定位网页正文。
    '''
    #行块大小
    _block = 3
    #title pattern
    _title_pattern = r'<title(.*?)</title>'
    _p_title_pattern = re.compile(_title_pattern, re.I)

    _title = ''
    _text = ''


if __name__ == '__main__':
    urls = [
            'www.sina.com.cn',
           ]

    extractor = HtmlExtractor()
    for url in urls:
        print 'url:', url
        extractor.extract(url=url)
        print 'title:', extractor.get_title()
        print 'text:', extractor.get_text()

