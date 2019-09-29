import pandas as pd
from file_paths import *
from ast import literal_eval
import sys

class Recommendation:
	def __init__(self):
		self.md = pd.read_csv(PATH_MOVIES)

	def filter_productions(self):
		self.md["production_companies"] = (
			self.md["production_companies"]
			.apply(literal_eval)
			.apply(
				lambda companies: [company["name"] for company in companies]
				if isinstance(companies, list)
				else list()
			)
		)	

	def filter_genres(self):
		"""
            Maps each genre to each movie title 
		"""
		self.md["genres"] = (
			self.md["genres"]
			.apply(literal_eval)
			.apply(
				lambda genres: [genre["name"] for genre in genres]
				if isinstance(genres, list)
				else list()
			)
		)

	def imdb_rating(self, film, C, m):
		"""
            param: film - DataFrame of the particular film 
                          (should contain vote_count and vote_average)
                   C - mean of the average ratings
                   m - minimum votes required to be listed

            return: rating of the film (float)
		"""
		vote_count = film["vote_count"]
		vote_average = film["vote_average"]

		return ((vote_count / (vote_count + m)) * vote_average) + ((m / (vote_count + m)) * C)

	def top_stats(self, md, percentile, genre=None):
		"""
            param: md - movie pandas DataFrame
                   percentile - cutoff percentile (0.0 to 1.0)
                   genre - genre based recommendation (default = None)
                   (Genres in TMDB dataset are: Action, Adventure, Fantasy, 
                   Science Fiction, Crime, Drama, Thriller, Animation, Family, 
                   Western, Comedy, Romance, Horror, Mystery, History, War, 
                   Music, Documentary, Foreign, TV Movie)

                   If genre is set to None, overall ranking will be returned.

            return: top_filtered - pandas DataFrame filtered by percentile threshold
                                   and genres. The attributes of the DataFrame are -
                                   original_title, id, vote_average, vote_count, 
                                   popularity, release_date.
                    imdb_C - mean value of all the vote_averages
                    imdb_m - minimum votes required to be listed 
		"""
		if genre != None:
			genre_md = (
				md.apply(lambda movie: pd.Series(movie["genres"]), axis=1)
				.stack()
				.reset_index(level=1, drop=True)
			)
			genre_md.name = "genre"
			md = md.drop("genres", axis=1).join(genre_md)

			genre_list = md["genre"].fillna("").unique().tolist()

			if genre in genre_list:
				md = md[md["genre"] == genre]
			else:
				categories = ", ".join(genre_list)
				raise ValueError(CATEGORY_ERROR + categories)

		filter_count = md[md["vote_count"].notnull()]["vote_count"].astype("float")
		filter_average = md[md["vote_average"].notnull()]["vote_average"].astype("float")
		imdb_C = filter_average.mean()
		imdb_m = filter_count.quantile(percentile)

		top_filtered = md[
			(md["vote_count"] >= imdb_m)
			& (md["vote_count"].notnull())
			& (md["vote_average"].notnull())
		][
			[
				"original_title",
				"id",
				"vote_average",
				"vote_count",
				"popularity",
				"release_date",
			]
		]
		top_filtered["vote_count"] = top_filtered["vote_count"].astype("float")
		top_filtered["vote_average"] = top_filtered["vote_average"].astype("float")

		return top_filtered, imdb_C, imdb_m

	def top_movies(self, md, percentile, limit, offset, genre=None):
		"""
            param: md - movie pandas DataFrame
                   percentile - cutoff percentile (0.0 to 1.0)
                   limit - no. of movies to display
                   offset - base value
                   genre - genre based recommendation (default = None)
                   (Genres in TMDB dataset are: Action, Adventure, Fantasy, 
                   Science Fiction, Crime, Drama, Thriller, Animation, Family, 
                   Western, Comedy, Romance, Horror, Mystery, History, War, 
                   Music, Documentary, Foreign, TV Movie)

                   If genre is set to None, overall ranking will be returned.

            return: pandas DataFrame of top movies calculated using the imdb
                    formula.
		"""
		top_filtered, imdb_C, imdb_m = self.top_stats(md, percentile, genre)
		top_filtered["rating"] = top_filtered.apply(
			self.imdb_rating, args=(imdb_C, imdb_m), axis=1
		)

		top_filtered = top_filtered.sort_values("rating", ascending=False)

		return top_filtered.iloc[offset : offset + limit]

if __name__ == "__main__":
	obj = Recommendation()
	obj.filter_genres()
	try:
		genre = sys.argv[1]
	except:
		genre = None
	movies = obj.top_movies(obj.md, percentile=0.85, limit=10, offset=0, genre=genre)
	print(movies)
