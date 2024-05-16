''' 약어 정리
GLOBAL : GL
PLANT : PLT
OEM : OEM
Status : STS
Market : MKRT
Yearly / Monthly / Weekly : yr / mo / wk
'''

#########################################################################################################
#########################################################################################################
### Section 1. Library 호출
#########################################################################################################
#########################################################################################################

import streamlit as st
st.set_option('deprecation.showPyplotGlobalUse', False)
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.1f}'.format

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import functions as fx
import sql

#########################################################################################################
#########################################################################################################
### Section 2. Setting 
#########################################################################################################
#########################################################################################################


common_URL = 'http://egqms.hankooktech.com/OE_Quality_Issue/OE_QualityIssue_Popup.html?callid=filter&cqmsQualityIssueSeq='
## General Setting
margins_P = {'t' : 100, 'b' : 100, 'l' : 70, 'r' : 70}

tbl_Month = pd.DataFrame({
    'Mo' : [ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'month' : range(1,13),
    })

Plant_lst = ["DP", "KP", "JP", "HP", "CP", "MP","IP", "TP"]
MTTC_items = ['P_Reg','P_Return','P_Countermeasure','P_Comp','MTTC']
MTTC_Target = [2,7,5,2,10]

#########################################################################################################
#########################################################################################################
### Section 3. 데이터 전처리
#########################################################################################################
#########################################################################################################

## Step 1 : SQL 호출
(df_OEQI,t_oe_app) = fx.execute_query(sql.QI_MAIN_Global(), 'snowflake') # CQMS Quality Issue
(df_Sell_CrossTab,t_oe_app) = fx.execute_query(sql.OeSellIn_Monthly_byPlant(), 'snowflake') # HOPE 월별/공장별 SellIn

## Step 2 : Main Table 생성
df_OEQI['URL'] = common_URL + df_OEQI['URL'] # Link 추가

# MTTC 추가
df_OEQI['P_Reg'] = fx.count_working_days(df_OEQI, 'OCC_D', 'REG_D') - 1
df_OEQI['P_Return'] = fx.count_working_days_for_return(df_OEQI, 'RETURN', 'REG_D', 'RETURN_D') - 1
df_OEQI['P_Countermeasure'] = fx.count_working_days_for_issue(df_OEQI, 'RETURN', 'REG_D', 'RETURN_D', 'ISSUEREG_D') - 1
df_OEQI['P_Comp'] = fx.count_working_days(df_OEQI, 'ISSUEREG_D', 'COMPLETE_DATE') - 1
df_OEQI['MTTC'] = df_OEQI[['P_Reg', 'P_Countermeasure', 'P_Comp']].sum(axis=1)

## Step 3 : 집계표 생성
# TOT
df_OEQI_tot = df_OEQI[MTTC_items].mean().round(2)
df_OEQI_tot['Supplies'] = df_Sell_CrossTab['Supplies'].sum()
df_OEQI_tot['Issue_cnt'] = df_OEQI.shape[0]
df_OEQI_tot['OEQI'] = (df_OEQI_tot['Issue_cnt'] / df_OEQI_tot['Supplies'] * 1000000).round(2)
df_OEQI_tot = df_OEQI_tot.reset_index(drop=False)

# Monthly
# (전처리)
grouped_OEQI = df_OEQI.groupby('YYYYMM')['PLANT'].count().reset_index().rename(columns={'PLANT': 'Issue_cnt'})
grouped_SELL = df_Sell_CrossTab.groupby('YYYYMM')['Supplies'].sum().reset_index()

df_OEQI_mo = pd.concat([grouped_OEQI, grouped_SELL],axis=0).reset_index(drop=False)
df_OEQI_mo = pd.merge(grouped_SELL, grouped_OEQI, on='YYYYMM', how = 'left')
df_OEQI_mo['month'] = df_OEQI_mo['YYYYMM'].astype(str).str[-2:].astype(int)
df_OEQI_mo = pd.merge(tbl_Month, df_OEQI_mo, on='month', how = 'left').drop(columns=['YYYYMM','month'])
df_OEQI_mo[['Supplies[CUM]','Issue_cnt[CUM]']] = df_OEQI_mo[['Supplies', 'Issue_cnt']].cumsum()
df_OEQI_mo['OEQI'] = (df_OEQI_mo['Issue_cnt'] / df_OEQI_mo['Supplies'] * 1000000).round(2)
df_OEQI_mo['OEQI[CUM]'] = (df_OEQI_mo['Issue_cnt[CUM]'] / df_OEQI_mo['Supplies[CUM]'] * 1000000).round(2)
df_OEQI_mo['Supp_mil'] = (df_OEQI_mo['Supplies']/1000000).round(2)
df_OEQI_mo['Supp_mil[CUM]'] = (df_OEQI_mo['Issue_cnt[CUM]'] / df_OEQI_mo['Supplies[CUM]'] * 1000000).round(2)

# Plant
# (전처리)
grouped_OEQI = df_OEQI.groupby('PLANT')['YYYYMM'].count().reset_index().rename(columns={'YYYYMM': 'Issue_cnt'})
grouped_SELL = df_Sell_CrossTab.groupby('PLANT')['Supplies'].sum().reset_index()
grouped_MTTC = df_OEQI.groupby('PLANT')[MTTC_items].mean().round(2).reset_index()

df_OEQI_plt = pd.merge(grouped_SELL, grouped_OEQI, on='PLANT', how = 'left').fillna(0)
df_OEQI_plt = df_OEQI_plt[df_OEQI_plt['PLANT'] != 'OT'].reset_index(drop=True)
df_OEQI_plt['OEQI'] = (df_OEQI_plt['Issue_cnt']/df_OEQI_plt['Supplies']*1000000).round(2)
df_OEQI_plt = pd.merge(df_OEQI_plt, grouped_MTTC, on='PLANT', how = 'left').fillna(0)

# 상태별 X 항목별 집계
df_OEQI_STS_PLT = fx.calculate_and_sort(df_OEQI, 'PLANT')     # Plant별 Quality Issue Count
df_OEQI_STS_MKRT = fx.calculate_and_sort(df_OEQI, 'MARKET')     # Market별 Quality Issue Count
df_OEQI_STS_OE = fx.calculate_and_sort(df_OEQI, 'OEM')     # OEM별 Quality Issue Count

#########################################################################################################
#########################################################################################################
### Section 4. Managing Charts
#########################################################################################################
#########################################################################################################

### pos111 OEQI Graph
fig_BarSca_OEQI_Mo = go.Figure()

# OE QI 막대 그래프 추가
fig_BarSca_OEQI_Mo.add_trace(go.Bar(
    x=df_OEQI_mo['Mo'],
    y=df_OEQI_mo['OEQI'],
    name='OE QI',
    text=df_OEQI_mo['OEQI'],
    hovertemplate='%{x}<br>OEQI : %{y:.2f}'
))

# Supplies 선 그래프 추가
fig_BarSca_OEQI_Mo.add_trace(go.Scatter(
    mode='markers+lines+text',
    name='Supllies',
    yaxis='y2',
    x=df_OEQI_mo['Mo'],
    y=df_OEQI_mo['Supplies'],
    text=df_OEQI_mo['Supp_mil'].apply(lambda x: f"{x:.1f} M"),
    textposition='top center',
    hovertemplate='%{x}<br>Supplies : %{y:,.0f}'
))
# Issue Count 점 그래프 추가
fig_BarSca_OEQI_Mo.add_trace(go.Scatter(
    mode='markers+text',
    name='Issue Count',
    x=df_OEQI_mo['Mo'],
    y=df_OEQI_mo['Issue_cnt'],
    text=df_OEQI_mo['Issue_cnt'],
    textposition='top center',
    hovertemplate='%{x}<br>Issue Count : %{y:,.0f}'
))

fig_BarSca_OEQI_Mo.update_layout(
    title='<b>Global OE QI<b>',
    xaxis_title='Month',
    yaxis_title='OE QI ( pp100 )',
    yaxis=dict(range=[0, 20]),
    yaxis2=dict(title='Supplies ( EA )',
                side="right",
                overlaying="y",
                range=[0, 3000000]),
    legend=dict(x=0.75, y=1.05),
    title_font = dict(size = 20),
    paper_bgcolor = 'rgba(0,0,0,0)', 
    plot_bgcolor = 'rgba(0,0,0,0)',
    font = dict(family = "나눔고딕", size = 12)
)

# pos112 MTTC 차트

fig_Indi_MTTC = go.Figure()

row_index = [0,0,2,2,1]
column_index = [0,2,0,2,1]

for r, c, i, t in zip(row_index, column_index, range(5), MTTC_Target) :
    fig_Indi_MTTC.add_trace(go.Indicator(
        type = 'indicator', mode = "gauge+number", title = df_OEQI_tot.iloc[i, 0], 
        domain = dict(row = r, column = c), value = df_OEQI_tot.iloc[i, 1], 
        gauge = dict(axis = dict(
            range = (0, t*2.0)),
                    steps = [
                        dict(range = (0, (t)*2.0*0.5), color = "green"),
                        dict(range = ((t)*2.0*0.5, (t)*2.0*0.75), color = "yellow"),
                        dict(range = ((t)*2.0*0.75, (t)*2.0),color = "red")],
                    threshold = dict(line = dict(color = 'white'),value = df_OEQI_tot.iloc[i, 1]),
                    bar = dict(color = "darkblue")), number = dict(suffix = ' days'),
        title_font = dict(size = 12))
                                    )
    
fig_Indi_MTTC.update_layout(grid=dict(rows=3, columns=3),
                            title = dict(text = '<b>Global MTTC<b>', x = 0.5, ),
                            margin = margins_P,
                            title_font = dict(size = 20),
                            paper_bgcolor = 'rgba(0,0,0,0)', 
                            plot_bgcolor = 'rgba(0,0,0,0)',
                            font = dict(family = "나눔고딕", size = 12)
)

# pos121 OEQI_Plant_hbar
fig_Bar_OEQI_PLT = go.Figure()

fig_Bar_OEQI_PLT.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_PLT.index, x = df_OEQI_STS_PLT['Complete'],
    text = df_OEQI_STS_PLT['Complete'], ## text 설정
    name='Complete',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_Bar_OEQI_PLT.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_PLT.index, x = df_OEQI_STS_PLT['On-going'],
    text = df_OEQI_STS_PLT['On-going'], ## text 설정
    name='On-going',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_Bar_OEQI_PLT.update_layout(barmode = 'stack',
                               title = dict(text = '<b>Plant<b>', x = 0.5),
                               title_font = dict(size = 20),
                               paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)',
                               xaxis = dict(showticklabels = False, showgrid = False),
                               yaxis = dict(gridwidth = 0),
                               font = dict(family = "나눔고딕", size = 12),
                               margin = dict(l=50, r=20, t=50, b=50),
                               legend = dict(orientation = 'h')
                               )

