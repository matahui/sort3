from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import os
import time
from datetime import datetime
import sys

def calculate_additional_fields(hundred, ten, unit):
    """计算和值、尾数和跨度"""
    h, t, u = map(int, [hundred, ten, unit])
    sum_value = h + t + u
    tail = sum_value % 10
    gap = max(h, t, u) - min(h, t, u)
    return sum_value, tail, gap

def fetch_p3_data_selenium(year):
    url = "https://www.00038.cn/zs_p3/chzs.htm"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        # 等待年份下拉框出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "year"))
        )
        # 选择年份
        select = Select(driver.find_element(By.ID, "year"))
        select.select_by_value(str(year))
        time.sleep(2)  # 等待页面刷新

        # 等待表格出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chartsTable"))
        )
        table = driver.find_element(By.ID, "chartsTable")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # 自动识别"奖号"列索引
        header_cols = rows[0].find_elements(By.TAG_NAME, "th")
        prize_col_idx = None
        for idx, th in enumerate(header_cols):
            if "奖号" in th.text:
                prize_col_idx = idx
                break
        if prize_col_idx is None:
            print("未找到奖号列")
            return []

        data = []
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) <= prize_col_idx:
                continue
            issue = cols[0].text.strip()
            prize = cols[prize_col_idx].text.strip()
            # 只保留期号为全数字的行，过滤掉统计、预选等非数据行
            if not issue.isdigit() or len(prize) != 3:
                continue
            hundred, ten, unit = prize[0], prize[1], prize[2]
            sum_value, tail, gap = calculate_additional_fields(hundred, ten, unit)
            data.append({
                "issue": issue,
                "prize": prize,
                "hundred": hundred,
                "ten": ten,
                "unit": unit,
                "sum": sum_value,
                "tail": tail,
                "gap": gap
            })

    finally:
        driver.quit()

    return data

def update_current_year_data():
    """更新当年数据"""
    current_year = datetime.now().year
    file_path = f"data/sort3_{current_year}.csv"
    
    print(f"开始更新{current_year}年数据...")
    
    # 获取新数据
    new_data = fetch_p3_data_selenium(current_year)
    if not new_data:
        print(f"未获取到{current_year}年数据。")
        return
    
    new_df = pd.DataFrame(new_data)
    
    # 如果文件存在，则比较和更新
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        # 找出新增的期号
        existing_issues = set(existing_df['issue'].astype(str))
        new_issues = set(new_df['issue'].astype(str))
        added_issues = list(new_issues - existing_issues)  # 转换为list
        
        if added_issues:
            # 只保留新增的数据
            new_records = new_df[new_df['issue'].isin(added_issues)]
            # 追加到现有文件
            updated_df = pd.concat([existing_df, new_records], ignore_index=True)
            updated_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            print(f"已更新{len(added_issues)}期新数据到 {file_path}")
        else:
            print("没有新数据需要更新。")
    else:
        # 如果文件不存在，直接保存
        new_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"数据已保存到 {file_path}")

def update_all_historical_data():
    """更新所有历史数据"""
    print("开始更新所有历史数据...")
    for year in range(2004, datetime.now().year + 1):
        print(f"正在获取{year}年数据...")
        year_data = fetch_p3_data_selenium(year)
        if not year_data:
            print(f"未获取到{year}年数据。")
        else:
            df = pd.DataFrame(year_data)
            df.to_csv(f"data/sort3_{year}.csv", index=False, encoding="utf-8-sig")
            print(f"数据已保存到 data/sort3_{year}.csv")

def start_scheduler():
    """启动后台定时任务"""
    scheduler = BackgroundScheduler()
    # 每天23:00运行更新任务
    scheduler.add_job(update_current_year_data, 'cron', hour=23, minute=0)
    scheduler.start()
    print("定时任务已启动，将在每天23:00更新数据...")
    return scheduler

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "update":
            # 立即更新当前年份数据
            update_current_year_data()
        elif command == "update_all":
            # 更新所有历史数据
            update_all_historical_data()
        elif command == "schedule":
            # 启动定时任务
            scheduler = start_scheduler()
            try:
                # 保持程序运行
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("正在停止定时任务...")
                scheduler.shutdown()
        else:
            print("用法:")
            print("  python p3_spider.py update      # 立即更新当前年份数据")
            print("  python p3_spider.py update_all  # 更新所有历史数据")
            print("  python p3_spider.py schedule    # 启动定时任务")
    else:
        # 默认行为：如果data目录为空，获取所有历史数据；否则只更新当前年份
        if not os.listdir("data"):
            print("首次运行，获取所有历史数据...")
            update_all_historical_data()
        else:
            print("更新当前年份数据...")
            update_current_year_data()