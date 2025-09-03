from urllib.parse import urlparse

from bs4 import BeautifulSoup
import re
import urllib.request, urllib.error
import gzip
import xlwt
import os
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
COL_TITLE = ["图片链接","标题","链接","地址","房屋信息","关注与发布时间",'总价',"单价"]


def getData(baseUrl):
    dataList = []
    #一页最多30个,这里暂时只爬一页
    for i in range(1, 2):
        # 修正URL格式：需要在页码后加斜杠
        url = baseUrl + "pg" + str(i) + "/"
        print(f"正在请求URL: {url}")

        html = askUrl(url)
        if not html:
            print("获取HTML失败")
            continue

        soup = BeautifulSoup(html, 'html.parser')

        # 先检查是否找到了房源列表
        house_list = soup.find_all('li', class_='clear LOGVIEWDATA LOGCLICKDATA')
        print(f"找到 {len(house_list)} 个房源")

        #AI的防反爬
        if len(house_list) == 0:
            print("可能被反爬了，页面内容：")
            print(html[:500])  # 打印前500字符查看内容
            continue

        #开始爬取信息,全部塞入dataList
        for house in house_list:
            # 1.获取图片以及相关信息
            img = house.find('img', class_='lj-lazy')
            if img:
                #获取真实图片地址
                real_src = img.get('data-original')
                #获取图片标题（非内容标题）
                # alt_text = img.get('alt', '')

                if real_src and '.jpg' in real_src and 'blank.gif' not in real_src:
                    # dataList.append({'图片链接': real_src})
                    # dataList.append({'图片标题': alt_text})
                    dataList.append(real_src)
                    # dataList.append(alt_text)

            # 2.#获取链接和标题
            title_div = house.find('div', class_='title')
            if title_div:
                link_tag = title_div.find('a')
                if link_tag:
                    href = link_tag.get('href')     #获取超链接
                    title = link_tag.get_text(strip=True)   #直接获取标题文本<a href = "">title<a/>
                    # dataList.append({"标题": title})
                    # dataList.append({"链接": href})
                    dataList.append(title)
                    dataList.append(href)

            # 3.获取地址信息
            position_div = house.find('div', class_='positionInfo')
            if position_div:
                links = position_div.find_all('a')
                posi = ""
                for link in links:
                    posi += link.get_text() + " "
                # dataList.append({"地址": posi.strip()})
                dataList.append(posi.strip())

            # 4.获取房屋信息
            house_div = house.find('div', class_='houseInfo')
            if house_div:
                house_info = house_div.get_text(strip=True)
                # dataList.append({"房屋信息": house_info})
                dataList.append(house_info)

            # 5.关注与发布时间
            follow_div = house.find('div', class_='followInfo')
            if follow_div:
                follow = follow_div.get_text(strip=True)
                # dataList.append({"关注与发布时间": follow})
                dataList.append(follow)

            # 6. 获取价格信息
            price_div = house.find('div', class_='priceInfo')
            house_data = {}
            if price_div:
                #获取总价
                total_price_div = price_div.find('div', class_='totalPrice totalPrice2')
                if total_price_div:
                    total_price_span = total_price_div.find('span')
                    if total_price_span:
                        house_data['总价'] = total_price_span.get_text(strip=True) + "万"
                    else:
                        house_data['总价'] = "未知"
                else:
                    house_data['总价'] = "未知"

                #获取单价
                unitPrice_div = price_div.find('div', class_='unitPrice')
                if unitPrice_div:
                    unitPrice_span = unitPrice_div.find('span')
                    if unitPrice_span:
                        house_data['单价'] = unitPrice_span.get_text(strip=True)
                    else:
                        house_data['单价'] = "未知"
                else:
                    house_data['单价'] = "未知"

                dataList.append(house_data["总价"])
                dataList.append(house_data["单价"])



    return dataList

#获取网页html文件
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

#下载网页图片

def download_images(data_list, save_dir="lianjia_images"):
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"创建目录: {save_dir}")

    # 下载计数器
    count = 0

    for i, item in enumerate(data_list):
        image_url = item['image_url']
        title = item['title']

        # 处理标题，移除非法字符
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]  # 限制文件名长度

        # 从URL中提取文件扩展名
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        if '.' in path:
            ext = os.path.splitext(path)[1]
            # 确保扩展名是图片格式
            if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'  # 默认使用jpg
        else:
            ext = '.jpg'

        # 生成文件名
        filename = f"{i + 1:03d}_{safe_title}{ext}"
        filepath = os.path.join(save_dir, filename)

        try:
            # 下载图片
            print(f"正在下载: {filename}")

            # 使用requests库下载图片
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()  # 检查请求是否成功

            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)

            count += 1
            print(f"成功下载: {filename}")

            # 添加延迟，避免请求过于频繁
            time.sleep(0.5)

        except Exception as e:
            print(f"下载失败 {image_url}: {e}")

    print(f"下载完成! 成功下载 {count}/{len(data_list)} 张图片")

# 测试
def demo():
    url = "https://bj.lianjia.com/ershoufang/pg1/"
    print(f"demo测试网页: {url}")
    html = askUrl(url)
    soup = BeautifulSoup(html, 'html.parser')
    house_list = soup.find_all('li', class_='clear LOGVIEWDATA LOGCLICKDATA')
    if house_list:
        first_house = house_list[0]
        title_div = first_house.find('div', class_='title')

        if title_div:
            # 查找<a>标签
            link_tag = title_div.find('a')
            if link_tag:
                href = link_tag.get('href')
                title_text = link_tag.get_text(strip=True)
                print(f"链接: {href}")
                print(f"标题: {title_text}")
            else:
                print("未找到<a>标签")
        else:
            print("未找到title div")


#输出
data = getData(BASEURL)
count = 0
for item in data:
    if count % len(COL_TITLE) == 0:
        print("-" * 100)
    count = (count+1) % len(COL_TITLE)
    print(f"{COL_TITLE[count]} : {item}")
print("-" * 100)
# download_images(data)
print(f"共爬取到 {len(data)} 条数据")

# demo()