# pos122 OEQI_Market_hbar
fig_Bar_OEQI_MKRT = go.Figure()

fig_Bar_OEQI_MKRT.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_MKRT.index, x = df_OEQI_STS_MKRT['Complete'],
    text = df_OEQI_STS_MKRT['Complete'], ## text 설정
    name='Complete',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_Bar_OEQI_MKRT.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_MKRT.index, x = df_OEQI_STS_MKRT['On-going'],
    text = df_OEQI_STS_MKRT['On-going'], ## text 설정
    name='On-going',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_Bar_OEQI_MKRT.update_layout(barmode = 'stack',
                                    title = dict(text = '<b>Market<b>', x = 0.5),
                                    title_font = dict(size = 20),
                                    paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)',
                                    xaxis = dict(showticklabels = False,
                                                    showgrid = False
                                                    ),
                                    yaxis = dict(gridwidth = 0),
                                    font = dict(family = "나눔고딕", size = 12
                                                ),
                                    margin = dict(l=80, r=20, t=50, b=50),
                                    legend = dict(orientation = 'h'),
                                    )

# pos123 OEQI_Market_hbar
fig_df_OEQI_STS_OE = go.Figure()

fig_df_OEQI_STS_OE.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_OE.index, x = df_OEQI_STS_OE['Complete'],
    text = df_OEQI_STS_OE['Complete'], ## text 설정
    name='Complete',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_df_OEQI_STS_OE.add_trace(go.Bar( ## bar 트레이스 추가
    y = df_OEQI_STS_OE.index, x = df_OEQI_STS_OE['On-going'],
    text = df_OEQI_STS_OE['On-going'], ## text 설정
    name='On-going',
    textposition = 'inside', ## textposition, textemplate 설정
    hovertemplate= 'PLANT : %{x}<br>Issue Count : %{y}',
    orientation='h'
    ))

