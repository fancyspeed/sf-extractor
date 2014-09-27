#!/usr/bin/env python
# coding: utf-8
import re
import time

class CXExtractor(object):
    # 每个窗口包含的行数
    block_width = 3
    # 当待抽取的网页正文中遇到成块的新闻标题未剔除时，只要增大此阈值即可
    # 阈值增大，准确率提升，召回率下降；值变小，噪声会大，但可以保证抽到只有一句话的正文
    default_threshold = 240

    _title = re.compile(r'<title>(.*?)</title>', re.I|re.S)
    _title2 = re.compile(r'<h1>(.*?)</h1>', re.I|re.S)
    _description = re.compile(r'<\s*meta\s*name=\"?Description\"?\s+content=\"?(.*?)\"?\s*>', re.I|re.S)
    _keywords = re.compile(r'<\s*meta\s*name=\"?Keywords\"?\s+content=\"?(.*?)\"?\s*>', re.I|re.S)

    # special chars
    _special_list = [(re.compile(r'&quot;', re.I|re.S), '\"'),
                     (re.compile(r'&amp;', re.I|re.S), '&'),
                     (re.compile(r'&lt;', re.I|re.S), '<'),
                     (re.compile(r'&gt;', re.I|re.S), '>'),
                     (re.compile(r'&nbsp;', re.I|re.S), ' '),
                     (re.compile(r'&#34;', re.I|re.S), '\"'),
                     (re.compile(r'&#38;', re.I|re.S), '&'),
                     (re.compile(r'&#60;', re.I|re.S), '<'),
                     (re.compile(r'&#62;', re.I|re.S), '>'),
                     (re.compile(r'&#160;', re.I|re.S), ' '),
                    ]
    _special_char = re.compile(r'&\w{2,6};|&#\w{2,5};', re.I|re.S)
    # html
    _html = re.compile(r'<\w*html', re.I|re.S)
    # DTD
    _doc_type = re.compile(r'<!DOCTYPE.*?>', re.I|re.S)
    # html annotation
    _annotation = re.compile(r'<!--.*?-->', re.I|re.S)
    # js
    _javascript = re.compile(r'<script[^>]*?>.*?</script>', re.I|re.S)
    # css
    _css = re.compile(r'<style[^>]*?>.*?</style>', re.I|re.S)
    _ad_links = re.compile(r'(<a\s+[^>\"\']+href=[\"\']?[^>\"\']+[\"\']?\s+[^>]*>[^<>]{0,50}</a>\s*([^<>]{0,40}?)){2,100}', re.I|re.S) 
    _comment_links = re.compile(r'(<span[^>]*>[^<>]{0,50}</span>\s*([^<>]{0,40}?)){2,100}', re.I|re.S) 
    _link = re.compile(r'<a.*?>|</a>', re.I|re.S)
    _paragraph = re.compile(r'<p(\s+[^>]+)??>|</p>|<br>', re.I|re.S)
    _special_tag = re.compile(r'<[^>\'\"]*[\'\"][^\'\"]{1,500}[\'\"][^>]*?>', re.I|re.S)
    # tag
    _other_tag = re.compile(r'<.*?>', re.I|re.S)
    _special_char = re.compile(r'&\w{2,6};|&#\w{2,5};', re.I|re.S)
    _new_line = re.compile(r'\r\n|\n\r|\r')
    _start_spaces = re.compile(r'^[ \t]+', re.M)
    _spaces = re.compile(r'[ \t]+')
    _multi = re.compile(r'\n|\r|\t')
    _end = re.compile(r'(备\d+号)|(Copyright\s*©)|(版权所有)|(all rights reserved)', re.I)


    def preprocess(self, text):
        #如果正文被压缩到一行,替换时添加换行符
        for r, o in self._special_list:
            text = r.sub(o, text)
        s = self._html.search(text)
        if not s: return ''
        if text.strip().startswith('document.write'): return ''

        num = text.count('\n')
        if num <= 5: c = '\n'
        else:        c = ''
        text = self._doc_type.sub(c, text)
        text = self._annotation.sub(c, text)
        text = self._javascript.sub(c, text)
        text = self._css.sub(c, text)
        text = self._ad_links.sub(c, text)
        text = self._comment_links.sub(c, text)
        text = self._link.sub(c, text)
        text = self._paragraph.sub('\n', text)
        text = self._special_tag.sub('', text)
        text = self._other_tag.sub('', text)
        text = self._special_char.sub(' ', text)
        text = self._new_line.sub('\n', text)
        text = self._start_spaces.sub('', text)
        text = self._spaces.sub(' ', text)
        #text = self._multi.sub('\n', text)

        #print 'after all'.center(100, '*')
        #print text
        return text

    def get_blocks(self, lines, thres):
        lens = [len(line) for line in lines]
        # 去掉前后各有2个空行的短句
        for i in range(len(lines) - 4):
            if lens[i] == 0 and \
               lens[i+1] == 0 and \
               lens[i+2] > 0 and lens[i+2] < 2 and \
               lens[i+3] == 0 and \
               lens[i+4] == 0:
                lens[i+2] = 0


        blocks = [sum(lens[i:i+self.block_width]) for i in range(len(lens))]
        return blocks

    def find_surge(self, blocks, end_i, thres, is_first_match):
        for i in range(end_i, len(blocks)-3):  
            if is_first_match:
                if blocks[i] > thres/2:
                    if blocks[i+1] > 0 or \
                       blocks[i+2] > 0:
                        return i
            if blocks[i] > thres:
                if blocks[i+1] > 0 or \
                   blocks[i+2] > 0 or \
                   blocks[i+3] > 0:
                    return i
        return -1

    def find_dive(self, blocks, start_i):
        for i in range(start_i, len(blocks)-1):
            if i < len(blocks) - 1:
                if blocks[i]   == 0 or \
                   blocks[i+1] == 0:
                    return i
        return len(blocks) - 1

    def extract_title(self, text):
        match = self._title.search(text)
        if not match:
            match = self._title2.search(text)
        if match:
            title = match.groups()[0]
            title = self._special_char.sub(' ', title)
            return self._multi.sub(' ', title)
        return ''

    def extract_keywords(self, text):
        match = self._keywords.search(text)
        if match:
            title = match.groups()[0]
            title = self._special_char.sub(' ', title)
            return self._multi.sub(' ', title)
        return ''

    def extract_description(self, text):
        match = self._description.search(text)
        if match:
            title = match.groups()[0]
            title = self._special_char.sub(' ', title)
            return self._multi.sub(' ', title)
        return ''

    def extract_content(self, text, thres):
        lines = text.split('\n')
        blocks = self.get_blocks(lines, thres)

        num_empty = sum([1 if len(v)>0 else 0 for v in lines]) 
        sum_blocks = sum(blocks)
        if sum_blocks == 0:
            return ''

        #print 'empty:', num_empty
        #print 'blocks:', len(blocks)
        #print 'sum_blocks:', sum_blocks
        #print 'lines:', len(lines)

        thres = min( thres, (sum_blocks*5/len(blocks)/2) << (num_empty/(len(lines)-num_empty) >> 1) )  
        thres = max( thres, 120 )

        #print 'thres:', thres

        start_i, end_i = 0, 0
        is_first_match = True
        content = ''
        while True:
            start_i = self.find_surge(blocks, end_i+1, thres, is_first_match)
            if start_i < 0: break
            if is_first_match: is_first_match = False
            end_i = self.find_dive(blocks, start_i+1)

            sub_content = '\n'.join([v for v in lines[start_i:end_i+1] if v])
            content += sub_content + '\n'
            if end_i >= len(blocks)/2:
                if self._end.search(sub_content):
                    break
        return self._multi.sub(' ', content)

    def extract(self, text, _thres=0):
        if not text: return '', ''

        _title = self.extract_title(text)
        _keywords = self.extract_keywords(text)
        _desc = self.extract_description(text)
        text = self.preprocess(text)
        _content = self.extract_content(text, _thres or self.default_threshold)
        return [_title, _content, _keywords, _desc]

