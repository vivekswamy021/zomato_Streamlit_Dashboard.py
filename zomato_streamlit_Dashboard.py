# zomato_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------
# Page Config
# ---------------------
st.set_page_config(page_title="Zomato Restaurant Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("🍽️ Zomato Restaurant Dashboard")

# ---------------------
# Load Data
# ---------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Zomato-data-.csv")

    # Rename columns
    df.rename(columns={
        'approx_cost(for two people)': 'cost_for_two',
        'listed_in(type)': 'restaurant_type'
    }, inplace=True)

    # Clean columns
    df['rate'] = df['rate'].astype(str).str.replace('/5', '', regex=True)
    df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
    df['cost_for_two'] = pd.to_numeric(df['cost_for_two'].astype(str).str.replace(',', ''), errors='coerce')
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce')

    # Drop rows with missing essentials
    df.dropna(subset=['rate', 'cost_for_two', 'votes'], inplace=True)

    return df

data = load_data()

# ----------------------
# Sidebar Filters
# ----------------------
st.sidebar.header("Filters")
selected_type = st.sidebar.selectbox(
    "Restaurant Type",
    ["All"] + sorted(data['restaurant_type'].dropna().unique())
)

if selected_type != "All":
    df = data[data['restaurant_type'] == selected_type]
else:
    df = data.copy()

# Rating slider
min_rate, max_rate = st.sidebar.slider(
    "Select Rating Range",
    min_value=float(data['rate'].min()),
    max_value=float(data['rate'].max()),
    value=(float(data['rate'].min()), float(data['rate'].max()))
)

# Cost slider
min_cost, max_cost = st.sidebar.slider(
    "Select Cost for Two Range",
    min_value=int(data['cost_for_two'].min()),
    max_value=int(data['cost_for_two'].max()),
    value=(int(data['cost_for_two'].min()), int(data['cost_for_two'].max()))
)

# Apply filters
df = data[
    (data['restaurant_type'].isin(restaurant_types)) &
    (data['rate'] >= min_rate) & (data['rate'] <= max_rate) &
    (data['cost_for_two'] >= min_cost) & (data['cost_for_two'] <= max_cost)
]

# ---------------------
# KPI Metrics
# ---------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Restaurants", len(df))
with col2:
    st.metric("Average Rating", round(df['rate'].mean(), 2))
with col3:
    st.metric("Average Cost for Two", round(df['cost_for_two'].mean(), 2))

# ---------------------
# Restaurant Type Distribution & Rating Histogram
# ---------------------
col4, col5 = st.columns(2)

with col4:
    type_counts = df['restaurant_type'].value_counts().reset_index()
    type_counts.columns = ['Type', 'Count']
    fig1 = px.bar(type_counts, x='Type', y='Count', color='Type',
                  title="Restaurant Type Distribution")
    st.plotly_chart(fig1, use_container_width=True)

with col5:
    fig2 = px.histogram(df, x='rate', nbins=20,
                        color_discrete_sequence=['blue'],
                        title="Distribution of Ratings")
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------
# Online vs Rating, Booking vs Rating
# ---------------------
col6, col7 = st.columns(2)
with col6:
    online_rating = df.groupby('online_order')['rate'].mean().reset_index()
    fig3 = px.bar(online_rating, x='online_order', y='rate', color='online_order',
                  title="Online Order vs Rating")
    st.plotly_chart(fig3, use_container_width=True)

with col7:
    booking_rating = df.groupby('book_table')['rate'].mean().reset_index()
    fig4 = px.bar(booking_rating, x='book_table', y='rate', color='book_table',
                  title="Table Booking vs Rating")
    st.plotly_chart(fig4, use_container_width=True)

# ---------------------
# Cost vs Rating Scatter & Correlation Heatmap
# ---------------------
col8, col9 = st.columns(2)
with col8:
    fig5 = px.scatter(df, x='cost_for_two', y='rate',
                      color='online_order', hover_data=['name'],
                      title="Cost vs Rating (Online Order Highlighted)")
    st.plotly_chart(fig5, use_container_width=True)

with col9:
    corr = df[['rate', 'votes', 'cost_for_two']].corr()
    fig6 = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r',
                     title="Correlation Heatmap")
    st.plotly_chart(fig6, use_container_width=True)

# ---------------------
# Top & Bottom Restaurants by Votes
# ---------------------
st.subheader("Top 10 Most Voted Restaurants")
top_voted = df.sort_values(by='votes', ascending=False).head(10)
fig7 = px.bar(top_voted, x='votes', y='name', orientation='h', color='votes',
              title="Top 10 Most Voted Restaurants")
st.plotly_chart(fig7, use_container_width=True)
st.dataframe(top_voted[['name','rate','votes','cost_for_two']])

st.subheader("Bottom 10 Least Voted Restaurants")
low_voted = df.sort_values(by='votes', ascending=True).head(10)
fig8 = px.bar(low_voted, x='votes', y='name', orientation='h', color='votes',
              title="Bottom 10 Least Voted Restaurants")
st.plotly_chart(fig8, use_container_width=True)
st.dataframe(low_voted[['name','rate','votes','cost_for_two']])

# ---------------------
# Average Cost by Restaurant Type
# ---------------------
st.subheader("Average Cost by Restaurant Type")
avg_cost = df.groupby('restaurant_type')['cost_for_two'].mean().reset_index()
fig9 = px.bar(avg_cost, x='restaurant_type', y='cost_for_two', color='restaurant_type',
              title="Avg Cost for Two by Type")
st.plotly_chart(fig9, use_container_width=True)

# ---------------------
# Pie: Both Online Order & Booking
# ---------------------
st.subheader("Restaurants with Online Order & Table Booking")
both = df[(df['online_order'] == 'Yes') & (df['book_table'] == 'Yes')]
labels = ['Both Features', 'Other Restaurants']
values = [both.shape[0], df.shape[0] - both.shape[0]]
fig10 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
fig10.update_layout(title="Online + Booking Availability")
st.plotly_chart(fig10, use_container_width=True)

# ---------------------
# Insights Section
# ---------------------
st.markdown("""
### 📌 Business Insights
- Restaurants offering **Online Ordering** tend to have **better ratings**.
- **Table Booking** also improves customer perception and ratings.
- **High-cost restaurants** often sustain **higher ratings** compared to low-cost ones.
- Restaurants that offer **online ordering** are rated better, possibly because of convenience, faster service, or customer expectations being met.
- Very few restaurants offer **both online ordering and table booking together**, while the majority don’t provide both services simultaneously.
""")
