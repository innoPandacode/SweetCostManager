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
    初始化檔案，若不存在則建立空的 CSV 檔案。
    """
    if not os.path.exists(INGREDIENTS_FILE):
        save_data(pd.DataFrame(columns=["食材名稱", "單位", "單價"]), INGREDIENTS_FILE)
    if not os.path.exists(ITEMS_FILE):
        save_data(pd.DataFrame(columns=["品項名稱", "食材名稱", "用量"]), ITEMS_FILE)
    if not os.path.exists(TIME_COST_FILE):
        save_data(pd.DataFrame(columns=["品項名稱", "製作時間(分鐘)", "時間成本比例(%)", "品項成本", "建議售價"]), TIME_COST_FILE)
    if not os.path.exists(TIME_COST_RATIO_FILE):
        save_data(pd.DataFrame({"每分鐘成本比例 (%)": [0.1]}), TIME_COST_RATIO_FILE)
    if not os.path.exists(UNITS_FILE):
        save_data(pd.DataFrame(columns=["單位名稱"]), UNITS_FILE)
    if not os.path.exists(SELLING_RESULT_FILE):
        save_data(pd.DataFrame(columns=["品項名稱", "數量", "總成本", "總建議售價", "總利潤"]), SELLING_RESULT_FILE)

    initialize_default_data()

def initialize_default_data():
    """
    初始化預設數據，如單位資訊等。
    """
    units = load_data(UNITS_FILE)
    if units.empty:
        default_units = ["g", "kg", "ml", "L", "pcs"]
        pd.DataFrame({"單位名稱": default_units}).to_csv(UNITS_FILE, index=False)

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
            st.success(f"已刪除食材：'{delete_name}'！")
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
            st.success(f"已刪除品項：'{delete_item}'！")
    else:
        st.warning("無可刪除的品項！")

# ---------------------------
# 5. 時間成本管理模組
# ---------------------------
def manage_time_cost():
    """
    管理每分鐘時間成本比例，並設定各品項的製作時間。
    同時自動更新「時間成本比例(%)」與「建議售價」及利潤。
    """
    st.header("時間成本管理")

    # 讀取或初始化資料
    per_minute_percentage_df = load_data(TIME_COST_RATIO_FILE)
    if per_minute_percentage_df.empty:
        # 若尚未有任何設定，預設為 0.1%
        per_minute_percentage_df = pd.DataFrame({"每分鐘成本比例 (%)": [0.1]})
        save_data(per_minute_percentage_df, TIME_COST_RATIO_FILE)
    per_minute_percentage = float(per_minute_percentage_df["每分鐘成本比例 (%)"].iloc[0])

    # 每分鐘時間成本比例設定
    st.subheader("每分鐘時間成本比例設定")
    new_per_minute_percentage = st.number_input(
        "每分鐘時間成本比例 (%)", 
        min_value=0.0, 
        step=0.01, 
        value=per_minute_percentage, 
        format="%.2f"
    )
    if st.button("保存時間成本比例"):
        pd.DataFrame({"每分鐘成本比例 (%)": [new_per_minute_percentage]}).to_csv(TIME_COST_RATIO_FILE, index=False)
        per_minute_percentage = new_per_minute_percentage
        success_message_1 = st.success(f"已保存每分鐘時間成本比例：{per_minute_percentage:.2f}%")
        time.sleep(1)
        success_message_1.empty()

        # 即時更新所有已存在的時間成本資料
        update_all_time_costs(per_minute_percentage)

    # 讀取最新資料
    time_cost = load_data(TIME_COST_FILE)

    # 新增或更新時間成本
    st.subheader("新增/更新品項時間成本")
    items = load_data(ITEMS_FILE)
    ingredients = load_data(INGREDIENTS_FILE)
    if not items.empty and not ingredients.empty:
        merged_data = items.merge(ingredients, on="食材名稱", how="left")
        merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
        item_costs = merged_data.groupby("品項名稱")["單行成本"].sum().reset_index()
        item_costs.columns = ["品項名稱", "品項成本"]

        # 確保 time_cost 表格內品項成本即時更新
        if not time_cost.empty:
            time_cost = time_cost.merge(item_costs, on="品項名稱", how="left", suffixes=("", "_new"))
            if "品項成本_new" in time_cost.columns:
                time_cost["品項成本"] = time_cost.pop("品項成本_new")
                time_cost["時間成本比例(%)"] = time_cost["製作時間(分鐘)"] * per_minute_percentage
                time_cost["建議售價"] = time_cost["品項成本"] + (time_cost["品項成本"] * (time_cost["時間成本比例(%)"] / 100))
                save_data(time_cost, TIME_COST_FILE)

        # 選擇品項並輸入製作時間
        with st.form("time_cost_form", clear_on_submit=True):
            # 只顯示已出現過的品項名稱
            item_options = item_costs["品項名稱"].unique().tolist()
            item_name = st.selectbox("選擇品項", options=item_options, key="select_time_cost")
            production_time = st.number_input("製作時間 (分鐘)", min_value=0.0, step=1.0, format="%.2f")
            submitted = st.form_submit_button("新增/更新")

            if submitted:
                if production_time > 0:
                    # 計算時間成本比例與建議售價
                    time_cost_percentage = production_time * per_minute_percentage
                    cost_value = item_costs.loc[item_costs["品項名稱"] == item_name, "品項成本"].values[0]
                    suggested_price = cost_value + (cost_value * (time_cost_percentage / 100))

                    updated_cost = pd.DataFrame([{
                        "品項名稱": item_name,
                        "製作時間(分鐘)": production_time,
                        "時間成本比例(%)": time_cost_percentage,
                        "品項成本": cost_value,
                        "建議售價": suggested_price
                    }])

                    # 合併並去重
                    time_cost = pd.concat([time_cost, updated_cost]).drop_duplicates(subset=["品項名稱"], keep="last")
                    save_data(time_cost, TIME_COST_FILE)

                    st.success(f"已成功新增或更新時間成本：'{item_name}'！")
    else:
        st.warning("請先建立品項與食材資料，才能定義時間成本。")

    # 顯示目前時間成本
    st.subheader("目前時間成本")
    placeholder = st.empty()
    if not time_cost.empty:
        # 若不存在品項成本欄位，補上預設
        if "品項成本" not in time_cost.columns:
            time_cost["品項成本"] = 0
        # 計算利潤（建議售價 - 品項成本）
        if "建議售價" in time_cost.columns and "品項成本" in time_cost.columns:
            time_cost["利潤"] = time_cost["建議售價"] - time_cost["品項成本"]
        else:
            time_cost["利潤"] = 0  # 預設值

        # 調整顯示欄位順序
        desired_order = ["品項名稱", "製作時間(分鐘)", "時間成本比例(%)", "品項成本", "建議售價", "利潤"]
        time_cost = time_cost[desired_order].fillna(0)
        with placeholder:
            st.dataframe(time_cost, use_container_width=True)
    else:
        with placeholder:
            st.warning("尚未定義任何時間成本！")

    # 刪除時間成本
    st.subheader("刪除品項時間成本")
    if not time_cost.empty:
        delete_name = st.selectbox("選擇要刪除的品項", time_cost["品項名稱"].unique(), key="delete_time_cost")
        if st.button("刪除時間成本"):
            time_cost = time_cost[time_cost["品項名稱"] != delete_name]
            save_data(time_cost, TIME_COST_FILE)

            time_cost = load_data(TIME_COST_FILE)
            if not time_cost.empty:
                if "建議售價" in time_cost.columns and "品項成本" in time_cost.columns:
                    time_cost["利潤"] = time_cost["建議售價"] - time_cost["品項成本"]
                desired_order = ["品項名稱", "製作時間(分鐘)", "時間成本比例(%)", "品項成本", "建議售價", "利潤"]
                time_cost = time_cost[desired_order].fillna(0)
                placeholder.empty()
                with placeholder:
                    st.dataframe(time_cost, use_container_width=True)
            else:
                placeholder.empty()
                with placeholder:
                    st.warning("尚未定義任何時間成本！")
            st.success(f"已刪除時間成本：'{delete_name}'！")

def update_all_time_costs(per_minute_percentage):
    """
    當使用者更新了「每分鐘時間成本比例」時，立即重新計算所有品項的時間成本與建議售價。
    """
    # 重新載入資料
    time_cost = load_data(TIME_COST_FILE)
    items = load_data(ITEMS_FILE)
    ingredients = load_data(INGREDIENTS_FILE)

    if not items.empty and not ingredients.empty:
        merged_data = items.merge(ingredients, on="食材名稱", how="left")
        merged_data["單行成本"] = merged_data["用量"] * merged_data["單價"]
        item_costs = merged_data.groupby("品項名稱")["單行成本"].sum().reset_index()
        item_costs.columns = ["品項名稱", "品項成本"]

        # 與 time_cost 表格進行合併
        if not time_cost.empty:
            time_cost = time_cost.merge(item_costs, on="品項名稱", how="left", validate="one_to_one", suffixes=("", "_new"))
            # 用新計算的品項成本覆蓋舊的
            if "品項成本_new" in time_cost.columns:
                time_cost["品項成本"] = time_cost.pop("品項成本_new")
            # 重新計算「時間成本比例(%)」與「建議售價」
            time_cost["時間成本比例(%)"] = time_cost["製作時間(分鐘)"] * per_minute_percentage
            time_cost["建議售價"] = time_cost["品項成本"] + time_cost["品項成本"] * (time_cost["時間成本比例(%)"] / 100)
        else:
            # 若時間成本表原本是空的，就直接使用 item_costs 建立初步結構
            time_cost = item_costs.copy()
            time_cost["製作時間(分鐘)"] = 0
            time_cost["時間成本比例(%)"] = 0
            time_cost["建議售價"] = time_cost["品項成本"]

        save_data(time_cost, TIME_COST_FILE)
        success_message = st.success("已更新所有品項的時間成本與建議售價！")
        time.sleep(1)  # 顯示一秒鐘後消失
        success_message.empty()  # 清除訊息
    else:
        st.warning("尚未定義品項和食材，無法更新時間成本。")

# ---------------------------
# 6. 建議售價與利潤計算模組
# ---------------------------
def calculate_selling_price_and_profit():
    """
    依據使用者選擇的品項與數量，計算總售價與總利潤，並可儲存結果。
    """
    st.header("建議售價和利潤計算")

    # 載入時間成本（含品項成本與建議售價）
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
            for item_name, qty in quantities.items():
                if qty > 0:
                    item_data = time_cost[time_cost["品項名稱"] == item_name]
                    suggested_price = item_data["建議售價"].values[0]
                    cost_value = item_data["品項成本"].values[0]

                    total_price = suggested_price * qty
                    total_cost = cost_value * qty
                    profit = total_price - total_cost

                    results.append({
                        "品項名稱": item_name,
                        "數量": qty,
                        "總成本": total_cost,
                        "總建議售價": total_price,
                        "總利潤": profit
                    })

            results_df = pd.DataFrame(results)
            st.subheader("計算結果")
            st.dataframe(results_df, use_container_width=True)

            # 提供保存結果選項
            if st.button("保存結果"):
                save_data(results_df, SELLING_RESULT_FILE)
                st.success(f"計算結果已保存至 {SELLING_RESULT_FILE} 檔案！")
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
        st.info("版本名稱: v0.0.3")
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
