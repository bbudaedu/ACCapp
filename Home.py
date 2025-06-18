import streamlit as st

st.set_page_config(
    page_title="現代化會計查詢與報表系統",
    page_icon="📊",
    layout="wide"
)

st.title("現代化會計查詢與報表系統")
st.sidebar.success("請從左方選擇一個功能模組。")

st.markdown(
    """
    歡迎使用現代化會計查詢與報表系統。

    本系統基於現有的 SQL Server 資料庫，提供強大且友善的介面，用於：
    *   進階的傳票查詢。
    *   會計科目餘額的動態查詢與鑽取。
    *   自動化的財務報表生成（損益表、資產負債表）。
    *   視覺化的數據儀表板，呈現關鍵營運指標 (KPI)。

    **👈 請從左側的側邊欄選擇一個功能頁面開始操作。**

    **各功能頁面說明:**
    *   **0_AI_Assistant:** (原 Chat_with_Data) 提供自然語言查詢會計數據的功能。
    *   **1_Journal_Voucher_Inquiry:** 傳票查詢功能。
    *   **2_Account_Balance_Inquiry:** 會計科目餘額查詢與鑽取。
    *   **3_Income_Statement:** 自動化損益表生成。
    *   **4_Balance_Sheet:** 自動化資產負債表生成。
    *   **5_Dashboard:** 視覺化數據儀表板。
    """
)