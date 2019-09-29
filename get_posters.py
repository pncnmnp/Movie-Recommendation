import pandas as pd
from file_paths import *

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w185"

def get_poster_paths(movie_ids, movie_titles):
	df = pd.read_csv(PATH_POSTERS)
	paths = dict()
	index = 0
	for m_id in movie_ids:
		try:
			paths[movie_titles[index]] = POSTER_BASE_URL + df["poster_path"][df.index[df["id"] == str(m_id)][0]]
			index += 1
		except:
			paths[movie_titles[index]] = "https://image.tmdb.org/t/p/w185/rhIRbceoE9lR4veEXuwCC2wARtG.jpg"
			index += 1
	return paths