import subprocess

# Install required libraries
subprocess.run(["pip", "install", "-r", "requirements.txt"])



# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
import io


st.set_page_config(page_title="Zomato EDA Dashboard", layout="wide")

st.title("Zomato — Exploratory Data Analysis & Insights")
st.markdown("Upload your `Zomato-data-.csv` file and interactively explore cleaned data, charts and summaries.")

# --- File uploader ---
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], help="Choose the Zomato CSV exported from your source.")

@st.cache_data
def load_and_clean(file) -> pd.DataFrame:
    df = pd.read_csv(file)

    # Standardize column names if present with slightly different text
    rename_map = {
        'approx_cost(for two people)': 'cost_for_two',
        'approx_cost(for two people) ': 'cost_for_two',
        'listed_in(type)': 'restaurant_type',
        'listed_in(type) ': 'restaurant_type'
    }
    df.rename(columns=rename_map, inplace=True)

    # Clean rate: remove '/5' and convert to float if possible
    if 'rate' in df.columns:
        # Some rows may contain '-' or 'NEW' or NaN; handle gracefully
        df['rate'] = df['rate'].astype(str).str.replace('/5', '', regex=True).replace(['-', 'nan', 'NONE', 'None', 'NEW'], np.nan)
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce')

    # Cost for two: try to convert to numeric
    if 'cost_for_two' in df.columns:
        df['cost_for_two'] = df['cost_for_two'].astype(str).str.replace(',', '').str.extract(r'(\d+)').astype(float)

    # Votes to numeric
    if 'votes' in df.columns:
        df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0).astype(int)

    # Standardize Yes/No columns
    for c in ['online_order', 'book_table']:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({'Yes': 'Yes', 'No': 'No', 'yes': 'Yes', 'no': 'No', '0': 'No', '1': 'Yes'})

    # Ensure restaurant_type exists
    if 'restaurant_type' not in df.columns:
        df['restaurant_type'] = df.get('listed_in(city)', 'Unknown')

    return df


