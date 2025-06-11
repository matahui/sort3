from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import time

def fetch_p3_data_selenium(year):
    url = "https://www.00038.cn/zs_p3/chzs.htm"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

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
        driver.quit()
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
        data.append({
            "issue": issue,
            "prize": prize,
            "hundred": hundred,
            "ten": ten,
            "unit": unit
        })

    driver.quit()
    return data

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    for year in range(2004, 2026):
        print(f"Fetching {year} ...")
        year_data = fetch_p3_data_selenium(year)
        if not year_data:
            print(f"未获取到{year}年数据。")
        else:
            df = pd.DataFrame(year_data)
            df.to_csv(f"data/sort3_{year}.csv", index=False, encoding="utf-8-sig")
            print(f"数据已保存到 data/sort3_{year}.csv")