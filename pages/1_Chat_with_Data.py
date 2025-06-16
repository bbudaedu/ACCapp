# pages/1_Chat_with_Data.py
import streamlit as st
import pandas as pd
from pandasai import SmartDataframe # Or SmartDatalake if we evolve to it
# Assuming pandasai is installed and accessible.
# The specific LLM class (GooglePalm or GoogleGenerativeAI) is encapsulated in get_llm()
from app.core.llm_config import get_llm
from app.core.db_connector import get_db_engine # Import the DB engine function

st.set_page_config(layout="wide", page_title="Chat with Your Accounting Data")

st.title("📊 与您的会计数据对话")
st.markdown("""
在这里，您可以使用自然语言提出关于您会计数据的问题。
**请注意:** 如果数据库连接失败或表中没有数据，此应用可能无法正常工作。
""")

# --- Initialization ---
@st.cache_resource # Cache resources for efficiency
def load_app_resources():
    # This function will now attempt to load both LLM and DB Engine
    # It will return None for resources that fail to initialize
    _llm = get_llm()
    _db_engine = get_db_engine()
    return _llm, _db_engine

llm, db_engine = load_app_resources()

if not llm:
    st.warning("LLM (语言模型) 未能初始化。请检查您的 API 密钥配置 (.streamlit/secrets.toml) 和错误信息。")
    st.markdown("确保 `GOOGLE_API_KEY` 在 `.streamlit/secrets.toml` 文件中的 `[google]` 部分下是正确的。")
    # We don't stop here, as data loading might still be attempted or user informed.
else:
    st.success("LLM (语言模型) 已成功初始化！")

if not db_engine:
    st.error("数据库引擎未能初始化。请检查您的数据库配置 (.streamlit/secrets.toml) 和错误信息。应用可能无法加载数据。")
    # We don't stop here, user should be informed about PandasAI initialization later if df is None
else:
    st.success("数据库引擎已成功初始化！")

# --- Data Loading from SQL Server ---
df = None # Initialize df as None
if db_engine: # Proceed only if db_engine was successfully initialized
    st.subheader("正在从 SQL Server 加载会计分录数据...")
    sql_query = """
    SELECT TOP 5000
        ASLIP.SP_DATE,
        ASLIP.SP_NO,
        ASLIP.SP_CHECK, 
        ASPDT.SD_ATNO,
        AACNT.AT_NAME,
        AACNT.AT_DCR AS ACC_DCR, -- Renaming to avoid conflict if SD_DCR is also selected
        ASPDT.SD_AMT,
        ASPDT.SD_DOC,
        ASPDT.SD_DCR AS VOUCHER_DETAIL_SUMMARY, -- Renaming for clarity
        ASLIP.SP_MKMAN
    FROM ASPDT
    INNER JOIN ASLIP ON ASPDT.SD_NO = ASLIP.SP_NO
    INNER JOIN AACNT ON ASPDT.SD_ATNO = AACNT.AT_NO
    WHERE ASLIP.SP_CHECK = 1  -- Assuming 1 means audited/checked
    ORDER BY ASLIP.SP_DATE DESC, ASLIP.SP_NO DESC;
    """
    try:
        with st.spinner("正在执行数据库查询..."):
            df = pd.read_sql(sql_query, db_engine)
        if df.empty:
            st.warning("查询成功，但未从数据库返回数据。请检查您的表 (ASPDT, ASLIP, AACNT) 是否包含符合条件的数据 (SP_CHECK = 1)。")
        else:
            st.success(f"成功从数据库加载了 {len(df)} 条会计分录。")
            with st.expander("查看从数据库加载的数据预览 (前10条)", expanded=False):
                st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"从数据库加载数据时出错: {e}")
        st.info("请检查数据库连接、表名 (ASPDT, ASLIP, AACNT) 和字段名是否正确，以及数据库是否可访问。")
        df = None # Ensure df is None if loading fails
else:
    st.warning("数据库引擎未初始化，无法加载数据。请检查您的 secrets.toml 文件中的数据库配置。")


