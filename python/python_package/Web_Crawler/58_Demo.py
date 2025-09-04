import requests
import time, random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASEURL = "https://hz.58.com/ershoufang/"
ua = UserAgent()


COOKIES = r'id58=CkwAGmi5A42Dbwi5C5i4Ag==; 58tj_uuid=cf45b49f-5344-4310-9490-0d94a5033f1a; new_uv=1; utm_source=; spm=; als=0; xxzlxxid=pfmxf+cDtoKz0tgHULztDKQQ4Qg5bKyQw2Ec0kH5vjvIbSKM1khQmtIlchksgSNMa+HU; 58_ctid=79; is_58_pc=1; commontopbar_new_city_info=18%7C%E6%9D%AD%E5%B7%9E%7Chz; aQQ_ajkguid=DB46F7FA-5759-41A8-85D0-SX0904111540; sessid=9249DDE1-151C-4C6E-240A-SX0904111540; xxzlclientid=61b10eda-d525-451a-9ed0-1756955741270; wmda_uuid=7979241439c0f3342a63a265ab85f355; wmda_new_uuid=1; wmda_visited_projects=%3B8788302075828; ved_loupans=530591%3A522885%3A521774; Hm_lvt_3f405f7f26b8855bc0fd96b1ae92db7e=1756955885; Hm_lpvt_3f405f7f26b8855bc0fd96b1ae92db7e=1756955885; HMACCOUNT=36518FC9445DFC2D; ipcity=hz%7C%u676D%u5DDE; myfeet_tooltip=end; new_session=0; 58home=hz; ajk-appVersion=; fzq_h=26fb92c49c4d1df26dff38094b97934b_1756955900209_2f8438907a894e4aaa6d1d8d7c488c3e_605365805; weapp_source=; wmda_report_times=11; lp_lt_ut=468eee181298175eedb08f8c6c12de6b; init_refer=; ctid=79; f=n; commontopbar_new_city_info=79%7C%E6%9D%AD%E5%B7%9E%7Chz; city=hz; commontopbar_ipcity=hz%7C%E6%9D%AD%E5%B7%9E%7C0; wmda_session_id_2385390625025=1756958634879-592309cd-ccf4-4689-b1a6-8afc036161ec; wmda_uuid=dd52df434366e6b8e9dc55064f1cb5af; wmda_new_uuid=1; wmda_session_id_10104579731767=1756958650201-d3d6498c-aa9e-4621-8b50-99085a9ad9e9; wmda_visited_projects=%3B8788302075828%3B2385390625025%3B10104579731767; wmda_report_times=17; www58com="UserID=114562380432713&UserName=ADDtestssss"; 58cooper="userid=114562380432713&username=ADDtestssss"; 58uname=ADDtestssss; passportAccount="atype=0&bstate=0"; PPU=UID=114562380432713&UN=ADDtestssss&TT=deec4fdb84df9bea8c18c939255e9c2d&PBODY=ZfFHBGpZqXx89TEAHCfOq29-GQOhcnNTw0aM6fpvCNG6r1B0QQ1-FsUHpm8deaxOq7gVv2f4rRdYz0jqIUbeyr4NilqXY-bUJcAOkGEp3CDIzoWoEX_1w-FOqZHT_aCyVUO4IK0gnpHeGUFm8fBXVCZPvPm4uQ0TgyqGgnjb81w&VER=1&CUID=L_Sk9E7i2t1qI9armbpA0A; xxzlbbid=pfmbM3wxMDI5MnwxLjEwLjB8MTc1Njk1ODkwMTAxMTk1ODc3OXxsbG5qdzkxK25IcGQvNHZZRERPNHg0c0RPSTRWcGVnM29CUk92MFNFd1c0PXxjZTA0MTJmYjIyZjhlNjZhZjM0MDMyNDc3OTM4NGZjZl8xNzU2OTU4OTAxMzI0X2ZiYTMyOTE5Mjk4MzQ3YjFiMmMxNTJiMzlmNTliOTdhXzYwNTM2NTgwNXwwOGIwMDM0NTc2OTU4NmRhY2QxM2ViNDQ4OWVhYjVjNl8xNzU2OTU4OTAwMDE2XzI1NQ=='

headers = {
    "User-Agent": ua.random,
    "Referer": "https://hz.58.com/ershoufang/",
    "Cookie": COOKIES,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}


def askUrl(url):
    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"请求错误: {e}")
        return ""

def askUrlRetries(url,retries = 3):
    for attempt in range(retries):
        try:
            print(f"正在第{attempt+1}/{retries}次重新请求...")
            time.sleep(random.uniform(0.5, 1.5))
            headers["User-Agent"] = ua.random
            response = requests.session().get(url, headers=headers, timeout=10)
            response.raise_for_status()
            if response.text.find("property-price-total-num") != -1:
                return response.text
            with open("retries_debug.txt", "w", encoding="utf-8") as f:
                f.write(response.text)

        except Exception as e:
            print(f"第{attempt+1}/{retries}次重新请求失败: {e}")

    return None


def getData(baseUrl = BASEURL):
    for i in range(1, 2):  # 测试 2 页
        headers["User-Agent"] = ua.random
        url = baseUrl + f"pn{i}/"
        html = askUrlRetries(url)
        if html == None:
            print("爬取失败")
            return []
        soup = BeautifulSoup(html, 'html.parser')

        link_sections = soup.find_all('section', class_='list')
        if not link_sections:
            print(f"未获取到网页信息，page{i} 可能被反爬了")
            # print(html)
            continue

        with open("html_debug.txt", "w",encoding="utf-8") as f:\
            f.write(html)

        link_section = link_sections[0].find_all('a', href=True)[0]
        price = link_section.find_all('span', class_='property-price-total-num')[0].get_text()
        unitPrice = link_section.find_all('p', class_='property-price-average')[0].get_text().strip()
        print(f"总价 : {price}")
        print(f"单价 : {unitPrice}")
    return

"""单界面测试"""
        # print("开始测试第一个链接")
        # print(link_section[0]['href'])
        # if link_section[0]['href'].find("ershoufang") != -1:
        #     print("这是个二手房")
        # else:
        #     print("这是个新房")
        # content = link_section[0]
        # price = content.find_all('span', class_='property-price-total-num')[0].get_text()
        # print(price)


getData(BASEURL)
