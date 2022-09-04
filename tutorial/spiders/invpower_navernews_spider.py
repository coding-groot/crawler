from ast import Global
from traceback import print_tb
from psutil import users
import scrapy
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re
import requests
from urllib.parse import urlparse, parse_qs
import time
import random
import json
from itertools import chain, repeat
import pandas as pd
from tutorial.items import TutorialItem
from datetime import datetime as dt
from datetime import timedelta

class NavernewsSpider(scrapy.Spider):
    name = "naver"
    
    def start_requests(self):
        
        # 검색어 입력 함수
        def Keyword_input():

            Key = input("검색어를 입력하세요: ")
            return Key

        # 시작 날짜와 종료 날짜 입력 함수
        def Date_input():
            
            start_date = input("시작 날짜(ex. 2022.7.10.): ")
            end_date = input("종료 날짜(ex. 2022.7.10.): ")
            
            try:
                datetime_format = "%Y.%m.%d."
                datetime_startdate = dt.strptime(start_date, datetime_format).date()
                datetime_enddate = dt.strptime(end_date, datetime_format).date()
                
            except ValueError:
                print("양식 맞춰서 입력해(2022.7.10.)")
                Date_input()
                
            if datetime_startdate > datetime_enddate:
                print("시작 날짜가 더 앞이겠지?")
                Date_input()
            else:
                return datetime_startdate, datetime_enddate
                

        Key = Keyword_input()
        datetime_startdate, datetime_enddate = Date_input()
        print(datetime_enddate)
        
        now = dt.now()
        now = now.date()
        f = open("내역.txt", 'a', encoding="UTF-8")
        data = f"\n크롤링 시작 날짜:{now}\n검색어:{Key}\n수집일:{datetime_startdate}부터 {datetime_enddate}까지\n"
        print(data)
        f.write(data)
        f.close()

        print("-------------STARTCRAWL---------------")
        
        self.keyword = Key
        key_words=urllib.parse.quote(self.keyword)
        searchtext=re.compile('https?:\/\/n\.news\.naver\.com\/mnews\/article\/')

        crawl_date = datetime_startdate
        fin_date = datetime_enddate + timedelta(days=1)

        while True:
            new_link_2=[]
            if crawl_date == fin_date:
                break

            date_for_crawl = str(crawl_date).replace('-','.')
            k=1

            while k!=3991:
            #while k!=11: #for tutorial
                print(k)
                url = 'https://search.naver.com/search.naver?where=news&sm=tab_pge&query={}&ds={}&de={}&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:dd,p:from{}to{},a:all&start={}'.format(key_words,date_for_crawl,date_for_crawl,date_for_crawl.replace('.',''),date_for_crawl.replace('.',''),k)
                with urllib.request.urlopen(url) as response:
                    data=(response.read())
                soup = BeautifulSoup(data, 'html.parser')
                anchor_set=soup.find_all("a",{'class':['info']})

                if len(anchor_set) == 0: #불필요한 K 없애기
                    break

                for i in anchor_set:

                    try :
                        if searchtext.match(str(i['href'])) != None and str(i['href']).startswith('https://n.news.naver.com/') and "sid=106" not in str(i['href']):
                            new_link_2.append(str(i['href']))
                    except :
                        pass
                k+=10
            

            d = timedelta(days = 1)
            crawl_date = crawl_date + d

            for url in new_link_2:
                try:
                    yield scrapy.Request(url=url, callback=self.parse)
                except:
                    pass


    def parse(self, response):

        tutorial_item = TutorialItem()
#기사제목
        articleTitle = response.css('div.media_end_head_title > h2::text').get()

        
#기사작성시간
        articleDate = dt.strptime(response.css('span.media_end_head_info_datestamp_time').attrib['data-date-time'],"%Y-%m-%d %H:%M:%S")
     
#기사 내용

        news_script = response.xpath('//*[@id="dic_area"]').get()
        articleContent = BeautifulSoup(news_script,"lxml").text

