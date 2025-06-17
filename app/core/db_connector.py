# app/core/db_connector.py

import streamlit as st
from sqlalchemy import create_engine, text  # <--- 修正後的匯入
import urllib

@st.cache_resource
def get_db_engine():
    """
    建立一個用於 SQL Server 的 SQLAlchemy 引擎。
    此函數會根據 secrets.toml 文件中是否提供了使用者名稱，
    智慧地在「SQL Server 驗證」和「Windows 驗證」之間切換。
    它還根據您的螢幕截圖包含了加密設定。
    """
    try:
        # 從 Streamlit secrets 載入憑證
        db_config = st.secrets["database"]
        server = db_config.get("SERVER")
        database = db_config.get("DATABASE")
        username = db_config.get("USERNAME")
        password = db_config.get("PASSWORD")

        # 基本驗證，確保必要欄位存在
        if not server or not database:
            st.error("資料庫設定錯誤: `SERVER` 和 `DATABASE` 欄位在 .streamlit/secrets.toml 文件中是必需的。")
            st.info("請參考您的 SQL Server Management Studio 連線資訊進行填寫。")
            return None
            
        # 這是最常見的 SQL Server ODBC 驅動程式。請確保它已安裝在您的系統上。
        driver = "{ODBC Driver 17 for SQL Server}"
        
        conn_str_params = {
            "DRIVER": driver,
            "SERVER": server,
            "DATABASE": database,
            "Encrypt": "yes",  # 根據您的「Encrypt: Mandatory」設定
            "TrustServerCertificate": "yes", # 根據您的「Trust Server Certificate」設定
        }

        # --- 智慧選擇驗證方法 ---
        if username:
            # 如果提供了 USERNAME，則使用 SQL Server 驗證
            conn_str_params["UID"] = username
            conn_str_params["PWD"] = password
            auth_method = "SQL Server 驗證"
        else:
            # 如果 USERNAME 為空，則使用 Windows 驗證
            conn_str_params["Trusted_Connection"] = "yes"
            auth_method = "Windows 驗證"

        # 組裝連線字串參數
        params_list = [f"{key}={value}" for key, value in conn_str_params.items()]
        params_str = ";".join(params_list)
        
        # 為連線 URL 引用參數
        quoted_params = urllib.parse.quote_plus(params_str)
        
        # 建立最終的 SQLAlchemy 連線字串
        conn_url = f"mssql+pyodbc:///?odbc_connect={quoted_params}"
        
        st.info(f"正在嘗試使用 `{auth_method}` 連接資料庫...") # 告知使用者使用了哪種方法
        
        # 建立引擎。此引擎將被 @st.cache_resource 快取
        engine = create_engine(conn_url)

        # 透過執行一個簡單的查詢來測試連線，以提供即時回饋
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")) # <--- text() 函數現在已經被定義了
        
        return engine

    except Exception as e:
        # 如果任何步驟失敗，提供詳細的錯誤訊息
        st.error(f"資料庫連線失敗: {e}")
        st.info("""
        **請檢查以下幾點:**
        1.  確認 `.streamlit/secrets.toml` 中的 `SERVER` 和 `DATABASE` 是否完全正確。
        2.  **如果您使用 Windows 驗證, 請確保 `USERNAME` 和 `PASSWORD` 為空。**
        3.  如果您使用 SQL Server 驗證, 請確保 `USERNAME` 和 `PASSWORD` 正確。
        4.  執行此應用程式的電腦**網路**是否可以連上資料庫伺服器。
        5.  伺服器上的**防火牆**是否已允許此連線。
        6.  系統的 **ODBC Driver 17 for SQL Server** 是否已正確安裝。
        """)
        return None