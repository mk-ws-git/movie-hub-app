from models import db, User, Movie

class DataManager:

    def create_user(self, name: str) -> User:
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    def user_exists(self, name: str) -> bool:
        return User.query.filter_by(name=name).first() is not None


    def get_users(self):
        return User.query.all()


    def get_movies(self, user_id: int):
        return Movie.query.filter_by(user_id=user_id).all()


    def add_movie(self, movie: Movie) -> Movie:
        db.session.add(movie)
        db.session.commit()
        return movie


    def movie_exists_for_user(self, user_id: int, imdb_id: str) -> bool:
        return Movie.query.filter_by(user_id=user_id, imdb_id=imdb_id).first() is not None


    def get_movie(self, movie_id: int) -> Movie | None:
        return Movie.query.get(movie_id)

    def get_movie_for_user(self, user_id: int, movie_id: int) -> Movie | None:
        return Movie.query.filter_by(id=movie_id, user_id=user_id).first()

    def update_movie(self, movie_id: int, new_title: str) -> Movie | None:
        movie = Movie.query.get(movie_id)
        if not movie:
            return None
        movie.title = new_title
        db.session.commit()
        return movie


    def delete_movie(self, movie_id: int) -> bool:
        movie = Movie.query.get(movie_id)
        if not movie:
            return False

        db.session.delete(movie)
        db.session.commit()
        return True