if uploaded_file is not None:
    data = load_and_clean(uploaded_file)

    st.sidebar.header("Filters")
    # Simple filters
    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        online_filter = st.sidebar.selectbox('Online Order', options=['All'] + sorted(data['online_order'].dropna().unique().tolist()), index=0)
    with col2:
        table_filter = st.sidebar.selectbox('Table Booking', options=['All'] + sorted(data['book_table'].dropna().unique().tolist()), index=0)
    with col3:
        rt_options = ['All'] + sorted(data['restaurant_type'].dropna().unique().tolist())
        rest_type_filter = st.sidebar.selectbox('Restaurant Type', options=rt_options, index=0)

    min_rate = float(data['rate'].min(skipna=True)) if not data['rate'].dropna().empty else 0.0
    max_rate = float(data['rate'].max(skipna=True)) if not data['rate'].dropna().empty else 5.0
    rate_range = st.sidebar.slider('Rating range', min_value=0.0, max_value=5.0, value=(min_rate, max_rate), step=0.1)

    # Apply filters
    df_filtered = data.copy()
    if online_filter != 'All':
        df_filtered = df_filtered[df_filtered['online_order'] == online_filter]
    if table_filter != 'All':
        df_filtered = df_filtered[df_filtered['book_table'] == table_filter]
    if rest_type_filter != 'All':
        df_filtered = df_filtered[df_filtered['restaurant_type'] == rest_type_filter]
    df_filtered = df_filtered[(df_filtered['rate'] >= rate_range[0]) & (df_filtered['rate'] <= rate_range[1])]

    # Show data summary
    st.subheader("Dataset snapshot")
    st.write(f"Rows: {data.shape[0]}  —  Columns: {data.shape[1]}")
    st.dataframe(df_filtered.head(100))

    # Download cleaned data
    towrite = io.BytesIO()
    df_filtered.to_csv(towrite, index=False)
    towrite.seek(0)
    st.download_button(label="Download filtered CSV", data=towrite, file_name="zomato_filtered.csv", mime="text/csv")

    # --- Key Metrics ---
    st.subheader("Key metrics")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Average Rating", round(data['rate'].mean(skipna=True), 2))
    with c2:
        st.metric("Average Votes", int(data['votes'].mean()))
    with c3:
        st.metric("Average Cost for Two", round(data['cost_for_two'].mean(skipna=True), 2))
    with c4:
        st.metric("Restaurants with Both Online & Booking", int(((data['online_order'] == 'Yes') & (data['book_table'] == 'Yes')).sum()))

    # --- Visualizations ---
    st.subheader("Visualizations")

    # 1. Distribution of restaurant types
    st.markdown("**Distribution of Restaurant Types**")
    fig_rt, ax_rt = plt.subplots(figsize=(10, 4))
    order = df_filtered['restaurant_type'].value_counts().index
    sns.countplot(y='restaurant_type', data=df_filtered, order=order, ax=ax_rt)
    ax_rt.set_xlabel('Count')
    ax_rt.set_ylabel('Restaurant Type')
    st.pyplot(fig_rt)

    # 2. Rating distribution
    st.markdown("**Rating distribution**")
    fig_rate, ax_rate = plt.subplots()
    sns.histplot(df_filtered['rate'].dropna(), kde=True, ax=ax_rate)
    ax_rate.set_xlabel('Rating')
    st.pyplot(fig_rate)

    # 3. Online Order vs Rating
    st.markdown("**Online Order vs Rating**")
    fig_online, ax_online = plt.subplots()
    sns.barplot(x='online_order', y='rate', data=df_filtered, ax=ax_online)
    st.pyplot(fig_online)

    # 4. Table booking vs Rating
    st.markdown("**Table Booking vs Rating**")
    fig_book, ax_book = plt.subplots()
    sns.barplot(x='book_table', y='rate', data=df_filtered, ax=ax_book)
    st.pyplot(fig_book)

    # 5. Cost vs Rating scatter
    st.markdown("**Cost for Two vs Rating (colored by Online Order)**")
    fig_scatter, ax_scatter = plt.subplots(figsize=(8, 4))
    sns.scatterplot(x='cost_for_two', y='rate', hue='online_order', data=df_filtered, ax=ax_scatter)
    ax_scatter.set_xlabel('Cost for Two')
    ax_scatter.set_ylabel('Rating')
    st.pyplot(fig_scatter)

    # 6. Couples preferred cost (countplot of cost buckets)
    st.markdown("**Cost buckets (couple preference proxy)**")
    if 'cost_for_two' in df_filtered.columns:
        bins = [0, 200, 400, 600, 800, 1000, 5000]
        labels = ['<200', '200-400', '400-600', '600-800', '800-1000', '1000+']
        df_filtered['cost_bucket'] = pd.cut(df_filtered['cost_for_two'].fillna(0), bins=bins, labels=labels)
        fig_bucket, ax_bucket = plt.subplots()
        sns.countplot(x='cost_bucket', data=df_filtered, ax=ax_bucket, order=labels)
        ax_bucket.set_xlabel('Approx cost for two')
        st.pyplot(fig_bucket)

    # 7. Correlation heatmap
    st.markdown("**Correlation: rate, votes, cost_for_two**")
    corr_cols = ['rate', 'votes', 'cost_for_two']
    corr_data = df_filtered[corr_cols].copy()
    fig_corr, ax_corr = plt.subplots()
    sns.heatmap(corr_data.corr(), annot=True, fmt='.2f', cmap='coolwarm', ax=ax_corr)
    st.pyplot(fig_corr)

    # Top rated and most voted
    st.subheader("Top restaurants")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top Rated (>=4.0)**")
        if 'rate' in df_filtered.columns:
            top_rated = df_filtered[df_filtered['rate'] >= 4.0][['name', 'rate', 'votes', 'cost_for_two']].sort_values(by=['rate','votes'], ascending=[False, False])
            st.dataframe(top_rated.head(10))
        else:
            st.write('No rate column available')

    with col_b:
        st.markdown("**Most Voted**")
        most_voted = df_filtered.sort_values(by='votes', ascending=False)[['name', 'rate', 'votes']].head(10)
        st.dataframe(most_voted)
        fig_mv, ax_mv = plt.subplots(figsize=(8,4))
        sns.barplot(x='votes', y='name', data=most_voted, ax=ax_mv)
        ax_mv.set_xlabel('Votes')
        ax_mv.set_ylabel('Restaurant')
        st.pyplot(fig_mv)

    # Low voted
    st.markdown("**Lowest Voted Restaurants (sample)**")
    low_voted = df_filtered.sort_values(by='votes', ascending=True)[['name','rate','votes']].head(10)
    st.table(low_voted)

    # Average cost by restaurant type
    st.markdown("**Average Cost for Two by Restaurant Type**")
    avg_cost_by_type = df_filtered.groupby('restaurant_type')['cost_for_two'].mean().sort_values(ascending=False).head(20)
    st.bar_chart(avg_cost_by_type)

    # Restaurants offering both services
    st.markdown("**Restaurants offering both Online Order & Table Booking**")
    both_df = data[(data['online_order'] == 'Yes') & (data['book_table'] == 'Yes')]
    st.write(f"Total: {both_df.shape[0]}")
    st.dataframe(both_df[['name','rate','votes','cost_for_two','restaurant_type']].head(20))

    # Business recommendations
    st.subheader('Business Expansion Suggestions')
    st.markdown(
        "- Expand Online Ordering in areas with low online coverage\n"
        "- Promote Table Booking as it correlates with slightly higher ratings\n"
        "- Run marketing campaigns for low-visibility restaurants (influencers, targeted ads)\n"
        "- Focus on value + quality rather than price alone\n"
        "- Prioritize cafes & quick-bites in high-conversion areas for partnerships\n"
    )

    st.success('Analysis complete — use the filters on the left to refine the view and download results.')

else:
    st.info("Upload the Zomato CSV file to begin. If you'd like a sample, click the 'Use sample data' button below.")
    if st.button('Use sample data'):
        # Create a tiny sample frame so user can see the app without uploading
        sample = pd.DataFrame({
            'name': ['A', 'B', 'C', 'D'],
            'online_order': ['Yes','No','Yes','No'],
            'book_table': ['Yes','No','No','Yes'],
            'rate': [4.2, 3.5, 4.0, 2.8],
            'votes': [120, 45, 87, 3],
            'cost_for_two': [350, 250, 800, 150],
            'restaurant_type': ['Casual Dining','Cafe','Fine Dining','Quick Bites']
        })
        st.dataframe(sample)
  


# End of app
