from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import logging
import glob

def setup_logger():
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'sort3_{today}.log')
    logger = logging.getLogger('sort3')
    logger.setLevel(logging.INFO)
    # 防止重复添加handler
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    # 自动清理3天前的日志
    log_files = sorted(glob.glob(os.path.join(log_dir, 'sort3_*.log')))
    if len(log_files) > 3:
        for old_file in log_files[:-3]:
            try:
                os.remove(old_file)
            except Exception as e:
                logger.warning(f'Failed to remove old log: {old_file}, {e}')
    return logger

logger = setup_logger()

def calculate_additional_fields(hundred, ten, unit):
    h, t, u = map(int, [hundred, ten, unit])
    sum_value = h + t + u
    tail = sum_value % 10
    gap = max(h, t, u) - min(h, t, u)
    return sum_value, tail, gap

def fetch_p3_data_selenium(year):
    logger.info(f'开始抓取{year}年数据...')
    url = "https://www.00038.cn/zs_p3/chzs.htm"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "year"))
        )
        select = Select(driver.find_element(By.ID, "year"))
        select.select_by_value(str(year))
        time.sleep(2)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chartsTable"))
        )
        table = driver.find_element(By.ID, "chartsTable")
        rows = table.find_elements(By.TAG_NAME, "tr")
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
        logger.info(f'{year}年数据抓取完成，共{len(data)}期')
    except Exception as e:
        logger.error(f'抓取{year}年数据出错: {e}')
    finally:
        driver.quit()
    return data

def update_current_year_data():
    current_year = datetime.now().year
    file_path = f"data/sort3_{current_year}.csv"
    logger.info(f"开始更新{current_year}年数据...")
    new_data = fetch_p3_data_selenium(current_year)
    if not new_data:
        logger.warning(f"未获取到{current_year}年数据。")
        return
    new_df = pd.DataFrame(new_data)
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        existing_issues = set(existing_df['issue'].astype(str))
        new_issues = set(new_df['issue'].astype(str))
        added_issues = list(new_issues - existing_issues)
        if added_issues:
            new_records = new_df[new_df['issue'].isin(added_issues)]
            updated_df = pd.concat([existing_df, new_records], ignore_index=True)
            updated_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            logger.info(f"已更新{len(added_issues)}期新数据到 {file_path}")
        else:
            logger.info("没有新数据需要更新。")
    else:
        new_df.to_csv(file_path, index=False, encoding="utf-8-sig")
        logger.info(f"数据已保存到 {file_path}") 