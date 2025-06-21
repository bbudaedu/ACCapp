import streamlit as st
import pandas as pd
from app.core.db_connector import get_db_engine
from sqlalchemy import text
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="科目餘額查詢 (Account Balance Inquiry)", layout="wide")
st.title("科目餘額查詢 (Account Balance Inquiry)")

# --- Database Connection ---
@st.cache_resource
def init_db_connection():
    engine = get_db_engine()
    return engine

db_engine = init_db_connection()
if not db_engine:
    st.error("資料庫引擎未能初始化。請檢查您的資料庫配置。")
    st.stop()

# --- Helper function to fetch data ---

@st.cache_data(ttl=300)
def execute_query(query, params=None):
    try:
        with db_engine.connect() as connection:
            return pd.read_sql(text(query), connection, params=params)
    except Exception as e:
        st.error(f"資料查詢時發生錯誤: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_account_details():
    acc_data_df = execute_query("SELECT AT_NO, AT_NAME, AT_DCR FROM AACNT ORDER BY AT_NO;")
    if not acc_data_df.empty:
        options = {row['AT_NO']: f"{row['AT_NO']} - {row['AT_NAME']} (Bal: {row['AT_DCR']})" for _, row in acc_data_df.iterrows()}
        details = {row['AT_NO']: {'name': row['AT_NAME'], 'dcr': row['AT_DCR']} for _, row in acc_data_df.iterrows()}
        return options, details
    return {}, {}

acc_options, acc_details = load_account_details()

# --- Filter Section ---
st.sidebar.header("篩選條件")

default_start_date_bal = datetime.date.today().replace(day=1)
default_end_date_bal = datetime.date.today()
st.sidebar.date_input("日期區間 (必填)", [default_start_date_bal, default_end_date_bal], key="date_range_balance")

st.sidebar.selectbox(
    "會計科目代碼 (必填)",
    options=[""] + list(acc_options.keys()),
    format_func=lambda x: "請選擇一個科目..." if x == "" else acc_options.get(x, "未知科目"),
    key="acc_code_balance"
)

# --- Session State Initialization ---
if 'account_balance_info' not in st.session_state:
    st.session_state.account_balance_info = None
# ... (rest of session state initializations are fine as they are)

# --- Calculation Logic ---
# (No changes needed in calculate_balances and fetch_drilldown_details functions)
def calculate_balances(account_code, start_date, end_date):
    account_detail = acc_details.get(account_code)
    if not account_detail:
        st.error("無效的會計科目選擇。")
        return None
    account_normal_balance_type = account_detail['dcr']

    # Fixed query with correct data types and date format
    opening_balance_query = """
    SELECT COALESCE(SUM(CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE -d.SD_AMT END), 0) AS OB
    FROM ASPDT d JOIN ASLIP h ON d.SD_NO = h.SP_NO
    WHERE h.SP_CHECK = 1 AND d.SD_ATNO LIKE :acc_pattern AND h.SP_DATE < :start_date;
    """
    ob_params = {'acc_pattern': f"{account_code}%", 'start_date': start_date}
    ob_df = execute_query(opening_balance_query, ob_params)
    opening_balance_raw = ob_df.iloc[0]['OB'] if not ob_df.empty and 'OB' in ob_df.columns else 0
    opening_balance = -opening_balance_raw if account_normal_balance_type == 'C' else opening_balance_raw

    period_movements_query = """
    SELECT
        COALESCE(SUM(CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE 0 END), 0) AS PeriodDebits,
        COALESCE(SUM(CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE 0 END), 0) AS PeriodCredits
    FROM ASPDT d JOIN ASLIP h ON d.SD_NO = h.SP_NO
    WHERE h.SP_CHECK = 1 AND d.SD_ATNO LIKE :acc_pattern AND h.SP_DATE BETWEEN :start_date AND :end_date;
    """
    pm_params = {'acc_pattern': f"{account_code}%", 'start_date': start_date, 'end_date': end_date}
    pm_df = execute_query(period_movements_query, pm_params)
    period_debits = pm_df.iloc[0]['PeriodDebits'] if not pm_df.empty and 'PeriodDebits' in pm_df.columns else 0
    period_credits = pm_df.iloc[0]['PeriodCredits'] if not pm_df.empty and 'PeriodCredits' in pm_df.columns else 0

    if account_normal_balance_type == 'D':
        closing_balance = opening_balance + period_debits - period_credits
    else:
        closing_balance = opening_balance - period_debits + period_credits
    return {"opening": opening_balance, "debits": period_debits, "credits": period_credits, "closing": closing_balance}

def fetch_drilldown_details(account_code, start_date, end_date, movement_type):
    doc_type_filter = "d.SD_DOC = 'D'" if movement_type == 'debits' else "d.SD_DOC = 'C'"
    drilldown_query = f"""
    SELECT CONVERT(varchar, h.SP_DATE, 111) AS SP_DATE_STR, h.SP_NO, d.SD_DCR AS VOUCHER_DETAIL_SUMMARY, d.SD_ATNO, a.AT_NAME,
           CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE 0 END AS DEBIT_AMOUNT, CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE 0 END AS CREDIT_AMOUNT,
           p.EM_NAME AS PREPARER_NAME
    FROM ASPDT d JOIN ASLIP h ON d.SD_NO = h.SP_NO
    LEFT JOIN AACNT a ON d.SD_ATNO = a.AT_NO LEFT JOIN PEMPLOYE p ON h.SP_MKMAN = p.EM_USERID
    WHERE h.SP_CHECK = 1 AND d.SD_ATNO LIKE :acc_pattern AND h.SP_DATE BETWEEN :start_date AND :end_date
      AND {doc_type_filter} ORDER BY h.SP_DATE, h.SP_NO;
    """
    drill_params = {'acc_pattern': f"{account_code}%", 'start_date': start_date, 'end_date': end_date}
    df_details = execute_query(drilldown_query, drill_params)
    display_columns_map = {'SP_DATE_STR': '傳票日期', 'SP_NO': '傳票號碼', 'VOUCHER_DETAIL_SUMMARY': '分錄摘要', 'SD_ATNO': '科目代碼', 'AT_NAME': '科目名稱', 'DEBIT_AMOUNT': '借方金額', 'CREDIT_AMOUNT': '貸方金額', 'PREPARER_NAME': '製單人'}
    return df_details.rename(columns=display_columns_map) if not df_details.empty else pd.DataFrame()


# --- Callback Function for Query Button ---
def perform_balance_query():
    # Get filter values from session_state
    date_range = st.session_state.date_range_balance
    acc_code = st.session_state.acc_code_balance
    
    # Perform validation
    if not date_range or len(date_range) != 2:
        st.warning("請提供完整的日期區間。")
        st.session_state.account_balance_info = None
        return
    if not acc_code:
        st.warning("請選擇一個會計科目。")
        st.session_state.account_balance_info = None
        return

    # If validation passes, proceed
    start_date, end_date = date_range[0], date_range[1]

    with st.spinner("正在計算餘額..."):
        # Calculate balances without company filter
        st.session_state.account_balance_info = calculate_balances(acc_code, start_date, end_date)
        st.session_state.drilldown_data = pd.DataFrame()
        st.session_state.drilldown_type = None
        
        # Store current selections for consistent display and drilldown
        st.session_state.last_selected_acc_code_bal = acc_code
        st.session_state.last_date_range_bal = (start_date, end_date)

# --- UI Interactions ---
st.sidebar.button("查詢餘額", type="primary", on_click=perform_balance_query)

# --- Display Area for Balance Information ---
if st.session_state.get('account_balance_info'):
    info = st.session_state.account_balance_info
    acc_name_display = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.subheader(f"科目餘額: {acc_name_display}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("期初餘額", f"{info['opening']:,.2f}")

    col2.metric("期間借方總額", f"{info['debits']:,.2f}")
    if info['debits'] > 0:
        if col2.button("查看借方明細", key="drill_debit"):
            with st.spinner("載入借方明細..."):
                st.session_state.drilldown_type = "借方發生額 (Debits)"
                st.session_state.drilldown_data = fetch_drilldown_details(
                    st.session_state.last_selected_acc_code_bal,
                    st.session_state.last_date_range_bal[0],
                    st.session_state.last_date_range_bal[1],
                    'debits'
                )

    col3.metric("期間貸方總額", f"{info['credits']:,.2f}")
    if info['credits'] > 0:
        if col3.button("查看貸方明細", key="drill_credit"):
            with st.spinner("載入貸方明細..."):
                st.session_state.drilldown_type = "貸方發生額 (Credits)"
                st.session_state.drilldown_data = fetch_drilldown_details(
                    st.session_state.last_selected_acc_code_bal,
                    st.session_state.last_date_range_bal[0],
                    st.session_state.last_date_range_bal[1],
                    'credits'
                )

    col4.metric("期末餘額", f"{info['closing']:,.2f}")
    st.caption(f"科目 {st.session_state.last_selected_acc_code_bal} ({acc_details.get(st.session_state.last_selected_acc_code_bal, {}).get('dcr', 'N/A')}類)")

else:
    st.info("請在側邊欄選擇日期區間和會計科目後，點擊「查詢餘額」。")

# --- Display Area for Drill-down Details ---
if not st.session_state.get('drilldown_data', pd.DataFrame()).empty:
    st.markdown("---")
    acc_name_display_drill = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.subheader(f"科目: {acc_name_display_drill} - {st.session_state.drilldown_type} 明細")
    st.dataframe(st.session_state.drilldown_data, height=300, use_container_width=True)
elif st.session_state.get('drilldown_type') and st.session_state.get('drilldown_data', pd.DataFrame()).empty:
    st.markdown("---")
    acc_name_display_drill = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.info(f"科目 {acc_name_display_drill} 在選定期間內無 {st.session_state.drilldown_type} 明細可顯示。")

st.sidebar.info("提示：選擇父科目將會彙總其所有子科目的餘額。")