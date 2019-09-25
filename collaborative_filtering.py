from surprise import Reader, Dataset, SVD
import pandas as pd
from file_paths import *
from content_based import ContentBased
from numpy import array

DEFAULT_ID = 700
RATING_ATTR = ['userId', 'movieId', 'rating']
LIMIT = 20

class CollaborativeFiltering:
	def __init__(self):
		self.df_credits = pd.read_csv(PATH_CREDITS)
		self.m_id_to_tmdb = pd.read_csv(PATH_MOVIELENS_TO_TMDB)
		self.df_movies = pd.read_csv(PATH_MOVIES)

	def get_tmdb_id(self, movieId):
		try:
			return self.m_id_to_tmdb['tmdbId'][self.m_id_to_tmdb.index[self.m_id_to_tmdb['movieId'] == movieId][0]]
		except: pass

	def get_m_id(self, tmdbId):
		try:
			return self.m_id_to_tmdb['movieId'][self.m_id_to_tmdb.index[self.m_id_to_tmdb['tmdbId'] == tmdbId][0]]
		except: pass

	def get_title_index(self, title):
		try:
			return self.df_credits['id'][self.df_credits.index[self.df_credits['title'] == title][0]]
		except:
			raise ValueError("No film : " + title + " found!")

	def get_movie_title(self, m_id):
		try:
			vals = self.df_movies.iloc[self.df_movies.index[self.df_movies['id'] == m_id][0]][["title", "id", "vote_average", "vote_count", "popularity", "release_date"]].values
			return vals
		except: return None

	def get_movie_ids(self):
		return pd.read_csv(PATH_RATINGS)['movieId'].unique().tolist()

	def train_svd(self, df, userId, user_m_ids, movies_watched):
		reader = Reader(rating_scale=(1,5))
		movie_ids = [m_id for m_id in self.get_movie_ids()]
		rec_result = dict()

		data = Dataset.load_from_df(df[RATING_ATTR], reader)
		trainset = data.build_full_trainset()
		model = SVD()
		model.fit(trainset)

		for m_id in movie_ids:
			pred = model.predict(uid=userId, iid=m_id)
			rec_result[m_id] = pred.est

		sorted_movies = sorted(rec_result.items(), key=lambda kv: kv[1])[::-1]
		selected_movie_ids = [self.get_tmdb_id(movie[0]) for movie in sorted_movies[:LIMIT]]
		# print(sorted_movies[:LIMIT])

		df_pref = pd.DataFrame(columns=["title", "id", "vote_average", "vote_count", "popularity", "release_date"])
		index = 0

		for m_id in selected_movie_ids:
			title_df = self.get_movie_title(m_id)
			try:
				if title_df[0] not in movies_watched:
					df_pref.loc[index] = array([title_df[0], title_df[1], title_df[2], title_df[3], title_df[4], title_df[5]])
					index += 1
			except:
				pass

		return df_pref

	def store_pref(self, pref, userId, index, rating):
		pref[RATING_ATTR[0]].append(userId)
		pref[RATING_ATTR[1]].append(index)
		pref[RATING_ATTR[2]].append(rating)
		return pref

	def user_model(self, movies_watched):
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
		df_pref_rating = df_rating.append(pd.DataFrame(pref), sort=False, ignore_index=True)

		return self.train_svd(df_pref_rating, userId, user_m_ids, movies_watched)

if __name__ == '__main__':
	rec = CollaborativeFiltering()
	print(rec.user_model({"Titanic": 4, "The Terminator": 5, "Avatar": 4.5, "The Matrix": 5, "Amélie": 1, "Singin' in the Rain": 1, "Raiders of the Lost Ark": 5, "Modern Times": 3}))
