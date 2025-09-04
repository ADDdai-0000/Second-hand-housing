"""
    @Project: 58同城二手房爬虫
    @Method: selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import random
import os
import xlwt


COL_TITLE = ["标题", "总价", "单价", "房屋信息"]
BASEURL = "https://hz.58.com/ershoufang/"
save_dir = "../../58_secondary_datas"

options = Options()
# options.add_argument("--headless")  # 无头模式
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")  # 添加最大化窗口


def getData(pg_begin, pg_end):
    dataList = []
    try:
        browser = webdriver.Chrome(options=options)
        print("正在创建对话...")
        time.sleep(2)

        # 初始化所有存储列表
        titles = []
        prices = []
        unitPrices = []
        houseInfos = []  # 存储完整的房屋信息

        for pg in range(pg_begin, pg_end + 1):
            print(f"正在爬取第 {pg} 页...")
            browser.get(BASEURL + f"pn{pg}/")
            wait = WebDriverWait(browser, 60)
            time.sleep(3)  # 等待页面加载

            # 在页面加载后执行滚动
            human_like_scroll(browser, scroll_time=3)

            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 提取标题
            page_titles = [t.get_text(strip=True) for t in soup.find_all("h3", class_="property-content-title-name")]
            titles.extend(page_titles)

            # 提取总价
            page_prices = [p.get_text(strip=True) for p in soup.find_all("span", class_="property-price-total-num")]
            prices.extend(page_prices)

            # 提取单价
            page_unitPrices = [up.get_text(strip=True) for up in soup.find_all("p", class_="property-price-average")]
            unitPrices.extend(page_unitPrices)

            # 提取房屋信息
            houseInfo_divs = soup.find_all("div", class_="property-content-info")
            for houseInfo_div in houseInfo_divs:
                info_items = houseInfo_div.find_all("p", class_="property-content-info-text")
                house_info = " | ".join([item.get_text(strip=True) for item in info_items])
                houseInfos.append(house_info)

            print(f"第 {pg} 页爬取完成，找到 {len(page_titles)} 个房源")

        # 打印结果
        print(f"\n共爬取到 {len(prices)} 套二手房信息：")
        print("=" * 80)

        for i in range(min(5, len(prices))):  # 只打印前5条作为示例
            print(f"第 {i + 1} 套二手房:")
            print(f"标题: {titles[i]}")
            print(f"总价: {prices[i]} 万元")
            print(f"单价: {unitPrices[i]} 元/㎡")
            print(f"房屋信息: {houseInfos[i]}")
            print("-" * 50)

        browser.quit()
        print("浏览器已关闭")

        # 将数据整理成列表返回
        for i in range(len(prices)):
            dataList.append({
                "title": titles[i],
                "total_price": prices[i],
                "unit_price": unitPrices[i],
                "house_info": houseInfos[i]
            })

        return dataList

    except Exception as e:
        print(f"发生异常: {str(e)}")
        if 'browser' in locals():
            browser.quit()
        return []


def human_like_scroll(driver, scroll_time=5):
    """模拟真人滚动行为"""
    print("开始模拟滚动...")
    for i in range(scroll_time):
        scroll_amount = random.randint(200, 800)  # 增加滚动距离
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        wait_time = random.uniform(0.5, 2.0)  # 增加等待时间
        time.sleep(wait_time)
        print(f"滚动 {i+1}/{scroll_time}, 距离: {scroll_amount}px, 等待: {wait_time:.2f}s")


def saveData(dataList, save_Dir=save_dir):
    """保存数据到Excel文件"""
    if not dataList:
        print("没有数据要保存")
        return False

    if not os.path.exists(save_Dir):
        os.makedirs(save_Dir)
        print(f"创建目录: {save_Dir}")

    try:
        book = xlwt.Workbook(encoding="utf-8", style_compression=0)
        sheet = book.add_sheet("58二手房", cell_overwrite_ok=True)

        # 写入标题行
        for col, title in enumerate(COL_TITLE):
            sheet.write(0, col, title)

        # 写入数据行 - 这里修复了主要的错误
        for row, data in enumerate(dataList, 1):  # 从第2行开始
            values = list(data.values())
            for col, value in enumerate(values):
                sheet.write(row, col, str(value))

        page = input("请输入页数标识（如1-5）: ")
        file_path = os.path.join(save_Dir, f"58_secondary_{page}.xls")
        book.save(file_path)
        print(f"数据已保存到 {file_path}")
        print(f"共保存 {len(dataList)} 条数据")
        return True

    except Exception as e:
        print(f"保存数据时发生错误: {str(e)}")
        return False

def waitForPageLoaded(driver,timeout=10):
    """人工验证检测环节"""
    try:
        print("等待手动验证...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "property-content-title-name"))
        )

        print("验证完成")
        return True

    except Exception as e:
        print(f"验证失败: {str(e)}")


def main():
    """主函数"""
    print("开始爬取58同城二手房数据...")

    # 获取数据
    data = getData(1, 60)

    if data:
        print(f"\n成功爬取 {len(data)} 条数据")

        # 保存数据
        success = saveData(data)
        if success:
            print("数据保存成功！")
        else:
            print("数据保存失败！")
    else:
        print("没有获取到数据")


if __name__ == "__main__":
    main()