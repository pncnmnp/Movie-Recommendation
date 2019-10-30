import pandas as pd
from file_paths import *

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
POSTER_BASE_URL_SMALL = "https://image.tmdb.org/t/p/w185"
def get_poster_paths(movie_ids, movie_titles, small=False):
	df = pd.read_csv(PATH_POSTERS)
	paths = dict()
	index = 0
	for m_id in movie_ids:
		try:
			if small:
				paths[movie_titles[index]] = POSTER_BASE_URL_SMALL + df["poster_path"][df.index[df["id"] == str(m_id)][0]]
			else:
				paths[movie_titles[index]] = POSTER_BASE_URL + df["poster_path"][df.index[df["id"] == str(m_id)][0]]
			index += 1
		except:
			if small:
				paths[movie_titles[index]] = "https://upload.wikimedia.org/wikipedia/commons/6/64/Poster_not_available.jpg"
			else:
				paths[movie_titles[index]] = "https://upload.wikimedia.org/wikipedia/commons/6/64/Poster_not_available.jpg"
			index += 1
	return paths