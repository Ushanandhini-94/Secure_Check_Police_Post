import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
from contextlib import contextmanager

# --- Configuration ---
st.set_page_config(page_title="Dashboard-Securecheck", layout="wide")

# --- 1. DATABASE FUNCTIONS ---

# Use contextmanager to ensure connection is properly closed, even when exceptions occur.
# This pattern is safer for non-Streamlit caching when you need to be sure it closes.
@contextmanager
def get_db_cursor():
    """A context manager to manage database connection and cursor."""
    connection = None
    try:
        
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='usha',
            database='securecheck',
            cursorclass=pymysql.cursors.DictCursor
        )
        yield connection.cursor()
    except Exception as e:
        # Print error to the console for debugging, as st.error cannot be used inside st.cache_data
        print(f"Database Connection Error: {e}")
        raise
    finally:
        if connection:
            connection.close()
            
# Use st.cache_data for fetching data. We rely on get_db_cursor for transient connections.
@st.cache_data(ttl=3600) # Cache the data for 1 hour
def fetch_data(query):
    """Fetches data from the database using the provided query."""
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            df = pd.DataFrame(result)
            
            if not df.empty:
                 # Standardize column names to lowercase for consistent DataFrame access
                df.columns = df.columns.str.lower()
            return df
    except Exception as e:
        # Display the error to the user outside of the caching layer
        st.error(f"Query Execution Error: The database might be unavailable or the query is invalid. Details: {e}")
        return pd.DataFrame()


# --- 2. MAIN DASHBOARD LOAD ---
st.title("Securecheck: Police Check Post Digital Ledger")
st.markdown("Data-driven decision support for modern law enforcement 🛡️ ")

# Load ALL data once for the overview, charts, and prediction section
st.header(" Crime report summary")
all_data_query = "SELECT * FROM policelog_data"
data = fetch_data(all_data_query)
st.dataframe(data, use_container_width=True)

if data.empty:
    st.error("Cannot proceed. The main dataset (`policelog_data`) failed to load or is empty. Please check your database connection details.")
    st.stop()
    
