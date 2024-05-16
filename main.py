import streamlit as st
st.set_option('deprecation.showPyplotGlobalUse', False)
import pandas as pd
pd.options.display.float_format = '{:.1f}'.format

from datetime import date, timedelta
import time
import functions as fx
import sql

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import tableauserverclient as TSC


##### get_date_information #####
today, yesterday, monthly_first_day, year_first_day = fx.get_date_information()
dic_plant_org = {'DP':10, 'KP':20, 'JP':30, 'HP':40, 'CP':50, 'IP':60, 'MP' :70, 'TP':80}
lst_plant_org = ['DP', 'KP', 'JP', 'HP', 'CP', 'IP', 'MP', 'TP']

df = {}

##### Steamlit 실행 구문 #####
st.set_page_config(page_title="RR", page_icon="🌍",layout="wide")

# Apply the CSS file
fx.local_css("styles.css")

tab0, tab1, tab2, tab3 = st.tabs(["Summary", "OE Application", "Test", "Sell In"])

# Summary
with tab0:
    server_url = 'https://bi.hankooktech.com/'
    username = '21300584'
    password = 'Kuac141026@'
    datasource_id = "e6e3df8f-4c15-4027-bfcf-7ead2e1d4e66"

    try:
        # Tableau 서버 연결 초기화
        tableau_auth = TSC.TableauAuth(username, password)
        server = TSC.Server(server_url, use_server_version=True)
        
        with server.auth.sign_in(tableau_auth):
            all_datasources, _ = server.datasources.get()
            
            # 지정된 데이터 소스 ID에 해당하는 데이터 소스 찾기
            target_datasource = next((datasource for datasource in all_datasources if datasource.id == datasource_id), None)
                
            if target_datasource:
                # 데이터 소스의 기본 테이블 가져오기
                primary_table = target_datasource.default_logical_table
                
                # 데이터를 DataFrame으로 로드
                data_frame = primary_table.to_dataframe()
                
                print("DataFrame loaded successfully:")
                print(data_frame.head())
                
                # Streamlit 앱 내에서 실행 중인 경우 데이터를 표시
                # st.write(data_frame)
            
            else:
                print("Datasource not found.")

    except Exception as e:
        print("An error occurred:", str(e))
            

with tab1:
    st.header("OE Application")
    (df_oe_app,t_oe_app) = fx.execute_query(sql.OeApp_raw(), 'snowflake')
    st.write(df_oe_app)
    lst_plant = df_oe_app["PLANT"].drop_duplicates()
    lst_Status = df_oe_app["Status"].drop_duplicates()
    with st.form(key='Period'):
        col1_1, col1_2 = st.columns(2)    
        with col1_1:
            plant = st.multiselect("Plant", lst_plant, lst_plant_org)
            
        with col1_2:
            status = st.multiselect("Status", lst_Status, 'Supplying')
 
        btn_oe_app = st.form_submit_button("Run")
    
    if btn_oe_app:
        state_oe_app = st.markdown("Operation in progress. Please wait.")
        state_oe_app.markdown(f"Database query execution completed. Query execution time: {t_oe_app:.2f} sec", unsafe_allow_html=True)
        filtered_df = df_oe_app[df_oe_app['PLANT'].isin(plant) & df_oe_app['Status'].isin(status)].reset_index(drop=True)
        st.dataframe(filtered_df)

# # Test    
with tab2:
    st.header("Test")
    state_test = tab2.markdown("Operation in progress. Please wait.")
    df_test, t_test = fx.execute_query(sql.test(),'oracle')
    state_test.markdown(f"Database query execution completed. Query execution time: {t_test:.2f} sec", unsafe_allow_html=True)
    tab2.dataframe(df_test)

# Sell In
with tab3:
    st.header("Sell In")

    with st.form(key='supply'):
        col2_1, col2_2, col2_3 = st.columns(3)
        with col2_1:
            start_date = st.text_input("Start Date", "20240101")
        with col2_2:
            end_date = st.text_input("End Date", "20240110")    
        with col2_3:
            mcode = st.text_input("M-Code", "1024247")
 
        btn_supply_qty = st.form_submit_button("Run")
        
    if btn_supply_qty:
        OeSellIn = sql.OeSellIn("20240101","20240110","1024247")
        (df_OeSellIn, execution_time) = fx.execute_query(OeSellIn,'snowflake')
        state_SellIn = st.markdown("Operation in progress. Please wait.")
        state_SellIn.markdown(f"Database query execution completed. Query execution time: {execution_time:.2f} sec", unsafe_allow_html=True)
        st.dataframe(df_OeSellIn)

# st.title('HTML Document')
# st.write('<h1>This is an HTML document</h1>', unsafe_allow_html=True)
# st.write('<p>This is a paragraph in HTML.</p>', unsafe_allow_html=True)