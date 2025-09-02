"""
    @Project: 豆瓣评分系统爬虫玩玩
    @File: request_package.py
    @Author: 111
"""

from bs4 import BeautifulSoup
import re
import urllib.request,urllib.error
import xlwt

findLink = re.compile(r'<a href="(.*?)">')
findImgSrc = re.compile(r'<img(.*)src="(.*?)"',re.S)
findTitle = re.compile(r'<span class="title">(.*)</span>')
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*?)</span>')
findJudge = re.compile(r'<span>(\d*)人评价</span>')
findInq = re.compile(r'<p class="quote">\s*<span>(.*?)</span>\s*</p>',re.S)
findBd = re.compile(r'<p>(.*?)</p>',re.S)

def main():
    baseUrl = 'https://movie.douban.com/top250?start='
    dataList = getData(baseUrl)
    print(dataList)
    savePath = '豆瓣top250.xls'
    saveData(dataList,savePath)

def getData(baseUrl):
    dataList = []
    for i in range(1):
        url = baseUrl + str(i * 25)
        html = askURL(url)
        soup = BeautifulSoup(html, 'html.parser')
        for item in soup.find_all('div', class_='item'):
            data = []
            item = str(item)
            link = re.findall(findLink,item)[0]
            data.append(link)

            titles = re.findall(findTitle,item)
            if len(titles) == 2:
                ctitle = titles[0]
                data.append(ctitle)
                otitle = titles[1].replace("\xa0","")
                otitle = otitle.replace("/","")
                data.append(otitle)
            elif len(titles) == 1:
                data.append(titles[0])
                data.append("None")
            else:
                data.append("None")
                data.append("None")

            # bd = re.findall(findBd, item)[0]
            # bd = re.sub(r'<br\s*/?>(\s+)?', ' ', bd)  # 处理各种形式的<br>标签
            # bd = re.sub(r'\xa0', '', bd)
            # bd = re.sub(r'/', '', bd)
            # bd = re.sub(r'\n', ' ', bd)
            # bd = re.sub(r'\s+', ' ', bd)
            # data.append(bd.strip())

            bd = re.findall(findBd, item)[0]
            # 在<br>位置添加明确的分隔符
            bd = re.sub(r'<br\s*/?>(\s+)?', ' | ', bd)  # 用竖线分隔
            # 移除所有HTML标签（更彻底）
            bd = re.sub(r'<[^>]+>', '', bd)
            bd = re.sub(r'\xa0', ' ', bd)
            bd = re.sub(r'/', ' ', bd)
            bd = re.sub(r'\n', ' ', bd)
            bd = re.sub(r'\s+', ' ', bd)
            data.append(bd.strip())

            dataList.append(data)


    return dataList

def saveData(datalist, savePath):
    print("saving...")
    book = xlwt.Workbook(encoding='utf-8',style_compression=0)
    sheet1 = book.add_sheet('豆瓣top25',cell_overwrite_ok=True)
    col = ("电影详情链接","电影中文名","电影其他名","相关信息")
    for i in range(len(col)):
        sheet1.write(0,i,col[i])

    for i in range(len(datalist)):
        data = datalist[i]
        for j in range(len(data)):
            sheet1.write(i+1,j,data[j])
    book.save(savePath)

#得到一个指定的html内容
def askURL(url):
    head = {  # 模拟浏览器头部信息，向豆瓣服务器发送消息
        "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 80.0.3987.122  Safari / 537.36"
    }
    # 用户代理，表示告诉豆瓣服务器，我们是什么类型的机器、浏览器（本质上是告诉浏览器，我们可以接收什么水平的文件内容）
    request = urllib.request.Request(url, headers=head)
    html = ""

    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf-8')
    except urllib.error.URLError as e:
        if hasattr(e, 'reason'):
            print(e.reason)
        if hasattr(e, 'code'):
            print(e.code)

    return html

if __name__ == '__main__':
    main()