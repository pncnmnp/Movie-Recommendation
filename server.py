from flask import Flask, render_template, request
import pandas as pd
from get_posters import get_poster_paths
from content_based import ContentBased
app = Flask(__name__, template_folder="./flask/templates/")

DEFAULT_LIMIT = 10

@app.route('/', methods=["GET"])
def home():
	if "recommend" in request.args:
		title = request.args["recommend"]
		rec = ContentBased()
		df = rec.recommend(title, DEFAULT_LIMIT, full_search=True, keywords_and_desc=True)
		poster_paths = get_poster_paths(df["id"].tolist(), df["original_title"].tolist())
		return render_template('recommendations.html', titles=df["original_title"].tolist(), images=poster_paths)
	else:
		return render_template('homepage.html')