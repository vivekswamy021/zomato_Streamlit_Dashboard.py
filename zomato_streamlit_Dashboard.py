import subprocess

# Install required libraries
subprocess.run(["pip", "install", "-r", "requirements.txt"])

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(page_title="Zomato Dashboard", page_icon=":bar_chart:", layout="wide")

st.title("Zomato Restaurant Insights Dashboard")

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv("Zomato-data-.csv")
    # Data cleaning
    data.rename(columns={'approx_cost(for two people)': 'cost_for_two', 'listed_in(type)': 'restaurant_type'}, inplace=True)
    data['rate'] = data['rate'].astype(str).str.replace('/5', '', regex=True)
    data['rate'] = pd.to_numeric(data['rate'], errors='coerce')
    data['cost_for_two'] = pd.to_numeric(data['cost_for_two'].astype(str).str.replace(',', ''), errors='coerce')
    data['votes'] = pd.to_numeric(data['votes'], errors='coerce')
    return data.dropna(subset=['rate','cost_for_two','votes'])

data = load_data()

# Sidebar filters
st.sidebar.header("Filters")
selected_restaurant_type = st.sidebar.selectbox("Select Restaurant Type", options=["All"] + list(data['restaurant_type'].unique()))

if selected_restaurant_type != "All":
    df = data[data['restaurant_type'] == selected_restaurant_type]
else:
    df = data.copy()

# Layout
col1, col2 = st.columns(2)

# Restaurant type distribution
with col1:
    type_counts = df['restaurant_type'].value_counts().reset_index()
    fig1 = px.bar(type_counts, x='index', y='restaurant_type', color='index',
                  labels={'index':'Restaurant Type','restaurant_type':'Count'},
                  title="Distribution of Restaurant Types")
    st.plotly_chart(fig1, use_container_width=True)

# Rating distribution
with col2:
    fig2 = px.histogram(df, x='rate', nbins=20, color_discrete_sequence=['blue'])
    fig2.update_layout(title="Distribution of Ratings", xaxis_title="Rating", yaxis_title="Count")
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# Online Order vs Rating
with col3:
    online_rating = df.groupby('online_order')['rate'].mean().reset_index()
    fig3 = px.bar(online_rating, x='online_order', y='rate', color='online_order',
                  title="Impact of Online Ordering on Ratings")
    st.plotly_chart(fig3, use_container_width=True)

# Table Booking vs Rating
with col4:
    booking_rating = df.groupby('book_table')['rate'].mean().reset_index()
    fig4 = px.bar(booking_rating, x='book_table', y='rate', color='book_table',
                  title="Impact of Table Booking on Ratings")
    st.plotly_chart(fig4, use_container_width=True)

# Scatter: Cost vs Rating
st.subheader("Cost for Two vs Ratings")
fig5 = px.scatter(df, x='cost_for_two', y='rate', color='online_order',
                 hover_data=['name'], title="Cost vs Rating (Colored by Online Order)")
st.plotly_chart(fig5, use_container_width=True)

# Correlation Heatmap
st.subheader("Correlation Matrix")
corr = df[['rate','votes','cost_for_two']].corr()
fig6 = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', title="Correlation Heatmap")
st.plotly_chart(fig6, use_container_width=True)

# Top 10 Rated Restaurants
st.subheader("Top 10 Rated Restaurants")
top_rated = df[df['rate'] >= 4.0][['name','rate','votes','cost_for_two']].sort_values(by='rate', ascending=False).head(10)
st.dataframe(top_rated)

# Most Voted Restaurants
col7, col8 = st.columns(2)

with col7:
    st.subheader("Top 10 Most Voted Restaurants")
    most_voted = df.sort_values(by='votes', ascending=False).head(10)
    fig7 = px.bar(most_voted, x='votes', y='name', orientation='h', color='votes',
                  title="Top Voted Restaurants")
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.subheader("Low Voted Restaurants")
    low_voted = df.sort_values(by='votes').head(10)
    fig8 = px.bar(low_voted, x='votes', y='name', orientation='h', color='votes',
                  title="Low Voted Restaurants")
    st.plotly_chart(fig8, use_container_width=True)

# Average Cost by Type
st.subheader("Average Cost by Restaurant Type")
avg_cost = df.groupby('restaurant_type')['cost_for_two'].mean().reset_index()
fig9 = px.bar(avg_cost, x='restaurant_type', y='cost_for_two', color='restaurant_type',
              title="Average Cost for Two by Type")
st.plotly_chart(fig9, use_container_width=True)

# Restaurants with Both Online Order & Table Booking
st.subheader("Restaurants Offering Both Online Order and Table Booking")
both = df[(df['online_order'] == 'Yes') & (df['book_table'] == 'Yes')]
labels = ['Both Features','Other Restaurants']
sizes = [both.shape[0], df.shape[0]-both.shape[0]]
fig10 = go.Figure(data=[go.Pie(labels=labels, values=sizes, hole=0.4)])
fig10.update_layout(title="Online + Table Booking")
st.plotly_chart(fig10, use_container_width=True)

st.markdown("""
### Business Insights
- Expand Online Ordering: Linked to better ratings.
- Promote Table Booking: Improves customer experience.
- Support Low-Visibility Restaurants: Marketing campaigns needed.
- Focus on Value + Quality: More impactful than pricing.
""")
