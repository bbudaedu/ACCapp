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
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_accounting_data(_db_engine): # Pass engine as argument for caching
    if not _db_engine:
        return None

    # Use a more specific name for the data, e.g., recent_transactions_df
    # Corrected JOIN condition and ensure SP_INDEX and SD_INDEX are used if they are part of the key.
    # Assuming ASLIP.SP_INDEX and ASPDT.SD_INDEX form part of the composite key with SP_NO/SD_NO.
    sql_query_str = """
    SELECT TOP 5000
        h.SP_DATE,
        h.SP_NO,
        h.SP_CHECK,
        d.SD_ATNO,
        a.AT_NAME,
        a.AT_DCR AS ACC_DCR,
        d.SD_AMT,
        d.SD_DOC,
        d.SD_DCR AS VOUCHER_DETAIL_SUMMARY,
        h.SP_MKMAN
    FROM ASPDT d
    INNER JOIN ASLIP h ON d.SD_NO = h.SP_NO -- Removed d.SD_INDEX = h.SP_INDEX from join
    INNER JOIN AACNT a ON d.SD_ATNO = a.AT_NO
    WHERE h.SP_CHECK = '1'  -- Assuming '1' means approved/relevant
    ORDER BY h.SP_DATE DESC, h.SP_NO DESC;
    """
    try:
        with st.spinner("正在从数据库加载最新的会计分录 (最多5000条)..."): # More specific spinner
            with _db_engine.connect() as connection:
                dataframe = pd.read_sql(text(sql_query_str), connection)
        
        if dataframe.empty:
            st.warning("查询成功，但未从数据库返回数据。")
        else:
            st.success(f"成功从数据库加载了 {len(dataframe)} 条最新的会计分录。")
            # Data preview is now inside the function, shown only once post-caching or on error.
            # Consider moving preview outside if needed on every run with cached data.
        return dataframe
    except Exception as e:
        st.error(f"从数据库加载数据时出错: {e}")
        return None

recent_transactions_df = load_accounting_data(db_engine)

if recent_transactions_df is not None and not recent_transactions_df.empty:
    with st.expander("查看数据预览 (View Data Preview)", expanded=False):
        st.dataframe(recent_transactions_df.head(10))

# --- 初始化 PandasAI Agent ---
agent = None
if llm and recent_transactions_df is not None and not recent_transactions_df.empty:
    st.markdown("---")
    st.subheader("AI 数据分析助手")
    try:
        # Pass the DataFrame to the agent
        agent = Agent(recent_transactions_df, config={"llm": llm, "verbose": True, "handle_pandas_errors": True, "handle_verification_errors": True})
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