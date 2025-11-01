import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# Database connection
def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='usha',
            database='securecheck',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# Fetch data from database
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
st.set_page_config(page_title="Securecheck Police Dashboard", layout="wide")
st.title("🚨 Securecheck: Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insights for law enforcement 🔎")

# Show full table
st.header("📋 Police Logs Overview")
query = "SELECT * FROM policelog_data"
data = fetch_data(query)
st.dataframe(data, use_container_width=True)

# Quick Metrics
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_stops = data.shape[0]
    st.metric("Total Police Stops", total_stops)

with col2:
    arrests = data[data['stop_outcome'].str.contains("arrest", case=False, na=False)].shape[0]
    st.metric("Total Arrests", arrests)

with col3:
    warnings = data[data['stop_outcome'].str.contains("warning", case=False, na=False)].shape[0]
    st.metric("Total Warnings", warnings)

with col4:
    drug_related = data[data['drugs_related_stop'] == 1].shape[0]
    st.metric("Drug Related Stops", drug_related)

st.header("🚦 Visual Insights")

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

# Advanced Queries
st.header("⚙️ Advanced Insights")

import streamlit as st

# Assume fetch_data is a function that executes the SQL query (e.g., using pandas or a database connector)
# For this correction, we'll define a placeholder for fetch_data
def fetch_data(query):
    # This is a placeholder for demonstration. In a real app, this would execute the SQL.
    # For now, it just returns a mock result or an empty dataframe.
    import pandas as pd
    print(f"Executing query:\n{query}")
    if "LIMIT 10" in query:
        return pd.DataFrame({'Example_Column': [1, 2], 'Result': ['A', 'B']})
    return pd.DataFrame()

selected_query = st.selectbox("Select a Query to Run", [
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
])

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
LIMIT 10""", # Corrected: Removed extra semicolon and used consistent triple quotes
    
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
GROUP BY 
    driver_age
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
GROUP BY 
    driver_race, driver_gender
ORDER BY 
    search_rate_percentage DESC
LIMIT 10""",
    
    "Time of day with the most traffic stops":
    """SELECT 
    HOUR(stop_time) AS hour_of_day,
    COUNT(*) AS total_stops
FROM 
    policelog_data
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
        WHEN HOUR(stop_time) BETWEEN 6 AND 17 THEN 'Day'
        ELSE 'Night'
    END AS time_of_day,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS arrest_rate_percentage
FROM 
    policelog_data
GROUP BY 
    time_of_day
ORDER BY 
    arrest_rate_percentage DESC""",
    
    "violations are most associated with searches or arrests":
    """SELECT 
    violation,
    COUNT(*) AS total_stops,
    
    -- Count of searches
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
    ROUND(SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS search_rate_percentage,
    
    -- Count of arrests
    SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percentage

FROM 
    policelog_data
GROUP BY 
    violation
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
    driver_age < 25
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
GROUP BY 
    country_name, violation
ORDER BY 
    arrest_rate_percentage DESC,
    total_arrests DESC""",
    
    "Which country has the most stops with search conducted":
    """SELECT 
    country_name,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches
FROM 
    policelog_data
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
    ROUND((total_arrests / total_stops) * 100, 2) AS arrest_rate_percentage,
    SUM(total_stops) OVER (PARTITION BY country_name ORDER BY year) AS cumulative_stops,
    SUM(total_arrests) OVER (PARTITION BY country_name ORDER BY year) AS cumulative_arrests
FROM (
    SELECT 
        country_name,
        YEAR(STR_TO_DATE(stop_date, '%Y-%m-%d')) AS year,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM 
        policelog_data
    GROUP BY 
        country_name, YEAR(STR_TO_DATE(stop_date, '%Y-%m-%d'))
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
    ROUND((total_searches / total_stops) * 100, 2) AS search_rate_percentage,
    ROUND((total_arrests / total_stops) * 100, 2) AS arrest_rate_percentage,
    
    -- Window function: Rank violations by search rate and arrest rate
    RANK() OVER (ORDER BY (total_searches / total_stops) DESC) AS search_rate_rank,
    RANK() OVER (ORDER BY (total_arrests / total_stops) DESC) AS arrest_rate_rank
    
FROM (
    -- Subquery: Aggregate stops, searches, and arrests per violation
    SELECT 
        violation,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM 
        policelog_data
    GROUP BY 
        violation
) AS violation_summary
ORDER BY 
    search_rate_percentage DESC""",
    
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
GROUP BY 
    country_name, driver_gender, driver_race
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
GROUP BY 
    violation
HAVING 
    COUNT(*) > 0
ORDER BY 
    arrest_rate_percentage DESC
LIMIT 5"""
}

if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.write(result)
    else:
        st.warning("No results found for the selected query.")
st.markdown("---") 
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")
st.header("🕵️ Custom Natural Language Filter")

st.markdown("Fill in the details below to get a natural language prediction of the stop **outcome** based on existing data.")

st.header("✍️ Add New Police Log & Predict **Outcome** and **Violation**")

# Input form for all fields (excluding outputs)
with st.form("new_log_form"):
    
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("County Name")
    driver_gender = st.selectbox("Driver Gender", ["", "Male", "Female"]) # Added empty string for "select"
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race")
    
    # Assuming '0' and '1' represent 'No' and 'Yes'
    search_conducted = st.selectbox("Was a Search Conducted?", ["", "0", "1"]) 
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was it Drug Related?", ["", "0", "1"])
    
    # --- FIXED LINE HERE: Using the pre-loaded variable ---
    stop_duration_options = [
    "0-15 Minutes",
    "16-30 Minutes",
    "31-60 Minutes",
    "1-2 Hours",
    "More than 2 Hours"
]
    stop_duration = st.selectbox("Stop Duration", stop_duration_options)
    
    vehicle_number = st.text_input("Vehicle Number")
    
    # Removed `timestamp = pd.timestamp.now()` as this is not a user input field in a form
    
    submitted = st.form_submit_button("Predict Stop Outcome & Violation")
    if submitted:
    # Filter data for prediction
     filtered_data = data[
        (data['driver_gender'] == driver_gender) &
        (data['driver_age'] == driver_age) &
        (data['search_conducted'] == int(search_conducted)) &
        (data['stop_duration'] == stop_duration) &
        (data['drugs_related_stop'] == int(drugs_related_stop))
    ]

    # Predict stop outcome
    if not filtered_data.empty:
        predicted_outcome = filtered_data['stop_outcome'].mode()[0]
        predicted_violation = filtered_data['violation'].mode()[0]
    else:
        predicted_outcome = "warning"  # Default fallback
        predicted_violation = "speeding" # Default fallback




# Natural Language summary variables
search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"

st.markdown(f"""
## 🏆 Prediction Summary
---
- **Predicted Violation:** **{predicted_violation}**
- **Predicted Stop Outcome:** **{predicted_outcome}**

A **{driver_age}** year-old **{driver_gender}** driver in **{country_name}** was stopped at **{stop_time.strftime('%I:%M %p')}** on **{stop_date}**
({search_text}), and the stop **{drug_text}**.
Stop duration: **{stop_duration}**.
Vehicle Number: **{vehicle_number}**.
""")