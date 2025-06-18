# Modernized Accounting Inquiry and Reporting System (現代化會計查詢與報表系統)

## Overview (概述)

**English:**
This project is a Streamlit-based web application designed to modernize accounting data inquiry and financial reporting. It connects to an existing SQL Server database to provide users with interactive tools for querying journal vouchers, analyzing account balances, and generating key financial statements like the Income Statement. It also features an AI Assistant for natural language queries (details to be expanded).

**中文:**
本專案是一個基於 Streamlit 的 Web 應用程式，旨在實現會計數據查詢和財務報告的現代化。它連接到現有的 SQL Server 資料庫，為用戶提供互動式工具，用於查詢傳票、分析科目餘額以及生成關鍵財務報表（如損益表）。此外，它還包含一個用於自然語言查詢的 AI 助理（詳細功能待擴展）。

## Features Implemented (已實現功能)

**English:**
1.  **Journal Voucher Inquiry (傳票查詢):**
    *   Filter journal vouchers by date range, account code, summary keyword, amount range, voucher number, preparer, and audit status.
    *   Display query results in a sortable table.
    *   Export query results to Excel.
2.  **Account Balance Inquiry (科目餘額查詢):**
    *   Query account balances for a selected company, account code (including parent accounts for consolidated balances), and date range.
    *   Display Opening Balance, Total Debits, Total Credits, and Closing Balance.
    *   Allows drill-down to view detailed transactions contributing to debit or credit totals for the period.
3.  **Income Statement (損益表):**
    *   Generate Income Statement for a selected company, year, and month.
    *   Supports comparison with the same period last year (YoY %) and the previous month (MoM %).
    *   Export the generated statement to Excel (with basic formulas for subtotals) and PDF.
4.  **Balance Sheet (資產負債表):**
    *   Generate Balance Sheet for a selected company as of a specific date.
    *   Displays Assets, Liabilities, and Equity sections with totals.
    *   Verifies the accounting equation (Total Assets = Total Liabilities + Equity).
    *   Export the generated statement to Excel and PDF.
5.  **Dashboard (營運儀表板):**
    *   Provides an overview of key financial metrics for a selected company and date range.
    *   Includes KPI cards (Period Revenue, Period Expenses, Period Net Profit, YTD Revenue).
    *   Features charts: Monthly Revenue Trend (bar), Expense Structure (pie), Profit Margin Trend (line).
6.  **AI Assistant (AI 助理):**
    *   (Initial Setup) Provides a conversational interface for querying accounting data using natural language. Functionality is currently foundational and will be expanded.

**中文:**
1.  **傳票查詢 (Journal Voucher Inquiry):**
    *   依據日期區間、會計科目、摘要關鍵字、金額範圍、傳票號碼、製單人及審核狀態篩選傳票。
    *   以可排序的表格顯示查詢結果。
    *   將查詢結果匯出至 Excel。
2.  **科目餘額查詢 (Account Balance Inquiry):**
    *   查詢選定公司、會計科目（包括父科目以顯示彙總餘額）及日期區間的科目餘額。
    *   顯示期初餘額、期間借方總額、期間貸方總額及期末餘額。
    *   允許點擊借方或貸方總額，以查看構成該期間總額的詳細交易記錄。
3.  **損益表 (Income Statement):**
    *   為選定公司、年份及月份生成損益表。
    *   支援與去年同期比較 (YoY %) 及與上月比較 (MoM %)。
    *   將生成的報表匯出至 Excel（包含小計的基本公式）和 PDF。
4.  **資產負債表 (Balance Sheet):**
    *   為選定公司生成特定截止日期的資產負債表。
    *   顯示資產、負債和權益部分及其總計。
    *   驗證會計方程式（資產總計 = 負債總計 + 權益總計）。
    *   將生成的報表匯出至 Excel 和 PDF。
5.  **營運儀表板 (Dashboard):**
    *   提供選定公司和日期區間的關鍵財務指標概覽。
    *   包含 KPI 卡片（本期收入、本期費用、本期淨利、年初至今收入）。
    *   特色圖表：月度收入趨勢（長條圖）、費用結構（圓餅圖）、利潤率趨勢（折線圖）。
6.  **AI 助理 (AI Assistant):**
    *   (初期設置) 提供一個對話式介面，可用自然語言查詢會計數據。此功能目前為基礎階段，將持續擴展。

## Technology Stack (技術棧)

*   **Python:** Core programming language.
*   **Streamlit:** Web application framework.
*   **Pandas:** Data manipulation and analysis.
*   **SQLAlchemy:** Database toolkit (for connecting to SQL Server).
*   **Openpyxl:** For reading/writing Excel files.
*   **FPDF (fpdf2):** For generating PDF files.
*   **SQL Server:** Backend database (assumed pre-existing).

## Setup and Installation (設置與安裝)

**English:**
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

**中文:**
1.  **克隆代碼庫:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **創建並激活虛擬環境 (建議):**
    ```bash
    python -m venv venv
    # Windows 系統
    venv\Scripts\activate
    # macOS/Linux 系統
    source venv/bin/activate
    ```
3.  **安裝依賴包:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration (配置)

**English:**
Database connection details must be configured in a `secrets.toml` file located in the `.streamlit` directory within the project root.

