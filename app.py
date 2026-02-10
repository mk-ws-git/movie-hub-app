import requests
from flask import Flask
from models import Movie
from data_manager import DataManager

OMDB_API_KEY = "YOUR_KEY"
dm = DataManager()

app = Flask(__name__)

def fetch_movie_from_omdb(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    Movie=(
        title=data["Title"],
        genre=data["Genre"],
        year=int(data["Year"]),
        director=data["Director"],
        actors = data["Actors"],
        country=data["Country"],
        plot=data["Plot"],
        runtime=data["Runtime"],
        imdb_rating = data["Rating"],
        poster_url=data("Poster"),
        imdb_id = data["imdbID"],
    }