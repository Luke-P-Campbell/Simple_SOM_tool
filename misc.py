from PIL import Image, ImageDraw, ImageFont
import os
from functools import partial

import weights as WEI
import visualisation as VIZ
import global_vars as glob
import pandas as pd

#-----------------------------------------------------------
# Code ref 4.1 - data importing
#-----------------------------------------------------------

def import_data(app, args):
	if len(args) == 1:
		filename = args[0]
		SOM_width = glob.get("SOM_width", 0)
		SOM_height = glob.get("SOM_height", 0)

	if len(args) != 1:
		app.write("Please enter the correct number of arguments (1 - filename)\n")

	elif not os.path.exists(filename):
		app.write("File not found\n")

	elif not (SOM_width and SOM_height):
		app.write("Please set the neighbourhood function before importing data\n")

	else:
		df = pd.read_csv(filename, index_col=0)

		# 1. Detect outliers on raw data, independently per column
		outlier_mask = pd.DataFrame(False, index=df.index, columns=df.columns)

		for column in df.columns:
			q1 = df[column].quantile(0.25)
			q3 = df[column].quantile(0.75)
			iqr = q3 - q1

			lower = q1 - 1.5 * iqr
			upper = q3 + 1.5 * iqr

			outlier_mask[column] = (
				(df[column] < lower) | (df[column] > upper)
			)

		# 2. Remove rows containing an outlier in ANY column
		rows_to_remove = outlier_mask.any(axis=1)

		df = df.loc[~rows_to_remove].copy()

		factors = {}
		means = {}
		stds = {}

		for column in df.columns:
			col_min = df[column].min()
			col_max = df[column].max()

			factors[column] = {
				"min": float(col_min),
				"max": float(col_max)
			}
			means[column] = df[column].mean()
			stds[column] = df[column].std()

			print(column,factors[column])

			if col_max == col_min:
				df[column] = 0.0
			else:
				df[column] = (df[column] - col_min) / (col_max - col_min)

		indexes = df.index.tolist()
		dimensions = df.columns.tolist()
		df = df.to_dict(orient="index")


		weights = WEI.random_weights(SOM_width,SOM_height,dimensions)

		glob.set("weights",weights)
		glob.set("indexes",indexes)
		glob.set("dimensions",dimensions)
		glob.set("normalising factors",factors)
		glob.set("global means",means)
		glob.set("global deviations",stds)
		glob.set("input data",df)

		app.write(f"Established randomised weights for dimensions: {[dimension for dimension in dimensions]}\n")

#-----------------------------------------------------------
# Code ref 4.2 - Other misc functions
#-----------------------------------------------------------

def show_som(app,args):
	pop_SOM = glob.get("population SOM", [])

	if not len(pop_SOM):
		app.write("Please train SOM before displaying.\n")
	else:
		VIZ.display_matrix(WEI.counts(pop_SOM),f"population SOM distribution")
		app.write(f"Population SOM displayed.\n")
		app.original_image = Image.open("image.png")
		app.render_image()

def clear(app, args):
	width = 1000
	height = 600

	image = Image.new(
		"RGB",
		(width, height),
		"white"
	)

	image.save("image.png")

	app.original_image = image
	app.render_image()

	app.write("Image cleared.\n")

comms = {
	"clear":(
	 	clear,
		"clear → clear image on screen"
	),

	"import_data":(
		import_data,
		"import_data → import filename and establish matching randomised weights [filename]"
	),

	"show_som":(
		show_som,
		"show_som → show the entire population placed on the SOM"
	)
}