# --- 3. QUICK METRICS ---
st.header(" Core Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_stops = data.shape[0]
    st.metric("Total Police Stops", total_stops)

with col2:
    # Use the lowercase column name 'stop_outcome' which is standardized above
    arrests = data[data['stop_outcome'].astype(str).str.contains("arrest", case=False, na=False)].shape[0]
    st.metric("Total Arrests", arrests)

with col3:
    warnings = data[data['stop_outcome'].astype(str).str.contains("warning", case=False, na=False)].shape[0]
    st.metric("Total Warnings", warnings)

with col4:
    # Assuming 'drugs_related_stop' is 1/0 or TRUE/FALSE. MySQL uses 1 for TRUE.
    drug_related = data[pd.to_numeric(data['drugs_related_stop'], errors='coerce') == 1].shape[0]
    st.metric("Drug Related Stops", drug_related)

# --- 4. VISUAL INSIGHTS ---
st.header(" Visual Insights")

tab1, tab2 = st.tabs(["Stops by Violation", "Driver Gender Distribution"])

with tab1:
    if not data.empty and 'violation' in data.columns:
        violation_data = data['violation'].value_counts().reset_index()
        violation_data.columns = ['Violation', 'Count']
        fig = px.bar(violation_data, x='Violation', y='Count', title="Stops by Violation Type", color='Violation')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Violation chart.")

with tab2:
    if not data.empty and 'driver_gender' in data.columns:
        gender_data = data['driver_gender'].value_counts().reset_index()
        gender_data.columns = ['Gender', 'Count']
        fig = px.pie(gender_data, names='Gender', values='Count', title="Driver Gender Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Driver Gender chart.")

# --- 5. ADVANCED QUERIES ---
st.header("In-Depth Data Analysis")

query_options = [
    "Top 10 vehicle_Number involved in drug-related stops",
    "Most frequently searched vehicles",
    "Driver age group with highest arrest rate",
    "Gender distribution of drivers stopped in each country",
    "Race and Gender combination with highest search rate",
    "Time of day with the most traffic stops",
    "The average stop duration for different violations",
    "Are stops during the night more likely to lead to arrests",
    "violations are most associated with searches or arrests",
    "violations,which are most common among younger drivers (<25)",
    "What is the arrest rate by country and violation",
    "Which country has the most stops with search conducted",
    "Yearly Breakdown of Stops and Arrests by Country",
    "Driver Violation Trends Based on Age and Race",
    "Time Period Analysis of Stops , Number of Stops by Year,Month, Hour of the Day",
    "Violations with High Search and Arrest Rates",
    "Driver Demographics by Country (Age, Gender, and Race)",
    "Top 5 Violations with Highest Arrest Rates"
]

selected_query = st.selectbox("Select a Query to Run", query_options)

# FIX: Updated SQL queries to use MySQL syntax (TRUE/1, YEAR(), HOUR(), etc.)
query_map = {
    "Top 10 vehicle_Number involved in drug-related stops":
    """SELECT 
    vehicle_number,
    COUNT(*) AS total_drug_related_stops
FROM 
    policelog_data
WHERE 
    drugs_related_stop = TRUE
GROUP BY 
    vehicle_number
ORDER BY 
    total_drug_related_stops DESC
LIMIT 10""", 
    
    "Most frequently searched vehicles":
    """SELECT 
    vehicle_number,
    COUNT(*) AS total_searches
FROM 
    policelog_data
WHERE 
    search_conducted = TRUE
GROUP BY 
    vehicle_number
ORDER BY 
    total_searches DESC
LIMIT 10""",
    
    "Driver age group with highest arrest rate":
    """SELECT 
    driver_age,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percentage
FROM 
    policelog_data
WHERE driver_age IS NOT NULL AND driver_age > 0
GROUP BY 
    driver_age
HAVING COUNT(*) > 50 
ORDER BY 
    arrest_rate_percentage DESC
LIMIT 10""",
    
    "Gender distribution of drivers stopped in each country":
    """SELECT 
    country_name,
    driver_gender,
    COUNT(*) AS total_stops,
    ROUND(
        COUNT(*) * 100.0 / 
        SUM(COUNT(*)) OVER (PARTITION BY country_name),
        2
    ) AS percentage_of_stops
FROM 
    policelog_data
WHERE country_name IS NOT NULL
GROUP BY 
    country_name, driver_gender
ORDER BY 
    country_name, total_stops DESC""",
    
    "Race and Gender combination with highest search rate":
    """SELECT 
    driver_race,
    driver_gender,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
    ROUND(
        SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 
        2
    ) AS search_rate_percentage
FROM 
    policelog_data
WHERE driver_race IS NOT NULL AND driver_gender IS NOT NULL
GROUP BY 
    driver_race, driver_gender
HAVING COUNT(*) > 100
ORDER BY 
    search_rate_percentage DESC
LIMIT 10""",
    
    "Time of day with the most traffic stops":
    """SELECT 
    HOUR(stop_time) AS hour_of_day,
    COUNT(*) AS total_stops
FROM 
    policelog_data
WHERE stop_time IS NOT NULL
GROUP BY 
    HOUR(stop_time)
ORDER BY 
    total_stops DESC""",
    
    "The average stop duration for different violations":
    """SELECT
    violation,
    ROUND(AVG(stop_duration), 2) AS avg_stop_duration
FROM 
    policelog_data
WHERE 
    stop_duration IS NOT NULL
GROUP BY 
    violation
ORDER BY 
    avg_stop_duration DESC""",
    
    "Are stops during the night more likely to lead to arrests": 
    """SELECT 
    CASE
        WHEN HOUR(stop_time) BETWEEN 6 AND 17 THEN 'Day (6AM-5PM)'
        ELSE 'Night (6PM-5AM)'
    END AS time_of_day,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS arrest_rate_percentage
FROM 
    policelog_data
WHERE stop_time IS NOT NULL
GROUP BY 
    time_of_day
ORDER BY 
    arrest_rate_percentage DESC""",
    
    "violations are most associated with searches or arrests":
    """SELECT 
    violation,
    COUNT(*) AS total_stops,
    
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
    ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS search_rate_percentage,
    
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percentage

FROM 
    policelog_data
WHERE violation IS NOT NULL
GROUP BY 
    violation
HAVING COUNT(*) > 100
ORDER BY 
    search_rate_percentage DESC, arrest_rate_percentage DESC
LIMIT 10""",
    
    "violations,which are most common among younger drivers (<25)":
    """SELECT 
    violation,
    COUNT(*) AS total_stops
FROM 
    policelog_data
WHERE 
    driver_age < 25 AND driver_age IS NOT NULL
GROUP BY 
    violation
ORDER BY 
    total_stops DESC
LIMIT 10""",
    
    "What is the arrest rate by country and violation":
    """SELECT 
    country_name,
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS arrest_rate_percentage
FROM 
    policelog_data
WHERE country_name IS NOT NULL AND violation IS NOT NULL
GROUP BY 
    country_name, violation
HAVING total_stops > 50
ORDER BY 
    arrest_rate_percentage DESC,
    total_arrests DESC
LIMIT 20""",
    
    "Which country has the most stops with search conducted":
    """SELECT 
    country_name,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches
FROM 
    policelog_data
WHERE country_name IS NOT NULL
GROUP BY 
    country_name
ORDER BY 
    total_searches DESC
LIMIT 1""",
    
    "Yearly Breakdown of Stops and Arrests by Country":
    """SELECT
    country_name,
    year,
    total_stops,
    total_arrests,
    ROUND((CAST(total_arrests AS DECIMAL(10, 2)) / total_stops) * 100, 2) AS arrest_rate_percentage,
    SUM(total_stops) OVER (PARTITION BY country_name ORDER BY year) AS cumulative_stops,
    SUM(total_arrests) OVER (PARTITION BY country_name ORDER BY year) AS cumulative_arrests
FROM (
    SELECT 
        country_name,
        YEAR(stop_date) AS year,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM 
        policelog_data
    WHERE stop_date IS NOT NULL AND country_name IS NOT NULL
    GROUP BY 
        country_name, YEAR(stop_date)
) AS yearly_summary
ORDER BY 
    country_name, year""",
    
    "Driver Violation Trends Based on Age and Race":
    """SELECT
    v.driver_race,
    v.violation,
    v.avg_driver_age,
    v.total_stops,
    ROUND(v.percent_of_race, 2) AS percent_of_race
FROM (
    SELECT
        driver_race,
        violation,
        ROUND(AVG(driver_age), 1) AS avg_driver_age,
        COUNT(*) AS total_stops,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY driver_race) AS percent_of_race
    FROM 
        policelog_data
    WHERE 
        driver_age IS NOT NULL 
        AND violation IS NOT NULL 
        AND driver_race IS NOT NULL
    GROUP BY 
        driver_race, violation
) AS v
ORDER BY 
    v.driver_race, v.percent_of_race DESC""",
    
    "Time Period Analysis of Stops , Number of Stops by Year,Month, Hour of the Day":
    """SELECT 
    YEAR(stop_date) AS year,
    MONTH(stop_date) AS month,
    HOUR(stop_time) AS hour_of_day,
    COUNT(*) AS total_stops
FROM 
    policelog_data
WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL
GROUP BY 
    YEAR(stop_date), MONTH(stop_date), HOUR(stop_time)
ORDER BY 
    year, month, hour_of_day""",
    
    "Violations with High Search and Arrest Rates":
    """SELECT
    violation,
    total_stops,
    total_searches,
    total_arrests,
    ROUND((CAST(total_searches AS DECIMAL(10, 2)) / total_stops) * 100, 2) AS search_rate_percentage,
    ROUND((CAST(total_arrests AS DECIMAL(10, 2)) / total_stops) * 100, 2) AS arrest_rate_percentage
FROM (
    SELECT 
        violation,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM 
        policelog_data
    WHERE violation IS NOT NULL
    GROUP BY 
        violation
    HAVING total_stops > 100
) AS violation_summary
ORDER BY 
    search_rate_percentage DESC
LIMIT 10""",
    
    "Driver Demographics by Country (Age, Gender, and Race)":
    """SELECT
    country_name,
    ROUND(AVG(driver_age), 1) AS avg_driver_age,
    driver_gender,
    driver_race,
    COUNT(*) AS total_stops,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY country_name), 2) AS percent_of_country
FROM 
    policelog_data
WHERE country_name IS NOT NULL AND driver_gender IS NOT NULL AND driver_race IS NOT NULL
GROUP BY 
    country_name, driver_gender, driver_race
HAVING total_stops > 10
ORDER BY 
    country_name, total_stops DESC""",
    
    "Top 5 Violations with Highest Arrest Rates":
    """SELECT
    violation,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percentage
FROM 
    policelog_data
WHERE violation IS NOT NULL
GROUP BY 
    violation
HAVING 
    COUNT(*) > 50
ORDER BY 
    arrest_rate_percentage DESC
LIMIT 5"""
}

if st.button("Run Query"):
    if selected_query in query_map:
        query = query_map[selected_query]
        result = fetch_data(query)
        if not result.empty:
            st.write(f"### Results for: {selected_query}")
            st.dataframe(result)
        else:
            st.warning("No results found for the selected query, or a database error occurred.")
    else:
        st.error("Selected query not found.")
        

st.markdown("---") 
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")
st.header("🕵️ Custom Natural Language Filter")

st.markdown("Fill in the details below to get a natural language prediction of the stop **outcome** based on existing data.")

st.header("✍️ Add New Police Log & Predict **Outcome** and **Violation**")

# --- 6. PREDICTION FORM (Input variables defined here) ---
# Initialize session state variables before the form to ensure they exist
if 'predicted_outcome' not in st.session_state:
    st.session_state.predicted_outcome = "N/A"
if 'predicted_violation' not in st.session_state:
    st.session_state.predicted_violation = "N/A"

# Initialize state variables for summary formatting
if 'formatted_time' not in st.session_state:
    st.session_state.formatted_time = ""
if 'formatted_date' not in st.session_state:
    st.session_state.formatted_date = ""

with st.form("new_log_form"):
        
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("County Name")
    # Added empty string for "select"
    driver_gender = st.selectbox("Driver Gender", ["", "Male", "Female"]) 
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27) 
    driver_race = st.text_input("Driver Race")
    
    # Store '0' or '1' as a string here
    search_conducted_str = st.selectbox("Was a Search Conducted?", ["", "0", "1"], key="search_str") 
    search_type = st.text_input("Search Type")
    # Store '0' or '1' as a string here
    drugs_related_stop_str = st.selectbox("Was it Drug Related?", ["", "0", "1"], key="drugs_str")
    
    stop_duration_options = ["0-15 Minutes", "16-30 Minutes", "31-60 Minutes", "1-2 Hours", "More than 2 Hours"]
    stop_duration = st.selectbox("Stop Duration", [""] + stop_duration_options)
    
    vehicle_number = st.text_input("Vehicle Number")
    
    submitted = st.form_submit_button("Predict Stop Outcome & Violation")

    # --- 7. PREDICTION LOGIC (Only runs on form submission) ---
    if submitted:
        
        # Check required fields
        if not all([driver_gender, country_name, driver_race, search_conducted_str, drugs_related_stop_str, stop_duration]):
            st.error("Please fill in all key fields (Gender, County, Race, Search, Drugs, Duration) for prediction.")
            st.session_state.predicted_outcome = "N/A"
            st.session_state.predicted_violation = "N/A"
            st.session_state.formatted_time = ""
            st.session_state.formatted_date = ""
        else:
            try:
                # Convert string inputs to integers for database comparison
                search_conducted_int = int(search_conducted_str)
                drugs_related_stop_int = int(drugs_related_stop_str)
                
                # Filter data for prediction
                filtered_data = data[
                    (data['driver_gender'] == driver_gender) &
                    (data['driver_age'] == driver_age) &
                    # Ensure the dataframe columns are checked against integers
                    (pd.to_numeric(data['search_conducted'], errors='coerce') == search_conducted_int) &
                    (data['stop_duration'] == stop_duration) &
                    (pd.to_numeric(data['drugs_related_stop'], errors='coerce') == drugs_related_stop_int) &
                    (data['driver_race'] == driver_race)
                ]
                
                # Predict stop outcome
                if not filtered_data.empty:
                    st.session_state.predicted_outcome = filtered_data['stop_outcome'].mode().iloc[0]
                    st.session_state.predicted_violation = filtered_data['violation'].mode().iloc[0]
                    st.success(f"Prediction Found based on {len(filtered_data)} historical match(es)!")
                    
                else:
                    # Default fallback
                    st.session_state.predicted_outcome = "Warning or Citation"
                    st.session_state.predicted_violation = "Speeding"
                    st.warning("No exact historical match found. Reverting to default prediction.")
                
                # Store formatted date/time for the summary
                st.session_state.formatted_time = stop_time.strftime('%I:%M %p')
                st.session_state.formatted_date = stop_date.strftime('%B %d, %Y')
                    
            except Exception as e:
                st.error(f"An unexpected error occurred during prediction: {e}")
                st.session_state.predicted_outcome = "Error"
                st.session_state.predicted_violation = "Error"
                st.session_state.formatted_time = ""
                st.session_state.formatted_date = ""

# --- 8. NATURAL LANGUAGE SUMMARY (Displays current state from session) ---

# Get current prediction states
current_outcome = st.session_state.predicted_outcome
current_violation = st.session_state.predicted_violation
summary_time = st.session_state.formatted_time
summary_date = st.session_state.formatted_date

# Natural Language summary variables (based on form strings)
search_text = "A search was conducted" if search_conducted_str == "1" else "No search was conducted"
drug_text = "was drug-related" if drugs_related_stop_str == "1" else "was not drug-related"

# Only show the summary if a successful prediction has occurred (i.e., not initial blank state or error)
if current_outcome not in ["N/A", "Error"] and summary_date and summary_time:
    st.markdown(f"""
    ## 🏆 Prediction Summary
    ---
    - **Predicted Violation:** **{current_violation}**
    - **Predicted Stop Outcome:** **{current_outcome}**
    
    A **{driver_age}** year-old **{driver_gender}** driver in **{country_name}** was stopped at **{summary_time}** on **{summary_date}**
    ({search_text}), and the stop **{drug_text}**.
    Stop duration: **{stop_duration}**.
    Vehicle Number: **{vehicle_number}**.
    """)
