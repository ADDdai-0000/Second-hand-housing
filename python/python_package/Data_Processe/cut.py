import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import pandas as pd
import warnings


def cut(file):
    # 如果是DataFrame（Excel已读取），直接处理
    if isinstance(file, pd.DataFrame):
        house_data = file.copy()
    else:  # 如果是HTML文件，先解析
        soup = BeautifulSoup(file, 'html.parser')
        price_elements = soup.find_all("div", class_="priceInfo")
        total_prices = [p.find("span").get_text(strip=True) for p in price_elements if p.find("span")]

        house_info = [h.get_text(strip=True) for h in soup.find_all("div", class_="houseInfo")]
        follow_info = [f.get_text(strip=True) for f in soup.find_all("div", class_="followInfo")]

        house_data = pd.DataFrame({
            "总价": total_prices,
            "房屋信息": house_info,
            "关注与发布时间": follow_info
        })

    # 1. 分割"房屋相关信息"
    if "房屋信息" in house_data.columns:
        house_details = house_data["房屋信息"].str.extractall(
            r"(?P<户型>.*?) \| (?P<面积>.*?) \| (?P<朝向>.*?) \| (?P<装修>.*?) \| (?P<楼层>[^|]*)"
        ).groupby(level=0).first()
        house_data.loc[:,["户型", "面积", "朝向", "装修", "楼层"]] = house_details.values

    # 2. 分割"关注相关信息"
    if "关注与发布时间" in house_data.columns:
        follow_details = house_data["关注与发布时间"].str.split(" / ", expand=True)
        house_data.loc[:, ["关注人数", "发布时间"]] = follow_details.values


    # 3. 清理总价
    if "总价" in house_data.columns:
        house_data.loc[:, "总价"] = house_data["总价"].str.replace("万", "").astype(float)

    # 删除原始合并列（如果存在）
    house_data.drop(columns=["房屋信息", "关注与发布时间"], inplace=True, errors='ignore')

    return house_data


def analyze(house_data):

    warnings.filterwarnings("ignore", category=FutureWarning)
    # pandas和seaborn里发生了暂时没有危险的冲突，我的建议是让seaborn这个库爬，不是我喜欢的报错，直接忽略

    analysis_results = {}

    # 1. 统计户型分布
    if "户型" in house_data.columns:
        room_dist = house_data["户型"].value_counts().sort_index()
        analysis_results["户型分布"] = room_dist

    # 2. 统计朝向分布
    if "朝向" in house_data.columns:
        orientation_dist = house_data["朝向"].value_counts().sort_index()
        analysis_results["朝向分布"] = orientation_dist

    # 3. 统计装修情况
    if "装修" in house_data.columns:
        decoration_dist = house_data["装修"].value_counts().sort_index()
        analysis_results["装修情况"] = decoration_dist

    # 4. 统计楼层分布
    if "楼层" in house_data.columns:
        def classify_floor(floor):
            if "低" in floor:
                return "低层"
            elif "中" in floor:
                return "中层"
            elif "高" in floor:
                return "高层"
            else:
                return "其他"
        floor_dist = house_data["楼层"].apply(classify_floor).value_counts()
        analysis_results["楼层分布"] = floor_dist

    # 5. 价格统计分析
    if "总价" in house_data.columns:
        prices = house_data["总价"].astype(float)
        price_stats = {
            "平均总价(万)": prices.mean().round(2),
            "中位数总价(万)": prices.median().round(2),
            "最低总价(万)": prices.min().round(2),
            "最高总价(万)": prices.max().round(2),
            "总价标准差": prices.std().round(2)
        }
        analysis_results["价格统计"] = pd.Series(price_stats)

    # 6. 面积统计分析
    if "面积" in house_data.columns:
        # 提取面积数值（去除"平米"）
        areas = house_data["面积"].str.extract("(\\d+\\.?\\d*)")[0].astype(float)
        area_stats = {
            "平均面积(平米)": areas.mean().round(2),
            "中位数面积(平米)": areas.median().round(2),
            "最小面积(平米)": areas.min().round(2),
            "最大面积(平米)": areas.max().round(2),
            "面积标准差": areas.std().round(2)
        }
        analysis_results["面积统计"] = pd.Series(area_stats)

    # 7. 关注人数统计
    if "关注人数" in house_data.columns:
        # 提取关注人数数值
        follow_counts = house_data["关注人数"].str.extract("(\\d+)")[0].astype(float)
        follow_stats = {
            "平均关注人数": follow_counts.mean().round(2),
            "中位数关注人数": follow_counts.median().round(2),
            "最大关注人数": follow_counts.max().round(2)
        }
        analysis_results["关注人数统计"] = pd.Series(follow_stats)

    return analysis_results

def picture(analysis_results):
    plt.figure(figsize=(12, 8))
    plt.suptitle("房屋数据分析结果", fontsize=16)

    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 子图1：户型分布
    if "户型分布" in analysis_results:
        plt.subplot(3, 2, 1)
        analysis_results["户型分布"].plot(kind="bar", color="skyblue")
        plt.title("户型分布")
        plt.xlabel("户型")
        plt.ylabel("数量")

    # 子图2：朝向分布
    if "朝向分布" in analysis_results:
        plt.subplot(3, 2, 2)
        analysis_results["朝向分布"].plot(kind="bar", color="lightgreen")
        plt.title("朝向分布")
        plt.xlabel("朝向")
        plt.ylabel("数量")

    # 子图3：装修情况
    if "装修情况" in analysis_results:
        plt.subplot(3, 2, 3)
        analysis_results["装修情况"].plot(kind="bar", color="salmon")
        plt.title("装修情况")
        plt.xlabel("装修类型")
        plt.ylabel("数量")

    # 子图4：楼层分布
    if "楼层分布" in analysis_results:
        plt.subplot(3, 2, 4)
        analysis_results["楼层分布"].plot(kind="bar", color="gold")
        plt.title("楼层分布")
        plt.xlabel("楼层类型")
        plt.ylabel("数量")

    # 子图5：价格统计（柱状图）
    if "价格统计" in analysis_results:
        plt.subplot(3, 2, 5)
        price_stats = analysis_results["价格统计"]
        sns.barplot(x=price_stats.index, y=price_stats.values, palette="viridis")
        plt.title("价格统计")
        plt.xlabel("指标")
        plt.ylabel("数值（万）")
        plt.xticks(rotation=45)

    # 子图6：面积统计（柱状图）
    if "面积统计" in analysis_results:
        plt.subplot(3, 2, 6)
        area_stats = analysis_results["面积统计"]
        sns.barplot(x=area_stats.index, y=area_stats.values, palette="magma")
        plt.title("面积统计")
        plt.xlabel("指标")
        plt.ylabel("数值（平米）")
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()



def test():

    # 文件式读取（北京，1页）
    #file_path = r"C:\Users\zjdql\Desktop\page1.html"
    #file=open(file_path, "r", encoding="utf-8")
    #house_data = cut(file)

    file_path = r"C:\Users\zjdql\Desktop\lianjia_data_hz_1-33.xls"
    file = pd.read_excel(file_path)  # 直接读取 Excel
    house_data = cut(file)

    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    #print("\n" + "=" * 50 + " 处理后的数据 " + "=" * 50)
    #print(house_data.to_string(index=False))

    analyze_results = analyze(house_data)

    print("\n" + "=" * 50 + " 统计后的数据 " + "=" * 50)
    for key, value in analyze_results.items():
        print(f"\n【{key}】")
        if isinstance(value, pd.Series):
            print(value.to_string())
        else:
            print(value)

    picture(analyze_results)

test()