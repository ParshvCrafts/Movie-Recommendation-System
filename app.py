from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
import requests
import numpy as np
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# Load data once when app starts
try:
    movies_list = pickle.load(open('movies.pkl', 'rb'))
    # If movies_list is already a DataFrame, don't convert again
    if isinstance(movies_list, pd.DataFrame):
        movies_tag = movies_list
    else:
        movies_tag = pd.DataFrame(movies_list)
    movie_titles = movies_tag['title'].values
except FileNotFoundError:
    app.logger.error("File 'movies.pkl' not found.")
    movies_tag = pd.DataFrame()
    movie_titles = []

try:
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    app.logger.error("File 'similarity.pkl' not found.")
    similarity = np.array([])

def fetch_poster(movie_id):
    """Function to fetch movie poster from TMDB API"""
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US",
            timeout=5
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if data.get('poster_path'):
            return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        else:
            return "https://via.placeholder.com/500x750/333/fff?text=No+Poster"
    except Exception as e:
        app.logger.error(f"Error fetching poster for movie_id {movie_id}: {e}")
        return "https://via.placeholder.com/500x750/333/fff?text=No+Poster"

def recommend(movie, num_recommendations=6):
    """Function to get movie recommendations"""
    try:
        # Check if movie exists
        matches = movies_tag[movies_tag['title'] == movie]
        if matches.empty:
            app.logger.error(f"Movie '{movie}' not found in database.")
            return []
        
        movie_index = matches.index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num_recommendations+1]

        recommendations = []
        for i, score in movies_list:
            movie_id = movies_tag.iloc[i].movie_id
            # Ensure movie_id is integer
            if isinstance(movie_id, np.integer):
                movie_id = int(movie_id)
            poster_url = fetch_poster(movie_id)
            
            recommendations.append({
                'title': movies_tag.iloc[i].title,
                'similarity_score': float(score),  # Ensure it's a float
                'poster_url': poster_url,
                'movie_id': movie_id
            })
        return recommendations
    except Exception as e:
        app.logger.error(f"Error in recommend function: {e}")
        return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html', movies=movie_titles)

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    try:
        selected_movie = request.json.get('movie')
        if not selected_movie:
            return jsonify({'success': False, 'error': 'No movie selected'})
        
        recommendations = recommend(selected_movie, 6)
        return jsonify({
            'success': True,
            'selected_movie': selected_movie,
            'recommendations': recommendations
        })
    except Exception as e:
        app.logger.error(f"Error in get_recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)