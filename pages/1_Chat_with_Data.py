# D:\accapp\pages\1_Chat_with_Data.py
import streamlit as st
import pandas as pd
from sqlalchemy import text 
from pandasai import Agent
from app.core.llm_config import get_llm
from app.core.db_connector import get_db_engine

st.set_page_config(layout="wide", page_title="Chat with Your Accounting Data")
st.title("📊 与您的会计数据对话")
st.markdown("在这里，您可以使用自然语言向您的会计数据提问。")

@st.cache_resource
def load_app_resources():
    _llm = get_llm()
    _db_engine = get_db_engine()
    return _llm, _db_engine

# --- 載入資源並顯示狀態 ---
llm, db_engine = load_app_resources()
if llm:
    st.success("LLM (语言模型) 已成功初始化！")
else:
    st.error("LLM (语言模型) 未能初始化。请检查您的 API 密钥。")

if db_engine:
    st.success("数据库引擎已成功初始化！")
else:
    st.error("数据库引擎未能初始化。请检查您的数据库配置。")

# --- 載入資料 ---
df = None
if db_engine:
    sql_query_str = """
    SELECT TOP 5000
        ASLIP.SP_DATE, ASLIP.SP_NO, ASLIP.SP_CHECK, 
        ASPDT.SD_ATNO, AACNT.AT_NAME, AACNT.AT_DCR AS ACC_DCR,
        ASPDT.SD_AMT, ASPDT.SD_DOC, ASPDT.SD_DCR AS VOUCHER_DETAIL_SUMMARY,
        ASLIP.SP_MKMAN
    FROM ASPDT
    INNER JOIN ASLIP ON ASPDT.SD_NO = ASLIP.SP_NO
    INNER JOIN AACNT ON ASPDT.SD_ATNO = AACNT.AT_NO
    WHERE ASLIP.SP_CHECK = 1
    ORDER BY ASLIP.SP_DATE DESC, ASLIP.SP_NO DESC;
    """
    try:
        with st.spinner("正在从数据库加载数据..."):
            with db_engine.connect() as connection:
                df = pd.read_sql(text(sql_query_str), connection)
        
        if df.empty:
            st.warning("查询成功，但未从数据库返回数据。")
        else:
            st.success(f"成功从数据库加载了 {len(df)} 条会计分录。")
            with st.expander("查看数据预览", expanded=False):
                st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"从数据库加载数据时出错: {e}")
        df = None

# --- 初始化 PandasAI Agent ---
agent = None
if llm and df is not None and not df.empty:
    st.markdown("---")
    st.subheader("AI 数据分析助手")
    try:
        agent = Agent(df, config={"llm": llm, "verbose": True})
        st.success("AI 数据分析助手已准备就绪。")
    except Exception as e:
        st.error(f"初始化 PandasAI Agent 时出错: {e}")
else:
    st.markdown("---")
    st.warning("AI 助手无法初始化，请确保语言模型和数据库都已成功连接并加载了数据。")

# --- 使用者互動 ---
st.markdown("---")
user_question = st.text_input("向您的会计数据提问:", placeholder="例如: '总收入是多少?' 或 '按类别列出支出总额'")

if st.button("发送查询", type="primary"):
    if user_question and agent:
        with st.spinner("AI 正在思考..."):
            try:
                response = agent.chat(user_question)
                st.markdown("### 💡 AI 回答:")
                # 根據回應類型顯示結果
                if response is None:
                    st.info("AI 已处理您的请求，但没有直接的文本或图表输出。")
                elif isinstance(response, (pd.DataFrame, pd.Series)):
                    st.dataframe(response)
                else:
                    st.write(response)
                
                # 安全地獲取並顯示生成的程式碼
                last_code = getattr(agent, 'last_code_executed', None)
                if last_code:
                     with st.expander("查看 AI 生成的代码"):
                        st.code(last_code, language='python')
            except Exception as e:
                st.error(f"执行查询时出错: {e}")
    elif not user_question:
        st.warning("请输入您的问题。")
    else:
        st.error("AI 助手未初始化，无法执行查询。")