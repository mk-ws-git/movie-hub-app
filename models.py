from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Store user-related data."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)


class Movie(db.Model):
    """Store movie-related data."""
    __tablename__ = 'movie'
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
    imdb_id = db.Column(db.String(20), nullable=False, unique=True)

class UserMovie(db.Model):
    """Junction table: one row per (user, movie) pair.
    Holds all user-specific data about a movie."""
    __tablename__ = 'user_movie'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    movie_id      = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    watched       = db.Column(db.Boolean, default=False, nullable=False)
    want_to_watch = db.Column(db.Boolean, default=False, nullable=False)
    user_rating   = db.Column(db.Float, nullable=True)   # 0.0–10.0, user's own rating

    user = db.relationship('User', backref=db.backref('collection', cascade='all, delete-orphan'))
    movie = db.relationship('Movie', backref=db.backref('owners'))

    # Prevent same movie added twice per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='uq_user_movie'),
    )