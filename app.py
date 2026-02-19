import requests
import os

from models import db, User, Movie
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

    rating = 0.0
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
        imdb_rating=rating,
        poster_url=data.get("Poster", ""),
        imdb_url=imdb_url,
        imdb_id=imdb_id,
        user_id=0 # temporary - will set in create_movie()
    )

    return movie


# App Routes

@app.route('/')
def index():
    users = dm.get_users()
    return render_template('index.html', users=users)


# List all users
@app.route('/users', methods=["GET"])
def list_users():
    users = dm.get_users()

    if not users:
        return "No users yet."

    return "<br>".join([f"{u.id}: {u.name}" for u in users])


# Create a user
@app.route("/users", methods=["POST"])
def create_user():
    name = request.form.get("name", "").strip()

    if not name:
        return "User name required", 400

    dm.create_user(name)
    print(f"User '{name}' created")
    return redirect(url_for("index"))


# List movies for a user
@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id):
    user = User.query.get_or_404(user_id)
    movies = dm.get_movies(user_id)
    return render_template("movies.html", user=user, movies=movies)


# Add movie via OMDb
@app.route("/users/<int:user_id>/movies", methods=["POST"])
def create_movie(user_id):
    title = request.form.get("title", "").strip()

    if not title:
        return redirect(url_for("list_movies", user_id=user_id))

    movie = fetch_movie_from_omdb(title)

    if movie is None:
        return redirect(url_for("list_movies", user_id=user_id))

    movie.user_id = user_id
    db.session.add(movie)
    db.session.commit()

    print(f"Movie '{movie.title}' added to user {user_id}")
    return redirect(url_for("list_movies", user_id=user_id))


# Update movie title
@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id, movie_id):
    new_title = request.form.get("new_title", "").strip()
    if not new_title:
        return redirect(url_for("list_movies", user_id=user_id))

    dm.update_movie(movie_id, new_title)
    return redirect(url_for("list_movies", user_id=user_id))


# Delete movies for a user
@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id, movie_id):
    dm.delete_movie(movie_id)
    return redirect(url_for("list_movies", user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)