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

    # Search box with dynamic suggestions
    if search_type == "Book Title":
        user_input = st.sidebar.text_input("Search for a book:", key="book_search")
        filtered_titles = data['title'][data['title'].str.contains(user_input, case=False, na=False)].unique()
        st.sidebar.write("Suggestions:")
        for title in filtered_titles[:5]:  # Show up to 5 suggestions
            if st.sidebar.button(title):
                user_input = title  # Update input with clicked suggestion
        by = 'title'
    else:
        user_input = st.sidebar.text_input("Search for an author:", key="author_search")
        filtered_authors = data['authors'][data['authors'].str.contains(user_input, case=False, na=False)].unique()
        st.sidebar.write("Suggestions:")
        for author in filtered_authors[:5]:  # Show up to 5 suggestions
            if st.sidebar.button(author):
                user_input = author  # Update input with clicked suggestion
        by = 'author'

    n_recommendations = st.sidebar.slider(
        "Number of recommendations:",
        min_value=1,
        max_value=10,
        value=5
    )

    # Get recommendations
    if user_input and st.sidebar.button("Get Recommendations"):
        recommendations = recommender.recommend_books(user_input, by, n_recommendations)
        
        if recommendations:
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
        else:
            st.warning("No recommendations found for your query. Please try a different search.")
