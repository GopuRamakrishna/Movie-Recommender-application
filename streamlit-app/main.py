import streamlit as st
import pandas as pd
import pickle
import gdown
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Movie Recommender", layout="centered")

# --- File URLs and Paths ---
SIMILARITY_FILE_ID = '1K1DiMIqZ7CNlzH6EgYcU0i_O1epsvTn0'  
SIMILARITY_URL = f'https://drive.google.com/uc?id={SIMILARITY_FILE_ID}'
SIMILARITY_PATH = 'similarity.pkl'
MOVIES_PATH = 'movies.pkl'

# --- Load similarity.pkl from Google Drive ---
@st.cache_data
def load_similarity_model():
    if not os.path.exists(SIMILARITY_PATH):
        gdown.download(SIMILARITY_URL, SIMILARITY_PATH, quiet=False)
    with open(SIMILARITY_PATH, 'rb') as f:
        return pickle.load(f)

similarity = load_similarity_model()

# --- Load movies.pkl (must be local) ---
if not os.path.exists(MOVIES_PATH):
    st.error("Missing 'movies.pkl'. Please make sure it's in the app directory.")
    st.stop()

with open(MOVIES_PATH, 'rb') as f:
    movies_dict = pickle.load(f)

movies = pd.DataFrame(movies_dict)

# --- Function to fetch poster from TMDB ---
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('TMDB_API_TOKEN')}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None

# --- Recommend Function ---
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_titles = []
    recommended_posters = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id  # Ensure movie_id exists in your movies.pkl
        recommended_titles.append(movies.iloc[i[0]].title)
        poster_url = fetch_poster(movie_id)
        recommended_posters.append(poster_url)

    return recommended_titles, recommended_posters

# --- Streamlit App Layout ---
st.title("🎬 Movie Recommender System")
st.markdown("Select a movie below and get 5 similar suggestions with posters!")

selected_movie = st.selectbox("Choose a movie:", movies['title'].values)

if st.button("Recommend"):
    with st.spinner("Fetching recommendations..."):
        names, posters = recommend(selected_movie)

    st.success(f"Top 5 movies similar to **{selected_movie}**:")
    cols = st.columns(5)
    for idx, (name, poster) in enumerate(zip(names, posters)):
        with cols[idx]:
            st.image(poster,width=200)
            st.caption(name)
