import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from app.core.db_connector import get_db_engine
from sqlalchemy import text
from dateutil.relativedelta import relativedelta

# --- Page Configuration ---
st.set_page_config(page_title="營運儀表板 (Operational Dashboard)", layout="wide")
st.title("📊 營運儀表板 (Operational Dashboard)")

# --- Database Connection ---
@st.cache_resource
def init_db_connection():
    engine = get_db_engine()
    return engine
db_engine = init_db_connection()

# --- Helper Functions for Data Fetching ---
@st.cache_data(ttl=300)
def fetch_scalar_data(query, params=None):
    if not db_engine: return 0
    try:
        with db_engine.connect() as connection:
            result = pd.read_sql(text(query), connection, params=params)
            if not result.empty and 'Amount' in result.columns:
                return result['Amount'].iloc[0] if pd.notna(result['Amount'].iloc[0]) else 0
            return 0
    except Exception as e:
        st.error(f"純量資料查詢時發生錯誤: {e}")
        return 0

@st.cache_data(ttl=3600)
def fetch_company_data(): # Renamed to fetch_company_data_dashboard for clarity if needed, but standalone is fine.
    if not db_engine:
        st.error("資料庫引擎未能初始化，無法獲取公司列表。")
        return pd.DataFrame(columns=['CP_UNINO', 'CP_NAME']) # Use new column names
    try:
        with db_engine.connect() as connection:
            # Use new query: SELECT CP_UNINO, CP_NAME FROM PCOMPANY ORDER BY CP_NAME
            df = pd.read_sql(text("SELECT CP_UNINO, CP_NAME FROM PCOMPANY ORDER BY CP_NAME"), connection)
            return df
    except Exception as e:
        st.error(f"獲取公司列表時發生錯誤: {e}")
        return pd.DataFrame(columns=['CP_UNINO', 'CP_NAME']) # Use new column names

# --- Account Patterns ---
KPI_ACCOUNT_PATTERNS = {
    "Revenue": "4%", "COGS": "5%", "OpEx": "6%",
    "NonOpIncome": "71%", "NonOpExpense": "75%"
}
EXPENSE_PIE_CHART_CATEGORIES = {
    "營業成本 (COGS)": KPI_ACCOUNT_PATTERNS["COGS"],
    "營業費用 (Operating Expenses)": KPI_ACCOUNT_PATTERNS["OpEx"]
    # Add more specific OpEx if Chart of Accounts allows, e.g.:
    # "薪資支出 (Salaries)": "601%", # Example
    # "租金支出 (Rent)": "602%",   # Example
}

# --- Sidebar Filters ---
st.sidebar.header("篩選條件 (Filters)")
companies_df_dash = fetch_company_data() # Use a distinct variable name
# Update to use CP_UNINO and CP_NAME
company_options_dash = {row['CP_UNINO']: row['CP_NAME'] for _, row in companies_df_dash.iterrows()} if not companies_df_dash.empty else {}
selected_company_unino_dash = None # Changed variable name
selected_company_name_dash = "無公司" # Changed variable name

if not company_options_dash:
    st.sidebar.warning("未找到任何公司資料。請檢查 PCOMPANY 表。")
else:
    default_company_unino_dash = list(company_options_dash.keys())[0]
    selected_company_unino_dash = st.sidebar.selectbox(
        "公司 (Company)", options=list(company_options_dash.keys()), # Options are CP_UNINO
        format_func=lambda x: company_options_dash.get(x, "未知公司"), # Format uses CP_NAME
        key="dashboard_company_unino", index=0 # Changed key
    )
    selected_company_name_dash = company_options_dash.get(selected_company_unino_dash, "未知公司")

