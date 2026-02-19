import requests
import os

from models import db, Movie
from data_manager import DataManager
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

    # Parse movie data and create Movie instance
    runtime = 0
    if data.get("Runtime") and data["Runtime"] != "N/A":
        runtime = int(data["Runtime"].split()[0])

    rating = 0
    if data.get("imdbRating") and data["imdbRating"] != "N/A":
        rating = float(data["imdbRating"])

    imdb_id = data.get("imdbID") or ""
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else ""

    movie = Movie(
        title=data.get["Title", ""],
        genre=data.get["Genre", ""],
        year=int(data.get["Year"]) if data.get("Year", "").isdigit() else 0,
        director=data.get["Director", ""],
        actors = data.get["Actors", ""],
        country=data.get["Country", ""],
        plot=data.get["Plot", ""],
        runtime=runtime,
        imdb_rating=float(rating),
        poster_url=data.get("Poster", ""),
        imdb_url=imdb_url,
        imdb_id=imdb_id,
        user_id=0 # temporary - will set in create_movie()
    )

    return movie


# App Routes

@app.route("/")
def home():
    return "movie hub"

# List all users
@app.route('/users', methods=["GET"])
def list_users():
    users = data_manager.get_users()
    return str(users) # temporarily returning a string

# Create a user
@app.route("/users", methods=["POST"])
def add_user():
    name = request.form.get("name", "").strip()

    if not name:
        return "User name required", 400

    dm.create_user(name)
    return f"User '{name}' created"

# List movies for a user
@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id):
    movies = dm.get_movies(user_id)

    if not movies:
        return "No movies for this user."

    return "<br>".join([f"{m.id}: {m.title} ({m.year})" for m in movies])

# Add movie via OMDb
@app.route("/users/<int:user_id>/movies", methods=["POST"])
def create_movie(user_id):
    title = request.form.get("title", "").strip()

    if not title:
        return "Movie title required", 400

    movie = fetch_movie_from_omdb(title)

    if movie is None:
        return "Movie not found in OMDb", 404

    movie.user_id = user_id
    db.session.add(movie)
    db.session.commit()

    return f"Movie '{movie.title}' added to user {user_id}"



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)