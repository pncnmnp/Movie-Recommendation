from flask import Flask, render_template, request, redirect, abort
import pandas as pd
from get_posters import get_poster_paths
from content_based import ContentBased
from file_paths import *
from recommendation import Recommendation
from ast import literal_eval

app = Flask(__name__, template_folder="./flask/templates/", static_folder="./flask/static/")

DEFAULT_LIMIT = 14
IMDB_ID_LEN = 7

def get_meta(title, m_id):
	rec = Recommendation()
	rec.filter_genres()
	rec.filter_productions()
	df_movies = rec.md
	df_credits = pd.read_csv(PATH_CREDITS)
	df_imdb_link = pd.read_csv(PATH_MOVIELENS_TO_TMDB)
	attributes = ["id", "original_title", "genres", "homepage", 
					"overview", "release_date", "production_companies", 
					"runtime", "tagline", "vote_average", "vote_count"]

	df_title = df_movies.iloc[df_movies.index[
								df_movies["original_title"] == title][0]][attributes]
	df_crew = df_credits.iloc[df_credits.index[df_credits["title"] == title][0]][["cast", "crew"]]
	cast = [cast["name"] for cast in literal_eval(df_crew["cast"])[0:5]]
	crew = [crew["name"] for crew in literal_eval(df_crew["crew"]) if crew["job"] in ["Director"]]
	try:
		imdb_link = str(df_imdb_link.iloc[df_imdb_link.index[df_imdb_link["tmdbId"] == int(m_id)][0]]["imdbId"])[:-2]
		imdb_link = ("https://www.imdb.com/title/tt" + "0"*(IMDB_ID_LEN - len(imdb_link)) + imdb_link)
	except:
		imdb_link = "https://www.imdb.com/search/title/?title=" + title

	return df_title, cast, crew, imdb_link

@app.route('/', methods=["GET"])
def home():
	if "recommend" in request.args:
		title = request.args["recommend"]
		rec = ContentBased()
		did_you_mean = False
		df = rec.recommend(title, DEFAULT_LIMIT, full_search=True, keywords_and_desc=False, critics=False)
		poster_paths = get_poster_paths(df["id"].tolist(), df["original_title"].tolist())
		if rec.changed_title != title:
			did_you_mean = True

		return render_template('recommendations.html', 
								titles=df["original_title"].tolist(), 
								images=poster_paths, 
								votes=df["vote_average"].tolist(), 
								m_id=df["id"].tolist(),
								rec_title=rec.changed_title,
								did_you_mean=did_you_mean)
	else:
		return render_template('homepage.html')

@app.route('/movie', methods=["GET"])
def movie_meta():
	if "title" in request.args:
		title = request.args["title"]
		m_id = request.args["id"]
		df_meta = get_meta(title, m_id)
		poster_path = get_poster_paths([int(m_id)], [title])[title]

		rec = ContentBased()
		df_rec = rec.recommend(title, 5, full_search=True, keywords_and_desc=False, critics=False)
		rec_poster_paths = get_poster_paths(df_rec["id"].tolist(), df_rec["original_title"].tolist(), small=True)

		return render_template('meta.html',
								title=df_meta[0]["original_title"],
								genres=df_meta[0]["genres"],
								homepage=df_meta[0]["homepage"],
								overview=df_meta[0]["overview"],
								release=df_meta[0]["release_date"],
								production=df_meta[0]["production_companies"],
								runtime=df_meta[0]["runtime"],
								tagline=df_meta[0]["tagline"],
								vote_average=df_meta[0]["vote_average"],
								vote_count=df_meta[0]["vote_count"],
								cast=df_meta[1],
								director=df_meta[2],
								poster_path=poster_path,
								rec_posters=rec_poster_paths,
								rec_titles=df_rec["original_title"].tolist(),
								rec_m_ids=df_rec["id"].tolist(),
								imdb_id=df_meta[3])
	else:
		abort(404)

@app.after_request
def apply_caching(response):
	response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
	response.headers['X-Content-Type-Options'] = 'nosniff'
	response.headers['X-Frame-Options'] = 'SAMEORIGIN'
	response.headers['X-XSS-Protection'] = '1; mode=block'
	return response