#댓글 test
        oid = str(response)[44:47]
        aid = str(response)[48:-9]
        articleId = oid + aid

        page_num = 1
        url = 'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&pool=cbox5&lang=ko&country=KR&objectId=news{}%2C{}&categoryId=&pageSize=100&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={}'
        
        header = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0',
            'accept' : "*/*",
            'accept-encoding' : 'gzip, deflate, br',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer' : str(response)[5:-1]
        }
        
        comment_list = []

        df_reply = pd.DataFrame()
        df_rereply = pd.DataFrame()

        while(True):
            req_url = url.format(oid, aid, page_num)
            html = requests.get(req_url, headers = header)

            test_text = html.text
            test_text = test_text.replace("_callback(","")[:-2]
            comment_text = json.loads(test_text)
            #comment_count = comment_text['result']['count']['comment']
            comment_count = len(comment_text['result']['commentList'])
            comment_info = comment_text['result']['commentList']
            replyUser = [i['userName'] for i in comment_info]
            replyContent = [i['contents'] for i in comment_info]
            replyPros = [i['sympathyCount'] for i in comment_info]           
            replyCons = [i['antipathyCount'] for i in comment_info]            
            replyDate = [dt.strptime(i['modTime'].split('+')[0],"%Y-%m-%dT%H:%M:%S") for i in comment_info]
            replyId = [i['commentNo'] for i in comment_info]

            df_reply = df_reply.append(pd.DataFrame({'articleId':[articleId]*len(replyContent),'replyId':replyId,'replyContent':replyContent,
            'replyUser':replyUser,'replyDate':replyDate,'replyPros':replyPros,'replyCons':replyCons}))
            
            rereply_count = []
            rereplyContent = []
            rereplyUser = []
            rereplyDate = []
            rereplyId = []


            for i in range(comment_count): # 수집한 댓글 개수만큼.

                rereply_count.append(comment_text['result']['commentList'][i]['replyCount'])

                rep_url = 'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=default_society&pool=cbox5&lang=ko&country=KR&objectId=news{}%2C{}&categoryId=&pageSize=100&indexSize=10&groupId=&listType=object&pageType=more&parentCommentNo={}&page=1&userType=&includeAllStatus=true&moreType=next'

                rep_list = []
                rep_url = rep_url.format(oid, aid, replyId[i])
                rep_html = requests.get(rep_url, headers = header)

                rep_test_text = rep_html.text
                rep_test_text = rep_test_text.replace("_callback(","")[:-2]
                rep_comment_text = json.loads(rep_test_text)

                reply_info = rep_comment_text['result']['commentList']
                rereplyUser.extend([i['userName'] for i in reply_info])
                rereplyContent.extend([i['contents'] for i in reply_info])          
                rereplyDate.extend([dt.strptime(i['modTime'].split('+')[0],"%Y-%m-%dT%H:%M:%S") for i in reply_info])
                rereplyId.extend([i['commentNo'] for i in reply_info])

            
            df_rereply = df_rereply.append(pd.DataFrame({'articleId':[articleId]*(sum(rereply_count)),'replyId': list(chain.from_iterable(repeat(id,n) for (id,n) in zip(replyId,rereply_count))),
            'rereplyId':rereplyId,'rereplyContent':rereplyContent,'rereplyUser':rereplyUser,'rereplyDate':rereplyDate}))
                
            if(page_num==comment_count//100+1) or (page_num%100 ==0):
                break
            page_num+=1
            print("FIN")

        tutorial_item['keyword'] = self.keyword
        tutorial_item['article'] = pd.DataFrame({'articleId':[articleId],'articleTitle':[articleTitle],'articleContent':[articleContent],'articleDate':[articleDate]})
        tutorial_item['reply'] = df_reply
        tutorial_item['rereply'] = df_rereply

        time.sleep(random.uniform(0.5, 1))
        yield tutorial_item