fig_df_OEQI_STS_OE.update_layout(barmode = 'stack',
                                    title = dict(text = '<b>OEM<b>', x = 0.5),
                                    title_font = dict(size = 20),
                                    paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)',
                                    xaxis = dict(gridwidth = 0, showticklabels = False, showgrid = False),
                                    yaxis = dict(gridwidth = 0),
                                    font = dict(family = "나눔고딕", size = 12),
                                    margin = dict(l=100, r=20, t=50, b=50),
                                    legend = dict(orientation = 'h'),
                                    )

# pos131 by_Quality Issue CAT

df_OEQI_byIssueCAT = df_OEQI.groupby(['CAT', 'SUB_CAT'])['PLANT'].count().reset_index()
all_sum = df_OEQI['PLANT'].count()
cat_sum = df_OEQI_byIssueCAT[['CAT','PLANT']].groupby(['CAT'])['PLANT'].sum().reset_index()

fig_Sun_OEQI_Issue = go.Figure()
fig_Sun_OEQI_Issue.add_trace(go.Sunburst(
    labels=['Total'] + df_OEQI_byIssueCAT['CAT'].unique().tolist() + df_OEQI_byIssueCAT['SUB_CAT'].tolist(),
    parents=[''] + ['Total'] * 7 + df_OEQI_byIssueCAT['CAT'].tolist(),
    values=[all_sum] + cat_sum['PLANT'].tolist() + df_OEQI_byIssueCAT['PLANT'].values.tolist(),
    branchvalues='total',
    insidetextorientation='radial',
    textinfo='label+value+percent entry',
    ))

