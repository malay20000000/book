import streamlit as st
import pandas as pd
from difflib import SequenceMatcher
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="📚 Book Buddy - Your Personal Book Recommender",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white; /* Button text color */
    }
    .recommendation-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin: 1rem 0;
        border-left: 5px solid #FF4B4B;
        color : black;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color:black;
    }
    h1 {
        color: #FF4B4B;
    }
    h3, h2, h4 {
        color: black;
    }
    h6 {
        color: black;
    }
    
    /* Style for the subtitle */
    .subtitle {
        color: white; /* Change subtitle color to white */
        font-size: 16px;
        background-color: #FF4B4B;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

class BookRecommender:
    def _init_(self, data):
        self.df = pd.DataFrame(data)
        self.df['title'] = self.df['title'].str.strip()
        self.df['authors'] = self.df['authors'].str.strip()
        self.df['clean_title'] = self.df['title'].str.replace(r'\(.*\)', '').str.strip()
        
        # Convert publication_date to datetime
        self.df['publication_date'] = pd.to_datetime(self.df['publication_date'], errors='coerce')

        # Handle missing values in the dataframe
        self.df = self.df.dropna(subset=['title', 'authors', 'average_rating'])

    def get_title_similarity(self, title1, title2):
        return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    
    def get_author_similarity(self, author1, author2):
        authors1 = set(author1.lower().replace('/', ',').split(','))
        authors2 = set(author2.lower().replace('/', ',').split(','))
        intersection = len(authors1.intersection(authors2))
        union = len(authors1.union(authors2))
        return intersection / union if union > 0 else 0

    def recommend_books(self, query, by='title', n_recommendations=5):
        similarities = []
        
        if by == 'title':
            for idx, row in self.df.iterrows():
                similarity = self.get_title_similarity(query, row['clean_title'])
                if similarity < 1.0:  # Exclude exact matches
                    similarities.append(self._create_recommendation_dict(row, similarity))
        
        elif by == 'author':
            for idx, row in self.df.iterrows():
                similarity = self.get_author_similarity(query, row['authors'])
                similarities.append(self._create_recommendation_dict(row, similarity))
        
        return sorted(similarities, 
                     key=lambda x: (x['similarity'], x['average_rating']), 
                     reverse=True)[:n_recommendations]
    
    def _create_recommendation_dict(self, row, similarity):
        recommendation = {
            'bookID': row['bookID'],
            'title': row['title'],
            'authors': row['authors'],
            'similarity': similarity,
            'average_rating': row['average_rating'],
            'publication_date': row['publication_date'],
            'ratings_count': row['ratings_count']
        }
        
        # Check if 'num_pages' column exists
        if 'num_pages' in row:
            recommendation['num_pages'] = row['num_pages']
        else:
            recommendation['num_pages'] = 'N/A'  # Use 'N/A' or a default value
        
        return recommendation

# Load data from CSV file with error handling for malformed rows
@st.cache_data
def load_data():
    try:
        # Read CSV with error handling for rows with mismatched columns
        data = pd.read_csv("books.csv", on_bad_lines='skip')  # Skip bad lines
        # Clean the data
        data['title'] = data['title'].str.strip()  # Ensure 'title' column exists
        data['authors'] = data['authors'].str.strip()  # Ensure 'authors' column exists
        data['publication_date'] = pd.to_datetime(data['publication_date'], errors='coerce')
        data = data.dropna(subset=['title', 'authors', 'average_rating'])  # Remove rows with missing key columns
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    st.title("📚 Book Buddy - Your Personal Book Recommender")
    st.markdown("#### Discover your next favorite read!")

    # Load data
    data = load_data()
    
    if data.empty:
        st.error("No data available to display. Please check the CSV file.")
        return

    recommender = BookRecommender(data)

    # Sidebar
    st.sidebar.header("Recommendation Settings")

    # Search type selection
    search_type = st.sidebar.radio(
        "Search by:",
        ["Book Title", "Author"],
        key="search_type"
    )

    # Dynamic dropdown based on search type
    if search_type == "Book Title":
        query = st.sidebar.selectbox(
            "Select a book:",
            options=data['title'].unique(),
            key="book_dropdown"
        )
        by = 'title'
    else:
        query = st.sidebar.selectbox(
            "Select an author:",
            options=data['authors'].unique(),
            key="author_dropdown"
        )
        by = 'author'

    n_recommendations = st.sidebar.slider(
        "Number of recommendations:",
        min_value=1,
        max_value=10,
        value=5
    )

    # Get recommendations
    if st.sidebar.button("Get Recommendations"):
        recommendations = recommender.recommend_books(query, by, n_recommendations)
        
        # Display recommendations in a grid
        for i, book in enumerate(recommendations, 1):
            with st.container():
                st.markdown(f"""
                <div class="recommendation-card">
                    <h3>{i}. {book['title']}</h3>
                    <p><strong>Author(s):</strong> {book['authors']}</p>
                    <p><strong>Similarity Score:</strong> {book['similarity']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

                # Create three columns for metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Rating</h4>
                        <h2>⭐ {book['average_rating']:.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Pages</h4>
                        <h2>📄 {book['num_pages']}</h2>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Reviews</h4>
                        <h2>📊 {book['ratings_count']:,}</h2>
                    </div>
                    """, unsafe_allow_html=True)

        # Visualization section
        st.subheader("📊 Visualization")

        # Create rating distribution plot
        fig_ratings = px.bar(
            pd.DataFrame(recommendations),
            x='title',
            y='average_rating',
            title='Ratings Comparison',
            labels={'title': 'Book Title', 'average_rating': 'Average Rating'},
            color='average_rating',
            color_continuous_scale='reds'
        )
        fig_ratings.update_layout(showlegend=False)
        st.plotly_chart(fig_ratings, use_container_width=True)

if _name_ == "_main_":
    main()
