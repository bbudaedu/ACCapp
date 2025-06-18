import streamlit as st
import pandas as pd
from app.core.db_connector import get_db_engine
from sqlalchemy import text # Removed and_, or_ as they are not used
import datetime
import io # Required for Excel export
import openpyxl # Explicitly import though pandas might handle it.

# --- Page Configuration ---
st.set_page_config(page_title="傳票查詢 (Journal Voucher Inquiry)", layout="wide")
st.title("傳票查詢 (Journal Voucher Inquiry)")

# --- Database Connection ---
@st.cache_resource
def init_db_connection():
    engine = get_db_engine()
    # Removed success/error messages from here to avoid repetition on rerun
    return engine

db_engine = init_db_connection()
if not db_engine:
    st.error("資料庫引擎未能初始化。請檢查您的資料庫配置。請在 `secrets.toml` 中進行配置。")
    st.stop() # Stop execution if DB is not available

# --- Helper function to fetch data for dropdowns ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_dropdown_data(query, params=None):
    try:
        with db_engine.connect() as connection:
            return pd.read_sql(text(query), connection, params=params)
    except Exception as e:
        st.error(f"載入下拉選單數據時發生錯誤: {e}")
        return pd.DataFrame()

# --- Load data for filters ---
acc_data = fetch_dropdown_data("SELECT AT_NO, AT_NAME FROM AACNT ORDER BY AT_NO;")
acc_options = {row['AT_NO']: f"{row['AT_NO']} - {row['AT_NAME']}" for index, row in acc_data.iterrows()} if not acc_data.empty else {}

emp_data = fetch_dropdown_data("SELECT EM_USERID, EM_NAME FROM PEMPLOYE ORDER BY EM_USERID;") # Removed WHERE EM_JOBSTS = 1
emp_options = {row['EM_USERID']: f"{row['EM_USERID']} - {row['EM_NAME']}" for index, row in emp_data.iterrows()} if not emp_data.empty else {}

# --- Filter Section ---
st.sidebar.header("篩選條件")

default_start_date = datetime.date.today().replace(day=1)
default_end_date = datetime.date.today()
date_range_selected = st.sidebar.date_input("日期區間 (必填)", [default_start_date, default_end_date], key="date_range_journal")

if len(date_range_selected) == 2:
    start_date, end_date = date_range_selected
else:
    start_date, end_date = None, None
    # This warning is now implicitly handled by the search button logic

selected_acc_codes = st.sidebar.multiselect(
    "會計科目代碼 (可多選)",
    options=list(acc_options.keys()),
    format_func=lambda x: acc_options.get(x, x) # Use .get for safety
)
summary_keyword = st.sidebar.text_input("摘要關鍵字 (模糊查詢 ASPDT.SD_DCR)")
col_min_amount, col_max_amount = st.sidebar.columns(2)
min_amount = col_min_amount.number_input("最小金額 (分錄金額)", value=None, placeholder="請輸入數字...", step=100.0)
max_amount = col_max_amount.number_input("最大金額 (分錄金額)", value=None, placeholder="請輸入數字...", step=100.0)
voucher_no_keyword = st.sidebar.text_input("傳票號碼 (ASLIP.SP_NO, 可部分符合)")
selected_preparers = st.sidebar.multiselect(
    "製單人 (可多選)",
    options=list(emp_options.keys()),
    format_func=lambda x: emp_options.get(x, x) # Use .get for safety
)
audit_status_options = {"all": "全部", "1": "已審核", "0": "未審核"} # Assuming '0' for unapproved, confirm this.
selected_audit_status_key = st.sidebar.selectbox(
    "審核狀態",
    options=list(audit_status_options.keys()),
    format_func=lambda x: audit_status_options[x],
    index=0
)

# --- Session State for Storing Results ---
if 'journal_voucher_results' not in st.session_state:
    st.session_state.journal_voucher_results = pd.DataFrame()
if 'journal_voucher_query_executed' not in st.session_state:
    st.session_state.journal_voucher_query_executed = False

