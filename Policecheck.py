import pandas as pd
import pymysql

import pandas as pd

# Read the Excel file
file_path = r"d:\Policeproject\traffic_stops.xlsx"
Policecheck_df = pd.read_excel(file_path)

# Display first few rows
Policecheck_df.head()

Policecheck_df = Policecheck_df.where(pd.notnull(Policecheck_df), None)

Policecheck_df.head(50)

Cleaned_df = Policecheck_df.fillna(Policecheck_df.mode().iloc[0])

Cleaned_df.head(50)
#pip install pymysql(in terminal)
import pymysql

mydb = pymysql.connect(
  host="localhost",
  user="root",
  password="usha"
  
  
)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE Securecheck")
mycursor.execute("SHOW DATABASES")
for x in mycursor:
  print(x)

  mycursor.execute("use Securecheck")
  
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS Policelog_data (
      stop_date  DATE,
      stop_time TIME,
      country_name  VARCHAR(50),
      driver_gender VARCHAR(10),
      driver_age_raw int,
      driver_age int,
      driver_race VARCHAR(50),
      violation_raw  VARCHAR(250),
      violation VARCHAR(50),
      search_conducted BOOLEAN,
      search_type VARCHAR(50),
      stop_outcome VARCHAR(50),
      is_arrested BOOLEAN,
      stop_duration int,
      drugs_related_stop BOOLEAN,
      vehicle_number  VARCHAR(50)


    );
""")

mycursor.execute("""
    ALTER TABLE Policelog_data
    MODIFY COLUMN stop_duration VARCHAR(50);
""")

mycursor.execute("""
    ALTER TABLE Policelog_data
    MODIFY COLUMN vehicle_number VARCHAR(50);
""")
mydb.commit()

insert_query = """
    INSERT INTO Policelog_data (
        stop_date, stop_time, country_name, driver_gender,
        driver_age_raw, driver_age, driver_race, violation_raw,
        violation, search_conducted, search_type, stop_outcome,
        is_arrested, stop_duration, drugs_related_stop, vehicle_number
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""
mycursor.executemany(insert_query,Cleaned_df.values.tolist())
mydb.commit()