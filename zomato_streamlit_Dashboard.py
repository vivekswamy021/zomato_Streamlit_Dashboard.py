import subprocess

# Install required libraries
subprocess.run(["pip", "install", "-r", "requirements.txt"])

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zomato Dashboard", layout="wide")

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("Zomato-data-.csv")
    # Clean data
    df.dropna(subset=["rate", "votes", "approx_cost(for two people)", "listed_in(type)", "online_order"], inplace=True)
    df['rate'] = df['rate'].astype(str).str.replace('/5', '').str.strip()
    df = df[df['rate'] != 'NEW']
    df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce')
    df['approx_cost(for two people)'] = df['approx_cost(for two people)'].astype(str).str.replace(',', '').astype(float)
    df.rename(columns={"approx_cost(for two people)": "cost_for_two", "listed_in(type)": "restaurant_type"}, inplace=True)
    return df

# Load
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filters")
restaurant_type = st.sidebar.multiselect("Select Restaurant Type", df['restaurant_type'].unique())
order_filter = st.sidebar.multiselect("Online Order", df['online_order'].unique())
booking_filter = st.sidebar.multiselect("Book Table", df['book_table'].dropna().unique()) if 'book_table' in df.columns else []

filtered_df = df.copy()
if restaurant_type:
    filtered_df = filtered_df[filtered_df['restaurant_type'].isin(restaurant_type)]
if order_filter:
    filtered_df = filtered_df[filtered_df['online_order'].isin(order_filter)]
if booking_filter:
    filtered_df = filtered_df[filtered_df['book_table'].isin(booking_filter)]

st.title("🍽️ Zomato Restaurant Analysis Dashboard")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Restaurants", len(filtered_df))
col2.metric("Average Rating", round(filtered_df['rate'].mean(), 2))
col3.metric("Average Cost for Two", round(filtered_df['cost_for_two'].mean(), 2))

# Rating Distribution
if not filtered_df.empty:
    fig_rating = px.histogram(filtered_df, x='rate', nbins=20, title="Rating Distribution", color_discrete_sequence=['#FF6347'])
    st.plotly_chart(fig_rating, use_container_width=True)
else:
    st.warning("No data available for Rating Distribution.")

# Restaurant Type Count
rt_counts = filtered_df['restaurant_type'].value_counts().reset_index()
rt_counts.columns = ['restaurant_type', 'count']
if not rt_counts.empty:
    fig_rt = px.bar(rt_counts, x='restaurant_type', y='count', title="Restaurant Types", color='count')
    st.plotly_chart(fig_rt, use_container_width=True)

# Online Order vs Rating
if 'online_order' in filtered_df.columns and not filtered_df.empty:
    fig_online = px.box(filtered_df, x='online_order', y='rate', color='online_order', title="Online Order vs Rating")
    st.plotly_chart(fig_online, use_container_width=True)

# Cost vs Rating
if not filtered_df.empty:
    fig_cost = px.scatter(filtered_df, x='cost_for_two', y='rate', size='votes', color='restaurant_type', title="Cost vs Rating")
    st.plotly_chart(fig_cost, use_container_width=True)

# Top Restaurants by Votes
top_votes = filtered_df.groupby('name')['votes'].sum().reset_index().sort_values(by='votes', ascending=False).head(10)
if not top_votes.empty:
    fig_top = px.bar(top_votes, x='name', y='votes', title="Top 10 Restaurants by Votes", color='votes')
    st.plotly_chart(fig_top, use_container_width=True)

# Download Filtered Data
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False),
    file_name='filtered_zomato_data.csv',
    mime='text/csv')
