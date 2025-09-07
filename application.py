import streamlit as st
import pickle
import pandas as pd
import requests

def fetch_poster(movie_id):
    # Function to fetch movie poster from TMDB API
    response = requests.get("https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US".format(movie_id, "8265bd1679663a7ea12ac168da84d2e8"))
    data = response.json()
    return "https://image.tmdb.org/t/p/w500/" + data['poster_path'] if data.get('poster_path') else None

movies_list = pickle.load(open('movies.pkl', 'rb'))
movies_tag = pd.DataFrame(movies_list)
movie_titles = movies_tag['title'].values

st.title("Movie Recommendation System")
st.write("Welcome to the Movie Recommendation System! Enter a movie title to get recommendations.")

selected_movie = st.selectbox("Select a movie", movie_titles)

similarity = pickle.load(open('similarity.pkl', 'rb'))

def recommend(movie, num_recommendations=5):
    movie_index = movies_tag[movies_tag['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num_recommendations+1]

    recommendations = []
    recommendations_posters = []
    for i, score in movies_list:
        movie_id = movies_tag.iloc[i].movie_id
        # fetching movie posters from TMDB API
        recommendations_posters.append(fetch_poster(movie_id))
        
        recommendations.append({
            'title': movies_tag.iloc[i].title,
            'similarity_score': round(score, 3)
        })
    return recommendations, recommendations_posters

if st.button("Get Recommendations"):
    recommendations, posters = recommend(selected_movie, 5)
    col1, col2, col3, col4, col5 = st.columns(5)
    if recommendations:
        with col1:
            st.text(recommendations[0]['title'])
            st.image(f"{posters[0]}")
        with col2:
            st.text(recommendations[1]['title'])
            st.image(f"{posters[1]}")
        with col3:
            st.text(recommendations[2]['title'])
            st.image(f"{posters[2]}")
        with col4:
            st.text(recommendations[3]['title'])
            st.image(f"{posters[3]}")
        with col5:
            st.text(recommendations[4]['title'])
            st.image(f"{posters[4]}")
    
    else:
        st.write(f"No recommendations found for '{selected_movie}'")
        
        
# To run the app, streamlit run application.py