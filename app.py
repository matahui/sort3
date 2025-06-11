import streamlit as st
import pandas as pd
import glob
import os

st.title("排列三历史号码连续查询")

# 输入
position = st.selectbox("选择位数", ["百位", "十位", "个位"])
seq = st.text_input("输入连续号码（如8057）")

# 位置映射
col_map = {"百位": "hundred", "十位": "ten", "个位": "unit"}

if st.button("查询") and seq.isdigit() and len(seq) >= 2:
    results = []
    files = glob.glob("data/sort3_*.csv")
    for file in files:
        year = os.path.basename(file).split("_")[1].split(".")[0]
        df = pd.read_csv(file, dtype=str)
        col = col_map[position]
        nums = df[col].tolist()
        seq_list = list(seq)
        n = len(seq_list)
        for i in range(len(nums) - n + 1):
            if nums[i:i+n] == seq_list:
                issues = [df.iloc[i+j]["issue"] for j in range(n)]
                results.append((year, issues))
    if results:
        st.success("找到如下匹配：")
        for idx, (year, issues) in enumerate(results, 1):
            st.write(f"匹配{idx}: 年份：{year}，期号：{','.join(issues)}")
    else:
        st.warning("未找到匹配记录。")
else:
    st.info("请输入2位及以上的连续号码后点击查询。") 