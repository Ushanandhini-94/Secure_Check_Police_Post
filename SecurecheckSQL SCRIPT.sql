select * from policelog_data;
use securecheck;
#What are the top 10 vehicle_Number involved in drug-related stops?

SELECT 
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
LIMIT 10;
#Which vehicles were most frequently searched?

SELECT 
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
LIMIT 10;
#Which driver age group had the highest arrest rate?

SELECT 
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
LIMIT 10;

#What is the gender distribution of drivers stopped in each country?

SELECT 
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
    country_name, total_stops DESC;
#Which race and gender combination has the highest search rate?

SELECT 
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
LIMIT 10;
#What time of day sees the most traffic stops?
SELECT 
    HOUR(stop_time) AS hour_of_day,
    COUNT(*) AS total_stops
FROM 
    policelog_data
GROUP BY 
    HOUR(stop_time)
ORDER BY 
    total_stops DESC;
    #What is the average stop duration for different violations?

    SELECT
    violation,
    ROUND(AVG(stop_duration), 2) AS avg_stop_duration
FROM 
    policelog_data
WHERE 
    stop_duration IS NOT NULL
GROUP BY 
    violation
ORDER BY 
    avg_stop_duration DESC;

   
   #Are stops during the night more likely to lead to arrests?
SELECT 
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
    arrest_rate_percentage DESC;
    
    
    #Which violations are most associated with searches or arrests?
    
    SELECT 
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
LIMIT 10;
#Which violations are most common among younger drivers (<25)?

SELECT 
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
LIMIT 10;

#Which countries report the highest rate of drug-related stops?
SELECT 
    country_name,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_related_stops,
    ROUND(
        SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 
        2
    ) AS drug_stop_rate_percentage
FROM 
    policelog_data
GROUP BY 
    country_name
ORDER BY 
    drug_stop_rate_percentage DESC;
    
    

#What is the arrest rate by country and violation?

SELECT 
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
    total_arrests DESC;
    #

#Which country has the most stops with search conducted?
SELECT 
    country_name,
    COUNT(*) AS total_stops,
    SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_searches
FROM 
    policelog_data
GROUP BY 
    country_name
ORDER BY 
    total_searches DESC
LIMIT 1;
#Yearly Breakdown of Stops and Arrests by Country (Using Subquery and Window Functions)

SELECT
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
        YEAR(STR_TO_DATE(stop_date, '%Y-%m-%d')) AS year,  -- adjust format if needed
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
    FROM 
        policelog_data
    GROUP BY 
        country_name, YEAR(STR_TO_DATE(stop_date, '%Y-%m-%d'))
) AS yearly_summary
ORDER BY 
    country_name, year;

 
    
#Driver Violation Trends Based on Age and Race (Join with Subquery)
-- Main query with JOIN and subquery for age groups
SELECT
    v.driver_race,
    v.violation,
    v.avg_driver_age,
    v.total_stops,
    ROUND(v.percent_of_race, 2) AS percent_of_race
FROM (
    -- Subquery: summarize trends per race & violation
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
    v.driver_race, v.percent_of_race DESC;

    
    #Time Period Analysis of Stops (Joining with Date Functions) , Number of Stops by Year,Month, Hour of the Day
    -- Time-based traffic stop analysis
SELECT 
    YEAR(stop_date) AS year,
    MONTH(stop_date) AS month,
    HOUR(stop_time) AS hour_of_day,
    COUNT(*) AS total_stops
FROM 
    policelog_data
GROUP BY 
    YEAR(stop_date), MONTH(stop_date), HOUR(stop_time)
ORDER BY 
    year, month, hour_of_day;
    
    
    #MySQL Query: Violations with High Search and Arrest Rates (Using Window Functions)
    
    SELECT
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
    search_rate_percentage DESC;

#Driver Demographics by Country (Age, Gender, and Race)

SELECT
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
    country_name, total_stops DESC;
#Top 5 Violations with Highest Arrest Rates
SELECT
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
LIMIT 5;









