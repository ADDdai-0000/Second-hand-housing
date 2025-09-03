import os
import xlwt
from logindemo import main as login_main
from demo import main as demo_main

COL_TITLE = ["图片链接", "标题", "链接", "地址", "房屋信息", "关注与发布时间", '总价', "单价"]

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
    page = input("请输入页数范围（例如：1-10）: ")
    file_path = os.path.join(save_dir, f"lianjia_data_{page}.xls")
    book.save(file_path)
    print(f"数据已保存到: {file_path}")


if __name__ == '__main__':
    # 获取数据
    # print("正在获取demo数据...")
    # data1 = demo_main()
    print("正在获取login_demo数据...")
    data = login_main()

    print(f"总共获取到 {len(data)} 条数据")

    # 保存数据
    saveData(data, "lianjia_datas")