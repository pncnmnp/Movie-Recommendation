import pandas as pd
from paths import PATH_MOVIES, PATH_RATINGS
from ast import literal_eval

class Recommendation:
	def __init__(self):
		self.md = pd.read_csv(PATH_MOVIES)

	def filter_genres(self):
		self.md['genres'] = self.md['genres'].apply(literal_eval).apply(lambda genres: [genre['name'] for genre in genres] if isinstance(genres, list) else [])

	def imdb_rating(self, film, C, m):
		vote_count = film['vote_count']
		vote_average = film['vote_average']

		return ((vote_count/(vote_count+m))*vote_average) + ((m/(vote_count+m))*C)

	def top_movies(self, percentile, limit, offset):
		filter_count = self.md[self.md['vote_count'].notnull()]['vote_count'].astype('float')
		filter_average = self.md[self.md['vote_average'].notnull()]['vote_average'].astype('float')
		imdb_C = filter_average.mean()
		imdb_m = filter_count.quantile(percentile)

		top_filtered = self.md[(self.md['vote_count'] >= imdb_m) & (self.md['vote_count'].notnull()) & (self.md['vote_average'].notnull())][['title', 'id', 'vote_average', 'vote_count', 'popularity']]
		top_filtered['vote_count'] = top_filtered['vote_count'].astype('float')
		top_filtered['vote_average'] = top_filtered['vote_average'].astype('float')

		top_filtered['rating'] = top_filtered.apply(self.imdb_rating, args=(imdb_C, imdb_m,), axis=1)

		top_filtered = top_filtered.sort_values('rating', ascending=False)

		return top_filtered.iloc[offset: offset+limit]

if __name__ == '__main__':
	obj = Recommendation()
	obj.filter_genres()
	movies = obj.top_movies(percentile=0.80, limit=10, offset=0)
	print(movies)
