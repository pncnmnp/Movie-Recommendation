from surprise import Reader, Dataset, SVD
import pandas as pd
from file_paths import *

class collaborativeFIltering:
	def model(self):
		reader = Reader(rating_scale=(1,5))
		df = pd.read_csv('./tests/' + PATH_RATINGS)

		data = Dataset.load_from_df(df[["userId", "movieId", "rating"]], reader)
		trainset = data.build_full_trainset()
		model = SVD()
		model.fit(trainset)

		print(model.predict(1, 31, 2.5))

if __name__ == '__main__':
	md_obj = collaborativeFIltering()
	md_obj.model()
