from recommendation import Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
from file_paths import *
from numpy import argsort
from ast import literal_eval
from os.path import isfile
from difflib import get_close_matches
import sys

SCAN_SIZE = 30
ACTOR_LIMIT = 5
CREW = ["Director"]
CREW_WT = 2
CAST_WT = 1

class ContentBased:
	def __init__(self):
		self.md_credits = pd.read_csv(PATH_CREDITS)
		self.changed_title = str() # used in case Levenstein distance matches a value close to another string

	def make_desc(self, df):
		"""
            param: df - movies pandas DataFrame 

            return: pandas DataFrame with overview and tagline combined
		"""
		df["tagline"] = df["tagline"].fillna("")
		df["overview"] = df["overview"] + df["tagline"]
		df["overview"] = df["overview"].fillna("")

		return df

	def make_keywords(self, df):
		"""
            param: df - movies pandas DataFrame

            return: pandas DataFrame with attribute 'all_keys', 
                    which combines crew andcast members, movie-keywords, genres.
		"""
		stemmer = SnowballStemmer("english")
		df["keywords"] = (
			df["keywords"]
			.apply(literal_eval)
			.apply(
				lambda keywords: [stemmer.stem(k["name"]) for k in keywords]
				if isinstance(keywords, list)
				else list()
			)
		)
		df = df.merge(self.md_credits, on="id")
		df["cast"] = (
			df["cast"]
			.apply(literal_eval)
			.apply(
				lambda actors: [
					# To count actor name as one word like 'tomcruise'
					actor["name"].lower().replace(" ", "")
					for actor in actors[:ACTOR_LIMIT]
				]
				if isinstance(actors, list)
				else list()
			)
		)
		df["crew"] = (
			df["crew"]
			.apply(literal_eval)
			.apply(
				lambda crews: [
					# To count director name as one word like "stanleykubrick"
					crew["name"].lower().replace(" ", "")
					for crew in crews
					if crew["job"] in CREW
				]
				if isinstance(crews, list)
				else list()
			)
		)

		df["all_keys"] = (
			df["keywords"] + df["cast"] * CAST_WT + df["crew"] * CREW_WT + df["genres"]
		)
		df["all_keys"] = df["all_keys"].apply(
			lambda keywords: " ".join(keywords) if isinstance(keywords, list) else str()
		)

		return df

	def tfidf(self, df):
		"""
            param: df - movies pandas DataFrame

            return: cosine similarity matrix based on overview and description
		"""
		tfidf = TfidfVectorizer(
			analyzer="word", stop_words=stopwords.words("english"), ngram_range=(1, 2)
		)
		tfidf_mat = tfidf.fit_transform(df["overview"])
		cosine_sim = linear_kernel(tfidf_mat, tfidf_mat)
		return cosine_sim

	def countvectorize(self, df):
		"""
            param: df - movies pandas DataFrame

            return: cosine similarity matrix based on crew, cast, keywords and genre
		"""
		count = CountVectorizer(
			analyzer="word", ngram_range=(1, 2), stop_words=stopwords.words("english")
		)
		count_matrix = count.fit_transform(df["all_keys"])
		cosine_sim = cosine_similarity(count_matrix, count_matrix)
		return cosine_sim

	def verify_title(self, df, title):
		"""
            param: df - movies pandas DataFrame
                   title - movie title (as in TMDB dataset)

            return: if title found - returns index value of the title from df
                    else - raises ValueError
		"""
		try:
			return df.index[df["title"] == title][0]
		except:
			try:
				title = (get_close_matches(title, [movie for movie in df["title"].tolist()])[0])
				self.changed_title = title
				return df.index[df["title"] == title][0]
			except:
				raise ValueError("No film : " + title + " found!")

	def recommend(
		self, title, limit, critics=False, full_search=False, use_pickle=True, keywords_and_desc=False
	):
		"""
            param: title - movie title (as in TMDB dataset)
                   limit - no. of movies to display
                   critics - True - will display critically acclaimed movies
                             False - will not sort movies on basis of their imdb rankings
                             (DEFAULT - False)
                   full_search - True - will search using cast, crew, keywords 
                                        and genre as metadata
                                 False - will search using overview and tagline 
                                         as metadata
                                 (DEFAULT - False)
                   use_pickle - True - will use pickled results
                                False - will compute the results from scratch
                                (DEFAULT - True)
                   keywords_and_desc - True - will merge results of keywords 
                                              and description
                                       False - will not merge results of keywords 
                                               and description

            return: pandas DataFrame object with attributes -
                    original_title, id, vote_average, vote_count, popularity, release_date
		"""
		rec = Recommendation()
		rec.filter_genres()
		title_index = self.verify_title(rec.md, title)

		if keywords_and_desc:
			if isfile(PATH_PICKLE_KEYWORDS) and isfile(PATH_PICKLE_DESC) and use_pickle:
				df_keywords = pd.read_pickle(PATH_PICKLE_KEYWORDS)
				df_desc = pd.read_pickle(PATH_PICKLE_DESC)
				rec_matrix_keywords = self.countvectorize(df_keywords)
				rec_matrix_desc = self.tfidf(df_desc)
				rec_matrix = rec_matrix_keywords + rec_matrix_desc
				df = df_keywords
		elif full_search:
			if isfile(PATH_PICKLE_KEYWORDS) and use_pickle:
				df = pd.read_pickle(PATH_PICKLE_KEYWORDS)
			else:
				df = self.make_keywords(rec.md)
				df.to_pickle(PATH_PICKLE_KEYWORDS)
			rec_matrix = self.countvectorize(df)
		else:
			if isfile(PATH_PICKLE_DESC) and use_pickle:
				df = pd.read_pickle(PATH_PICKLE_DESC)
			else:
				df = self.make_desc(rec.md)
				df.to_pickle(PATH_PICKLE_DESC)
			rec_matrix = self.tfidf(df)

		rec_movie = rec_matrix[title_index]
		ids = rec_movie.argsort()[::-1][1 : SCAN_SIZE + 1]

		if critics:
			return rec.top_movies(df.iloc[ids], percentile=0.50, limit=limit, offset=0)
		else:
			return df.iloc[ids[:limit]][
				[
					"original_title",
					"id",
					"vote_average",
					"vote_count",
					"popularity",
					"release_date",
				]
			]

if __name__ == "__main__":
	rec = ContentBased()
	print(
		rec.recommend(sys.argv[1], 14, critics=True, full_search=False, use_pickle=False, keywords_and_desc=False)
	)
