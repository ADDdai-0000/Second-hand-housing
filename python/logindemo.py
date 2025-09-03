from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
import urllib.request, urllib.error
import gzip
import xlwt
import os
import random
import time
import requests
from fake_useragent import UserAgent

# 随机生成user agent
ua = UserAgent()
BASEURL = "https://bj.lianjia.com/ershoufang/"
COL_TITLE = ["图片链接", "标题", "链接", "地址", "房屋信息", "关注与发布时间", '总价', "单价"]


# 更真实的浏览器配置
def create_stealth_browser():
    chrome_options = Options()

    # 移除自动化特征
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # 更真实的用户代理
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'--user-agent={user_agent}')

    # 窗口大小和位置
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')

    # 其他配置
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')

    # 禁用图片加载加速
    prefs = {
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 1,
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,
        "profile.managed_default_content_settings.plugins": 1,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(options=chrome_options)


# 检测是否被重定向到登录页
def is_login_page(soup):
    """检查是否被重定向到登录页面"""
    title = soup.title.string if soup.title else ""
    return "登录" in title or "login" in title.lower()


# 模拟人类操作行为
def human_like_behavior(browser):
    """模拟人类浏览行为"""
    # 随机滚动页面
    scroll_actions = [
        lambda: browser.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);"),
        lambda: browser.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);"),
        lambda: browser.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
        lambda: browser.execute_script("window.scrollTo(0, 0);")
    ]

    # 执行2-3次随机滚动
    for _ in range(random.randint(2, 3)):
        random.choice(scroll_actions)()
        time.sleep(random.uniform(0.5, 1.5))

    # 随机移动鼠标（模拟）
    time.sleep(random.uniform(1, 2))


