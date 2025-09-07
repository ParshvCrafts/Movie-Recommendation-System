from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
import requests
import numpy as np
import logging
import os

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

def ensure_models_exist():
    """Download models if they don't exist"""
    models_exist = os.path.exists('movies.pkl') and os.path.exists('similarity.pkl')
    
    if not models_exist:
        app.logger.info("Model files not found. Attempting to download...")
        try:
            from download_models import download_models
            download_models()
            app.logger.info("Models downloaded successfully")
        except ImportError:
            app.logger.error("download_models.py not found. Please ensure model files are available.")
            return False
        except Exception as e:
            app.logger.error(f"Error downloading models: {e}")
            return False
    
    return True

def load_models():
    """Load the model files with error handling"""
    global movies_tag, movie_titles, similarity
    
    # Ensure models are available
    if not ensure_models_exist():
        app.logger.error("Cannot proceed without model files")
        movies_tag = pd.DataFrame()
        movie_titles = []
        similarity = np.array([])
        return False
    
    # Load movies data
    try:
        app.logger.info("Loading movies.pkl...")
        movies_list = pickle.load(open('movies.pkl', 'rb'))
        
        # If movies_list is already a DataFrame, don't convert again
        if isinstance(movies_list, pd.DataFrame):
            movies_tag = movies_list
        else:
            movies_tag = pd.DataFrame(movies_list)
        
        movie_titles = movies_tag['title'].values
        app.logger.info(f"Loaded {len(movie_titles)} movies")
        
    except FileNotFoundError:
        app.logger.error("File 'movies.pkl' not found after download attempt.")
        movies_tag = pd.DataFrame()
        movie_titles = []
        return False
    except Exception as e:
        app.logger.error(f"Error loading movies.pkl: {e}")
        movies_tag = pd.DataFrame()
        movie_titles = []
        return False

    # Load similarity matrix
    try:
        app.logger.info("Loading similarity.pkl...")
        similarity = pickle.load(open('similarity.pkl', 'rb'))
        app.logger.info(f"Loaded similarity matrix with shape: {similarity.shape}")
        
    except FileNotFoundError:
        app.logger.error("File 'similarity.pkl' not found after download attempt.")
        similarity = np.array([])
        return False
    except Exception as e:
        app.logger.error(f"Error loading similarity.pkl: {e}")
        similarity = np.array([])
        return False
    
    return True

# Initialize global variables
movies_tag = pd.DataFrame()
movie_titles = []
similarity = np.array([])

# Load models when app starts
app.logger.info("Initializing application and loading models...")
models_loaded = load_models()

if not models_loaded:
    app.logger.warning("Application started without models. Some features may not work.")

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
        # Check if models are loaded
        if movies_tag.empty or similarity.size == 0:
            app.logger.error("Models not loaded. Cannot provide recommendations.")
            return []
        
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
            try:
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
            except Exception as e:
                app.logger.error(f"Error processing recommendation {i}: {e}")
                continue
                
        return recommendations
    except Exception as e:
        app.logger.error(f"Error in recommend function: {e}")
        return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/recommendations')
def recommendations_page():
    # Check if models are loaded
    if len(movie_titles) == 0:
        app.logger.warning("No movies available. Attempting to reload models...")
        load_models()
    
    return render_template('recommendations.html', movies=movie_titles)

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    try:
        # Check if models are loaded
        if movies_tag.empty or similarity.size == 0:
            return jsonify({
                'success': False, 
                'error': 'Movie recommendation system is not ready. Please try again later.'
            })
        
        selected_movie = request.json.get('movie')
        if not selected_movie:
            return jsonify({'success': False, 'error': 'No movie selected'})
        
        recommendations = recommend(selected_movie, 6)
        
        if not recommendations:
            return jsonify({
                'success': False, 
                'error': f'No recommendations found for "{selected_movie}". Please try another movie.'
            })
        
        return jsonify({
            'success': True,
            'selected_movie': selected_movie,
            'recommendations': recommendations
        })
    except Exception as e:
        app.logger.error(f"Error in get_recommendations: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred. Please try again.'})

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    status = {
        'status': 'healthy',
        'models_loaded': not movies_tag.empty and similarity.size > 0,
        'movies_count': len(movie_titles),
        'similarity_shape': str(similarity.shape) if similarity.size > 0 else 'Not loaded'
    }
    return jsonify(status)

@app.route('/reload_models')
def reload_models():
    """Endpoint to manually reload models (useful for debugging)"""
    try:
        success = load_models()
        if success:
            return jsonify({
                'success': True, 
                'message': 'Models reloaded successfully',
                'movies_count': len(movie_titles)
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to reload models'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error reloading models: {e}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