fig_Sun_OEQI_Issue.update_layout(
    margin = dict(l=20, r=20, t=50, b=50),
    )

fig_Sun_OEQI_Issue.update_layout()

#pos132
fig_radar_OEQI = go.Figure()

fig_radar_OEQI.add_trace(go.Scatterpolar(
    theta = df_OEQI_plt['PLANT'],
    r = df_OEQI_plt['OEQI'],
    fill = 'toself'
))

fig_radar_OEQI.update_layout(polar =
                                dict(
                                    ## angularaxis 속성 설정
                                    angularaxis =
                                    dict(ticktext = df_OEQI_plt['PLANT'],
                                        tickvals = df_OEQI_plt['PLANT'],
                                        linewidth = 2, linecolor = 'black', gridcolor = 'gray'),
                                    
                                    ## radialaxis 속성 설정
                                    radialaxis =
                                    dict(linewidth = 2, linecolor = 'dodgerblue', gridcolor = 'skyblue',
                                        nticks = 5, title = 'OE QI')),
                                title = dict(text = 'OE QI', x = 0.5),
                                margin = margins_P)

#pos133
fig_radar_MTTC = go.Figure()

fig_radar_MTTC.add_trace(go.Scatterpolar(
    theta = df_OEQI_plt['PLANT'],
    r = df_OEQI_plt['MTTC'],
    fill = 'toself'
))

fig_radar_MTTC.update_layout(polar =
                                dict(
                                    ## angularaxis 속성 설정
                                    angularaxis =
                                    dict(ticktext = df_OEQI_plt['PLANT'],
                                        tickvals = df_OEQI_plt['PLANT'],
                                        linewidth = 2, linecolor = 'black', gridcolor = 'gray'),
                                    ## radialaxis 속성 설정
                                    radialaxis =
                                    dict(linewidth = 2, linecolor = 'dodgerblue', gridcolor = 'skyblue',
                                        nticks = 5, title = 'MTTC')),
                                title = dict(text = 'MTTC', x = 0.5),
                                margin = margins_P)