# 后几页爬取方法（增强版）
def getData_p_v(pg_begin, pg_end):
    dataList = []
    browser = None

    try:
        browser = create_stealth_browser()

        # 先访问首页建立会话
        print("正在建立会话...")
        browser.get("https://bj.lianjia.com/")
        time.sleep(random.uniform(3, 5))

        for pg in range(pg_begin, pg_end + 1):
            url = BASEURL + "pg" + str(pg) + "/"
            print(f"正在爬取第 {pg} 页: {url}")

            try:
                browser.get(url)

                # 等待页面加载
                try:
                    WebDriverWait(browser, 1000).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sellListContent"))
                    )
                except TimeoutException:
                    print(f"第 {pg} 页加载超时")
                    continue

                # 模拟人类行为
                human_like_behavior(browser)
                time.sleep(random.uniform(3, 5))

                html = browser.page_source
                soup = BeautifulSoup(html, 'html.parser')

                # 检查是否被重定向到登录页
                if is_login_page(soup):
                    print(f"第 {pg} 页被重定向到登录页面，尝试重新建立会话...")
                    # 清除cookies并重新访问
                    browser.delete_all_cookies()
                    browser.get("https://bj.lianjia.com/")
                    time.sleep(random.uniform(5, 8))
                    continue

                # 查找房源列表
                house_list1 = soup.find_all('li', class_='clear LOGVIEWDATA LOGCLICKDATA')
                house_list2 = soup.find_all('li', class_='clear LOGCLICKDATA')
                house_list3 = soup.find_all('li', class_='clear LOGVIEWDATA')
                house_list = house_list1 + house_list2 + house_list3
                # if len(house_list) == 0:
                #     print(f"第 {pg} 页未找到房源信息，可能被反爬")
                #
                #     # 保存页面用于调试
                #     with open(f'debug_page_{pg}.html', 'w', encoding='utf-8') as f:
                #         f.write(html)
                #     print(f"已保存第 {pg} 页的HTML到 debug_page_{pg}.html")
                #
                #     # 检查是否有验证码
                #     if soup.find('div', class_='verifycode-wrap'):
                #         print("检测到验证码，需要手动处理")
                #         input("请手动处理验证码后按回车继续...")
                #     continue

                # 开始爬取信息
                findHoustData(dataList, house_list)
                print(f"第 {pg} 页爬取完成，获取到 {len(house_list)} 条房源信息")

                # 随机延迟，模拟人工操作
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                print(f"爬取第 {pg} 页时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    except Exception as e:
        print(f"浏览器操作发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if browser:
            browser.quit()
            print("浏览器已关闭")

    return dataList


# 原有的数据提取函数保持不变...
def findHoustData(dataList, house_list):
    for house in house_list:
        datas = []
        # 1.获取图片以及相关信息
        findImg(datas, house)

        # 2.#获取链接和标题
        findTitle(datas, house)

        # 3.获取地址信息
        finPos(datas, house)

        # 4.获取房屋信息
        findHouseInfo(datas, house)

        # 5.关注与发布时间
        findFollow(datas, house)

        # 6. 获取价格信息
        findPrice(datas, house)

        dataList.append(datas)


def findPrice(datas, house):
    price_div = house.find('div', class_='priceInfo')
    house_data = {}
    if price_div:
        # 获取总价
        total_price_div = price_div.find('div', class_='totalPrice totalPrice2')
        if total_price_div:
            total_price_span = total_price_div.find('span')
            if total_price_span:
                house_data['总价'] = total_price_span.get_text(strip=True) + "万"
            else:
                house_data['总价'] = "未知"
        else:
            house_data['总价'] = "未知"

        # 获取单价
        unitPrice_div = price_div.find('div', class_='unitPrice')
        if unitPrice_div:
            unitPrice_span = unitPrice_div.find('span')
            if unitPrice_span:
                house_data['单价'] = unitPrice_span.get_text(strip=True)
            else:
                house_data['单价'] = "未知"
        else:
            house_data['单价'] = "未知"

        datas.append(house_data["总价"])
        datas.append(house_data["单价"])


def findFollow(datas, house):
    follow_div = house.find('div', class_='followInfo')
    if follow_div:
        follow = follow_div.get_text(strip=True)
        # dataList.append({"关注与发布时间": follow})
        datas.append(follow)


def findHouseInfo(datas, house):
    house_div = house.find('div', class_='houseInfo')
    if house_div:
        house_info = house_div.get_text(strip=True)
        # dataList.append({"房屋信息": house_info})
        datas.append(house_info)


def finPos(datas, house):
    position_div = house.find('div', class_='positionInfo')
    if position_div:
        links = position_div.find_all('a')
        posi = ""
        for link in links:
            posi += link.get_text() + " "
        # dataList.append({"地址": posi.strip()})
        datas.append(posi.strip())


def findTitle(datas, house):
    title_div = house.find('div', class_='title')
    if title_div:
        link_tag = title_div.find('a')
        if link_tag:
            href = link_tag.get('href')  # 获取超链接
            title = link_tag.get_text(strip=True)  # 直接获取标题文本<a href = "">title<a/>
            # dataList.append({"标题": title})
            # dataList.append({"链接": href})
            datas.append(title)
            datas.append(href)


def findImg(datas, house):
    img = house.find('img', class_='lj-lazy')
    if img:
        # 获取真实图片地址
        real_src = img.get('data-original')
        # 获取图片标题（非内容标题）
        # alt_text = img.get('alt', '')

        if real_src and '.jpg' in real_src and 'blank.gif' not in real_src:
            # dataList.append({'图片链接': real_src})
            # dataList.append({'图片标题': alt_text})
            datas.append(real_src)
            # dataList.append(alt_text)


def saveData(data_list, save_dir="lianjia_datas"):
    if not data_list:
        print("没有数据需要保存")
        return

    print("正在保存数据...")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = book.add_sheet('链家二手房', cell_overwrite_ok=True)

    # 写入标题行
    for i in range(len(COL_TITLE)):
        sheet.write(0, i, COL_TITLE[i])

    # 写入数据
    for i, data in enumerate(data_list):
        for j in range(min(len(data), len(COL_TITLE))):
            sheet.write(i + 1, j, str(data[j]))

    # 生成文件名,如DATA_NAME_1-10
    page = input("输入页数")
    file_path = os.path.join(save_dir, f"lianjia_data_{page}.xls")
    book.save(file_path)
    print(f"数据已保存到: {file_path}")

# 改进的main函数
def main():
    try:
        print("开始爬取链家二手房数据...")

        data = getData_p_v(1, 33)

        if not data:
            print("没有获取到任何数据")
            return
        return data
    except Exception as e:
        print(e)

    #     print("\n爬取结果汇总:")
    #     print("=" * 100)
    #
    #     for i, item in enumerate(data):
    #         print(f"\n第 {i + 1} 条数据:")
    #         print("-" * 50)
    #         for j in range(min(len(COL_TITLE), len(item))):
    #             print(f"{COL_TITLE[j]}: {item[j]}")
    #
    #     print("=" * 100)
    #     print(f"共爬取到 {len(data)} 条数据")
    #
    #     saveData(data)
    #
    # except Exception as e:
    #     print(f"程序执行出错: {str(e)}")
    #     import traceback
    #     traceback.print_exc()
