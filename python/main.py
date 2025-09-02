from bs4 import BeautifulSoup
import re
import urllib.request, urllib.error
import gzip
import xlwt
import time
import requests

BASEURL = "https://bj.lianjia.com/ershoufang/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def getData(baseUrl):
    dataList = []
    for i in range(1, 2):
        # 修正URL格式：需要在页码后加斜杠
        url = baseUrl + "pg" + str(i) + "/"
        print(f"正在请求URL: {url}")

        html = askUrl(url)
        if not html:
            print("获取HTML失败")
            continue

        # if "redirect" in html.lower() or "location.href" in html.lower():
        #     print("可能被重定向了，尝试添加更多请求头")
        #     continue

        soup = BeautifulSoup(html, 'html.parser')

        # 先检查是否找到了房源列表
        house_list = soup.find_all('li', class_='clear LOGVIEWDATA LOGCLICKDATA')
        print(f"找到 {len(house_list)} 个房源")

        if len(house_list) == 0:
            print("可能被反爬了，页面内容：")
            print(html[:500])  # 打印前500字符查看内容
            continue

        for house in house_list:
            img = house.find('img', class_='lj-lazy')
            if img:
                real_src = img.get('data-original')
                alt_text = img.get('alt', '')

                # 简化过滤条件：只要包含.jpg且不包含blank.gif
                if real_src and '.jpg' in real_src and 'blank.gif' not in real_src:
                    print(f"图片链接: {real_src}")
                    print(f"标题: {alt_text}")
                    print("-" * 50)
                    dataList.append({
                        'image_url': real_src,
                        'title': alt_text
                    })

    return dataList


def askUrl(url):
    request = urllib.request.Request(url, headers=headers)
    html = ""

    try:
        response = urllib.request.urlopen(request, timeout=10)
        # 检查响应是否经过gzip压缩
        content_encoding = response.info().get('Content-Encoding', '')
        content = response.read()

        if 'gzip' in content_encoding:
            html = gzip.decompress(content).decode('utf-8', errors='ignore')
        else:
            html = content.decode('utf-8', errors='ignore')

    except Exception as e:
        print(f"请求错误: {e}")

    return html


# 测试
data = getData(BASEURL)
print(f"共爬取到 {len(data)} 条数据")