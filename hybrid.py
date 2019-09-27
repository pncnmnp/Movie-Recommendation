from content_based import ContentBased
from collaborative_filtering import CollaborativeFiltering
from collections import Counter
import pandas as pd
from numpy import array
from ast import literal_eval
import pprint

class Hybrid:
	def __init__(self):
		self.LIMIT = 20

	def convert_literal_eval(self, json_str):
		return literal_eval("[" + json_str.replace("\n", ",") + "]")

	def get_movie_json(self, title, rec_coll, rec_content):
		for movie in rec_coll:
			if movie["title"] == title:
				return movie
		for movie in rec_content:
			if movie["original_title"] == title:
				return movie

	def get_recommendation(self, movie, review, critics=False, full_search=False):																		
		rec_content_obj, rec_coll_obj = ContentBased(), CollaborativeFiltering()
		rec_content = rec_content_obj.recommend(movie, self.LIMIT, critics, full_search)
		rec_content = self.convert_literal_eval(rec_content.to_json(orient='records', lines=True))
		print("CONTENT")
		# pprint.pprint(rec_content)

		rec_coll_obj.LIMIT = 1000
		rec_coll = rec_coll_obj.user_model({movie: review})
		rec_coll = self.convert_literal_eval(rec_coll.to_json(orient='records', lines=True))
		print("COLAB")
		# pprint.pprint(rec_coll)

		movies_freq = Counter(
						list([movie["title"] for movie in rec_coll])
						+list([movie["original_title"] for movie in rec_content])
					).most_common(self.LIMIT//2)

		print(movies_freq)
		total_movies_rec = [movie[0] for movie in movies_freq]
		movie_df = pd.DataFrame(columns=["title", "id", "vote_average", "vote_count", "popularity", "release_date"])
		index = 0

		for movie in total_movies_rec:
			movie_json = self.get_movie_json(movie, rec_coll, rec_content)
			movie_df.loc[index] = array(list(movie_json.values()))
			index += 1

		print("HYBRID")
		return movie_df

if __name__ == '__main__':
	obj = Hybrid()
	print(obj.get_recommendation('The Dark Knight', 5, False, True))
