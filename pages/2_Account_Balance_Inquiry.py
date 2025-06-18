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
@st.cache_data(ttl=3600) # Cache company data longer
def fetch_company_data_abi(): # For Account Balance Inquiry
    if not db_engine:
        return pd.DataFrame(columns=['CP_UNINO', 'CP_NAME']) # Use new column names
    try:
        with db_engine.connect() as connection:
            # Use new query: SELECT CP_UNINO, CP_NAME FROM PCOMPANY ORDER BY CP_NAME
            df = pd.read_sql(text("SELECT CP_UNINO, CP_NAME FROM PCOMPANY ORDER BY CP_NAME"), connection)
            return df
    except Exception as e:
        st.error(f"獲取公司列表時發生錯誤 (科目餘額查詢): {e}")
        return pd.DataFrame(columns=['CP_UNINO', 'CP_NAME']) # Use new column names

@st.cache_data(ttl=300) # Cache for 5 minutes for query results
def execute_query(query, params=None):
    try:
        with db_engine.connect() as connection:
            return pd.read_sql(text(query), connection, params=params)
    except Exception as e:
        st.error(f"資料查詢時發生錯誤: {e}")
        return pd.DataFrame()

# --- Load data for filters ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def load_account_details():
    acc_data_df = execute_query("SELECT AT_NO, AT_NAME, AT_DCR FROM AACNT ORDER BY AT_NO;") # Removed AT_LEVEL from query
    if not acc_data_df.empty:
        options = {
            # Removed AT_LEVEL from display string
            row['AT_NO']: f"{row['AT_NO']} - {row['AT_NAME']} (Bal: {row['AT_DCR']})"
            for _, row in acc_data_df.iterrows()
        }
        # Removed 'level': row['AT_LEVEL'] from details dict
        details = {row['AT_NO']: {'name': row['AT_NAME'], 'dcr': row['AT_DCR']} for _, row in acc_data_df.iterrows()}
        return options, details
    return {}, {}

acc_options, acc_details = load_account_details()

# --- Filter Section ---
st.sidebar.header("篩選條件")

# Company Selector
companies_df_abi = fetch_company_data_abi()
# Update to use CP_UNINO and CP_NAME
company_options_abi = {row['CP_UNINO']: row['CP_NAME'] for _, row in companies_df_abi.iterrows()} if not companies_df_abi.empty else {}
selected_company_unino_abi = None # Changed variable name
selected_company_name_abi = "無公司"

if not company_options_abi:
    st.sidebar.warning("未找到任何公司資料 (科目餘額查詢)。")
else:
    default_company_unino_abi = list(company_options_abi.keys())[0]
    selected_company_unino_abi = st.sidebar.selectbox(
        "公司 (Company)", options=list(company_options_abi.keys()), # Options are CP_UNINO
        format_func=lambda x: company_options_abi.get(x, "未知公司"), # Format uses CP_NAME
        key="abi_company_unino", index=0 # Changed key
    )
    selected_company_name_abi = company_options_abi.get(selected_company_unino_abi, "未知公司") # This remains for initial display if needed, but button logic will use session_state

default_start_date_bal = datetime.date.today().replace(day=1)
default_end_date_bal = datetime.date.today()
date_range_bal_selected = st.sidebar.date_input("日期區間 (必填)", [default_start_date_bal, default_end_date_bal], key="date_range_balance")

start_date_bal, end_date_bal = (date_range_bal_selected[0], date_range_bal_selected[1]) if len(date_range_bal_selected) == 2 else (None, None)

selected_acc_code_bal = st.sidebar.selectbox(
    "會計科目代碼 (必填)",
    options=[""] + list(acc_options.keys()),
    format_func=lambda x: "請選擇一個科目..." if x == "" else acc_options.get(x, "未知科目"),
    key="acc_code_balance"
)

# --- Session State ---
if 'account_balance_info' not in st.session_state:
    st.session_state.account_balance_info = None # Will store dict: {opening, debit, credit, closing}
