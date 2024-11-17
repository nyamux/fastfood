import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Set page config
st.set_page_config(
    page_title="US Fast Food Analysis",
    page_icon="🍔",
    layout="wide"
)

# Load and preprocess data
@st.cache_data
def load_data():
    # Loading data from your GitHub repository
    url = "https://raw.githubusercontent.com/nyamux/fastfood/main/fastfoodus.csv"
    
    try:
        df = pd.read_csv(url)
        # Clean categories column
        df['categories'] = df['categories'].str.split(' and ')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_density_map(filtered_df):
    # Sample data for map if too large
    MAX_MAP_POINTS = 1000
    if len(filtered_df) > MAX_MAP_POINTS:
        map_df = filtered_df.sample(n=MAX_MAP_POINTS, random_state=42)
    else:
        map_df = filtered_df

    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    
    for idx, row in map_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            popup=f"{row['name']} - {row['city']}, {row['province']}",
            color='red',
            fill=True
        ).add_to(m)
    
    return m

def main():
    st.title("🍔 US Fast Food Restaurant Analysis")
    
    # Load data with error handling
    with st.spinner('Loading data...'):
        df = load_data()
        
    if df is None:
        st.error("Failed to load data. Please try again later.")
        return
        
    # Show data loading success
    st.success(f"Successfully loaded {len(df)} records!")
    
    # Add data info expander
    with st.expander("Dataset Information"):
        st.write(f"Total records: {len(df)}")
        st.write(f"States covered: {len(df['province'].unique())}")
        st.write(f"Cities covered: {len(df['city'].unique())}")
        st.write(f"Restaurant chains: {len(df['name'].unique())}")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # State selection
    states = sorted(df['province'].unique())
    selected_state = st.sidebar.multiselect(
        "Select State(s)",
        states,
        default=states[:3]
    )
    
    # Restaurant chain filter
    chains = sorted(df['name'].unique())
    selected_chains = st.sidebar.multiselect(
        "Select Restaurant Chains",
        chains,
        default=[]
    )
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📍 Location Density", "🥤 Restaurant Categories", "📊 State Analysis"])
    
    # Filter data based on selections
    filtered_df = df[df['province'].isin(selected_state)]
    if selected_chains:
        filtered_df = filtered_df[filtered_df['name'].isin(selected_chains)]
    
    with tab1:
        st.header("Fast Food Restaurant Locations")
        
        if not filtered_df.empty:
            with st.spinner('Creating map...'):
                m = create_density_map(filtered_df)
                folium_static(m)
            
            # Show density statistics
            st.subheader("Restaurant Density by State")
            density_df = filtered_df['province'].value_counts().reset_index()
            density_df.columns = ['State', 'Count']
            
            fig = px.bar(density_df, x='State', y='Count',
                        title='Number of Fast Food Restaurants by State')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Please select at least one state to view the map.")
    
    with tab2:
        if not filtered_df.empty:
            st.header("Restaurant Categories Analysis")
            
            # Process categories
            categories_df = filtered_df.explode('categories')
            category_counts = categories_df['categories'].value_counts()
            
            # Create pie chart
            fig = px.pie(values=category_counts.values,
                        names=category_counts.index,
                        title='Distribution of Restaurant Categories')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top categories table
            st.subheader("Top Categories")
            st.dataframe(category_counts.head(10))
        else:
            st.warning("Please select at least one state to view categories.")
    
    with tab3:
        if not filtered_df.empty:
            st.header("State-wise Analysis")
            
            selected_state_analysis = st.selectbox(
                "Select a state for detailed analysis",
                selected_state
            )
            
            state_df = df[df['province'] == selected_state_analysis]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Show top cities
                st.subheader(f"Top Cities in {selected_state_analysis}")
                city_counts = state_df['city'].value_counts().head(10)
                fig = px.bar(x=city_counts.index, y=city_counts.values,
                            title=f'Top 10 Cities with Most Fast Food Restaurants')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Show top restaurant chains
                st.subheader("Popular Restaurant Chains")
                chain_counts = state_df['name'].value_counts().head(10)
                fig = px.bar(x=chain_counts.index, y=chain_counts.values,
                            title='Top 10 Restaurant Chains')
                st.plotly_chart(fig, use_container_width=True)
                
            # Additional Analysis
            st.subheader("Restaurant Distribution Analysis")
            
            # Average restaurants per city
            avg_per_city = len(state_df) / len(state_df['city'].unique())
            st.metric("Average Restaurants per City", f"{avg_per_city:.2f}")
            
            # Most common categories in state
            st.subheader("Popular Categories in State")
            state_categories = state_df.explode('categories')['categories'].value_counts().head(5)
            st.bar_chart(state_categories)
            
        else:
            st.warning("Please select at least one state to view analysis.")

if __name__ == "__main__":
    main()