today = datetime.date.today()
first_day_current_month = today.replace(day=1)
next_month_start = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
last_day_current_month = next_month_start - datetime.timedelta(days=1)
st.sidebar.subheader("主要日期區間 (Main Date Range)")
date_range_dash_selected = st.sidebar.date_input(
    "選擇日期區間 (Select Date Range)", [first_day_current_month, last_day_current_month],
    key="dashboard_date_range"
)
start_date_dash, end_date_dash = date_range_dash_selected if len(date_range_dash_selected) == 2 else (None, None)
if start_date_dash and end_date_dash:
    st.sidebar.caption(f"已選期間: {start_date_dash.strftime('%Y-%m-%d')} 至 {end_date_dash.strftime('%Y-%m-%d')}")
else:
    st.sidebar.warning("請選擇完整的日期區間。")

# --- Data Loading Function ---
def get_period_financial_data(company_unino, start_date_str, end_date_str, account_pattern): # Param name changed
    query = """
    SELECT COALESCE(SUM(CASE WHEN d.SD_DOC = 'C' THEN d.SD_AMT ELSE -d.SD_AMT END), 0) AS Amount
    FROM ASPDT d JOIN ASLIP h ON d.SD_NO = h.SP_NO -- Removed d.SD_INDEX = h.SP_INDEX from join
    WHERE h.SP_CHECK = '1' AND d.SD_ATNO LIKE :acc_pattern
      AND h.SP_DATE BETWEEN :start_date AND :end_date AND h.SP_CO_NO = :company_unino -- Param name in query changed
    """
    params = {
        'acc_pattern': account_pattern,
        'start_date': start_date_str, 'end_date': end_date_str,
        'company_unino': company_unino # Param name in dict changed
    }
    return fetch_scalar_data(query, params)

