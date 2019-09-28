from content_based import ContentBased
from collaborative_filtering import CollaborativeFiltering
from collections import Counter
import pandas as pd
import sys
from numpy import array
from ast import literal_eval

class Hybrid:
	def __init__(self):
		self.LIMIT = 20

	def convert_literal_eval(self, json_str):
		"""
            param: json_str - pandas DataFrame converted to JSON format

            return: Literal Eval of the JSON string in List format
		"""
		return literal_eval("[" + json_str.replace("\n", ",") + "]")

	def get_movie_json(self, title, rec_coll, rec_content):
		"""
            param: title - movie title to search (as mentioned in TMDB dataset)
                   rec_coll - movies recommended by Collaborative Filtering
                   rec_content - movies recommended by ContentBased          
                  NOTE: Parse both the results (rec_coll and rec_content) 
                  in convert_literal_eval before passing the parameters.
                  See get_recommendation() for example.

            return: movie data in JSON format
		"""
		for movie in rec_coll:
			if movie["title"] == title:
				return movie
		for movie in rec_content:
			if movie["original_title"] == title:
				return movie

	def get_recommendation(
		self, movie, review, critics=False, full_search=False, use_pickle=True
	):
		"""
            For hybrid recommendations: LIMIT (instance var) determines no. of movies outputted
            param: movie - title of the movie (as mentioned in DB)
                   review - rating of the movie on the scale of 1-5
                   critics - (True or False type) Critically acclaimed recommendations
                   full_search - True: Recommendations generated using keywords, cast, crew and genre
                                 False: Recommendations generated on basis of tagline and overview

            return: pandas DataFrame object with attributes -
                    title, id, vote_average, vote_count, popularity, release_date

            Recommendations which have frequency greater than 1 in both 
            collaborative and content based filtering results are chosen 
            as result. If the total result found are less than limit than 
            the difference is divided into a ratio of 2:1, for content based 
            and collaborative results. i.e Out of the remaining results, 
            2x of them will be content based and 1x collaborative based. 
		"""
		rec_content_obj, rec_coll_obj = ContentBased(), CollaborativeFiltering()
		rec_content = rec_content_obj.recommend(
			movie, self.LIMIT, critics, full_search, use_pickle
		)
		rec_content = self.convert_literal_eval(
			rec_content.to_json(orient="records", lines=True)
		)
		print("Content Filtering completed.....")

		rec_coll_obj.LIMIT = 1000
		rec_coll = rec_coll_obj.user_model({movie: review})
		rec_coll = self.convert_literal_eval(
			rec_coll.to_json(orient="records", lines=True)
		)
		print("Collaborative Filtering completed.....")

		movies_freq = Counter(
			list([movie["title"] for movie in rec_coll])
			+ list([movie["original_title"] for movie in rec_content])
		).most_common(self.LIMIT)

		# accepting movies whose frequency is greater than 1 from collaborative and content based results
		total_movies_rec = [movie[0] for movie in movies_freq if movie[1] > 1]
		# print(total_movies_rec)
		movie_df = pd.DataFrame(
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

		for movie in total_movies_rec:
			movie_json = self.get_movie_json(movie, rec_coll, rec_content)
			movie_df.loc[index] = array(list(movie_json.values()))
			index += 1

		if len(total_movies_rec) < self.LIMIT:
			rec_content_cutoff = ((self.LIMIT - len(total_movies_rec)) * 2) // 3
			start_index = index
			rec_title_name = {0: "original_title", 1: "title"}
			curr_rec = 0  # as we start with content based results
			for rec in [rec_content, rec_coll]:
				for movie in rec:
					if (
						movie[rec_title_name[curr_rec]]
						not in movie_df["title"].tolist()
					):
						movie_df.loc[index] = array(list(movie.values())[:6])
						index += 1
					if start_index + rec_content_cutoff == index and rec == rec_content:
						curr_rec = 1
						break
					elif index == self.LIMIT:
						break

				if index == self.LIMIT:
					break

		print("Hybrid Filtering completed.....")
		return movie_df


if __name__ == "__main__":
	obj = Hybrid()
	print(obj.get_recommendation(sys.argv[1], 5, True, True, True))