if 'drilldown_data' not in st.session_state:
    st.session_state.drilldown_data = pd.DataFrame()
if 'drilldown_type' not in st.session_state:
    st.session_state.drilldown_type = None
if 'last_selected_acc_code_bal' not in st.session_state:
    st.session_state.last_selected_acc_code_bal = None
if 'last_date_range_bal' not in st.session_state:
    st.session_state.last_date_range_bal = None
if 'last_selected_company_no_abi' not in st.session_state:
    st.session_state.last_selected_company_no_abi = None # This will store CP_UNINO
if 'last_selected_company_name_abi' not in st.session_state: # To store name for display
    st.session_state.last_selected_company_name_abi = None


# --- Calculation Logic ---
def calculate_balances(account_code, start_date, end_date, company_unino): # Parameter name changed
    if not company_unino: # Check updated param name
        st.error("錯誤：計算餘額時未提供公司統編。")
        return None
    account_detail = acc_details.get(account_code)
    if not account_detail:
        st.error("無效的會計科目選擇。")
        return None

    account_normal_balance_type = account_detail['dcr'] # 'D' or 'C'

    # Query for Opening Balance
    # Sum amounts for transactions BEFORE the start_date
    # IMPORTANT: Date format for SQL Server YYYYMMDD
    opening_balance_query = """
    SELECT COALESCE(SUM(CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE -d.SD_AMT END), 0) AS OB
    FROM ASPDT d
    JOIN ASLIP h ON d.SD_NO = h.SP_NO -- Removed d.SD_INDEX = h.SP_INDEX from join
    WHERE h.SP_CHECK = '1' AND d.SD_ATNO LIKE :acc_pattern AND h.SP_DATE < :start_date_str
      AND h.SP_CO_NO = :company_unino; -- Use company_unino
    """
    ob_params = {'acc_pattern': f"{account_code}%",
                 'start_date_str': start_date.strftime('%Y%m%d'),
                 'company_unino': company_unino} # Use company_unino
    ob_df = execute_query(opening_balance_query, ob_params)
    opening_balance_raw = ob_df.iloc[0]['OB'] if not ob_df.empty and 'OB' in ob_df.columns else 0

    # Adjust raw opening balance based on account's normal balance type
    # If normal balance is Credit (e.g. Liabilities, Equity, Income), then OB is -raw_value
    # If normal balance is Debit (e.g. Assets, Expenses), then OB is raw_value
    opening_balance = -opening_balance_raw if account_normal_balance_type == 'C' else opening_balance_raw

    # Query for Period Debits and Credits
    period_movements_query = """
    SELECT
        COALESCE(SUM(CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE 0 END), 0) AS PeriodDebits,
        COALESCE(SUM(CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE 0 END), 0) AS PeriodCredits
    FROM ASPDT d
    JOIN ASLIP h ON d.SD_NO = h.SP_NO -- Removed d.SD_INDEX = h.SP_INDEX from join
    WHERE h.SP_CHECK = '1' AND d.SD_ATNO LIKE :acc_pattern AND h.SP_DATE BETWEEN :start_date_str AND :end_date_str
      AND h.SP_CO_NO = :company_unino; -- Use company_unino
    """
    pm_params = {
        'acc_pattern': f"{account_code}%",
        'start_date_str': start_date.strftime('%Y%m%d'),
        'end_date_str': end_date.strftime('%Y%m%d'),
        'company_unino': company_unino # Use company_unino
    }
    pm_df = execute_query(period_movements_query, pm_params)
    period_debits = pm_df.iloc[0]['PeriodDebits'] if not pm_df.empty and 'PeriodDebits' in pm_df.columns else 0
    period_credits = pm_df.iloc[0]['PeriodCredits'] if not pm_df.empty and 'PeriodCredits' in pm_df.columns else 0

    # Calculate Closing Balance
    if account_normal_balance_type == 'D': # Assets, Expenses
        closing_balance = opening_balance + period_debits - period_credits
    else: # 'C' - Liabilities, Equity, Income
        closing_balance = opening_balance - period_debits + period_credits

    return {
        "opening": opening_balance,
        "debits": period_debits,
        "credits": period_credits,
        "closing": closing_balance
    }

