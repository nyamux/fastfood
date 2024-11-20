# Import necessary libraries
import streamlit as st  
import pandas as pd  
import plotly.express as px  
import plotly.graph_objs as go  

# Function to load and clean the data
@st.cache_data
def load_and_clean_data():
    try:
        # Loading data from GitHub repository (same as code one)
        url = "https://raw.githubusercontent.com/nyamux/fastfood/main/fastfoodus.csv"
        df = pd.read_csv(url)
        
        # Drop duplicate rows based on 'id' column
        df = df.drop_duplicates(subset=['id'], keep='last')
        
        # Clean the 'categories' column
        df['categories'] = df['categories'].str.strip().str.lower()
        
        return df
    
    except pd.errors.EmptyDataError:
        st.error("Error: No data found in the file.")
    except KeyError:
        st.error("Error: The 'categories' column is missing in the data.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# Set up the page for the Streamlit app
st.set_page_config(page_title="Fast Food Location Dashboard", layout="wide")

# Load data
df = load_and_clean_data()

if df is not None:
    st.sidebar.title("Filters")

    # Set the main title of the web app
    st.title("Fast Food Locations Data Visualization")

    # Dropdown menu for selecting a province
    selected_province = st.sidebar.selectbox("Select State", options=["All"] + sorted(df['province'].unique().tolist()))

    # Function to filter data by the selected province
    def filter_data_by_province(province="All"):
        """Filter data by province, default is All"""
        if province == "All":
            return df
        return df[df['province'] == province]

    # Apply the province filter
    filtered_df = filter_data_by_province(selected_province)

    # Filter available cities based on the selected province
    if selected_province == "All":
        available_cities = sorted(df['city'].unique().tolist())
    else:
        available_cities = sorted(df[df['province'] == selected_province]['city'].unique().tolist())

    # Dropdown menu for selecting a city
    selected_city = st.sidebar.selectbox("Select City", options=["All"] + available_cities)

    # Function to filter data by city and province
    def filter_data_by_city_province(df, city, province):
        """Filter the DataFrame by selected city and province."""
        if province == "All":
            if city == "All":
                return df
            return df[df['city'].str.lower() == city.lower()]
        if city == "All":
            return df[df['province'] == province]
        return df[(df['city'].str.lower() == city.lower()) & (df['province'] == province)]

    # Apply the city and province filter
    filtered_city_province_df = filter_data_by_city_province(filtered_df, selected_city, selected_province)

    # Display filtered data
    st.title("Fast Food Restaurant Data")

    if not filtered_city_province_df.empty:
        location_text = f"{selected_city}, {selected_province}" if selected_province != "All" else "All Locations"
        st.subheader(f"Details for Fast Food Restaurants in {location_text}")
        st.write(filtered_city_province_df[['name', 'address', 'categories','city', 'postalCode', 'province']])
    else:
        st.write(f"No fast food restaurants found in the selected location.")

    # Count locations per province
    province_counts = filtered_city_province_df['province'].value_counts().reset_index()
    province_counts.columns = ['province', 'count']

    # Join counts back to filtered DataFrame
    map_data = pd.merge(filtered_city_province_df, province_counts, on='province', how='left')

    # Plotting the map
    if not map_data.empty:
        fig_map = px.scatter_mapbox(
            map_data,
            lat="latitude",
            lon="longitude",
            color="count",
            size="count",
            hover_name="name",
            hover_data={"address": True, "city": True, "province": True, "count": True},
            zoom=10,
            height=600,
            title=f"Density Map of Fast-Food Locations in {location_text}"
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map)

    # Category analysis
    categories_selected = st.sidebar.multiselect(
        "Select Categories",
        options=sorted(df['categories'].unique().tolist())
    )

    # Function to filter data by categories
    def get_category_data(categories_selected):
        """Filter data by selected categories."""
        if not categories_selected:
            return df
        return df[df['categories'].isin(categories_selected)]

    # Apply category filter
    category_data = get_category_data(categories_selected)
    category_counts = category_data.groupby(['province', 'categories']).size().reset_index(name='count')

    # Plot category frequency
    fig_bar = px.bar(
        category_counts,
        x="province",
        y="count",
        color="categories",
        title="Fast-Food Category Frequency by State",
        labels={"count": "Number of Locations", "province": "State"}
    )
    fig_bar.update_layout(barmode='stack')
    st.plotly_chart(fig_bar)

    # Pie chart for category distribution
    type_counts = category_data['categories'].value_counts()
    fig_pie = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Distribution of Fast-Food Types"
    )
    st.plotly_chart(fig_pie)

    # Top 10 restaurants analysis
    def get_top_10_restaurants(df):
        """Get the top 10 most common restaurant names."""
        restaurant_counts = df.groupby(['name']).size().reset_index(name='count')
        return restaurant_counts.sort_values(by=['count'], ascending=False).head(10)

    # Get and display top 10 restaurants
    if selected_province == "All":
        location_text = "All States"
    else:
        location_text = selected_province
        
    st.title(f"Top 10 Most Common Restaurants in {location_text}")
    
    top_10_restaurants_data = get_top_10_restaurants(filtered_df)
    st.write(top_10_restaurants_data)

    # Map of top 10 restaurants
    top_10_data = df[df['name'].isin(top_10_restaurants_data['name'])]
    
    if not top_10_data.empty:
        fig_top_10_map = px.scatter_mapbox(
            top_10_data,
            lat='latitude',
            lon='longitude',
            color='name',
            hover_name='name',
            hover_data=['city', 'address', 'postalCode'],
            size_max=15,
            zoom=10,
            title=f"Top 10 Most Common Restaurants in {location_text}"
        )
        fig_top_10_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_top_10_map)

    # Additional information in sidebar
    st.sidebar.title("Fast-Food Accessibility Dashboard")
    st.sidebar.markdown("Explore fast-food locations by state, popular food types, and more!")

else:
    st.error("Failed to load data. Please try again later.")
