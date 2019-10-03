from file_paths import *
import pandas as pd
import requests
from PIL import Image
import time
import os

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w185"

poster_df = pd.read_csv(PATH_POSTERS)
poster_df["poster_path"] = POSTER_BASE_URL + poster_df["poster_path"]

movie_ids = pd.read_csv(PATH_MOVIES)["id"].tolist()

for i in range(0, 45466):
	if os.path.exists("./flask/static/posters/" + poster_df["id"][i] + ".jpg"):
		if int(poster_df["id"][i]) in movie_ids:
			movie_ids.remove(int(poster_df["id"][i]))
		print("DUPLICATE: " + poster_df["id"][i])
		continue
	elif int(poster_df["id"][i]) in movie_ids:
		url = poster_df["poster_path"][i]
		img = Image.open(requests.get(url, stream=True).raw)
		img.save("./flask/static/posters/" + poster_df["id"][i] + ".jpg")
		print("SAVED: " + poster_df["id"][i] + "LEFT: " + str(len(movie_ids)))
		time.sleep(0.5)
		movie_ids.remove(int(poster_df["id"][i]))

	if len(movie_ids) < 1000:
		break