#########################################################################################################
#########################################################################################################
### Section 5. Organizing Streamlit
#########################################################################################################
#########################################################################################################

st.set_page_config(page_title="CQMS BI", page_icon="🌍",layout="wide")

## Main Page
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Global", "Plant", "Each", "OE Quality Group", "etc."])

with tab1:
    st.subheader("Global OE Quality KPI")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_BarSca_OEQI_Mo, theme=None, use_container_width=True)
    
    with col2:
        st.plotly_chart(fig_Indi_MTTC, theme=None, use_container_width=True)

    st.subheader("Quality issue by subject")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(fig_Bar_OEQI_PLT, theme=None, use_container_width=True)
    
    with col2:
        st.plotly_chart(fig_Bar_OEQI_MKRT, theme=None, use_container_width=True)    

    with col3:    
        st.plotly_chart(fig_df_OEQI_STS_OE, theme=None, use_container_width=True)

    
    col1, col2, col3 = st.columns(3)
    with col1 : 
        st.subheader("Quality issue types")
        st.plotly_chart(fig_Sun_OEQI_Issue, theme=None, use_container_width=True)
    
    with col2 : 
        st.plotly_chart(fig_radar_OEQI, theme=None, use_container_width=True)
    
    with col3 : 
        st.plotly_chart(fig_radar_MTTC, theme=None, use_container_width=True)

    
    
    ## Main DB
    st.dataframe(df_OEQI,
                column_config={
                    "URL" : st.column_config.LinkColumn(
                        "URL",
                        help="To Show, please click",
                        display_text="Show",
                        width= "small"
                    ),
                    "OEQ GROUP" : st.column_config.Column(
                        width = "medium"
                    ),
                    "PROJECT" : st.column_config.Column(
                        width = "medium"
                    ),
                },
                hide_index=True
    )
    
