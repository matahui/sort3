import streamlit as st
import pandas as pd
import glob
import os
import altair as alt
import logging
from datetime import datetime
import glob as pyglob

# 日志设置
log_dir = 'log'
os.makedirs(log_dir, exist_ok=True)
today = datetime.now().strftime('%Y%m%d')
log_file = os.path.join(log_dir, f'sort3_{today}.log')
logger = logging.getLogger('sort3_app')
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
# 自动清理3天前的日志
log_files = sorted(pyglob.glob(os.path.join(log_dir, 'sort3_*.log')))
if len(log_files) > 3:
    for old_file in log_files[:-3]:
        try:
            os.remove(old_file)
        except Exception as e:
            logger.warning(f'Failed to remove old log: {old_file}, {e}')

# 显示数据更新提示
st.markdown("<div style='font-size:20px;font-weight:bold;color:#e67e22;'>每晚23:00自动更新数据</div>", unsafe_allow_html=True)

st.title("排列三历史号码连续查询")

# 输入
indicator = st.selectbox("选择数据指标", ["全部", "和尾", "跨度", "百位", "十位", "个位"], index=0)
seq = st.text_input("输入连续号码（如2687）")
search_mode = st.selectbox("查找模式", ["顺序查找", "逆序查找", "双向查找"], index=2)

# 指标映射
col_map = {"百位": "hundred", "十位": "ten", "个位": "unit", "和尾": "tail", "跨度": "gap"}

if st.button("查询") and seq and seq.isdigit() and len(seq) >= 2 and indicator:
    files = glob.glob("data/sort3_*.csv")
    seq_list = list(seq)
    n = len(seq_list)
    
    # 需要搜索的指标
    if indicator == "全部":
        indicators_to_search = ["和尾", "跨度", "百位", "十位", "个位"]
    else:
        indicators_to_search = [indicator]
    all_results = {}
    all_dfs = {}
    for ind in indicators_to_search:
        results = []
        dfs = []
        for file in files:
            year = os.path.basename(file).split("_")[1].split(".")[0]
            df = pd.read_csv(file, dtype=str)
            df["year"] = year
            df["row_idx"] = range(len(df))
            dfs.append(df)
            col = col_map[ind]
            # 取出要比对的列，全部转为字符串
            nums = df[col].astype(str).tolist()
            # 顺序查找
            if search_mode in ["顺序查找", "双向查找"]:
                for i in range(len(nums) - n + 1):
                    if nums[i:i+n] == seq_list:
                        issues = [df.iloc[i+j]["issue"] for j in range(n)]
                        idxs = [i+j for j in range(n)]
                        results.append((year, issues, "顺序", idxs, file))
            # 逆序查找
            if search_mode in ["逆序查找", "双向查找"]:
                seq_reverse = seq_list[::-1]
                for i in range(len(nums) - n + 1):
                    if nums[i:i+n] == seq_reverse:
                        issues = [df.iloc[i+j]["issue"] for j in range(n)]
                        idxs = [i+j for j in range(n)]
                        results.append((year, issues, "逆序", idxs, file))
        all_results[ind] = results
        all_dfs[ind] = pd.concat(dfs, ignore_index=True)
    
    # 展示每个指标的表格输出，标题高亮，子项目缩进，命中数字大红色
    for ind in [i for i in ["和尾", "跨度", "百位", "十位", "个位"] if i in all_results]:
        results = all_results[ind]
        df = all_dfs[ind]
        # 大标题高亮
        st.markdown(f'<div style="font-size:28px;font-weight:bold;color:#0074D9;margin-top:32px;margin-bottom:12px;">{ind} 匹配区间明细表：</div>', unsafe_allow_html=True)
        if results:
            for idx, (year, issues, mode, idxs, file) in enumerate(results, 1):
                df_file = pd.read_csv(file, dtype=str)
                df_file["hundred"] = df_file["hundred"].astype(int)
                df_file["ten"] = df_file["ten"].astype(int)
                df_file["unit"] = df_file["unit"].astype(int)
                df_file["sum"] = df_file["hundred"] + df_file["ten"] + df_file["unit"]
                df_file["tail"] = df_file["sum"] % 10
                df_file["gap"] = df_file[["hundred", "ten", "unit"]].max(axis=1) - df_file[["hundred", "ten", "unit"]].min(axis=1)
                col = col_map[ind]
                start = max(idxs[0] - 3, 0)
                end = min(idxs[-1] + 3, len(df_file) - 1)
                show_df = df_file.iloc[start:end+1].copy()
                show_df.reset_index(drop=True, inplace=True)
                hit_range = set(idxs)
                def trend_row(row, i):
                    balls = []
                    # 指标不同，走势不同
                    if ind in ["百位", "十位", "个位"]:
                        for j in range(10):
                            if getattr(row, col) == j and (start + i) in hit_range:
                                balls.append(f'<span style="color:#e60000;font-weight:bold;">{j}</span>')
                            else:
                                balls.append(f'<span style="color:#bbb;">{j}</span>')
                    elif ind == "和尾":
                        for j in range(10):
                            if getattr(row, "tail") == j and (start + i) in hit_range:
                                balls.append(f'<span style="color:#e60000;font-weight:bold;">{j}</span>')
                            else:
                                balls.append(f'<span style="color:#bbb;">{j}</span>')
                    elif ind == "跨度":
                        for j in range(10):
                            if getattr(row, "gap") == j and (start + i) in hit_range:
                                balls.append(f'<span style="color:#e60000;font-weight:bold;">{j}</span>')
                            else:
                                balls.append(f'<span style="color:#bbb;">{j}</span>')
                    return " ".join(balls)
                show_df["走势"] = [trend_row(row, i) for i, row in enumerate(show_df.itertuples(), start=0)]
                # 美化匹配信息标题，缩进
                mode_color = {'顺序': '#2ecc40', '逆序': '#ff8000'}
                mode_disp = '<span style="color:{};font-weight:bold;">{}</span>'.format(mode_color.get(mode, '#0074D9'), mode)
                match_info = (
                    '<div style="margin-left:32px;">'
                    '<span style="font-size:20px;font-weight:bold;color:#0074D9;">匹配{}:</span> '
                    '<span style="font-size:16px;color:#555;">年份：</span><span style="font-size:16px;font-weight:bold;color:#222;">{}</span>，'
                    '<span style="font-size:16px;color:#555;">期号：</span><span style="font-size:16px;font-weight:bold;color:#0074D9;">{}</span>，'
                    '<span style="font-size:16px;color:#555;">模式：</span>{}'
                    '</div>'
                ).format(idx, year, ','.join(issues), mode_disp)
                st.markdown(match_info, unsafe_allow_html=True)
                # 输出表格，整体缩进
                table_html = f"<div style='margin-left:32px;'><table border='1' style='border-collapse:collapse;'>"
                table_html += f"<tr><th>期号</th><th>奖号</th><th>和值</th><th>{ind}走势</th></tr>"
                for i, row in show_df.iterrows():
                    table_html += f"<tr><td>{row['issue']}</td><td>{row['hundred']}{row['ten']}{row['unit']}</td><td>{row['sum']}</td><td style='font-family:monospace;'>{row['走势']}</td></tr>"
                table_html += "</table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.warning("未找到匹配记录。")
else:
    st.info("请输入2位及以上的连续号码后点击查询。") 