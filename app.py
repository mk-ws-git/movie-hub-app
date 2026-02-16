import requests
import os

from flask import Flask
from models import db, Movie
from data_manager import DataManager
from omdb import fetch_movie_from_omdb
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and data manager
db.init_app(app)

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

dm = DataManager()


def fetch_movie_from_omdb(title: str) -> Movie | None:
    if not OMDB_API_KEY:
        raise RuntimeError("OMDB_API_KEY environment variable is not set.")
    response = requests.get(
        "https://www.omdbapi.com/",
        params={"t": title, "apikey": OMDB_API_KEY},
        timeout=10,
    )
    data = response.json()

    if data.get("Response") == "False":
        return None

    movie= Movie(
        title=data["Title"],
        genre=data["Genre"],
        year=int(data["Year"]),
        director=data["Director"],
        actors = data["Actors"],
        country=data["Country"],
        plot=data["Plot"],
        runtime=data["Runtime"],
        imdb_rating = float(data["Rating"]) if data.get("imdbRating") != "N/A" else None,
        poster_url=data("Poster"),
        imdb_id = data["imdbID"],
    )
    return movie


# App Routes
@app.route('/')
def home():
    return "movie hub"

@app.route('/users', methods=['POST'])
def get_users():
    users = dm.get_users()
    return str(users)  # Temporarily returning users as a string

@app.route('/users/<int:user_id>/movies', methods=['GET'])
def list_movies(user_id):
    movies = dm.get_movies(user_id)
    return str(movies) # Temporarily returning movies as a string


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def create_movie(user_id):



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)