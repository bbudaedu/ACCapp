# app/core/db_connector.py
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pyodbc # Ensure pyodbc is explicitly imported if not automatically handled by sqlalchemy with mssql+pyodbc

def get_db_engine():
    """
    Loads SQL Server connection details from Streamlit secrets
    and returns a SQLAlchemy engine.
    """
    try:
        db_secrets = st.secrets["database"]
        # db_type = db_secrets.get("DB_TYPE", "sqlserver") # DB_TYPE is informational for now
        server = db_secrets["SERVER"]
        database = db_secrets["DATABASE"]
        username = db_secrets["USERNAME"]
        password = db_secrets["PASSWORD"]
        driver = db_secrets.get("DRIVER") # Optional

    except KeyError as e:
        st.error(f"Missing database configuration in .streamlit/secrets.toml under [database]: {e}. Required keys: SERVER, DATABASE, USERNAME, PASSWORD.")
        st.info("""
        Example .streamlit/secrets.toml:
        ```toml
        [database]
        SERVER = "YOUR_SQL_SERVER_NAME_HERE"
        DATABASE = "YOUR_DATABASE_NAME_HERE"
        USERNAME = "YOUR_DB_USERNAME_HERE"
        PASSWORD = "YOUR_DB_PASSWORD_HERE"
        # Optional: DRIVER = "ODBC Driver 17 for SQL Server"
        ```
        """)
        return None
    except FileNotFoundError: # Should be caught by st.secrets if file is missing.
        st.error(".streamlit/secrets.toml file not found. Please ensure it exists and is correctly named.")
        return None
    except Exception as e: # Catch any other st.secrets access issues
        st.error(f"Error accessing Streamlit secrets: {e}")
        return None

    if any(val.startswith("YOUR_") for val in [server, database, username, password]) or \
       any(not val or not val.strip() for val in [server, database, username, password]):
        st.error("Please replace placeholder database credentials in .streamlit/secrets.toml with your actual SQL Server details. All fields (SERVER, DATABASE, USERNAME, PASSWORD) are required.")
        return None

    query_params = {}
    if driver:
        query_params["driver"] = driver.strip()
    else:
        # Default to a common, modern ODBC driver for SQL Server if not specified.
        # This improves out-of-the-box experience for many users.
        query_params["driver"] = "ODBC Driver 17 for SQL Server"
        # st.info(f"Using default ODBC driver: '{query_params['driver']}'. Specify 'DRIVER' in secrets.toml if you need a different one.")


    try:
        # Construct the URL using sqlalchemy.engine.URL.create
        # This handles special characters in username/password if any (though they should be URL-encoded if passed directly in a string)
        url_object = URL.create(
            "mssql+pyodbc",
            username=username,
            password=password,
            host=server,
            database=database,
            query=query_params
        )
        
        # Create engine. `echo=False` is default, can be True for debugging.
        # `pool_pre_ping` checks connection validity from pool.
        engine = create_engine(url_object, pool_pre_ping=True)
        
        # Test connection by trying to execute a simple query
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")) # Basic query to check connectivity
            
        # st.success("Database engine created successfully and connection verified.") # Can be verbose for user
        return engine
        
    except pyodbc.Error as e:
        # Specific pyodbc errors can give more insight
        st.error(f"pyODBC Error connecting to database: {e}")
        st.error(f"Connection details used: Server='{server}', Database='{database}', Username='{username}', Driver='{query_params['driver']}'")
        st.info("Ensure SQL Server is running, accessible, and credentials/driver are correct. Check firewall settings. If using a non-standard port, include it in the SERVER (e.g., 'your_server,1433').")
        return None
    except Exception as e:
        # Catch other SQLAlchemy or general errors
        st.error(f"Failed to create database engine or connect: {e}")
        st.error(f"Connection details used: Server='{server}', Database='{database}', Username='{username}', Driver='{query_params['driver']}'")
        return None

if __name__ == "__main__":
    # This part is for testing the function directly.
    # Note: `st.secrets` is designed for use within a running Streamlit application.
    # For direct script execution, you would typically mock `st.secrets` or manually load
    # the .streamlit/secrets.toml file using a library like `toml`.
    
    print("Attempting to create database engine (direct script run)...")
    
    # --- Mocking st.secrets for local testing ---
    # This is a simplified mock. In a real test suite, you might use unittest.mock.
    class MockSecrets(dict):
        def __init__(self, *args, **kwargs):
            super(MockSecrets, self).__init__(*args, **kwargs)
            self.__dict__ = self # Allows attribute-style access if your code uses it (e.g. st.secrets.database)

        def __getitem__(self, key):
            # Allow dict-style access (e.g. st.secrets["database"])
            return super().__getitem__(key)

    try:
        import toml
        with open(".streamlit/secrets.toml", "r") as f:
            secrets_data = toml.load(f)
        st.secrets = MockSecrets(secrets_data) # Replace st.secrets with our mock
        print("Mocked st.secrets with data from .streamlit/secrets.toml")
    except FileNotFoundError:
        print("Local .streamlit/secrets.toml not found. Mocking with placeholder data for testing structure.")
        # Provide minimal structure for the function to run without erroring on st.secrets access
        st.secrets = MockSecrets({
            "database": {
                "SERVER": "YOUR_SQL_SERVER_NAME_HERE", # Placeholder
                "DATABASE": "YOUR_DATABASE_NAME_HERE", # Placeholder
                "USERNAME": "YOUR_DB_USERNAME_HERE", # Placeholder
                "PASSWORD": "YOUR_DB_PASSWORD_HERE", # Placeholder
                "DRIVER": "ODBC Driver 17 for SQL Server"
            }
        })
    except Exception as e:
        print(f"Error loading/mocking secrets.toml for local testing: {e}")
        st.secrets = MockSecrets({}) # Empty mock to prevent AttributeError

    # --- End Mocking st.secrets ---

    engine = get_db_engine()
    if engine:
        print(f"Database engine creation attempt finished. Engine object: {engine}")
        print("To verify, check for error messages above if actual connection was attempted with placeholders.")
    else:
        print("Database engine creation failed. See error messages above for details.")
        print("If using placeholder credentials (YOUR_... values), failure is expected.")
        print("Ensure you have actual credentials in .streamlit/secrets.toml for a real test.")

```
