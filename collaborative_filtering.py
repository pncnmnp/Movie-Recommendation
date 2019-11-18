from surprise import Reader, Dataset, KNNBaseline
import pandas as pd
from file_paths import *
from content_based import ContentBased
from numpy import array
from os.path import isfile
import joblib

DEFAULT_ID = 700
RATING_ATTR = ["userId", "movieId", "rating"]
LIMIT = 20

class CollaborativeFiltering:
	def __init__(self):
		self.df_credits = pd.read_csv(PATH_CREDITS)
		self.m_id_to_tmdb = pd.read_csv(PATH_MOVIELENS_TO_TMDB)
		self.df_movies = pd.read_csv(PATH_MOVIES)

	def get_tmdb_id(self, movieId):
		"""
            param: movieId - movieId of the movie (as seen in MovieLens dataset)

            return: tmdbId corresponding to the movieID
		"""
		try:
			return self.m_id_to_tmdb["tmdbId"][
				self.m_id_to_tmdb.index[self.m_id_to_tmdb["movieId"] == movieId][0]
			]
		except:
			pass

	def get_m_id(self, tmdbId):
		"""
            param: tmdbId - tmdbId of the movie (as seen in TMDB dataset)

            return: movieId corresponding to the tmdbId
		"""
		try:
			return self.m_id_to_tmdb["movieId"][
				self.m_id_to_tmdb.index[self.m_id_to_tmdb["tmdbId"] == tmdbId][0]
			]
		except:
			pass

	def get_title_index(self, title):
		"""
            param: title - movie title (as in TMDB dataset)


            return: if title found - returns index value of the title from df_credits
		"""
		try:
			return self.df_credits["id"][
				self.df_credits.index[self.df_credits["title"] == title][0]
			]
		except:
			raise ValueError("No film : " + title + " found!")

	def get_movie_title(self, m_id):
		"""
            param: m_id - index value (id) (corresponding to df_movies)

            return: movie title corresponding to m_id (as in df_movies)
		"""
		try:
			vals = self.df_movies.iloc[
				self.df_movies.index[self.df_movies["id"] == m_id][0]
			][
				[
					"title",
					"id",
					"vote_average",
					"vote_count",
					"popularity",
					"release_date",
				]
			].values
			return vals
		except:
			return None

	def get_movie_ids(self):
		"""
            param: None

            return: List of all the unique movieIds (from PATH_RATINGS path)
		"""
		return pd.read_csv(PATH_RATINGS)["movieId"].unique().tolist()

	def train_knn(self, df, userId, user_m_ids, movies_watched):
		"""
            param: df - movies pandas DataFrame
                   userId - user ID to predict movies with
                   user_m_ids - List of movieIDs of movies to be recommended upon
                                (as seen in TMDB dataset)
                   movies_watched - List of movie titles watched 
                                    (as seen in TMDB dataset)

            return: pandas DataFrame of the recommended movies with attributes - 
                    title, id, vote_average, vote_count, popularity, release date

            Collaborative filtering is done using KNN-Baseline and prediction is 
            done using pearson_baseline. The technique used is item-item based.
		"""
		reader = Reader(rating_scale=(1, 5))
		movie_ids = self.get_movie_ids()
		rec_result = dict()

		sim_options = {"name": "pearson_baseline", "user_based": False}

		data = Dataset.load_from_df(df[RATING_ATTR], reader)
		if isfile(PATH_COLL_FILTERING_CACHE):
			model = joblib.load(PATH_COLL_FILTERING_CACHE)
		else:
			trainset = data.build_full_trainset()
			model = KNNBaseline(sim_options=sim_options)
			model.fit(trainset)
			joblib.dump(model, PATH_COLL_FILTERING_CACHE)

		inn_id = model.trainset.to_inner_iid(user_m_ids[0])
		# print(self.get_movie_title(self.get_tmdb_id(user_m_ids[0])))
		inn_id_neigh = model.get_neighbors(inn_id, k=10)
		# print(inn_id_neigh)

		df_pref = pd.DataFrame(
			columns=[
				"title",
				"id",
				"vote_average",
				"vote_count",
				"popularity",
				"release_date",
			]
		)
		index = 0

		for m_id in inn_id_neigh:
			title_df = self.get_movie_title(
				self.get_tmdb_id(model.trainset.to_raw_iid(m_id))
			)
			try:
				if title_df[0] not in movies_watched:
					df_pref.loc[index] = array(
						[
							title_df[0],
							title_df[1],
							title_df[2],
							title_df[3],
							title_df[4],
							title_df[5],
						]
					)
					index += 1
			except:
				pass

		return df_pref

	def store_pref(self, pref, userId, index, rating):
		"""
            param: pref - dict with keys - userId, movieId, rating
                   userId - userId to be inserted (int)
                   index - movieId to be inserted (int)
                   rating - rating on a scale of (1-5)

            return: pref with userId, index and rating values appended
		"""
		pref[RATING_ATTR[0]].append(userId)
		pref[RATING_ATTR[1]].append(index)
		pref[RATING_ATTR[2]].append(rating)
		return pref

	def user_model(self, movies_watched, limit=LIMIT):
		"""
            param: movies_watched - dict of form -
                                    {'movieName1': rating1,
                                     'movieName2': rating2,
                                     .....}
                   limit - no. of movies to display
                           (default = LIMIT)
		"""
		LIMIT = limit
		userId = DEFAULT_ID
		pref = dict()
		user_m_ids = list()

		for attribute in RATING_ATTR:
			pref[attribute] = list()

		for title in movies_watched:
			index = self.get_title_index(title)
			m_index = self.get_m_id(index)
			user_m_ids.append(m_index)
			pref = self.store_pref(pref, userId, m_index, movies_watched[title])

		df_rating = pd.read_csv(PATH_RATINGS)
		df_pref_rating = df_rating.append(
			pd.DataFrame(pref), sort=False, ignore_index=True
		)

		return self.train_knn(df_pref_rating, userId, user_m_ids, movies_watched)

if __name__ == "__main__":
	rec = CollaborativeFiltering()
	print(
		rec.user_model(
			{
				"Apollo 13": 5
			}
		)
	)