with tab2:
    
    with st.form(key='Period'):
        Selected_plant = st.multiselect("Plant", Plant_lst, Plant_lst)
        btn_oe_app = st.form_submit_button("Run")
    
    # TEST를 위한 셋팅    
    if btn_oe_app:
    
        filtered_df_OEQI = df_OEQI[df_OEQI['PLANT'].isin(Selected_plant)].reset_index(drop=True)
        filtered_df_Sell = df_Sell_CrossTab[df_Sell_CrossTab['PLANT'].isin(Selected_plant)]['Supplies'].sum()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric('Quality Issue', len(filtered_df_OEQI))
        col2.metric('On-going',len(filtered_df_OEQI[filtered_df_OEQI['STATUS'] == 'On-going']))
        col3.metric('OE Supplies', filtered_df_Sell)
        col4.metric('OEQI', (len(filtered_df_OEQI)/filtered_df_Sell*1000000).round(2))
        col5.metric('MTTC', filtered_df_OEQI['MTTC'].mean().round(2))
        
        filtered_df_OEQI_mo = filtered_df_OEQI.groupby('YYYYMM').size().reset_index(name='issue_cnt')
        filtered_df_Sell_mo = df_Sell_CrossTab[df_Sell_CrossTab['PLANT'].isin(Selected_plant)]\
            .groupby('YYYYMM')['Supplies'].sum().reset_index()
        filtered_df_OEQI_mo = pd.DataFrame.merge(filtered_df_Sell_mo,filtered_df_OEQI_mo, how = 'left', on = 'YYYYMM')
        filtered_df_OEQI_mo['month'] = filtered_df_OEQI_mo['YYYYMM'].astype(str).str[-2:].astype(int)
        filtered_df_OEQI_mo = pd.merge(tbl_Month, filtered_df_OEQI_mo, on='month', how = 'left').drop(columns=['YYYYMM','month'])
        filtered_df_OEQI_mo['OEQI'] = (filtered_df_OEQI_mo['issue_cnt']/filtered_df_OEQI_mo['Supplies']*1000000).round(2)
        
        st.subheader("On-going Quality Issue")
        st.dataframe(filtered_df_OEQI[filtered_df_OEQI['STATUS'] == 'On-going'])
        # Plotly 초기화
        fig_line_OEQI_PLT = go.Figure()
        
        fig_line_OEQI_PLT.add_trace(go.Scatter(
            mode='lines+text',
            x=filtered_df_OEQI_mo['Mo'],
            y=filtered_df_OEQI_mo["Supplies"],
            text = (filtered_df_OEQI_mo["Supplies"]/1000000).apply(lambda x: f"{x:,.2f} M"),
            name='Supplies',
            line_shape = 'spline'
        ))

        fig_line_OEQI_PLT.add_trace(go.Bar(
            x=filtered_df_OEQI_mo['Mo'],
            y=filtered_df_OEQI_mo["issue_cnt"],
            yaxis = 'y2',
            text = filtered_df_OEQI_mo["issue_cnt"],
            name='Issue Count',
        ))

        fig_line_OEQI_PLT.update_layout(margin = margins_P,
                                        yaxis = dict(fixedrange = True,
                                                        range = [0, filtered_df_OEQI_mo["Supplies"].max()*1.2],
                                                        overlaying = "y2",
                                                        showgrid = False,
                                                        showticklabels = False
                                                        ),
                                        yaxis2 = dict(side = "right",
                                                        range = [0, filtered_df_OEQI_mo["issue_cnt"].max()*2],
                                                        showgrid = False,
                                                        showticklabels = False),
                                        paper_bgcolor = 'rgba(0,0,0,0)',
                                        plot_bgcolor = 'rgba(0,0,0,0)',
                                        legend = dict(orientation = 'h',
                                                        x=0.95, y = 1.05,
                                                        xanchor = 'right'),
                                        font = dict(size = 18)
                                        )

        st.plotly_chart(fig_line_OEQI_PLT, theme=None, use_container_width=True)
        
        
        MTTC_items_result = [s + ':Result' for s in MTTC_items]
        
        filtered_df_OEQI[MTTC_items_result] = 'FAIL'  # 기본적으로 'FAIL'로 설정
        
        MTTC_PASS_RATE = []
        for i in range(5):
            filtered_df_OEQI.loc[filtered_df_OEQI[MTTC_items[i]] <= MTTC_Target[i], MTTC_items_result[i]] = 'PASS'
            filtered_df_OEQI.loc[filtered_df_OEQI[MTTC_items[i]].isnull(), MTTC_items_result[i]] = np.nan

        filtered_df_OEQI_CrossTab = filtered_df_OEQI[MTTC_items_result].unstack().reset_index(name='PF').drop(columns='level_1')
        filtered_df_OEQI_CrossTab = pd.crosstab(index = filtered_df_OEQI_CrossTab['level_0'], columns=filtered_df_OEQI_CrossTab['PF'])
        filtered_df_OEQI_CrossTab = filtered_df_OEQI_CrossTab.T.reset_index(drop=False)
        
        MTTC_OnTime_Rate = go.Figure()
        
        MTTC_OnTime_Rate = make_subplots(rows=1, cols=5, subplot_titles=MTTC_items,
                        specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]])

        for i in range(5):
            MTTC_OnTime_Rate.add_trace(go.Pie(
                values=filtered_df_OEQI_CrossTab[MTTC_items_result[i]],
                labels=filtered_df_OEQI_CrossTab['PF'],
                direction='clockwise',
                ## hole을 사용한 도넛 차트
                ),
                row = 1, col = i+1)
            MTTC_OnTime_Rate.update_traces(marker = dict( colors =['red','green'] ))
            

        MTTC_OnTime_Rate.update_layout(title=dict(text='MTTC On-time completion rates', x=0.5, 
                                    font = dict(size = 24)))
        
        st.plotly_chart(MTTC_OnTime_Rate, theme=None, use_container_width=True)
    
    
with tab4 :
    st.dataframe(df_Sell_CrossTab)     

with tab5 :
    st.dataframe(df_OEQI)            
    st.dataframe(df_Sell_CrossTab)            
    
    st.subheader("TEST")
    st.dataframe(df_OEQI_plt)            