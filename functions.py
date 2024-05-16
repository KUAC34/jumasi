from datetime import date, timedelta
import cx_Oracle
import snowflake.connector
import tableauserverclient as TSC
from datetime import datetime
import time
import pandas as pd
import streamlit as st
import re
import numpy as np
from datetime import datetime


#################### Function ####################
# CQMS BI를 구현하기 위해서 필요한 함수를 작성한 파일 #
#################### Function ####################

### Date Setting 을 위한 함수
def get_date_information():
    # Get today's date
    today = date.today()
    yesterday_delta = timedelta(days=1)
    yesterday = today - yesterday_delta
    monthly_first_day = date(today.year, today.month, 1)
    year_first_day = date(today.year, 1, 1)

    # date_str = date.strftime("%Y%m%d")
    # Example > today_str = today.strftime("%Y%m%d")
    
    return today, yesterday, monthly_first_day, year_first_day


### Oracle/snowflake 데이터 베이스 접근을 위한 함수
def execute_query(query, database):
    if database == 'oracle' :
        # Oracle 연결 설정
        conn_str = f"HQGMES/HQGMES@202.31.25.83:1521/DKPPODA.kppodad/"

        start_time = time.time()
        # with 문을 사용하여 Oracle 연결 및 커서 실행
        with cx_Oracle.connect(conn_str) as conn:
            try:
                # 쿼리 실행 및 결과를 Pandas DataFrame으로 변환
                df = pd.read_sql_query(query, conn)
                
                end_time = time.time()
                execution_time = float(end_time - start_time)        
            
                return df, execution_time
            
            except cx_Oracle.Error as e:
                error, = e.args
                print(f"Oracle error {error.code}: {error.message}")
                return None, None
            
    elif database == 'snowflake':

        # Snowflake 연결 설정
        conn = snowflake.connector.connect(
            user='21300584',                                  # 발급받은 ID를 입력합니다.
            password='Kuac141026@',                             # 본인 ID의 패스워드를 입력합니다.
            account='ls58031.ap-northeast-2.privatelink',     # 통합 데이터 분석 플랫폼의 Snowflake Account를 입력합니다. (고정)
            warehouse='SMALL_WH',                             # 사용하고자 하는 Warehouse 성능을 입력합니다. (default = SMALL_WH)
            database='HKT_DW',                                # 해당 데이터테이블이 있는 database를 입력합니다.
            schema='KPPMES'     
            )
        start_time = time.time()
        # with 문을 사용하여 Snowflake 연결 및 커서 실행
        with conn:
            try:
                # 쿼리 실행 및 결과를 Pandas DataFrame으로 변환
                df = pd.read_sql_query(query, conn)
                
                end_time = time.time()
                execution_time = float(end_time - start_time)        
            
                return df, execution_time
                
            except snowflake.connector.errors.DatabaseError as e:
                print(f"Database error: {e}")
                return None, None

            
# Function to insert CSS file
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        

def categorize_plant(value):
    if value in ['DP', 'KP', 'IP', 'OT'] :
        return 'ASIA'
    elif value in ['JP','HP','CP'] :
        return 'China'
    elif value == 'MP' : 
        return 'Europe'
    elif value == 'TP':
        return 'America' 
    else : 
        return 'Unknown'
    
def convert_to_desired_format(date_str):
    # Check if the input value is a string
    if isinstance(date_str, str):
        # Split the Korean date string to extract the date part
        date_part = date_str.split()[0]
        # Concatenate the date part with the desired time format
        datetime_str = f"{date_part} {date_str.split()[-1]}"
        return datetime_str
    elif pd.isna(date_str):
        return None  # Preserve None values
    else:
        # Return a default value or handle the case where input is not a string
        return "Unknown"

def format_columns_1f(df, cols):
    for col in cols:
        df[col] = df[col].apply(lambda x: '{:.1f}'.format(x))
    return df

# MTTC 계산 모듈    
def count_working_days(df, start_col, end_col):
    num_working_days = []
    today = datetime.now()
    today_formatted_date = today.strftime('%Y-%m-%d')
    for start_date, end_date in zip(df[start_col], df[end_col]):
        if pd.isnull(start_date):
            num_working_days.append(np.nan)
            continue
        elif pd.isnull(end_date):
            working_days = pd.bdate_range(start=start_date, end=today_formatted_date).shape[0]
        else : 
            working_days = pd.bdate_range(start=start_date, end=end_date).shape[0]
        num_working_days.append(working_days)
    return pd.Series(num_working_days, index=df.index)

def count_working_days_for_return(df, return_col, start_col, end_col, holidays=None):
    num_working_days = []
    today = datetime.now()
    today_formatted_date = today.strftime('%Y-%m-%d')
    for return_YN, start_date, end_date in zip(df[return_col], df[start_col], df[end_col]):
        if return_YN == 'N':
            num_working_days.append(np.nan)
            continue
        elif return_YN == 'Y' and pd.isnull(end_date):
            working_days = pd.bdate_range(start=start_date, end=today_formatted_date, holidays=None).shape[0]
        else:
            working_days = pd.bdate_range(start=start_date, end=end_date, holidays=None).shape[0]
        num_working_days.append(working_days)
    return pd.Series(num_working_days, index=df.index)

def count_working_days_for_issue(df, return_col, start_col, mid_col, end_col, holidays=None):
    num_working_days = []
    today = datetime.now()
    today_formatted_date = today.strftime('%Y-%m-%d')
    for return_YN, start_date, mid_date, end_date in zip(df[return_col], df[start_col], df[mid_col], df[end_col]):
        if (return_YN == 'N' and pd.isnull(start_date)) or (return_YN == 'Y' and pd.isnull(mid_date)):
            num_working_days.append(np.nan)
            continue
        elif return_YN == 'Y' and pd.isnull(end_date):
            working_days = pd.bdate_range(start=mid_date, end=today_formatted_date, holidays=None).shape[0]
        elif return_YN == 'N' and pd.isnull(end_date):
            working_days = pd.bdate_range(start=start_date, end=today_formatted_date, holidays=None).shape[0]
        elif return_YN == 'Y':
            working_days = pd.bdate_range(start=mid_date, end=end_date, holidays=None).shape[0]
        elif return_YN == 'N':
            working_days = pd.bdate_range(start=start_date, end=end_date, holidays=None).shape[0]
        num_working_days.append(working_days)
    return pd.Series(num_working_days, index=df.index)

# 각 항목별 Quality Issue Count 계산 및 정렬
def calculate_and_sort(dataframe, groupby_column):
    grouped_status = dataframe.groupby([groupby_column, 'STATUS'])['PLANT'].count().unstack().fillna(0)
    grouped_status['TOTAL'] = grouped_status['Complete'] + grouped_status['On-going']
    grouped_status.sort_values(by="TOTAL", ascending=True, inplace=True)
    return grouped_status