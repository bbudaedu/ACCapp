import streamlit as st

# 設定頁面標題和圖標
st.set_page_config(
    page_title="應用程式首頁",
    page_icon="🏠",
)

# 顯示主標題和說明文字
st.title("歡迎來到我的應用程式！")
st.sidebar.success("從上方選擇一個頁面來開始。")

st.markdown(
    """
    這是一個使用 Streamlit 建立的多頁面應用程式。
    **👈 請從左側的側邊欄選擇一個功能頁面** 來與你的資料互動！
    """
)