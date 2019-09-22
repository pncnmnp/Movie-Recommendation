from recommendation import Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from nltk.corpus import stopwords
import pandas as pd
from variables import *
from numpy import argsort

SCAN_SIZE = 30

class ContentBased:
	def __init__(self):
		pass

	def make_desc(self, df):
		df['tagline'] = df['tagline'].fillna('')
		df['overview'] = df['overview'] + df['tagline']
		df['overview'] = df['overview'].fillna('')
		return df

	def tfidf(self, df):
		tfidf = TfidfVectorizer(analyzer='word' ,stop_words=stopwords.words('english'), ngram_range=(1,3))
		tfidf_mat = tfidf.fit_transform(df['overview'])
		cosine_sim = linear_kernel(tfidf_mat, tfidf_mat)
		return cosine_sim

	def recommend(self, title, limit, critics=False):
		rec = Recommendation()
		rec.filter_genres()
		df = rec.md

		df = self.make_desc(df)
		rec_matrix = self.tfidf(df)

		title_index = df.index[df['title'] == title][0]
		rec_movie = rec_matrix[title_index]
		ids = rec_movie.argsort()[::-1][1:SCAN_SIZE+1]

		if critics:
			return rec.top_movies(df.iloc[ids], percentile=0.50, limit=limit, offset=0)
		else:
			return df.iloc[ids[:limit]][['title', 'id', 'vote_average', 'vote_count', 'popularity', 'release_date']]

if __name__ == '__main__':
	rec = ContentBased()
	print(rec.recommend('Iron Man', 10, critics=False))
