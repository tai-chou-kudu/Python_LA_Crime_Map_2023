
# Los Angeles County 2023 Crime Map 

## Table of Contents

- [Project Overview](#project-overview)
- [Data Sources](#data-sources)
- [Tools](#tools)
- [Data Cleaning/Preparation](#data-cleaningpreparation)
- [Exploratory Data Analysis](#exploratory-data-analysis)
- [Data Analysis and Transformation](#data-analysis-and-transformation)
- [Results](#results)
- [Limitations](#limitations)
 
### Project Overview

This data project aims to provide insights into crime trends in Los Angeles County in 2023. This mapping tool is designed to assist the progressive organization in identifying key areas to concentrate its decriminalization and anti-carceral initiatives.

### Data Sources

Crime Data: The primary dataset used for this analysis is the "2023crimedata.csv" file, containing detailed information from the Sheriff's office about crime incidents in LA county in 2023.

[LA County GIS Data](https://lacounty.maps.arcgis.com/home/item.html?id=a76e9954365d4608aa8ae81959f402f7&sortOrder=desc&sortField=defaultFSOrder): The "City_and_Unincorporated_Boundaries_(Legal).shp" is a key dataset that enables the geographical mapping of Los Angeles County and its cities. This dataset serves as a base for creating a combined geographic table with crime data.

### Tools

- Excel - Data Cleaning
- PG Admin 4 - Database Administration - Data Analysis
  - [Download here](https://www.pgadmin.org/download/pgadmin-4-windows/)
- PostgreSQL - Relational Database Management Systems (RDBMS) - Data Analysis
  - [Download here](https://www.postgresql.org/download/)
- Python - Data Transformation and Data Visualization
  - [Download here](https://www.python.org/downloads/)
- PyCharm - Integrated Development Environment (IDE)
  - [Download here](https://www.jetbrains.com/pycharm/download/?section=mac)

### Data Cleaning/Preparation

In the initial data preparation phase, I performed the following tasks:
1. Data loading and inspection
2. Handling missing values
3. Data cleaning and formatting

### Exploratory Data Analysis

EDA involved exploring the crime data, coming across questions such as:

- There are only 88 official cities in LA, so why does our crime dataset include more than that?
- Is all of this crime data contained within LA county?
- How many crime categories are there, and how might we aggregate these?

  
### Data Analysis and Transformation

```sql
SELECT DISTINCT city
FROM crime2023la
ORDER BY city ASC
```

This query returned 200 cities. Los Angeles County has 88 incorporated cities. Further research led to the understanding that LA county has additional unincorporated cities. 


```sql
SELECT DISTINCT category
FROM crime2023la
ORDER BY category ASC
```

There are 30 distinct categories of crimes.  Initial observations suggest that these categories can likely be aggregated into broader categories such as property-related crimes and person-related crimes, if needed.

Moving on from SQL, I found and downloaded shapefiles of LA County’s official cities and unincorporated places boundaries.

I used Python: geopandas, plotly, dash web app, and other libraries to create a heat map, aggregated crime, and specific crime maps for 2023 LA county crime data.


### Results

[Link to Los Angeles County 2023 Crime Map Web App]( )
 

### Limitations

This mapping tool is dedicated solely to crime data. There is potential to enhance it by incorporating additional layers, such as racial demographics and socio-economic status, to examine patterns and connections related to bias within the criminal justice system. 