def load_dashboard_data(company_unino, current_start_dt, current_end_dt): # Param name changed
    if not company_unino or not current_start_dt or not current_end_dt: # Check updated param
        st.session_state.dashboard_kpis = {k: {"value": 0, "delta": "N/A"} for k in ["revenue", "expenses", "net_profit", "ytd_revenue"]}
        st.session_state.dashboard_charts_data = {
            "monthly_revenue": pd.DataFrame(), "profit_margins": pd.DataFrame(),
            "expense_structure": pd.DataFrame()
        }
        st.warning("請選擇公司和完整的日期區間以載入數據。")
        return

    start_date_str_period = current_start_dt.strftime('%Y%m%d')
    end_date_str_period = current_end_dt.strftime('%Y%m%d')

    # --- KPI Calculations ---
    revenue_period = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, KPI_ACCOUNT_PATTERNS["Revenue"])
    cogs_period_raw = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, KPI_ACCOUNT_PATTERNS["COGS"])
    opex_period_raw = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, KPI_ACCOUNT_PATTERNS["OpEx"])
    non_op_income_period = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, KPI_ACCOUNT_PATTERNS["NonOpIncome"])
    non_op_expense_period = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, KPI_ACCOUNT_PATTERNS["NonOpExpense"])

    current_period_total_expenses_display = -(cogs_period_raw + opex_period_raw) # For KPI display (positive)
    current_period_net_profit = revenue_period + cogs_period_raw + opex_period_raw + non_op_income_period + non_op_expense_period

    year_start_dt_for_ytd = current_end_dt.replace(month=1, day=1)
    ytd_revenue = get_period_financial_data(company_unino, year_start_dt_for_ytd.strftime('%Y%m%d'), end_date_str_period, KPI_ACCOUNT_PATTERNS["Revenue"])

    st.session_state.dashboard_kpis = {
        "revenue": {"value": revenue_period, "delta": "N/A"},
        "expenses": {"value": current_period_total_expenses_display, "delta": "N/A"},
        "net_profit": {"value": current_period_net_profit, "delta": "N/A"},
        "ytd_revenue": {"value": ytd_revenue, "delta": "N/A"}
    }

    # --- Chart Data: Monthly Revenue and Profit Margins (12 months) ---
    monthly_revenue_list = []
    profit_margins_list = []
    for i in range(12):
        month_loop_end_dt_approx = current_end_dt - relativedelta(months=i)
        month_loop_end_dt = month_loop_end_dt_approx.replace(day=1) + relativedelta(months=1) - datetime.timedelta(days=1)
        month_label = month_loop_end_dt.strftime('%Y-%m')
        month_start_str = month_loop_end_dt.replace(day=1).strftime('%Y%m%d')
        month_end_str = month_loop_end_dt.strftime('%Y%m%d')

        rev = get_period_financial_data(company_unino, month_start_str, month_end_str, KPI_ACCOUNT_PATTERNS["Revenue"])
        monthly_revenue_list.append({'月份 (Month)': month_label, '收入 (Revenue)': rev})

        cogs = get_period_financial_data(company_unino, month_start_str, month_end_str, KPI_ACCOUNT_PATTERNS["COGS"])
        opex = get_period_financial_data(company_unino, month_start_str, month_end_str, KPI_ACCOUNT_PATTERNS["OpEx"])
        non_op_inc = get_period_financial_data(company_unino, month_start_str, month_end_str, KPI_ACCOUNT_PATTERNS["NonOpIncome"])
        non_op_exp = get_period_financial_data(company_unino, month_start_str, month_end_str, KPI_ACCOUNT_PATTERNS["NonOpExpense"])

        gross_profit_month = rev + cogs
        net_profit_month = gross_profit_month + opex + non_op_inc + non_op_exp
        gp_margin = (gross_profit_month / rev * 100) if rev != 0 else 0
        np_margin = (net_profit_month / rev * 100) if rev != 0 else 0
        profit_margins_list.append({'月份 (Month)': month_label, '毛利率 (Gross Margin)': gp_margin, '淨利率 (Net Margin)': np_margin})

    st.session_state.dashboard_charts_data['monthly_revenue'] = pd.DataFrame(monthly_revenue_list).sort_values(by='月份 (Month)').reset_index(drop=True)
    st.session_state.dashboard_charts_data['profit_margins'] = pd.DataFrame(profit_margins_list).sort_values(by='月份 (Month)').reset_index(drop=True)

    # --- Chart Data: Expense Structure Pie Chart (Current Period) ---
    expense_pie_data = []
    for category_name, acc_pattern in EXPENSE_PIE_CHART_CATEGORIES.items():
        raw_expense_value = get_period_financial_data(company_unino, start_date_str_period, end_date_str_period, acc_pattern)
        display_expense_value = abs(raw_expense_value)
        if display_expense_value > 0:
             expense_pie_data.append({'費用類別 (Expense Category)': category_name, '金額 (Amount)': display_expense_value})

    st.session_state.dashboard_charts_data['expense_structure'] = pd.DataFrame(expense_pie_data)

    # Use selected_company_name_dash for the success message as it's from the current UI selection
    st.success(f"{selected_company_name_dash} ({company_unino}) 儀表板數據已更新 ({current_start_dt.strftime('%Y-%m-%d')} 至 {current_end_dt.strftime('%Y-%m-%d')})")

# --- Session State Init ---
if 'dashboard_kpis' not in st.session_state:
    st.session_state.dashboard_kpis = {k: {"value": 0, "delta": "N/A"} for k in ["revenue", "expenses", "net_profit", "ytd_revenue"]}
if 'dashboard_charts_data' not in st.session_state:
    st.session_state.dashboard_charts_data = {
        "monthly_revenue": pd.DataFrame(columns=['月份 (Month)', '收入 (Revenue)']),
        "profit_margins": pd.DataFrame(columns=['月份 (Month)', '毛利率 (Gross Margin)', '淨利率 (Net Margin)']),
        "expense_structure": pd.DataFrame(columns=['費用類別 (Expense Category)', '金額 (Amount)'])
    }

# --- Refresh button logic ---
if st.sidebar.button("刷新儀表板 (Refresh Dashboard)", type="primary", key="dash_refresh_button"):
    if selected_company_unino_dash and start_date_dash and end_date_dash: # Check updated variable
        load_dashboard_data(selected_company_unino_dash, start_date_dash, end_date_dash) # Pass CP_UNINO
    else:
        st.sidebar.error("請選擇公司和完整的日期區間。")

