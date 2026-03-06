from models import db, User, Movie, UserMovie

class DataManager:

    # ── Users ──────────────────────────────────────────────

    def create_user(self, name: str) -> User:
        user = User(name=name)
        db.session.add(user)
        db.session.commit()
        return user

    def user_exists(self, name: str) -> bool:
        return User.query.filter_by(name=name).first() is not None


    def get_users(self):
        return User.query.all()

    def delete_user(self, user_id: int) -> bool:
        user = User.query.get(user_id)
        if not user:
            return False

        um_rows = UserMovie.query.filter_by(user_id=user_id).all()
        movie_ids = [um.movie_id for um in um_rows]

        db.session.delete(user)
        db.session.flush()

        # Delete related movies
        for movie_id in movie_ids:
            still_used = UserMovie.query.filter_by(movie_id=movie_id).first()
            if not still_used:
                movie = Movie.query.get(movie_id)
                if movie:
                    db.session.delete(movie)

        db.session.commit()
        return True


    # ── Movies ─────────────────────────────────────────────

    def get_movies(self, user_id: int) -> list[Movie]:
        """Return all Movie objects in a user's collection."""
        return (
            Movie.query
            .join(UserMovie, Movie.id == UserMovie.movie_id)
            .filter(UserMovie.user_id == user_id)
            .all()
        )

    def get_user_movie(self, user_id: int, movie_id: int) -> UserMovie | None:
        """Return the UserMovie junction row """
        return UserMovie.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()

    def add_movie(self, movie_data: Movie, user_id: int) -> Movie:
        """Add a movie to the shared table and link to user."""
        existing = Movie.query.filter_by(imdb_id=movie_data.imdb_id).first()
        if existing:
            movie = existing
        else:
            db.session.add(movie_data)
            db.session.flush()  # get movie.id without full commit
            movie = movie_data

        link = UserMovie(user_id=user_id, movie_id=movie.id)
        db.session.add(link)
        db.session.add(movie)
        db.session.commit()
        return movie


    def movie_exists_for_user(self, user_id: int, imdb_id: str) -> bool:
        return (
                UserMovie.query
                .join(Movie, Movie.id == UserMovie.movie_id)
                .filter(UserMovie.user_id == user_id, Movie.imdb_id == imdb_id)
                .first() is not None
        )


    def get_movie(self, movie_id: int) -> Movie | None:
        return Movie.query.get(movie_id)

    def get_movie_for_user(self, user_id: int, movie_id: int) -> Movie | None:
        """Return the movie only if it belongs to this user."""
        return (
            Movie.query
            .join(UserMovie, Movie.id == UserMovie.movie_id)
            .filter(UserMovie.user_id == user_id, Movie.id == movie_id)
            .first()
        )

    def update_movie(self, movie_id: int, new_title: str) -> Movie | None:
        """Update the movie only if it belongs to this user."""
        movie = Movie.query.get(movie_id)
        if not movie:
            return None
        movie.title = new_title
        db.session.commit()
        return movie


    def delete_movie(self, movie_id: int) -> bool:
        """Remove movie from user's collection.
                Deletes the shared Movie row only if no other users own it."""
        link = UserMovie.query.filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()
        if not link:
            return False

        db.session.delete(link)
        db.session.flush()

        # Clean movies with no user
        still_used = UserMovie.query.filter_by(movie_id=movie_id).first()
        if not still_used:
            movie = Movie.query.get(movie_id)
            if movie:
                db.session.delete(movie)

        db.session.commit()
        return True


    # ── User-specific movie stats ────────────────────────────

    def set_watched(self, user_id: int, movie_id: int, watched: bool) -> bool:
        link = self.get_user_movie(user_id, movie_id)
        if not link:
            return False
        link.watched = watched
        db.session.commit()
        return True

    def set_want_to_watch(self, user_id: int, movie_id: int, want: bool) -> bool:
        link = self.get_user_movie(user_id, movie_id)
        if not link:
            return False
        link.want_to_watch = want
        db.session.commit()
        return True

    def set_user_rating(self, user_id: int, movie_id: int, rating: float | None) -> bool:
        link = self.get_user_movie(user_id, movie_id)
        if not link:
            return False
        link.user_rating = rating
        db.session.commit()
        return True