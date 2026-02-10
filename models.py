from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_movie = db.Table(
    "user_movie",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("movie_id", db.Integer, db.ForeignKey("movie.id"), primary_key=True),
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    director = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    poster_url = db.Column(db.String(100), nullable=False)
    imdb_url = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)