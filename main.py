# -*- coding: utf-8 -*-
"""
甜點成本管理系統（Clean Code 版本）
===================================
這個系統幫助使用者管理食材、品項，以及對應的成本與建議售價。
同時可計算每分鐘時間成本，並根據選擇的品項與數量計算總利潤。

主要功能：
1. 食材管理
2. 品項管理
3. 時間成本管理
4. 建議售價與利潤計算

執行方式：
1. 安裝必要套件：streamlit、pandas、os
2. 在命令列執行：streamlit run <本檔案名稱>.py
3. 在瀏覽器中查看介面。

注意：
- 程式首次執行會自動產生各種 .csv 資料檔。
- 可隨時透過系統介面新增、更新或刪除各類資料。
"""

import os
import time
import pandas as pd
import streamlit as st

# ---------------------------
# 全域常數定義：CSV 檔案命名更容易理解
# ---------------------------
INGREDIENTS_FILE = "食材清單.csv"
ITEMS_FILE = "品項清單.csv"
TIME_COST_FILE = "時間成本清單.csv"
TIME_COST_RATIO_FILE = "每分鐘時間成本比例.csv"
UNITS_FILE = "可用單位.csv"
SELLING_RESULT_FILE = "建議售價與利潤結果.csv"

# ---------------------------
# 1. 資料初始化相關函式
# ---------------------------
def initialize_data():
    """
    初始化檔案與預設數據。
    """
    # 定義檔案初始化資訊
    file_initializations = [
        ("食材清單.csv", ["食材名稱", "單位", "單價"]),
        ("品項清單.csv", ["品項名稱", "食材名稱", "用量"]),
        ("時間成本清單.csv", [
            "品項名稱", "切份數量", "製作時間(分鐘)", "每份薪資", "品項成本", 
            "每份品項成本", "每份建議售價", "每份利潤"
        ]),
        ("基本時薪.csv", {"基本時薪": [192]}),
        ("可用單位.csv", ["單位名稱"]),
        ("建議售價與利潤結果.csv", ["品項名稱", "數量", "總成本", "總建議售價", "總利潤"]),
    ]

    # 初始化檔案
    for file_name, columns_or_data in file_initializations:
        if not os.path.exists(file_name):
            if isinstance(columns_or_data, list):
                save_data(pd.DataFrame(columns=columns_or_data), file_name)
            elif isinstance(columns_or_data, dict):
                save_data(pd.DataFrame(columns_or_data), file_name)

    # 初始化預設單位數據
    units = load_data("可用單位.csv")
    if units.empty:
        default_units = ["g", "kg", "ml", "L", "pcs"]
        save_data(pd.DataFrame({"單位名稱": default_units}), "可用單位.csv")

# ---------------------------
# 2. 讀取與儲存資料的工具函式
# ---------------------------
def load_data(file_path):
    """
    加載 CSV 檔案，並確保相容性。
    檔案編碼為 UTF-8 或 UTF-8 with BOM。
    """
    try:
        return pd.read_csv(file_path, encoding="utf-8-sig")  # 支援 UTF-8 with BOM
    except UnicodeDecodeError:
        # 若 UTF-8 解碼失敗，嘗試其他編碼格式
        return pd.read_csv(file_path, encoding="big5")  # 適用於某些舊版 Excel 編輯的檔案
    except Exception as e:
        print(f"讀取檔案時發生錯誤: {file_path}, 錯誤訊息: {e}")
        return pd.DataFrame()
    
def save_data(df, file_path):
    """
    儲存 CSV 檔案，統一為 UTF-8 with BOM 編碼。
    """
    try:
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"成功儲存檔案: {file_path}")
    except Exception as e:
        print(f"儲存檔案時發生錯誤: {file_path}, 錯誤訊息: {e}")

def delete_row(df, condition):
    """
    根據給定的條件刪除資料表中的列，回傳更新後的 DataFrame。
    condition 為布林遮罩。
    """
    return df[~condition]

