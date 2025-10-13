# zomato_dashboard.py

import subprocess
# Install dependencies from requirements.txt if present
subprocess.run(["pip", "install", "-r", "requirements.txt"])

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------
# Page Config
# ----------------------
st.set_page_config(page_title="Zomato Restaurant Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("🍽️ Zomato Restaurant Dashboard")

# ----------------------
# Load Data
# ----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Zomato-data-.csv")

    # Cleaning
    df.rename(columns={
        'approx_cost(for two people)': 'cost_for_two',
        'listed_in(type)': 'restaurant_type'
    }, inplace=True)

    df['rate'] = df['rate'].astype(str).str.replace('/5', '', regex=True)
    df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
    df['cost_for_two'] = pd.to_numeric(df['cost_for_two'].astype(str).str.replace(',', ''), errors='coerce')
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce')

    df.dropna(subset=['rate', 'cost_for_two', 'votes'], inplace=True)
    return df

data = load_data()

# ----------------------
# Sidebar Filters
# ----------------------
st.sidebar.header("Filters")

# Restaurant Type
selected_type = st.sidebar.selectbox(
    "Restaurant Type",
    ["All"] + sorted(data['restaurant_type'].dropna().unique())
)

# Rating Slider
rate_min, rate_max = float(data['rate'].min()), float(data['rate'].max())
min_rate, max_rate = st.sidebar.slider(
    "Select Rating Range",
    min_value=rate_min,
    max_value=rate_max,
    value=(rate_min, rate_max),
    step=0.1
)

# Cost Slider
cost_min, cost_max = int(data['cost_for_two'].min()), int(data['cost_for_two'].max())
min_cost, max_cost = st.sidebar.slider(
    "Select Cost for Two",
    min_value=cost_min,
    max_value=cost_max,
    value=(cost_min, cost_max),
    step=50
)

# Online / Booking Filter
online_filter = st.sidebar.multiselect("Online Order", options=['Yes', 'No'], default=['Yes', 'No'])
booking_filter = st.sidebar.multiselect("Table Booking", options=['Yes', 'No'], default=['Yes', 'No'])

# ----------------------
# Filter Data Function
# ----------------------
@st.cache_data
def filter_data(df, r_type, r_min, r_max, c_min, c_max, online, booking):
    df_filtered = df.copy()
    if r_type != "All":
        df_filtered = df_filtered[df_filtered['restaurant_type'] == r_type]
    df_filtered = df_filtered[(df_filtered['rate'] >= r_min) & (df_filtered['rate'] <= r_max)]
    df_filtered = df_filtered[(df_filtered['cost_for_two'] >= c_min) & (df_filtered['cost_for_two'] <= c_max)]
    df_filtered = df_filtered[df_filtered['online_order'].isin(online) & df_filtered['book_table'].isin(booking)]
    return df_filtered

df = filter_data(data, selected_type, min_rate, max_rate, min_cost, max_cost, online_filter, booking_filter)

# ----------------------
# KPIs
# ----------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Restaurants", len(df))
with col2:
    st.metric("Avg Rating", round(df['rate'].mean(), 2))
with col3:
    st.metric("Avg Cost for Two", f"₹{round(df['cost_for_two'].mean(), 2)}")
with col4:
    st.metric("Max Votes", int(df['votes'].max()))

# ----------------------
# Tabs for Layout
# ----------------------
tab_overview, tab_analysis, tab_insights = st.tabs(["Overview", "Analysis", "Insights"])

with tab_overview:
    st.subheader("Filtered Data Preview")
    st.dataframe(df.head(10))
    st.download_button(
        label="Download Filtered Data",
        data=df.to_csv(index=False),
        file_name="filtered_zomato.csv",
        mime="text/csv"
    )

with tab_analysis:
    # Row 1: Restaurant Type Distribution & Rating Histogram
    col1, col2 = st.columns(2)
    with col1:
        type_counts = df['restaurant_type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig1 = px.bar(type_counts, x='Type', y='Count', color='Type', title="Restaurant Type Distribution")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.histogram(df, x='rate', nbins=20, color_discrete_sequence=['blue'], title="Distribution of Ratings")
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2: Online vs Rating & Booking vs Rating
    col3, col4 = st.columns(2)
    with col3:
        online_rating = df.groupby('online_order')['rate'].mean().reset_index()
        fig3 = px.bar(online_rating, x='online_order', y='rate', color='online_order', title="Online Order vs Rating")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        booking_rating = df.groupby('book_table')['rate'].mean().reset_index()
        fig4 = px.bar(booking_rating, x='book_table', y='rate', color='book_table', title="Table Booking vs Rating")
        st.plotly_chart(fig4, use_container_width=True)

    # Row 3: Cost vs Rating & Correlation Heatmap
    col5, col6 = st.columns(2)
    with col5:
        try:
            import statsmodels.api as sm
            fig5 = px.scatter(df, x='cost_for_two', y='rate', color='online_order',
                              hover_data=['name'], trendline="ols", title="Cost vs Rating (with Trendline)")
        except ImportError:
            fig5 = px.scatter(df, x='cost_for_two', y='rate', color='online_order',
                              hover_data=['name'], title="Cost vs Rating")
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        corr_columns = ['rate', 'votes', 'cost_for_two']
        corr = df[corr_columns].corr()
        fig6 = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Heatmap")
        st.plotly_chart(fig6, use_container_width=True)

    # Row 4: Top Restaurants
    col7, col8 = st.columns(2)
    with col7:
        top_voted = df.sort_values(by='votes', ascending=False).head(10)
        fig7 = px.bar(top_voted, x='votes', y='name', orientation='h', color='votes', title="Top 10 Most Voted Restaurants")
        st.plotly_chart(fig7, use_container_width=True)
        st.dataframe(top_voted[['name','votes','rate','cost_for_two']])

    # Average Cost by Type
    st.subheader("Average Cost by Restaurant Type")
    avg_cost = df.groupby('restaurant_type')['cost_for_two'].mean().reset_index()
    fig9 = px.bar(avg_cost, x='restaurant_type', y='cost_for_two', color='restaurant_type', title="Avg Cost for Two by Type")
    st.plotly_chart(fig9, use_container_width=True)

    # Both Online & Booking Pie
    st.subheader("Restaurants with Online Order & Table Booking")
    both = df[(df['online_order'] == 'Yes') & (df['book_table'] == 'Yes')]
    labels = ['Both Features', 'Other Restaurants']
    values = [both.shape[0], df.shape[0] - both.shape[0]]
    fig10 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
    fig10.update_traces(textinfo='percent+label')
    fig10.update_layout(title="Online + Booking Availability")
    st.plotly_chart(fig10, use_container_width=True)

with tab_insights:
    st.markdown(f"""
    ### 📌 Business Insights
    - Total restaurants after filtering: **{len(df)}**
    - Restaurants offering **Online Ordering** tend to have **better ratings**.
    - **Table Booking** also improves customer perception and ratings.
    - **High-cost restaurants** often sustain **higher ratings** compared to low-cost ones.
    - Restaurants that offer **online ordering** are rated better, possibly due to convenience or faster service.
    - Restaurants with both **online ordering and table booking**: **{both.shape[0]}**, while others: **{df.shape[0] - both.shape[0]}**
    """)