1.  Create a directory named `.streamlit` in the project root if it doesn't exist.
2.  Inside `.streamlit`, create a file named `secrets.toml`.
3.  Add your SQL Server connection details to `secrets.toml` as follows:

    ```toml
    [database]
    db_type = "sqlserver" # Or other supported types if db_connector is adapted
    db_username = "your_username"
    db_password = "your_password"
    db_host = "your_server_address" # e.g., localhost, server.example.com
    db_port = "1433" # Default SQL Server port
    db_name = "your_database_name"
    # For SQL Server with pyodbc, you might need to specify the driver
    # Ensure the driver is installed on your system, e.g., "ODBC Driver 17 for SQL Server"
    db_driver = "ODBC Driver 17 for SQL Server"
    ```

**中文:**
資料庫連接詳細資訊必須在位於專案根目錄 `.streamlit` 文件夾中的 `secrets.toml` 文件中進行配置。

1.  如果專案根目錄中不存在 `.streamlit` 文件夾，請創建它。
2.  在 `.streamlit` 文件夾內，創建一個名為 `secrets.toml` 的文件。
3.  將您的 SQL Server 連接詳細資訊按以下格式添加到 `secrets.toml`：

    ```toml
    [database]
    db_type = "sqlserver" # 如果 db_connector 被調整過，也可是其他支援的類型
    db_username = "your_username"
    db_password = "your_password"
    db_host = "your_server_address" # 例如：localhost, server.example.com
    db_port = "1433" # SQL Server 預設端口
    db_name = "your_database_name"
    # 對於使用 pyodbc 的 SQL Server，您可能需要指定驅動程式
    # 請確保您的系統上已安裝該驅動程式，例如："ODBC Driver 17 for SQL Server"
    db_driver = "ODBC Driver 17 for SQL Server"
    ```

## Running the Application (運行應用程式)

**English:**
Once the dependencies are installed and `secrets.toml` is configured:
1.  Navigate to the root directory of the project in your terminal.
2.  Run the Streamlit application:
    ```bash
    streamlit run Home.py
    ```
3.  The application should open in your default web browser.

**中文:**
依賴包安裝完成且 `secrets.toml` 配置妥當後：
1.  在您的終端機中，導航到專案的根目錄。
2.  運行 Streamlit 應用程式：
    ```bash
    streamlit run Home.py
    ```
3.  應用程式應在您的預設網頁瀏覽器中打開。

## Basic Usage (基本使用說明)

**English:**
*   **Navigation:** Use the sidebar to select the desired module (AI Assistant, Journal Voucher Inquiry, Account Balance Inquiry, Income Statement, Balance Sheet, Dashboard).
*   **Journal Voucher Inquiry:**
    *   Set filters in the sidebar (date range is mandatory). Company filter might be applicable if data contains multiple companies but this page does not have a company selector.
    *   Click "查詢傳票" (Query Vouchers) to view results.
    *   Click "匯出 Excel" (Export Excel) to download the results.
*   **Account Balance Inquiry:**
    *   Select a company, date range, and an account code in the sidebar (all mandatory).
    *   Click "查詢餘額" (Query Balance).
    *   View balances and click "查看借方明細" (View Debit Details) or "查看貸方明細" (View Credit Details) for transaction drill-down.
*   **Income Statement:**
    *   Select a company, year, and month in the sidebar.
    *   Optionally, check boxes for "與去年同期比較 (%)" (Compare with LY Same Period) or "與上月比較 (%)" (Compare with Last Month).
    *   Click "生成報表" (Generate Report).
    *   Use the "匯出 Excel" or "匯出 PDF" buttons to download the statement.
*   **Balance Sheet:**
    *   Select a company and an "as of" date in the sidebar.
    *   Click "生成報表" (Generate Report).
    *   Use the "匯出 Excel" or "匯出 PDF" buttons to download the statement.
*   **Dashboard:**
    *   Select a company and date range in the sidebar.
    *   Click "刷新儀表板" (Refresh Dashboard) to load/update data.

**中文:**
*   **導覽:** 使用側邊欄選擇所需的功能模組（AI 助理、傳票查詢、科目餘額查詢、損益表、資產負債表、營運儀表板）。
*   **傳票查詢:**
    *   在側邊欄中設定篩選條件（日期區間為必填）。如果數據包含多家公司，此頁面目前無公司選擇器，可能顯示所有公司數據。
    *   點擊「查詢傳票」按鈕查看結果。
    *   點擊「匯出 Excel」按鈕下載結果。
*   **科目餘額查詢:**
    *   在側邊欄中選擇公司、日期區間和會計科目（三者皆為必填）。
    *   點擊「查詢餘額」按鈕。
    *   查看餘額數據，並可點擊「查看借方明細」或「查看貸方明細」以鑽取交易詳情。
*   **損益表:**
    *   在側邊欄中選擇公司、年份和月份。
    *   可選中「與去年同期比較 (%)」或「與上月比較 (%)」的複選框。
    *   點擊「生成報表」按鈕。
    *   使用「匯出 Excel」或「匯出 PDF」按鈕下載報表。
*   **資產負債表:**
    *   在側邊欄中選擇公司和截止日期。
    *   點擊「生成報表」按鈕。
    *   使用「匯出 Excel」或「匯出 PDF」按鈕下載報表。
*   **營運儀表板:**
    *   在側邊欄中選擇公司和日期區間。
    *   點擊「刷新儀表板」按鈕以加載/更新數據。
