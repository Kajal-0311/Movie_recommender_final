import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown

# --- CONFIGURATION ---
# IMPORTANT: These IDs point to your public Google Drive files.
# The script will download them automatically on Streamlit Cloud.
MOVIE_DICT_URL = "1rwsBSX9EBprfym13ckj3Ho4unVwSVLq0"
SIMILARITY_URL = "10SeawXBEqELSnTWHavR3JK10ip-ksEPY"
# ---------------------

def download_files_if_not_present():
    """Downloads the large .pkl files from Google Drive if they don't exist locally."""
    # Check for the main data file
    if not os.path.exists('movie_dict.pkl'):
        st.info("Downloading movie data (movie_dict.pkl) from Google Drive...")
        try:
            gdown.download(id=MOVIE_DICT_URL, output='movie_dict.pkl', quiet=False)
        except Exception as e:
            st.error(f"Failed to download movie_dict.pkl. Please check the Google Drive ID and sharing settings: {e}")
            return False

    # Check for the similarity matrix file
    if not os.path.exists('similarity.pkl'):
        st.info("Downloading similarity matrix (similarity.pkl) from Google Drive...")
        try:
            gdown.download(id=SIMILARITY_URL, output='similarity.pkl', quiet=False)
        except Exception as e:
            st.error(f"Failed to download similarity.pkl. Please check the Google Drive ID and sharing settings: {e}")
            return False

    return True

# Attempt to download files
if not download_files_if_not_present():
    # Stop the app if download fails
    st.stop()

def fetch_poster(movie_id):
    # Your TMDB API key is included here.
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=48ac9b216648016fcafa8c1e4d835356&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        # Return a valid placeholder URL if the path is missing
        return "https://via.placeholder.com/500x750?text=No+Image"
    except Exception as e:
        print(f"Error fetching poster for {movie_id}: {e}")
        return "https://via.placeholder.com/500x750?text=No+Image"

def recommend(movie):
    # Ensure the movie name exists before proceeding
    if movie not in movies['original_title'].values:
        return ["Movie not found"], ["https://via.placeholder.com/500x750?text=Error"]

    # This part loads the pickled data (now that we ensure they are downloaded)
    try:
        movie_index = movies[movies['original_title'] == movie].index[0]
    except IndexError:
        return ["Movie data error"], ["https://via.placeholder.com/500x750?text=Error"]

    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []
    for i in movies_list:
        # Fetch TMDB ID from the DataFrame
        movie_id = movies.iloc[i[0]].id
        recommended_movies.append(movies.iloc[i[0]].original_title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters

# --- Load Data after Download is Confirmed ---
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except Exception as e:
    st.error(f"Could not load data files even after download: {e}")
    st.stop()


# Add custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: white;
    }
    .stApp {
        background-color: #0e1117 !important;
    }
    .movie-title {
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        color: white;
    }
    img {
        border-radius: 10px;
        transition: transform 0.2s;
        margin-bottom: 15px;
    }
    img:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(255,255,255,0.3);
    }
    </style>
""", unsafe_allow_html=True)


st.markdown("<h1 style='text-align: center; color: #FFDD00;'>🎬 Movie Recommender System 🍿</h1>", unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    'Select a Movie to Get Recommendations:',
    movies['original_title'].values)

if st.button('Recommend'):
    with st.spinner('Generating recommendations...'):
        names,posters  = recommend(selected_movie_name)
        cols = st.columns(5)

        for col, name, poster in zip(cols, names, posters):
            with col:
                st.markdown(f"<div class='movie-title'>{name}</div>", unsafe_allow_html=True)
                # Use use_container_width for responsiveness (avoids deprecated warning)
                st.image(poster, use_container_width=True)
