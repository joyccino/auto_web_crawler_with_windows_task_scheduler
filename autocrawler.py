import requests
from pandas import DataFrame
from bs4 import BeautifulSoup
import re, os, math
from datetime import datetime
import pymongo, dns
from pymongo import MongoClient
import json

client = pymongo.MongoClient("mongodb+srv://joy:<password>@cluster0.2qfpu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['test']
col = db['test1']

def crawler():
    # 시간 함께 저장 위함
    date = str(datetime.now()) 
    date = date[:date.rfind(':')].replace(' ', '_') 
    date = date.replace(':','시') + '분' 
    # Input 생성
    # 검색할 키워드, 추출할 뉴스 기사 수를 저장하는 변수입니다.
    # query에서 ' ' 를 '+'로 바꾸어주는 이유는 띄어쓰기 시 URL 조건 절에 '+'로 적용되어 요청 인자가 들어가기 때문입니다.
    # query = input('검색 키워드를 입력하세요 : ') 
    query = '코로나'
    query = query.replace(' ', '+') 

    # news_num = int(input('총 필요한 뉴스기사 수를 입력해주세요(숫자만 입력) : ')) 
    news_num = 10

    news_url = 'https://search.naver.com/search.naver?where=news&sm=tab_jum&query={}'

    req = requests.get(news_url.format(query))
    soup = BeautifulSoup(req.text, 'html.parser')

    # 원하는 정보를 담을 변수 생성(딕셔너리)
    # 뉴스 기사 정보를 저장할 딕셔너리를 생성합니다. (key : 번호, value : 뉴스 기사 정보)
    # idx : 현재 뉴스의 번호
    # cur_page : 네이버 뉴스의 웹 페이지입니다. 추출하려는 기사 수가 현재 페이지에 있는 기사보다 많은 경우 다음 페이지로 넘어가야 하기 때문에 현 페이지 번호를 기억하도록 변수로 설정한 것입니다.

    news_dict = {}
    idx = 0
    cur_page = 1

    # parsing 한 HTML 코드에서 원하는 정보 탐색(뉴스 기사 title, URL)
    # idx(현재 뉴스 기사 번호)가 news_num(원하는 뉴스 기사 수) 보다 작은 동안 아래 코드를 실행합니다.
    # table : 뉴스 바운딩 박스(ul 태그)
    # li_list : 뉴스 바운딩 박스 안의 각 뉴스 기사(li 태그)
    # area_list : 뉴스 기사 안의 뉴스 제목, 본문이 담긴 태그(div 태그) 
    # a_list : 각 뉴스기사 내부 title, URL 정보가 담긴 태그(a 태그)
    # news_dict : 뉴스 기사를 담는 딕셔너리
    # key : 뉴스 기사 번호
    # value : 뉴스 기사 title, url을 key로 하는 딕셔너리

    # next_page_url : 현재 수집한 뉴스 기사 수가 부족한 경우 다음 페이지로 넘어가야 하므로 다음 페이지에 해당하는 URL을 추출합니다.
    # 형식은 div 태그이며 class 속성 값이 "sc_page_inner"입니다.
    # 하위에 존재하는 a 태그 내부에 페이지 번호와, URL(href 속성 값) 정보가 있습니다.
    print()
    print('크롤링 중...')

    while idx < news_num:
    ### 네이버 뉴스 웹페이지 구성이 바뀌어 태그명, class 속성 값 등을 수정함(20210126) ###
        table = soup.find('ul',{'class' : 'list_news'})
        li_list = table.find_all('li', {'id': re.compile('sp_nws.*')})
        area_list = [li.find('div', {'class' : 'news_area'}) for li in li_list]
        a_list = [area.find('a', {'class' : 'news_tit'}) for area in area_list]
        
        for n in a_list[:min(len(a_list), news_num-idx)]:
            news_dict[idx] = {'title' : n.get('title'),
                            'url' : n.get('href') }
            idx += 1

        cur_page += 1
        
        pages = soup.find('div', {'class' : 'sc_page_inner'})
        next_page_url = [p for p in pages.find_all('a') if p.text == str(cur_page)][0].get('href')
        
        req = requests.get('https://search.naver.com/search.naver' + next_page_url)
        soup = BeautifulSoup(req.text, 'html.parser')
    #     STEP 4. 최종 데이터 생성
    # 7. 데이터 프레임 변환 및 저장
    # 크롤링한 뉴스 정보가 담긴 딕셔너리(news_dict)를 데이터 프레임(news_df)으로 변환합니다.
    # 그리고 크롤링한 키워드(query)와 크롤링 날짜(date)를 엑셀 파일 명으로 하여 저장합니다.
    # 마지막으로 저장을 완료한 폴더를 띄웁니다.
    print('크롤링 완료')

    print('데이터프레임 변환')
    news_df = DataFrame(news_dict).T

    folder_path = os.getcwd()
    xlsx_file_name = '네이버뉴스_{}_{}.xlsx'.format(query, date)

    news_df.to_excel(xlsx_file_name)

    print('엑셀 저장 완료 | 경로 : {}\\{}'.format(folder_path, xlsx_file_name))
    os.startfile(folder_path)
    
    # DB에 insert
    keyword = query
    df = DataFrame(news_dict).T
    # print(df)
    # records = json.loads(df.T.to_json()).values()
    title = str(df['title'])
    url = str(df['url'])

    post = {"date":date, "keyword":keyword, "title":title, "url":url}
    col.insert_one(post)
    print('done.')


if __name__ == '__main__':
    crawler()

# 스케줄러 사용 위해 간단 배치파일 (*.bat) 만들기
# 서식은 아래와 같다
# "python.exe가/위치하는/폴더 경로/python.exe"(space bar)"작성한/python/파일이/위치하는/경로/CRAW_SHOP.py"

# pause