def test():
    ext = CXExtractor()

    urls = [
        'http://baike.baidu.com/view/25215.htm',
        'http://tieba.baidu.com/p/3069273254',
        'http://hi.baidu.com/handylee/blog/item/6523c4fc35a235fffc037fc5.html',
        'http://xiezuoshi.baijia.baidu.com/article/15330',
        'http://www.techweb.com.cn/news/2010-08-11/659082.shtml',
        'http://www.ifanr.com/15876',
        'http://news.cnhubei.com/xw/yl/201404/t2894467_5.shtml',
        ]

    import sys
    sys.path.append('../py-crawler')
    from spider_urllib2 import UrlSpider
    spider = UrlSpider()
    for url in urls:
        raw_html, err = spider.download(url) 
        if raw_html:
            print 'url:', url
            start_time = time.time()
            for i in xrange(0, 10):
                title, content, keywords, desc= ext.extract(raw_html)
            end_time = time.time()
            print 'QPS:', 10/ (end_time-start_time) 
            print 'title:', title
            print 'content:', content
        else:
            print 'url:', url
            print 'error_msg:', err 

def test_file(p_in):
    ext = CXExtractor()
    import sys
    sys.path.append('../py-crawler')
    from spider_urllib2 import UrlSpider
    spider = UrlSpider()
    for url in open(p_in):
        url = url.strip()
        if not url: continue
        raw_html, err = spider.download(url) 
        if raw_html:
            print '\nurl:', url
            title, content, keywords, desc = ext.extract(raw_html)
            print 'title:', title
            print 'content:', content

if __name__ == '__main__':
    import sys
    if len(sys.argv)==2:
        test_file(sys.argv[1])
    else:
        test()

