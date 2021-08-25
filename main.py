from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

# ---------------------------------- VARIABLES USED FOR API CALL -----------------------------------------

MOVIE_API_KEY = ""  # CREATE A FREE ACCOUNT ON THE MOVIE DB AND GET YOUR API KEY TO FILL THIS.
MOVIE_BASE_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# ----------------------------- APP INITIALISATION AND CONFIGURATION---------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = ''  # CREATE A RANDOM SECRET KEY FOR YOUR FLASK APPLICATION
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -------------------------------- CLASS DEFINITIONS FOR YOUR MOVIE LIBRARY-----------------------------------

class MovieDetails(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(200))
    image_url = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        movie = {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'description': self.description,
            'rating': self.rating,
            'ranking': self.ranking,
            'review': self.review,
            'image_url': self.image_url
        }
        return movie


db.create_all()  # THIS ONLY EXECUTES ONE TIME WHEN DB NEEDS TO BE CREATED AND CAN BE COMMENTED LATER.


class MyForm(FlaskForm):
    new_rating = FloatField('Your Rating (out of 10)', validators=[DataRequired()])
    new_review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Change Rating', validators=[DataRequired()])


class AddMovie(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie', validators=[DataRequired()])


# -----------------------------------------APPLICATION ROUTES---------------------------------------------
@app.route("/")
def home():
    all_movies = MovieDetails.query.order_by(MovieDetails.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:movie_id>", methods=['POST', 'GET'])
def edit(movie_id):
    form = MyForm()
    movie_to_edit = MovieDetails.query.get(movie_id)
    if form.validate_on_submit():
        rating = form.new_rating.data
        review = form.new_review.data
        movie_to_edit.rating = rating
        movie_to_edit.review = review
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('edit.html', form=form, movie=movie_to_edit)


@app.route("/<int:movie_id>")
def delete(movie_id):
    movie_to_delete = MovieDetails.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    add_movie_form = AddMovie()
    if add_movie_form.validate_on_submit():
        movie_title = add_movie_form.movie_title.data

        parameters = {
            'api_key': MOVIE_API_KEY,
            'query': movie_title
        }

        response = requests.get(MOVIE_BASE_URL, params=parameters)
        response.raise_for_status()
        movie_data = response.json()['results']

        return render_template('select.html', movie_list=movie_data)

    return render_template('add.html', form=add_movie_form)


@app.route('/find')
def find_movie():
    movie_id = request.args.get('movie_id')
    movie_detail_base_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    detail_params = {
        'api_key': MOVIE_API_KEY
    }
    response_detail = requests.get(movie_detail_base_url, params=detail_params)
    response_detail.raise_for_status()
    data = response_detail.json()
    new_movie = MovieDetails(
        title=data["title"],
        # The data in release_date includes month and day, we will want to get rid of.
        year=data["release_date"].split("-")[0],
        image_url=f"{MOVIE_DB_IMAGE_URL}/{data['poster_path']}",
        description=data["overview"]
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
