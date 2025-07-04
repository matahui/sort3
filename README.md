# 排列三历史号码连续查询

这是一个用于查询排列三历史号码连续出现情况的应用。

## 功能特点

- 支持查询百位、十位、个位的连续号码
- 可以输入任意长度的连续号码进行查询
- 显示匹配的年份和期号信息
- 移动端友好的界面设计

## 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
streamlit run app.py
```

## 数据文件

应用需要 `data` 目录下的 CSV 文件，文件名格式为 `sort3_YYYY.csv`，其中 YYYY 为年份。

## 部署说明

本应用已部署在 Streamlit Cloud，访问地址：

👉 [https://byplt6wt2sonhpvvjyukg5.streamlit.app](https://byplt6wt2sonhpvvjyukg5.streamlit.app/)

## 使用说明

1. 选择要查询的位数（百位、十位、个位）
2. 输入要查询的连续号码（至少2位）
3. 点击查询按钮
4. 查看查询结果

## 注意事项

- 输入号码必须为数字
- 连续号码长度至少为2位
- 查询结果按年份和期号排序显示 