# ---------------------------
# 3. 食材管理模組
# ---------------------------
def manage_ingredients():
    """
    進行食材的新增、更新與刪除操作，並即時顯示食材清單。
    """
    st.header("食材管理")

    # 載入資料
    ingredients = load_data(INGREDIENTS_FILE)
    units = load_data(UNITS_FILE)
    unit_options = units["單位名稱"].tolist() if not units.empty else []

    # 顯示目前食材清單
    st.subheader("目前食材清單")
    placeholder = st.empty()  # 用以動態更新資料表
    if not ingredients.empty:
        with placeholder:
            st.dataframe(ingredients, use_container_width=True)
    else:
        with placeholder:
            st.warning("目前無任何食材！")

    # 新增或更新食材
    st.subheader("新增/更新食材")
    with st.form("ingredient_form", clear_on_submit=True):
        name = st.text_input("食材名稱")
        unit = st.selectbox("單位", options=unit_options)
        price = st.number_input("單價", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("新增/更新")

        if submitted:
            if name and price > 0:
                # 若食材已存在，則更新；否則新增
                if "食材名稱" in ingredients.columns and name in ingredients["食材名稱"].values:
                    ingredients.loc[ingredients["食材名稱"] == name, ["單位", "單價"]] = [unit, price]
                else:
                    new_row = pd.DataFrame([{"食材名稱": name, "單位": unit, "單價": price}])
                    if not new_row.empty and not new_row.isna().all(axis=None):
                        ingredients = pd.concat([ingredients, new_row], ignore_index=True)

                # 儲存並即時更新顯示
                save_data(ingredients, INGREDIENTS_FILE)
                ingredients = load_data(INGREDIENTS_FILE)
                placeholder.empty()
                with placeholder:
                    st.dataframe(ingredients, use_container_width=True)
                success_message = st.success(f"已成功新增/更新食材：'{name}'！")
                time.sleep(1)
                success_message.empty()

    # 刪除食材
    st.subheader("刪除食材")
    if not ingredients.empty:
        delete_name = st.selectbox("選擇要刪除的食材", ingredients["食材名稱"], key="delete_ingredient")
        if st.button("刪除食材"):
            ingredients = ingredients[ingredients["食材名稱"] != delete_name]
            save_data(ingredients, INGREDIENTS_FILE)

            ingredients = load_data(INGREDIENTS_FILE)
            placeholder.empty()
            with placeholder:
                st.dataframe(ingredients, use_container_width=True)
            success_message = st.success(f"已刪除食材：'{delete_name}'！")
            time.sleep(1)
            success_message.empty()
    else:
        st.warning("無可刪除的食材！")

# ---------------------------
# 4. 品項管理模組
# ---------------------------
def manage_items():
    """
    進行品項的新增、更新與刪除操作，並即時顯示品項清單與單行成本。
    """
    st.header("品項管理")

    # 載入資料
    ingredients = load_data(INGREDIENTS_FILE)
    items = load_data(ITEMS_FILE)

    # 若品項與食材皆不空，計算單行成本
    if not items.empty and not ingredients.empty:
        merged_data = items.merge(ingredients, on="食材名稱", how="left")
        merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
        # 移除「製作時間」欄位，僅保留相關欄位
        merged_data = merged_data[["品項名稱", "食材名稱", "用量", "單行成本"]]
        merged_data = merged_data.sort_values(by=["品項名稱", "食材名稱"])
    else:
        merged_data = items.copy()

    # 顯示目前品項清單
    st.subheader("目前品項清單")
    placeholder = st.empty()
    if not merged_data.empty:
        with placeholder:
            st.dataframe(merged_data, use_container_width=True)
    else:
        with placeholder:
            st.warning("目前無任何品項！")

    # 新增/更新品項
    st.subheader("新增/更新品項")
    with st.form("item_form", clear_on_submit=True):
        item_name = st.text_input("品項名稱")
        if not ingredients.empty:
            ingredient_name = st.selectbox("選擇食材", options=ingredients["食材名稱"].unique(), key="select_ingredient")
        else:
            ingredient_name = None
            st.warning("請先新增食材！")
        quantity = st.number_input("用量", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("新增/更新")

        if submitted and ingredient_name:
            if item_name and quantity > 0:
                existing_row = items[
                    (items["品項名稱"] == item_name) & (items["食材名稱"] == ingredient_name)
                ]

                if not existing_row.empty:
                    # 已存在同樣的品項+食材組合，更新用量
                    items.loc[
                        (items["品項名稱"] == item_name) & (items["食材名稱"] == ingredient_name),
                        "用量"
                    ] = quantity
                else:
                    # 新增該品項的食材資訊
                    new_row = pd.DataFrame([{
                        "品項名稱": item_name,
                        "食材名稱": ingredient_name,
                        "用量": quantity
                    }])
                    if not new_row.empty and not new_row.isna().all(axis=None):
                        items = pd.concat([items, new_row], ignore_index=True)

                save_data(items, ITEMS_FILE)

                # 更新顯示
                items = load_data(ITEMS_FILE)
                merged_data = items.merge(ingredients, on="食材名稱", how="left")
                merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
                merged_data = merged_data[["品項名稱", "食材名稱", "用量", "單行成本"]]
                merged_data = merged_data.sort_values(by=["品項名稱", "食材名稱"])
                placeholder.empty()
                with placeholder:
                    st.dataframe(merged_data, use_container_width=True)
                success_message = st.success(f"已成功新增/更新品項：'{item_name}'，食材：'{ingredient_name}'！")
                time.sleep(1)
                success_message.empty()

    # 刪除品項
    st.subheader("刪除品項")
    if not items.empty:
        delete_item = st.selectbox("選擇要刪除的品項", items["品項名稱"].unique(), key="delete_item")
        if st.button("刪除品項"):
            items = items[items["品項名稱"] != delete_item]
            save_data(items, ITEMS_FILE)

            # 更新顯示
            items = load_data(ITEMS_FILE)
            merged_data = items.merge(ingredients, on="食材名稱", how="left")
            merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
            merged_data = merged_data[["品項名稱", "食材名稱", "用量", "單行成本"]]
            merged_data = merged_data.sort_values(by=["品項名稱", "食材名稱"])
            placeholder.empty()
            with placeholder:
                st.dataframe(merged_data, use_container_width=True)
            success_message = st.success(f"已刪除品項：'{delete_item}'！")
            time.sleep(1)
            success_message.empty()
    else:
        st.warning("無可刪除的品項！")

# ---------------------------
# 5. 時間成本管理模組
# ---------------------------
def manage_time_cost():
    """
    管理每分鐘時間成本比例，並設定各品項的製作時間。
    同時自動更新每分鐘薪資、品項成本、每份建議售價及利潤。
    """
    import os
    import pandas as pd
    import streamlit as st

    TIME_COST_FILE = "時間成本清單.csv"
    ITEMS_FILE = "品項清單.csv"
    INGREDIENTS_FILE = "食材清單.csv"
    BASE_WAGE_FILE = "基本時薪.csv"

    def load_data(file_name):
        if os.path.exists(file_name):
            return pd.read_csv(file_name)
        return pd.DataFrame()

    def save_data(data, file_name):
        data.to_csv(file_name, index=False)

    # 讀取或設定基本時薪
    if not os.path.exists(BASE_WAGE_FILE):
        save_data(pd.DataFrame({"基本時薪": [192]}), BASE_WAGE_FILE)
    base_wage_df = load_data(BASE_WAGE_FILE)
    base_wage = base_wage_df["基本時薪"].iloc[0]

    st.header("時間成本管理")

    # 基本時薪設定區
    st.subheader("基本時薪設定")
    new_base_wage = st.number_input("輸入基本時薪 (新台幣)", min_value=0, step=1, value=int(base_wage), format="%d")
    if st.button("保存基本時薪"):
        save_data(pd.DataFrame({"基本時薪": [new_base_wage]}), BASE_WAGE_FILE)
        base_wage = new_base_wage  # 更新基薪數值
        success_message = st.success(f"基本時薪已更新為 {new_base_wage} 元！")
        time.sleep(1)
        success_message.empty()

    # 計算每分鐘薪資
    per_minute_wage = base_wage / 60

    # 載入數據
    time_cost = load_data(TIME_COST_FILE)
    items = load_data(ITEMS_FILE)
    ingredients = load_data(INGREDIENTS_FILE)

    # 確保必需欄位存在，若缺少則補全
    required_columns = [
        "品項名稱", "切份數量", "製作時間(分鐘)", "每份薪資", 
        "品項成本", "每份品項成本", "每份建議售價", "每份利潤"
    ]
    for column in required_columns:
        if column not in time_cost.columns:
            time_cost[column] = 0

    # 計算品項成本
    if not items.empty and not ingredients.empty:
        merged_data = items.merge(ingredients, on="食材名稱", how="left")
        merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
        item_costs = merged_data.groupby("品項名稱")["單行成本"].sum().reset_index()
        item_costs.columns = ["品項名稱", "品項成本"]

        if not time_cost.empty:
            time_cost = time_cost.merge(item_costs, on="品項名稱", how="left", suffixes=("", "_new"))
            if "品項成本_new" in time_cost.columns:
                time_cost["品項成本"] = time_cost.pop("品項成本_new")

    # 即時更新時間成本
    if not time_cost.empty:
        time_cost["每份薪資"] = (time_cost["製作時間(分鐘)"] * per_minute_wage) / time_cost["切份數量"]
        time_cost["每份品項成本"] = time_cost["品項成本"] / time_cost["切份數量"]
        time_cost["每份建議售價"] = time_cost["每份薪資"] + time_cost["每份品項成本"]
        time_cost["每份利潤"] = time_cost["每份建議售價"] - time_cost["每份品項成本"]
        save_data(time_cost, TIME_COST_FILE)  # 保存更新後的時間成本

    # 新增/更新時間成本
    st.subheader("新增/更新品項時間成本")
    if not items.empty:
        with st.form("time_cost_form", clear_on_submit=True):
            item_name = st.selectbox("選擇品項", options=item_costs["品項名稱"].unique(), key="select_time_cost")
            production_time = st.number_input("製作時間 (分鐘)", min_value=0.0, step=1.0, format="%.2f")
            split_quantity = st.number_input("切份數量", min_value=1, step=1, value=1, format="%d")
            submitted = st.form_submit_button("新增/更新")

        if submitted:
            if production_time > 0:
                item_cost = item_costs.loc[item_costs["品項名稱"] == item_name, "品項成本"].values[0]
                cost_per_unit = item_cost / split_quantity
                salary_per_unit = (per_minute_wage * production_time) / split_quantity
                suggested_price = cost_per_unit + salary_per_unit
                profit_per_unit = suggested_price - cost_per_unit

                # 更新或新增資料
                updated_cost = pd.DataFrame([{
                    "品項名稱": item_name,
                    "切份數量": split_quantity,
                    "製作時間(分鐘)": production_time,
                    "每份薪資": round(salary_per_unit, 2),
                    "品項成本": round(item_cost, 2),
                    "每份品項成本": round(cost_per_unit, 2),
                    "每份建議售價": round(suggested_price, 2),
                    "每份利潤": round(profit_per_unit, 2)
                }])
                if not updated_cost.empty and not updated_cost.isna().all(axis=None):
                    time_cost = pd.concat([time_cost, updated_cost]).drop_duplicates(subset=["品項名稱"], keep="last")
                save_data(time_cost, TIME_COST_FILE)
                success_message = st.success(f"已成功新增或更新時間成本：'{item_name}'！")
                time.sleep(1)
                success_message.empty()

    # 顯示目前時間成本
    st.subheader("目前時間成本")
    placeholder = st.empty()
    if not time_cost.empty:
        desired_order = [
            "品項名稱", "切份數量", "製作時間(分鐘)", "每份薪資", 
            "品項成本", "每份品項成本", "每份建議售價", "每份利潤"
        ]
        time_cost = time_cost[desired_order]
        with placeholder:
            st.dataframe(time_cost, use_container_width=True)
    else:
        with placeholder:
            st.warning("尚未定義任何時間成本或品項成本！")

   # 刪除品項時間成本
    st.subheader("刪除品項時間成本")
    if not time_cost.empty:
        delete_name = st.selectbox("選擇要刪除的品項", time_cost["品項名稱"].unique(), key="delete_time_cost")
        if st.button("刪除時間成本"):
            # 刪除指定時間成本
            time_cost = time_cost[time_cost["品項名稱"] != delete_name]
            save_data(time_cost, TIME_COST_FILE)

            # 更新顯示
            if not time_cost.empty:
                placeholder.empty()
                with placeholder:
                    st.dataframe(time_cost, use_container_width=True)
            else:
                placeholder.empty()
                with placeholder:
                    st.warning("尚未定義任何時間成本！")
            success_message = st.success(f"已刪除時間成本：'{delete_name}'！")
            time.sleep(1)
            success_message.empty()

# ---------------------------
# 6. 建議售價與利潤計算模組
# ---------------------------
def calculate_selling_price_and_profit():
    """
    依據使用者選擇的品項與數量，計算總售價與總利潤，並可儲存結果。
    """

    TIME_COST_FILE = "時間成本清單.csv"
    SELLING_RESULT_FILE = "利潤計算結果.csv"

    def load_data(file_name):
        if os.path.exists(file_name):
            return pd.read_csv(file_name)
        return pd.DataFrame()

    def save_data(data, file_name):
        data.to_csv(file_name, index=False)

    st.header("建議售價和利潤計算")

    # 載入時間成本（含每份品項成本、建議售價和利潤）
    time_cost = load_data(TIME_COST_FILE)
    if time_cost.empty:
        st.warning("尚未定義時間成本！請先在『時間成本管理』中設定建議售價。")
        return

    # 選擇項目並輸入數量
    st.subheader("選擇項目並輸入數量")
    selected_items = st.multiselect("選擇品項", options=time_cost["品項名稱"].unique(), key="select_items")
    quantities = {}
    for index, item in enumerate(selected_items):
        quantities[item] = st.number_input(f"{item} 數量", min_value=0, step=1, key=f"quantity_{item}_{index}")

    if st.button("計算總售價和利潤"):
        if selected_items:
            results = []
            total_cost_sum = 0
            total_price_sum = 0
            total_profit_sum = 0

            for item_name, qty in quantities.items():
                if qty > 0:
                    item_data = time_cost[time_cost["品項名稱"] == item_name]
                    cost_per_unit = item_data["每份品項成本"].values[0]
                    suggested_price_per_unit = item_data["每份建議售價"].values[0]
                    profit_per_unit = item_data["每份利潤"].values[0]

                    total_price = suggested_price_per_unit * qty
                    total_cost = cost_per_unit * qty
                    total_profit = profit_per_unit * qty

                    total_cost_sum += total_cost
                    total_price_sum += total_price
                    total_profit_sum += total_profit

                    results.append({
                        "品項名稱": item_name,
                        "數量": qty,
                        "總成本": total_cost,
                        "總建議售價": total_price,
                        "總利潤": total_profit
                    })

            results_df = pd.DataFrame(results)
            st.subheader("計算結果")
            st.dataframe(results_df, use_container_width=True)

            # 顯示總計
            st.write("### 總計")
            st.write(f"總成本：{total_cost_sum}")
            st.write(f"總建議售價：{total_price_sum}")
            st.write(f"總利潤：{total_profit_sum}")

        else:
            st.warning("請至少選擇一個品項並輸入數量！")

# ---------------------------
# 7. 主函式：Streamlit App 入口
# ---------------------------
def main():
    """
    整個 Streamlit 應用程式的進入點，負責分頁籤切換與模組整合。
    """
    # 初始化資料
    initialize_data()

    st.set_page_config(
        page_title="迷途貓咖啡 - 成本管理系統",
        layout="wide",
        initial_sidebar_state="collapsed"  # 預設側邊欄收合
    )

    # 主標題
    st.title("😸 迷途貓咖啡 - 成本管理系統")

    # 側邊欄資訊
    with st.sidebar:
        st.title("系統資訊")
        st.info("版本名稱: v0.0.5")
        st.info("開發者: Panda 🐼")

    # 建立頁籤
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 食材管理",
        "🍪 品項管理",
        "⏳ 時間成本管理",
        "💰 建議售價和利潤計算"
    ])

    with tab1:
        manage_ingredients()

    with tab2:
        manage_items()

    with tab3:
        manage_time_cost()

    with tab4:
        calculate_selling_price_and_profit()

# ---------------------------
# Python 主程式入口
# ---------------------------
if __name__ == "__main__":
    main()