def fetch_drilldown_details(account_code, start_date, end_date, movement_type, company_unino): # Parameter name changed
    if not company_unino: # Check updated param name
        st.error("錯誤：載入明細時未提供公司統編。")
        return pd.DataFrame()
    doc_type_filter = "d.SD_DOC = 'D'" if movement_type == 'debits' else "d.SD_DOC = 'C'"

    drilldown_query = f"""
    SELECT
        CONVERT(varchar, h.SP_DATE, 111) AS SP_DATE_STR,
        h.SP_NO,
        d.SD_DCR AS VOUCHER_DETAIL_SUMMARY,
        d.SD_ATNO,
        a.AT_NAME,
        CASE WHEN d.SD_DOC = 'D' THEN d.SD_AMT ELSE 0 END AS DEBIT_AMOUNT,
        CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE 0 END AS CREDIT_AMOUNT,
        p.EM_NAME AS PREPARER_NAME
    FROM ASPDT d
    JOIN ASLIP h ON d.SD_NO = h.SP_NO -- Removed d.SD_INDEX = h.SP_INDEX from join
    LEFT JOIN AACNT a ON d.SD_ATNO = a.AT_NO
    LEFT JOIN PEMPLOYE p ON h.SP_MKMAN = p.EM_USERID
    WHERE h.SP_CHECK = '1' AND d.SD_ATNO LIKE :acc_pattern
      AND h.SP_DATE BETWEEN :start_date_str AND :end_date_str
      AND {doc_type_filter}
      AND h.SP_CO_NO = :company_unino -- Use company_unino
    ORDER BY h.SP_DATE, h.SP_NO;
    """
    drill_params = {
        'acc_pattern': f"{account_code}%",
        'start_date_str': start_date.strftime('%Y%m%d'),
        'end_date_str': end_date.strftime('%Y%m%d'),
        'company_unino': company_unino # Use company_unino
    }
    df_details = execute_query(drilldown_query, drill_params)

    # Rename for display
    display_columns_map = {
        'SP_DATE_STR': '傳票日期', 'SP_NO': '傳票號碼',
        'VOUCHER_DETAIL_SUMMARY': '分錄摘要', 'SD_ATNO': '科目代碼', 'AT_NAME': '科目名稱',
        'DEBIT_AMOUNT': '借方金額', 'CREDIT_AMOUNT': '貸方金額', 'PREPARER_NAME': '製單人'
    }
    return df_details.rename(columns=display_columns_map) if not df_details.empty else pd.DataFrame()


# --- UI Interactions ---
if st.sidebar.button("查詢餘額", type="primary", key="query_balance_button"):
    # Retrieve selected company from session state using the widget's key
    selected_company_unino_from_state = st.session_state.get('abi_company_unino')
    # The selected_company_name_abi can be fetched using the UNINO from state and options dict
    current_selected_company_name = company_options_abi.get(selected_company_unino_from_state, "未知公司")

    if not selected_company_unino_from_state:
        st.warning("請選擇一個公司。")
    elif not start_date_bal or not end_date_bal:
        st.warning("請提供完整的日期區間。")
    elif not selected_acc_code_bal:
        st.warning("請選擇一個會計科目。")
    else:
        with st.spinner(f"正在為 {current_selected_company_name} 計算餘額..."):
            st.session_state.account_balance_info = calculate_balances(
                selected_acc_code_bal,
                start_date_bal,
                end_date_bal,
                selected_company_unino_from_state # Use value from session state
            )
            st.session_state.drilldown_data = pd.DataFrame()
            st.session_state.drilldown_type = None
            # Store all current selections in session state for consistent display and drilldown
            st.session_state.last_selected_acc_code_bal = selected_acc_code_bal
            st.session_state.last_date_range_bal = (start_date_bal, end_date_bal)
            st.session_state.last_selected_company_no_abi = selected_company_unino_from_state
            st.session_state.last_selected_company_name_abi = current_selected_company_name


