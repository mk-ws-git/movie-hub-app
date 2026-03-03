import requests
import os
import logging

from models import db, User, Movie
from data_manager import DataManager
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# Log errors and exceptions
# Create logs/ directory if needed
os.makedirs("logs", exist_ok=True)

file_handler = RotatingFileHandler(
    "logs/moviehub.log",
    maxBytes=1_000_000,  # 1 MB
    backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s"
))

app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.info("MovieHub startup")

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

    # OMDB request with error handling
    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={"t": title, "apikey": OMDB_API_KEY},
            timeout=10,
    )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        app.logger.warning("OMDb request failed title=%r", title, exc_info=True)
        return None

    if data.get("Response") == "False":
        app.logger.info("OMDb not found title=%r error=%r", title, data.get("Error"))
        return None

    # Parse movie data and create Movie instance
    year_str = (data.get("Year") or "").strip()

    # OMDb sometimes returns "1997" or "1997–" (series), so extract the first 4 digits
    year = 0
    if len(year_str) >= 4 and year_str[:4].isdigit():
        year = int(year_str[:4])

    runtime = 0
    if data.get("Runtime") and data["Runtime"] != "N/A":
        runtime = int(data["Runtime"].split()[0])

    rating = 0.0
    if data.get("imdbRating") and data["imdbRating"] != "N/A":
        rating = float(data["imdbRating"])

    imdb_id = data.get("imdbID") or ""
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else ""

    movie = Movie(
        title=data.get("Title", ""),
        genre=data.get("Genre", ""),
        year=year,
        director = data.get("Director", ""),
        actors = data.get("Actors", ""),
        country = data.get("Country", ""),
        plot = data.get("Plot", ""),
        runtime=runtime,
        imdb_rating=rating,
        poster_url=data.get("Poster", ""),
        imdb_url=imdb_url,
        imdb_id=imdb_id,
        user_id=0
    )

    app.logger.info("OMDb fetched title=%r imdb_id=%s", data.get("Title"), imdb_id)
    return movie


# App Routes

@app.route('/')
def index():
    users = dm.get_users()
    return render_template('index.html', users=users)


""" APP ROUTES """

# Create a user
@app.route("/users", methods=["POST"])
def create_user():
    name = request.form.get("name", "").strip()

    if not name:
        app.logger.info("Create user failed: empty name")
        flash("User name is required.", "error")
        return redirect(url_for("index"))

    if dm.user_exists(name):
        app.logger.info("Create user failed: duplicate name=%r", name)
        flash("That user name already exists. Enter another user name.", "error")
        return redirect(url_for("index"))

    dm.create_user(name)
    app.logger.info("User created name=%r", name)
    flash(f"User '{name}' created.", "success")
    return redirect(url_for("index"))


# List movies for a user
@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id):
    user = User.query.get(user_id)
    if not user:
        app.logger.info("List movies: user not found user_id=%s", user_id)
        flash("User not found.", "error")
        return redirect(url_for("index"))

    movies = dm.get_movies(user_id)
    return render_template("movies.html", user=user, movies=movies)


# Add movie for a user via OMDb
@app.route("/users/<int:user_id>/movies", methods=["POST"])
def create_movie(user_id):
    user = User.query.get(user_id)
    if not user:
        app.logger.info("Add movie failed: user not found user_id=%s", user_id)
        flash("User not found.", "error")
        return redirect(url_for("index"))

    title = request.form.get("title", "").strip()
    if not title:
        app.logger.info("Add movie failed: empty title user_id=%s", user_id)
        flash("Movie title is required. Enter a movie title.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    movie = fetch_movie_from_omdb(title)
    if movie is None:
        app.logger.warning("Add movie failed: OMDb fetch failed user_id=%s title=%r", user_id, title)
        flash("Movie title not found or OMDB unavailable. Enter another title.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    if dm.movie_exists_for_user(user_id, movie.imdb_id):
        app.logger.info("Add movie skipped: duplicate user_id=%s imdb_id=%s title=%r", user_id, movie.imdb_id,
                        movie.title)
        flash("That movie is already in this user’s list.", "warning")
        return redirect(url_for("list_movies", user_id=user_id))

    movie.user_id = user_id

    try:
        dm.add_movie(movie)
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("DB error adding movie user_id=%s title=%r imdb_id=%s", user_id, title, movie.imdb_id)
        flash("Database error occurred while adding the movie.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    app.logger.info("Movie added user_id=%s movie_id=%s imdb_id=%s title=%r", user_id, movie.id, movie.imdb_id,
                    movie.title)
    flash(f"Added '{movie.title}'.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


# Update movie title
@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id, movie_id):
    user = User.query.get(user_id)
    if not user:
        app.logger.info("Update movie failed: user not found user_id=%s movie_id=%s", user_id, movie_id)
        flash("User not found.", "error")
        return redirect(url_for("index"))

    new_title = request.form.get("new_title", "").strip()
    if not new_title:
        app.logger.info("Update movie failed: empty new_title user_id=%s movie_id=%s", user_id, movie_id)
        flash("New title is required. Enter new movie title.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    movie = dm.get_movie_for_user(user_id, movie_id)
    if not movie:
        app.logger.info("Update movie failed: movie not found for user user_id=%s movie_id=%s", user_id, movie_id)
        flash("Movie not found for this user.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    try:
        dm.update_movie(movie_id, new_title)
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("DB error updating movie user_id=%s movie_id=%s new_title=%r", user_id, movie_id,
                             new_title)
        flash("Database error occurred while updating the movie.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    app.logger.info("Movie updated user_id=%s movie_id=%s new_title=%r", user_id, movie_id, new_title)
    flash("Movie title updated.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


# Delete movies for a user
@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id, movie_id):
    user = User.query.get(user_id)
    if not user:
        app.logger.info("Delete movie failed: user not found user_id=%s movie_id=%s", user_id, movie_id)
        flash("User not found.", "error")
        return redirect(url_for("index"))

    movie = dm.get_movie_for_user(user_id, movie_id)
    if not movie:
        app.logger.info("Delete movie failed: movie not found for user user_id=%s movie_id=%s", user_id, movie_id)
        flash("Movie not found for this user.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    try:
        ok = dm.delete_movie(movie_id)
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("DB error deleting movie user_id=%s movie_id=%s", user_id, movie_id)
        flash("Database error occurred while deleting movie.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    app.logger.info("Movie deleted user_id=%s movie_id=%s ok=%s", user_id, movie_id, ok)
    flash("Movie deleted." if ok else "Movie not found.", "success" if ok else "error")
    return redirect(url_for("list_movies", user_id=user_id))


# 404 handling
@app.errorhandler(404)
def page_not_found(e):
    app.logger.info("404 Not Found path=%s", request.path)
    return render_template("404.html"), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)