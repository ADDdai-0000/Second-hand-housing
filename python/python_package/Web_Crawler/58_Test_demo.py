"""
    @Project: 58同城二手房爬虫
    @Method: selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import os
import xlwt

# 更新列标题，添加标签和VR信息
COL_TITLE = ["标题", "总价", "单价", "房屋信息", "房屋标签", "VR房源"]
BASEURL = "https://hz.58.com/ershoufang/"
save_dir = "../../58_secondary_datas"

options = Options()
# options.add_argument("--headless")  # 无头模式
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 添加用户代理
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]
options.add_argument(f"user-agent={random.choice(user_agents)}")


def check_verification(browser):
    """检查是否需要验证"""
    try:
        # 检查常见的验证码元素
        verification_selectors = [
            "#verify_img",  # 验证码图片
            ".verify-code",  # 验证码框
            ".geetest_btn",  # 极验验证
            ".captcha",  # 验证码
            "#nc_1_n1z",  # 滑块验证
            ".vcode",  # 验证码
        ]

        for selector in verification_selectors:
            elements = browser.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print("⚠️ 检测到验证码，请手动处理...")
                return True

        # 检查是否跳转到验证页面
        if "verify" in browser.current_url or "security" in browser.current_url:
            print("⚠️ 检测到验证页面，请手动处理...")
            return True

        return False

    except Exception as e:
        print(f"检查验证时出错: {e}")
        return False


def wait_for_page_loaded(browser, timeout=30):
    """等待页面完全加载并检查验证"""
    try:
        print("等待页面加载...")

        # 等待主要内容加载
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "property-content-title-name"))
        )

        # 检查是否需要验证
        if check_verification(browser):
            print("⏳ 需要验证，请手动完成验证后按回车继续...")
            input("完成后按回车键继续爬取...")
            time.sleep(3)  # 给一些时间让页面重新加载

        print("✅ 页面加载完成")
        return True

    except Exception as e:
        print(f"页面加载超时或出错: {e}")
        return False


def human_like_scroll(driver, scroll_time=5):
    """模拟真人滚动行为"""
    print("开始模拟滚动...")
    for i in range(scroll_time):
        scroll_amount = random.randint(200, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        wait_time = random.uniform(0.5, 2.0)
        time.sleep(wait_time)
        print(f"滚动 {i + 1}/{scroll_time}, 距离: {scroll_amount}px, 等待: {wait_time:.2f}s")


def extract_house_tags(house_item):
    """提取房屋标签信息"""
    tags = []

    # 查找标签元素
    tag_elements = house_item.find_all("span", class_="property-content-info-tag")
    for tag in tag_elements:
        tag_text = tag.get_text(strip=True)
        if tag_text:
            tags.append(tag_text)

    return " | ".join(tags) if tags else "无标签"


def check_vr_house(house_img):
    """检查是否为VR房源"""
    vr_elements = house_img.find_all("div", class_="property-image-vr")
    return "是" if vr_elements else "否"


def getData(pg_begin, pg_end):
    dataList = []
    browser = None
    try:
        browser = webdriver.Chrome(options=options)
        print("正在创建对话...")
        time.sleep(2)

        # 初始化所有存储列表
        titles = []
        prices = []
        unitPrices = []
        houseInfos = []
        houseTags = []  # 存储房屋标签
        vrHouses = []  # 存储VR房源信息

        for pg in range(pg_begin, pg_end + 1):
            print(f"正在爬取第 {pg} 页...")
            browser.get(BASEURL + f"pn{pg}/")

            # 等待页面加载并检查验证
            if not wait_for_page_loaded(browser):
                print(f"第 {pg} 页加载失败，跳过...")
                continue

            # 模拟真人滚动
            human_like_scroll(browser, scroll_time=3)

            # 再次检查验证（滚动后可能触发）
            if check_verification(browser):
                print("⏳ 滚动后触发验证，请手动处理...")
                input("完成后按回车键继续...")
                time.sleep(3)

            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 找到所有房屋项目
            house_imgs = soup.find_all("div", class_="property-image")
            house_items = soup.find_all("div", class_="property-content")  # 可能需要调整选择器
            if len(house_items) != len(house_imgs):
                print(f"{len(house_items)} != {len(house_imgs)}")
                break
            # 如果没有找到房屋项目，尝试其他选择器
            if not house_items:
                house_items = soup.find_all("li", class_="property") or soup.find_all("div", class_="house-cell")

            print(f"找到 {len(house_items)} 个房屋项目")

            for house_item in house_items:
                # 提取标题
                title_elem = house_item.find("h3", class_="property-content-title-name")
                title = title_elem.get_text(strip=True) if title_elem else "无标题"

                # 提取总价
                price_elem = house_item.find("span", class_="property-price-total-num")
                price = price_elem.get_text(strip=True) if price_elem else "未知"

                # 提取单价
                unit_price_elem = house_item.find("p", class_="property-price-average")
                unit_price = unit_price_elem.get_text(strip=True) if unit_price_elem else "未知"

                # 提取房屋信息
                house_info_div = house_item.find("div", class_="property-content-info")
                house_info = ""
                if house_info_div:
                    info_items = house_info_div.find_all("p", class_="property-content-info-text")
                    house_info = " | ".join([item.get_text(strip=True) for item in info_items])

                # 提取房屋标签
                tags = extract_house_tags(house_item)



                # 添加到列表
                titles.append(title)
                prices.append(price)
                unitPrices.append(unit_price)
                houseInfos.append(house_info)
                houseTags.append(tags)

            for house_img in house_imgs:
                # 检查是否为VR房源
                vr_info = check_vr_house(house_img)
                vrHouses.append(vr_info)

            print(f"第 {pg} 页爬取完成，找到 {len(titles)} 个有效房源")

            # 随机延迟，避免请求过于频繁
            delay = random.uniform(2, 5)
            print(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)

        # 整理数据
        for i in range(len(titles)):
            dataList.append({
                "title": titles[i],
                "total_price": prices[i],
                "unit_price": unitPrices[i],
                "house_info": houseInfos[i],
                "house_tags": houseTags[i],
                "vr_house": vrHouses[i]
            })

        return dataList

    except Exception as e:
        print(f"发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if browser:
            browser.quit()
            print("浏览器已关闭")


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

        # 写入数据行
        for row, data in enumerate(dataList, 1):
            sheet.write(row, 0, data["title"])
            sheet.write(row, 1, data["total_price"])
            sheet.write(row, 2, data["unit_price"])
            sheet.write(row, 3, data["house_info"])
            sheet.write(row, 4, data["house_tags"])
            sheet.write(row, 5, data["vr_house"])

        # 自动生成文件名（包含时间戳）
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        extra_text = input("请输入页数")
        file_path = os.path.join(save_Dir, f"58_secondary_{timestamp}_{extra_text}.xls")

        book.save(file_path)
        print(f"✅ 数据已保存到 {file_path}")
        print(f"📊 共保存 {len(dataList)} 条数据")
        return True

    except Exception as e:
        print(f"❌ 保存数据时发生错误: {str(e)}")
        return False


def main():
    """主函数"""
    print("开始爬取58同城二手房数据...")
    print("如果出现验证码，请手动完成验证后按回车继续")
    print("-" * 50)

    # 获取数据
    data = getData(1, 100)  # 可以调整爬取的页数

    if data:
        print(f"\n✅ 成功爬取 {len(data)} 条数据")

        # 打印一些样本数据
        for i in range(min(3, len(data))):
            print(f"\n样本数据 {i + 1}:")
            print(f"标题: {data[i]['title']}")
            print(f"标签: {data[i]['house_tags']}")
            print(f"VR房源: {data[i]['vr_house']}")

        # 保存数据
        success = saveData(data)
        if success:
            print("🎉 数据保存成功！")
        else:
            print("❌ 数据保存失败！")
    else:
        print("❌ 没有获取到数据，可能被反爬或网络问题")


if __name__ == "__main__":
    main()