# --- Display Area for Balance Information ---
# Use values from session state that were set when the button was clicked
if st.session_state.account_balance_info and \
   st.session_state.get('last_selected_acc_code_bal') and \
   st.session_state.get('last_selected_company_no_abi') and \
   st.session_state.get('last_selected_company_name_abi'):

    info = st.session_state.account_balance_info
    company_display_name = st.session_state.last_selected_company_name_abi
    acc_name_display = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.subheader(f"公司: {company_display_name} - 科目餘額: {acc_name_display}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("期初餘額", f"{info['opening']:,.2f}")

    # Metric for Debits with Drilldown Button
    col2.metric("期間借方總額", f"{info['debits']:,.2f}")
    if info['debits'] > 0:
        if col2.button("查看借方明細", key="drill_debit"):
            with st.spinner("載入借方明細..."):
                st.session_state.drilldown_type = "借方發生額 (Debits)"
                st.session_state.drilldown_data = fetch_drilldown_details(
                    st.session_state.last_selected_acc_code_bal,
                    st.session_state.last_date_range_bal[0],
                    st.session_state.last_date_range_bal[1],
                    'debits',
                    st.session_state.last_selected_company_no_abi
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
                    'credits',
                    st.session_state.last_selected_company_no_abi
                )

    col4.metric("期末餘額", f"{info['closing']:,.2f}")
    st.caption(f"科目 {st.session_state.last_selected_acc_code_bal} ({acc_details.get(st.session_state.last_selected_acc_code_bal, {}).get('dcr', 'N/A')}類) 於公司 {company_display_name}。")

else:
    st.info("請在側邊欄選擇公司、日期區間和會計科目後，點擊「查詢餘額」。")

# --- Display Area for Drill-down Details ---
if not st.session_state.drilldown_data.empty:
    st.markdown("---")
    # Use stored company name for drilldown subheader
    company_display_name_drill = st.session_state.last_selected_company_name_abi
    acc_name_display_drill = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.subheader(f"公司: {company_display_name_drill} - 科目: {acc_name_display_drill} - {st.session_state.drilldown_type} 明細")
    st.dataframe(st.session_state.drilldown_data, height=300, use_container_width=True)
elif st.session_state.drilldown_type and st.session_state.drilldown_data.empty:
    st.markdown("---")
    # Use stored company name
    company_display_name_drill = st.session_state.last_selected_company_name_abi
    acc_name_display_drill = acc_options.get(st.session_state.last_selected_acc_code_bal, "選定科目")
    st.info(f"公司 {company_display_name_drill} 之科目 {acc_name_display_drill} 在選定期間內無 {st.session_state.drilldown_type} 明細可顯示。")


st.sidebar.info("提示：選擇父科目將會彙總其所有子科目的餘額。")

# SRS points:
# FR-2.3 Display content:期初餘額, 期間借方總額, 期間貸方總額, 期末餘額 -> Implemented
# FR-2.4 Drill-down: 「期間借方總額」與「期間貸方總額」的數值應為可點擊的連結。點擊後，彈出一個新視窗 (Modal)，以表格形式顯示構成該總額的所有傳票分錄明細（欄位同 FR-1.3）。
# -> Implemented with buttons below metrics, showing details in the same page. Modal is trickier with Streamlit's flow.
# Business Logic DB-3: ...資產與費用類科目餘額為「借減貸」，負債、權益、收入類科目餘額為「貸減借」。 -> Implemented in opening_balance and closing_balance calculations.
# Join key assumption: ASPDT.SD_INDEX = ASLIP.SP_INDEX. This is critical.
# SP_CHECK='1' for all calculations.
