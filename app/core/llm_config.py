# D:\accapp\app\core\llm_config.py
import streamlit as st
from pandasai.llm.google import GoogleGenerativeAI

def get_llm():
    try:
        google_api_key = st.secrets["google"]["GOOGLE_API_KEY"]
        if not google_api_key or "YOUR" in google_api_key:
            st.error("Google API Key 未設定或為佔位符。")
            return None
        # 使用最新的 GoogleGenerativeAI 連接器
        llm = GoogleGenerativeAI(api_key=google_api_key)
        return llm
    except Exception as e:
        st.error(f"初始化語言模型時出錯: {e}")
        return None