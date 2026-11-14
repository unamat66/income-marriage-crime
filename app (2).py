import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Scientific Visualisation Dashboard", layout="wide")

st.title("📈 Scientific Visualisation Assignment")
st.subheader("Income, Marriages, and Prison Statistics in Malaysia (2020 - 2024)")

# Load Data
@st.cache_data
def load_data():
    income_df = pd.read_csv('income.csv')
    marriages_df = pd.read_csv('marriages_age.csv')
    crime_df = pd.read_csv('crime.csv')
    
    for df in [income_df, marriages_df, crime_df]:
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
    income_filtered = income_df[(income_df['year'] >= 2020) & (income_df['year'] <= 2024)].copy()
    marriages_filtered = marriages_df[(marriages_df['year'] >= 2020) & (marriages_df['year'] <= 2024)].copy()
    crime_filtered = crime_df[(crime_df['year'] >= 2020) & (crime_df['year'] <= 2024)].copy()
    
    income_filtered['income'] = pd.to_numeric(income_filtered['income'].replace('?', pd.NA), errors='coerce')
    
    # 1. National Level aggregation
    income_yearly = income_filtered[income_filtered['variable'] == 'mean'].groupby('year')['income'].mean().reset_index(name='avg_income')
    marriages_yearly = marriages_filtered[marriages_filtered['age'] == 'all'].groupby('year')['abs'].sum().reset_index(name='total_marriages')
    crime_yearly = crime_filtered[(crime_filtered['state'] == 'Malaysia') & (crime_filtered['sex'] == 'both')].groupby('year')['prisoners'].sum().reset_index(name='total_prisoners')
    
    merged_yearly = income_yearly.merge(marriages_yearly, on='year', how='outer')
    merged_yearly = merged_yearly.merge(crime_yearly, on='year', how='outer')
    
    # 2. State Level aggregation
    income_filtered['state'] = income_filtered['state'].astype(str).str.strip("'").str.strip()
    crime_filtered['state'] = crime_filtered['state'].astype(str).str.strip("'").str.strip()
    
    income_state = income_filtered[income_filtered['variable'] == 'mean'].groupby(['year', 'state'])['income'].mean().reset_index(name='avg_income')
    crime_state = crime_filtered[crime_filtered['sex'] == 'both'].groupby(['year', 'state'])['prisoners'].sum().reset_index(name='total_prisoners')
    merged_state = pd.merge(income_state, crime_state, on=['year', 'state'], how='inner')
    
    return merged_yearly, merged_state

try:
    merged_yearly_df, merged_state_df = load_data()
except Exception as e:
    st.error(f"Error loading datasets. Please make sure 'income.csv', 'marriages_age.csv', and 'crime.csv' are in the same folder. {e}")
    st.stop()

# Create layout tabs
tab1, tab2, tab3 = st.tabs(["Income vs Prisoners", "Marriages vs Prisoners", "Correlation Heatmap"])

with tab1:
    st.header("1. National Average Income vs Total Prisoners")
    plot_yearly = merged_yearly_df.dropna(subset=['avg_income', 'total_prisoners']).sort_values('year')
    
    fig_line = make_subplots(specs=[[{"secondary_y": True}]])
    fig_line.add_trace(
        go.Scatter(x=plot_yearly['year'], y=plot_yearly['avg_income'], name="Average Income (RM)", mode='lines+markers', line=dict(color='blue', width=3)),
        secondary_y=False,
    )
    fig_line.add_trace(
        go.Scatter(x=plot_yearly['year'], y=plot_yearly['total_prisoners'], name="Total Prisoners", mode='lines+markers', line=dict(color='red', width=3)),
        secondary_y=True,
    )
    fig_line.update_layout(
        xaxis_title="Year",
        xaxis=dict(tickmode='array', tickvals=[2022, 2024]),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig_line.update_yaxes(title_text="Average Income (RM)", secondary_y=False, color='blue')
    fig_line.update_yaxes(title_text="Total Prisoners", secondary_y=True, color='red')
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.header("2. National Yearly Marriages vs Total Prisoners")
    fig_bar = make_subplots(specs=[[{"secondary_y": True}]])
    fig_bar.add_trace(
        go.Bar(x=merged_yearly_df['year'], y=merged_yearly_df['total_marriages'], name="Total Marriages", marker_color='rgb(158,202,225)'),
        secondary_y=False,
    )
    fig_bar.add_trace(
        go.Bar(x=merged_yearly_df['year'], y=merged_yearly_df['total_prisoners'], name="Total Prisoners", marker_color='rgb(227,119,194)'),
        secondary_y=True,
    )
    fig_bar.update_layout(
        xaxis_title="Year",
        barmode='group',
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig_bar.update_yaxes(title_text="Total Marriages", secondary_y=False)
    fig_bar.update_yaxes(title_text="Total Prisoners", secondary_y=True)
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.header("3. Correlation Heatmap: Income vs Marriages vs Prisoners")
    state_correlation_df = merged_state_df.merge(merged_yearly_df[['year', 'total_marriages']], on='year', how='inner')
    corr_matrix = state_correlation_df[['avg_income', 'total_marriages', 'total_prisoners']].corr()
    
    fig_heatmap = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='RdBu_r',
        labels=dict(color="Correlation"),
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
