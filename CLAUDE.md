# CLAUDE.md

本檔案為 Claude Code (claude.ai/code) 在此儲存庫中工作時提供指導。

## 應用程式概述

這是一個基於 Streamlit 的會計查詢與報表系統，連接至 SQL Server 資料庫。應用程式提供：

- 傳票查詢功能，包含篩選與 Excel 匯出
- 科目餘額查詢，具備交易明細鑽取功能
- 自動化財務報表生成（損益表、資產負債表）
- 互動式儀表板，包含 KPI 與圖表
- AI 助理，使用 PandasAI 進行自然語言查詢

## 執行應用程式

```bash
# 安裝依賴套件
pip install -r requirements.txt

# 執行應用程式
streamlit run Home.py
```

應用程式將在預設瀏覽器中開啟，網址為 `http://localhost:8501`。

## 核心架構

### 資料庫連線 (`app/core/db_connector.py`)
- 使用 SQLAlchemy 透過 pyodbc 連接 SQL Server
- 支援 Windows 驗證與 SQL Server 驗證
- 連線參數設定於 `.streamlit/secrets.toml`
- 使用 `@st.cache_resource` 快取資料庫引擎

### LLM 設定 (`app/core/llm_config.py`)
- 使用 Google Generative AI 作為 AI 助理功能
- 需要在 secrets 設定中提供 Google API 金鑰
- 回傳與 PandasAI 相容的 LLM 實例

### 頁面結構
- `Home.py`: 主要進入點與導覽
- `pages/`: Streamlit 頁面，遵循 `N_PageName.py` 命名規則
  - `0_AI_Assistant.py`: 自然語言資料查詢
  - `1_Journal_Voucher_Inquiry.py`: 傳票搜尋與篩選
  - `2_Account_Balance_Inquiry.py`: 餘額查詢與鑽取
  - `3_Income_Statement.py`: 自動損益表生成
  - `4_Balance_Sheet.py`: 資產負債表生成
  - `5_Dashboard.py`: KPI 儀表板與視覺化

## 設定需求

應用程式需要 `.streamlit/secrets.toml` 檔案，結構如下：

```toml
[database]
SERVER = "your_server_address"
DATABASE = "your_database_name"
USERNAME = "your_username"  # Windows 驗證時可選
PASSWORD = "your_password"  # Windows 驗證時可選
DB_DRIVER = "ODBC Driver 17 for SQL Server"  # 可選

[google]
GOOGLE_API_KEY = "your_google_api_key"  # AI 助理使用
```

## 資料庫結構假設

應用程式預期特定的 SQL Server 資料表結構：
- `ASLIP`: 傳票表頭 (SP_DATE, SP_NO, SP_CHECK 等)
- `ASPDT`: 傳票明細 (SD_ATNO, SD_AMT, SD_DOC 等)
- `AACNT`: 會計科目表 (AT_NO, AT_NAME, AT_DCR 等)
- `PEMPLOYE`: 員工資料 (EM_USERID, EM_NAME 等)

## 開發模式

- 對資料庫連線與 LLM 初始化使用 `@st.cache_resource`
- 對可快取的資料查詢使用 `@st.cache_data(ttl=3600)`
- 所有資料庫查詢使用 SQLAlchemy 的 `text()` 函數執行原生 SQL
- 錯誤處理以中文顯示使用者友善訊息
- Excel 匯出使用 openpyxl，PDF 匯出使用 fpdf2
- 資料視覺化使用 Plotly

## 測試與除錯

- 檢查 `pandasai.log` 進行 AI 助理除錯
- 資料庫連線問題會記錄詳細的疑難排解步驟
- 所有頁面都包含資料庫引擎驗證才繼續執行