from recommendation import Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
from file_paths import *
from numpy import argsort
from ast import literal_eval
import sys

SCAN_SIZE = 30
ACTOR_LIMIT = 5
CREW = ['Director']
CREW_WT = 2
CAST_WT = 1

class ContentBased:
	def __init__(self):
		self.md_credits = pd.read_csv(PATH_CREDITS)

	def make_desc(self, df):
		df['tagline'] = df['tagline'].fillna('')
		df['overview'] = df['overview'] + df['tagline']
		df['overview'] = df['overview'].fillna('')

		return df

	def make_keywords(self, df):
		"""
        Based on crew and cast members, movie-keywords, genres
		"""
		stemmer = SnowballStemmer("english")
		df['keywords'] = df['keywords'].apply(literal_eval).apply(lambda keywords: [stemmer.stem(k['name']) for k in keywords] if isinstance(keywords, list) else list())
		df = df.merge(self.md_credits, on='id')
		df['cast'] = df['cast'].apply(literal_eval).apply(lambda actors: [actor['name'].lower().replace(" ", "") for actor in actors[:ACTOR_LIMIT]] if isinstance(actors, list) else list())
		df['crew'] = df['crew'].apply(literal_eval).apply(lambda crews: [crew['name'].lower().replace(" ", "") for crew in crews if crew['job'] in CREW] if isinstance(crews, list) else list())

		df['all_keys'] = df['keywords'] + df['cast']*CAST_WT + df['crew']*CREW_WT + df['genres']
		df['all_keys'] = df['all_keys'].apply(lambda keywords: ' '.join(keywords) if isinstance(keywords, list) else str())

		return df

	def tfidf(self, df):
		tfidf = TfidfVectorizer(analyzer='word' ,stop_words=stopwords.words('english'), ngram_range=(1,2))
		tfidf_mat = tfidf.fit_transform(df['overview'])
		cosine_sim = linear_kernel(tfidf_mat, tfidf_mat)
		return cosine_sim

	def countvectorize(self, df):
		count = CountVectorizer(analyzer='word', ngram_range=(1, 2), stop_words=stopwords.words('english'))
		count_matrix = count.fit_transform(df['all_keys'])
		cosine_sim = cosine_similarity(count_matrix, count_matrix)
		return cosine_sim

	def verify_title(self, df, title):
		try:
			return df.index[df['title'] == title][0]
		except:
			raise ValueError("No film : " + title + " found!")

	def recommend(self, title, limit, critics=False, full_search=False):
		rec = Recommendation()
		rec.filter_genres()
		title_index = self.verify_title(rec.md, title)

		if full_search:
			df = self.make_keywords(rec.md)
			rec_matrix = self.countvectorize(df)
		else:
			df = self.make_desc(rec.md)
			rec_matrix = self.tfidf(df)

		rec_movie = rec_matrix[title_index]
		ids = rec_movie.argsort()[::-1][1:SCAN_SIZE+1]

		if critics:
			return rec.top_movies(df.iloc[ids], percentile=0.50, limit=limit, offset=0)
		else:
			return df.iloc[ids[:limit]][['original_title', 'id', 'vote_average', 'vote_count', 'popularity', 'release_date']]

if __name__ == '__main__':
	rec = ContentBased()
	print(rec.recommend(sys.argv[1], 10, critics=False, full_search=True))
