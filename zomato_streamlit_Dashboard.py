# zomato_dashboard.py

import subprocess
subprocess.run(["pip", "install", "-r", "requirements.txt"])

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Zomato Insights Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("🍽️ Zomato Restaurant Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("Zomato-data-.csv")
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

# Sidebar + color mapping
st.sidebar.header("Filters")
unique_types = sorted(data['restaurant_type'].dropna().unique())
selected_type = st.sidebar.selectbox("Restaurant Type", ["All"] + unique_types)

color_palette = px.colors.qualitative.Set3
color_map = {t: color_palette[i % len(color_palette)] for i, t in enumerate(unique_types)}

if selected_type != "All":
    df = data[data['restaurant_type'] == selected_type]
    selected_color = color_map.get(selected_type, "#636EFA")
else:
    df = data.copy()
    selected_color = "#636EFA"

# KPIs
col0_1, col0_2, col0_3 = st.columns(3)
col0_1.metric("Total Restaurants", len(df))
col0_2.metric("Avg Rating", round(df['rate'].mean(), 2))
col0_3.metric("Avg Cost for Two", round(df['cost_for_two'].mean(), 2))

# Type Distribution & Rating Histogram
col1, col2 = st.columns(2)
with col1:
    type_counts = df['restaurant_type'].value_counts().reset_index()
    type_counts.columns = ['Type', 'Count']
    fig1 = px.bar(type_counts, x='Type', y='Count', color='Type',
                  color_discrete_map=color_map, title="Restaurant Type Distribution")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.histogram(df, x='rate', nbins=20,
                        color_discrete_sequence=[selected_color],
                        title=f"Distribution of Ratings ({selected_type})")
    st.plotly_chart(fig2, use_container_width=True)

# Online vs Rating, Booking vs Rating
col3, col4 = st.columns(2)
with col3:
    online_rating = df.groupby('online_order')['rate'].mean().reset_index()
    fig3 = px.bar(online_rating, x='online_order', y='rate', color='online_order',
                  color_discrete_sequence=[selected_color],
                  title=f"Online Order vs Rating ({selected_type})")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    booking_rating = df.groupby('book_table')['rate'].mean().reset_index()
    fig4 = px.bar(booking_rating, x='book_table', y='rate', color='book_table',
                  color_discrete_sequence=[selected_color],
                  title=f"Table Booking vs Rating ({selected_type})")
    st.plotly_chart(fig4, use_container_width=True)

# Cost vs Rating
col5, col6 = st.columns(2)
with col5:
    fig5 = px.scatter(df, x='cost_for_two', y='rate',
                      color_discrete_sequence=[selected_color],
                      hover_data=['name'],
                      title=f"Cost vs Rating ({selected_type})")
    st.plotly_chart(fig5, use_container_width=True)

# Correlation Heatmap
with col6:
    corr = df[['rate', 'votes', 'cost_for_two']].corr()
    fig6 = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r',
                     title="Correlation Heatmap")
    st.plotly_chart(fig6, use_container_width=True)

# Top Restaurants
col7, col8 = st.columns(2)
with col7:
    top_voted = df.sort_values(by='votes', ascending=False).head(10)
    fig7 = px.bar(top_voted, x='votes', y='name', orientation='h',
                  color_discrete_sequence=[selected_color],
                  title=f"Top 10 Most Voted Restaurants ({selected_type})")
    st.plotly_chart(fig7, use_container_width=True)

# Avg Cost by Type
st.subheader("Average Cost by Restaurant Type")
avg_cost = df.groupby('restaurant_type')['cost_for_two'].mean().reset_index()
fig9 = px.bar(avg_cost, x='restaurant_type', y='cost_for_two',
              color='restaurant_type', color_discrete_map=color_map,
              title="Avg Cost for Two by Type")
st.plotly_chart(fig9, use_container_width=True)

# Pie chart
st.subheader("Restaurants with Online Order & Table Booking")
both = df[(df['online_order'] == 'Yes') & (df['book_table'] == 'Yes')]
labels = ['Both Features', 'Other Restaurants']
values = [both.shape[0], df.shape[0] - both.shape[0]]
fig10 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4,
                               marker_colors=[selected_color, 'lightgrey'])])
fig10.update_layout(title=f"Online + Booking Availability ({selected_type})")
st.plotly_chart(fig10, use_container_width=True)

# Insights
st.markdown("""
### 📌 Business Insights
- Restaurants offering **Online Ordering** tend to have **better ratings**.
- **Table Booking** also improves customer perception and ratings.
- **High-cost restaurants** often sustain **higher ratings** compared to low-cost ones.
- Restaurants that offer **online ordering** are rated better, possibly because of convenience, faster service, or customer expectations being met.
- Very few restaurants offer both **online ordering and table booking** together.
""")