# --- Search Button and Query Logic ---
if st.sidebar.button("查詢傳票", type="primary"):
    if not start_date or not end_date:
        st.warning("請提供完整的日期區間。")
    else:
        st.session_state.journal_voucher_query_executed = True
        # Build the SQL query
        sql_base = """
        SELECT
            CONVERT(varchar, h.SP_DATE, 111) AS SP_DATE_STR, -- Format as yyyy/mm/dd
            h.SP_NO,
            h.SP_MEMO AS VOUCHER_HEADER_SUMMARY, --傳票摘要 (from ASLIP)
            d.SD_ATNO,
            a.AT_NAME,
            d.SD_DCR AS VOUCHER_DETAIL_SUMMARY, -- 分錄摘要 (from ASPDT)
            CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE 0 END AS DEBIT_AMOUNT,
            CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE 0 END AS CREDIT_AMOUNT,
            p.EM_NAME AS PREPARER_NAME,
            CASE h.SP_CHECK WHEN '1' THEN '已審核' ELSE '未審核' END AS AUDIT_STATUS_DESC,
            h.SP_CHECK -- for filtering
        FROM ASPDT d
        INNER JOIN ASLIP h ON d.SD_NO = h.SP_NO AND d.SD_INDEX = h.SP_INDEX -- Assuming SD_INDEX is part of the key
        LEFT JOIN AACNT a ON d.SD_ATNO = a.AT_NO
        LEFT JOIN PEMPLOYE p ON h.SP_MKMAN = p.EM_USERID
        """

        conditions = []
        params = {}

        # Date Range (Mandatory)
        conditions.append("h.SP_DATE BETWEEN :start_date AND :end_date")
        params['start_date'] = start_date.strftime('%Y%m%d')
        params['end_date'] = end_date.strftime('%Y%m%d')

        # Account Codes
        if selected_acc_codes:
            conditions.append(f"d.SD_ATNO IN ({', '.join([':acc_code_'+str(i) for i in range(len(selected_acc_codes))])})")
            for i, code in enumerate(selected_acc_codes):
                params['acc_code_'+str(i)] = code

        # Summary Keyword (ASPDT.SD_DCR)
        if summary_keyword:
            conditions.append("d.SD_DCR LIKE :summary_keyword")
            params['summary_keyword'] = f"%{summary_keyword}%"

        # Amount Range (on SD_AMT)
        if min_amount is not None:
            conditions.append("d.SD_AMT >= :min_amount")
            params['min_amount'] = min_amount
        if max_amount is not None:
            conditions.append("d.SD_AMT <= :max_amount")
            params['max_amount'] = max_amount

        # Voucher Number (ASLIP.SP_NO)
        if voucher_no_keyword:
            conditions.append("h.SP_NO LIKE :voucher_no_keyword")
            params['voucher_no_keyword'] = f"%{voucher_no_keyword}%"

        # Preparers
        if selected_preparers:
            conditions.append(f"h.SP_MKMAN IN ({', '.join([':preparer_'+str(i) for i in range(len(selected_preparers))])})")
            for i, prep_id in enumerate(selected_preparers):
                params['preparer_'+str(i)] = prep_id

        # Audit Status
        if selected_audit_status_key != "all":
            conditions.append("h.SP_CHECK = :audit_status")
            params['audit_status'] = selected_audit_status_key

        sql_query = sql_base
        if conditions:
            sql_query += " WHERE " + " AND ".join(conditions)

        sql_query += " ORDER BY h.SP_DATE, h.SP_NO, d.SD_SEQ;" # Assuming SD_SEQ for detail order

        try:
            with st.spinner("正在查詢資料庫..."):
                with db_engine.connect() as connection:
                    df_results = pd.read_sql(text(sql_query), connection, params=params)

            # Rename columns for display as per FR-1.3
            # SP_DATE_STR (傳票日期), SP_NO (傳票號碼), VOUCHER_HEADER_SUMMARY (傳票摘要),
            # SD_ATNO (科目代碼), AT_NAME (科目名稱), VOUCHER_DETAIL_SUMMARY (分錄摘要),
            # DEBIT_AMOUNT (借方金額), CREDIT_AMOUNT (貸方金額), PREPARER_NAME (製單人),
            # AUDIT_STATUS_DESC (審核狀態)
            display_columns = {
                'SP_DATE_STR': '傳票日期',
                'SP_NO': '傳票號碼',
                'VOUCHER_HEADER_SUMMARY': '傳票摘要',
                'SD_ATNO': '科目代碼',
                'AT_NAME': '科目名稱',
                'VOUCHER_DETAIL_SUMMARY': '分錄摘要',
                'DEBIT_AMOUNT': '借方金額',
                'CREDIT_AMOUNT': '貸方金額',
                'PREPARER_NAME': '製單人',
                'AUDIT_STATUS_DESC': '審核狀態'
            }
            # Ensure all expected columns are present before renaming
            # Create missing columns with default values (e.g., None or 0) if necessary
            for col in display_columns.keys():
                if col not in df_results.columns:
                    # Decide a default value based on expected data type, e.g., for numeric or text
                    if 'AMOUNT' in col:
                         df_results[col] = 0
                    else:
                         df_results[col] = None

            df_display = df_results[list(display_columns.keys())].rename(columns=display_columns)
            st.session_state.journal_voucher_results = df_display

            if df_display.empty:
                st.info("根據您的篩選條件，查無任何傳票分錄。")
            # Display handled below, outside the button click logic to persist on rerun

        except Exception as e:
            st.error(f"查詢傳票時發生錯誤: {e}")
            st.session_state.journal_voucher_results = pd.DataFrame()


# --- Display Area for Results ---
if st.session_state.journal_voucher_query_executed:
    st.subheader("查詢結果")
    if not st.session_state.journal_voucher_results.empty:
        df_to_display = st.session_state.journal_voucher_results
        st.dataframe(df_to_display, height=600) # Adjust height as needed

        # --- Export to Excel ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_to_display.to_excel(writer, index=False, sheet_name='傳票查詢結果')
        excel_data = output.getvalue()

        # Determine filename components safely
        start_date_str = start_date.strftime('%Y%m%d') if start_date else 'nodate'
        end_date_str = end_date.strftime('%Y%m%d') if end_date else 'nodate'

        st.download_button(
            label="📥 匯出 Excel",
            data=excel_data,
            file_name=f"journal_vouchers_{start_date_str}_{end_date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif st.session_state.journal_voucher_query_executed: # Query was run but no results
        # This message is now shown within the button click logic when df_display is empty
        # or implicitly by st.info if the dataframe is empty after a successful query.
        pass
else:
    st.info("請設定篩選條件後點擊側邊欄的「查詢傳票」按鈕。")

st.sidebar.info("提示：日期格式為 YYYY/MM/DD。摘要關鍵字會對分錄摘要進行模糊比對。")

# Note: ASPDT.SD_INDEX and ASLIP.SP_INDEX are assumed to be part of the join condition.
# ASPDT.SD_SEQ is assumed for ordering details within a voucher. These may need confirmation.
# The audit status value for "unapproved" is assumed to be '0'. This also needs confirmation as per SRS.
# The date format for ASLIP.SP_DATE in SQL Server is assumed to be compatible with YYYYMMDD for BETWEEN clauses.
# CONVERT(varchar, h.SP_DATE, 111) is used for display, actual filtering uses direct date objects.
