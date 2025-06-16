# ACCapp (智能會計助理)

## 概覽

ACCapp 是一款創新的應用程式，旨在讓您通過自然語言與您的會計數據進行互動。您可以像與人交談一樣，向應用程式提問關於存儲在 SQL Server 資料庫中的會計分錄，ACCapp 將利用先進的 AI 技術來理解您的問題並提供相應的答案、數據洞察或圖表。

## 主要功能

*   **自然語言查詢 (NLP)**：直接用中文提問，無需編寫複雜的 SQL 查詢語句。
*   **AI 驅動的數據分析**：利用 Google 先進的語言模型進行智能數據分析和查詢。
*   **連接 SQL Server 資料庫**：直接從您的 SQL Server 資料庫中安全地獲取和分析最新的會計數據。
*   **數據預覽**：在進行查詢前，可以預覽從資料庫加載的部分原始數據。
*   **AI 生成代碼透明化**：查看由 AI 生成用以回答您問題的 Python/Pandas 代碼，增加操作的透明度。
*   **數據可視化潛力**：AI 可以根據您的問題生成圖表，幫助您更直觀地理解數據趨勢 (例如，當 PandasAI 返回圖表時)。
*   **安全的憑證管理**：通過 Streamlit 的 secrets 功能 (`secrets.toml`) 安全地管理您的 Google API 金鑰和資料庫連接訊息。
*   **Streamlit 支持**：本應用基於 Streamlit 開發，界面簡潔易用。

## 技術棧

*   **Python**: 作為主要的開發語言。
*   **Streamlit**: 用於構建交互式 Web 應用程式界面。
*   **PandasAI**: 作為連接語言模型與 Pandas DataFrame 的核心組件，實現自然語言查詢功能。
*   **Google Generative AI**: (例如 Gemini Pro) 提供底層的自然語言理解和生成能力。
*   **SQLAlchemy & pyodbc**: 用於連接和操作 SQL Server 資料庫。
*   **Pandas**: 用於高效的數據處理和分析。

## 設定與安裝

請按照以下步驟設定和安裝 ACCapp：

1.  **先決條件**:
    *   確保您的系統已安裝 Python 3.7 或更高版本。
    *   確保您的系統可以訪問 SQL Server 資料庫。

2.  **克隆儲存庫 (可選)**:
    如果您擁有本專案的 Git 儲存庫存取權限，可以將其克隆到您的本地電腦：
    ```bash
    git clone <儲存庫URL>
    cd ACCapp # 進入專案目錄
    ```
    如果直接獲得源代碼文件，請解壓縮到您的工作目錄。

3.  **創建並激活虛擬環境 (推薦)**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

4.  **安裝依賴套件**:
    由於專案未包含 `requirements.txt` 文件，您需要手動安裝必要的套件。請運行以下命令：
    ```bash
    pip install streamlit pandas pandasai google-generativeai pyodbc SQLAlchemy
    ```
    *   `streamlit`: 用於運行 Web 應用。
    *   `pandas`: 用於數據處理。
    *   `pandasai`: 用於 AI 與數據的交互。
    *   `google-generativeai`: Google AI 的客戶端庫。
    *   `pyodbc`: 用於從 Python 連接到 SQL Server 的 ODBC 驅動程式。
    *   `SQLAlchemy`: SQL 工具包和 ORM，用於與資料庫交互。

## 配置

在運行應用程式之前，您需要配置您的 Google API 金鑰和 SQL Server 資料庫連接訊息。

1.  **創建 `secrets.toml` 文件**:
    在您的專案根目錄下（與 `app` 和 `pages` 文件夾同級），創建一個名為 `.streamlit` 的文件夾（如果尚不存在）。然後，在 `.streamlit` 文件夾內創建一個名為 `secrets.toml` 的文件。

2.  **編輯 `secrets.toml` 文件**:
    將以下內容複製到 `secrets.toml` 文件中，並用您的實際訊息替換佔位符：

    ```toml
    [google]
    GOOGLE_API_KEY = "YOUR_GOOGLE_AI_STUDIO_API_KEY_HERE"

    [database]
    SERVER = "YOUR_SQL_SERVER_NAME_OR_IP_HERE" # 例如：localhost, SQLEXPRESS, 192.168.1.100, your_server.database.windows.net
    DATABASE = "YOUR_DATABASE_NAME_HERE"
    USERNAME = "YOUR_DB_USERNAME_HERE"
    PASSWORD = "YOUR_DB_PASSWORD_HERE"
    # DRIVER = "ODBC Driver 17 for SQL Server" # 可選，如果未指定，默認為 'ODBC Driver 17 for SQL Server'。根據您的系統和 SQL Server 版本可能需要更改。
    ```

    **重要提示**:
    *   將 `"YOUR_GOOGLE_AI_STUDIO_API_KEY_HERE"` 替換為您從 Google AI Studio 獲取的真實 API 金鑰。
    *   將 `SERVER`, `DATABASE`, `USERNAME`, 和 `PASSWORD` 替換為您的 SQL Server 資料庫的實際連接訊息。
    *   如果您的 SQL Server 需要特定的 ODBC 驅動程式，請取消註釋 `DRIVER` 行並指定正確的驅動程式名稱。常見的驅動程式包括 "ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server", 或 "SQL Server Native Client 11.0"。

## 運行應用程式

完成設定和配置後，您可以通過以下命令運行 Streamlit 應用程式：

```bash
streamlit run pages/1_Chat_with_Data.py
```

應用程式應該會在您的默認 Web 瀏覽器中打開。

## 使用方法

1.  **啟動應用程式**：執行上述 `streamlit run` 命令。
2.  **等待初始化**：應用程式啟動後，會嘗試初始化語言模型 (LLM) 和資料庫連接。您會在界面上看到相關的狀態消息。
3.  **數據加載**：成功連接資料庫後，應用程式會自動從 `ASPDT`, `ASLIP`, 和 `AACNT` 表中加載最近的 5000 條已審核會計分錄。如果需要，您可以展開數據預覽部分查看加載的數據。
4.  **提出問題**：在標有「例如: '總收入是多少?' 或 '按类别列出支出总额' 或 '哪个地区的收入最高?'」的文本輸入框中，用自然語言輸入您關於會計數據的問題。
5.  **發送查詢**：點擊「發送查詢」按鈕。
6.  **查看結果**：AI 會處理您的問題並查詢數據。結果將顯示在「AI 回答」部分，可能是文本、表格數據或圖表。
7.  **查看 AI 生成的代碼 (可選)**：您可以展開「查看 AI 生成的代碼」部分，了解 AI 是如何理解您的問題並從數據中提取信息的。

請注意，如果 LLM 或資料庫連接配置不正確，或資料庫中沒有符合條件的數據，應用程式可能無法正常工作。請留意界面上的錯誤或警告信息。
