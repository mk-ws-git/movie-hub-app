from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_movie = db.Table(
    "user_movie",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("movie_id", db.Integer, db.ForeignKey("movie.id"), primary_key=True),
)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    director = db.Column(db.String(50))
    actors = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    plot = db.Column(db.String(500), nullable=False)
    runtime = db.Column(db.Integer, nullable=True)
    imdb_rating = db.Column(db.Float, nullable=True)
    poster_url = db.Column(db.String(250), nullable=True)
    imdb_url = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)