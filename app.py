import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Function to connect to SQLite database
def get_data(query, params=None):
    conn = sqlite3.connect("securecheck.sqlite")
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Streamlit App Title
st.set_page_config(page_title="Securecheck Police", layout="wide")