# --- Initialize PandasAI SmartDataframe ---
smart_df = None
# We proceed with PandasAI setup only if LLM is available AND df is loaded and not empty
if llm and df is not None and not df.empty:
    st.markdown("---")
    st.subheader("AI 数据分析助手初始化")
    try:
        # Configuration for PandasAI
        # verbose=True helps in debugging by showing thoughts of the LLM
        # enable_cache=True caches responses for same queries
        # enforce_privacy=True can be used if you want to prevent data from being sent to the LLM
        pandas_ai_config = {
            "llm": llm,
            "verbose": True,
            "enable_cache": True, 
            "enforce_privacy": False, # Set to True if dealing with very sensitive data not to be shared with LLM provider
        }
        smart_df = SmartDataframe(df, config=pandas_ai_config)
        st.success("AI 数据分析助手 (PandasAI SmartDataframe) 已成功初始化 (使用从数据库加载的数据)。")
    except Exception as e:
        st.error(f"初始化 PandasAI SmartDataframe 时出错: {e}")
        # Do not stop the app, just inform the user. smart_df will remain None.
elif not llm:
    st.error("AI 数据分析助手无法初始化，因为 LLM (语言模型) 未配置。")
elif df is None or df.empty:
    st.warning("没有从数据库加载数据，或数据为空。AI 数据分析助手无法初始化。")
    st.markdown("请检查数据库连接和查询逻辑。如果使用的是占位符凭据，请更新为您的实际数据库信息。")


# --- User Input and Querying ---
# This section should only be active if smart_df was successfully initialized
st.markdown("---")
st.subheader("💬 向 AI 提问:")
user_question = st.text_input("例如: '总收入是多少?' 或 '按类别列出支出总额' 或 '哪个地区的收入最高?'")

if st.button("发送查询", type="primary") and user_question and smart_df:
    with st.spinner("AI 正在思考并查询数据... 请稍候..."):
        try:
            # The .chat() method sends the natural language query
            response = smart_df.chat(user_question)

            st.markdown("### 💡 AI 回答:")
            if response is None:
                # PandasAI version 1.x and later might return None if the action taken doesn't produce a direct answer (e.g. saving a plot)
                # Check for last_result or other attributes if needed, or rely on verbose logs.
                st.info("AI 已处理您的请求。如果预期有可见输出但未显示，它可能已执行了诸如生成图表之类的操作（请检查是否有图表显示或保存在工作目录中），或者它可能无法直接回答。")
                # Try to display last generated chart if available
                if hasattr(smart_df, 'last_generated_chart') and smart_df.last_generated_chart:
                    st.image(smart_df.last_generated_chart)
            elif isinstance(response, pd.DataFrame) or isinstance(response, pd.Series):
                st.dataframe(response)
            elif isinstance(response, (str, int, float, list, dict)):
                # Check if it's a plot path (common way pandasai returns plots)
                if isinstance(response, str) and (response.endswith(".png") or response.endswith(".jpg")):
                    st.image(response)
                elif isinstance(response, dict) and response.get("type") == "plot" and "value" in response:
                     st.image(response["value"])
                else:
                    st.write(response)
            else:
                # For any other type of response, try to display it as a string
                st.write(str(response))
                
            # Display last generated code if available (for transparency)
            if hasattr(smart_df, 'last_code_generated') and smart_df.last_code_generated:
                 with st.expander("查看 AI 生成的代码", expanded=False):
                    st.code(smart_df.last_code_generated, language='python')

        except Exception as e:
            st.error(f"执行查询时出错: {e}")
            # Optionally, show last generated code even on error for debugging
            if hasattr(smart_df, 'last_code_generated') and smart_df.last_code_generated:
                 with st.expander("查看 AI 生成的代码 (出错前)", expanded=False):
                    st.code(smart_df.last_code_generated, language='python')

elif st.button("发送查询", type="primary") and not user_question:
    st.warning("请输入您的问题。")

st.markdown("---")
st.info("""
**关于此页面:**
- 此页面使用 PandasAI 连接到您的 SQL Server 数据库，允许您使用自然语言查询会计数据。
- 数据通过 `app.core.db_connector.py` 中的 `get_db_engine()` 函数从 SQL Server 加载。
- 使用的表包括 `ASPDT`, `ASLIP`, 和 `AACNT`。查询获取最近5000条已审核的会计分录。
- API 密钥 (用于 LLM) 和数据库凭据通过 `.streamlit/secrets.toml` 文件安全管理。
- LLM (语言模型) 通过 `app.core.llm_config.py` 配置。
""", icon="ℹ️")

# To run this app:
# 1. Ensure all dependencies are installed:
#    pip install streamlit pandas pandasai google-generativeai pyodbc SQLAlchemy
# 2. Configure `.streamlit/secrets.toml` with your GOOGLE_API_KEY and actual SQL Server database credentials.
# 3. Run Streamlit: e.g., `streamlit run Home.py` (if you have a main Home page) or `streamlit run pages/1_Chat_with_Data.py`
```
