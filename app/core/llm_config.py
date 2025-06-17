# D:\accapp\app\core\llm_config.py
import streamlit as st
import google.generativeai as genai
from pandasai_litellm import LiteLLM

def get_llm():
    try:
        google_api_key = st.secrets["google"]["GOOGLE_API_KEY"]
        if not google_api_key or "YOUR" in google_api_key:
            st.error("Google API Key 未設定或為佔位符。")
            return None
        genai.configure(api_key=google_api_key)
        # It's important to pass the model name as a string to LiteLLM,
        # as LiteLLM handles the interaction with the underlying SDK.
        # LiteLLM will use the genai.configure() call from above.
        model = LiteLLM(model="gemini/gemini-2.0-flash")
        return model
    except Exception as e:
        st.error(f"初始化語言模型時出錯: {e}")
        return None