# --- Main Dashboard Area ---
st.markdown(f"### 公司: {selected_company_name_dash}") # Use updated variable
st.markdown("---")

# Helper for date caption, defined once
def get_date_caption_str(start_date, end_date):
    if start_date and end_date: return f"期間: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
    return "未選擇有效日期區間"

# KPI Display
st.subheader("關鍵績效指標 (Key Performance Indicators)")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
date_caption = get_date_caption_str(start_date_dash, end_date_dash)
kpis = st.session_state.dashboard_kpis
def format_kpi_value(value): return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)

with kpi_col1: st.metric(label="本期營收 (Period Revenue)", value=format_kpi_value(kpis['revenue']['value']), delta=kpis['revenue']['delta']); st.caption(date_caption)
with kpi_col2: st.metric(label="本期費用 (Period Expenses)", value=format_kpi_value(kpis['expenses']['value']), delta=kpis['expenses']['delta']); st.caption(date_caption)
with kpi_col3: st.metric(label="本期淨利 (Period Net Profit)", value=format_kpi_value(kpis['net_profit']['value']), delta=kpis['net_profit']['delta']); st.caption(date_caption)
with kpi_col4: st.metric(label="年初至今營收 (YTD Revenue)", value=format_kpi_value(kpis['ytd_revenue']['value']), delta=kpis['ytd_revenue']['delta']); st.caption(f"截至 {end_date_dash.strftime('%Y-%m-%d')}" if end_date_dash else "未選擇日期")
st.markdown("---")

# --- Charts Display ---
charts_data = st.session_state.dashboard_charts_data
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("月度收入趨勢 (Monthly Revenue Trend)")
    df_rev_trend = charts_data.get('monthly_revenue', pd.DataFrame())
    if not df_rev_trend.empty:
        fig_revenue_trend = px.bar(df_rev_trend, x='月份 (Month)', y='收入 (Revenue)', text_auto=".2s", title="過去12個月收入")
        fig_revenue_trend.update_layout(xaxis_title="月份", yaxis_title="收入金額")
        st.plotly_chart(fig_revenue_trend, use_container_width=True)
    else:
        st.info("無足夠數據顯示月度收入趨勢。")

with chart_col2:
    st.subheader("費用結構分析 (Expense Structure)")
    df_expense_structure = charts_data.get('expense_structure', pd.DataFrame())
    if not df_expense_structure.empty and df_expense_structure['金額 (Amount)'].sum() > 0 :
        fig_expense_structure = px.pie(df_expense_structure, values='金額 (Amount)', names='費用類別 (Expense Category)',
                                       title=f"本期費用結構 ({start_date_dash.strftime('%Y-%m-%d')} 至 {end_date_dash.strftime('%Y-%m-%d')})" if start_date_dash else "本期費用結構")
        fig_expense_structure.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_expense_structure, use_container_width=True)
    else:
        st.info("無足夠數據顯示費用結構，或總費用為零。")

st.markdown("---")
st.subheader("利潤率趨勢 (Profit Margin Trend)")
df_margin_trend = charts_data.get('profit_margins', pd.DataFrame())
if not df_margin_trend.empty:
    fig_profit_margin = px.line(df_margin_trend, x='月份 (Month)', y=['毛利率 (Gross Margin)', '淨利率 (Net Margin)'],
                                markers=True, title="過去12個月利潤率")
    fig_profit_margin.update_layout(xaxis_title="月份", yaxis_title="利潤率 (%)", yaxis_tickformat=".1f")
    st.plotly_chart(fig_profit_margin, use_container_width=True)
else:
    st.info("無足夠數據顯示利潤率趨勢。")

st.sidebar.info("提示：圖表數據基於選定日期區間的過去12個月。費用結構圖顯示本期數據。")
