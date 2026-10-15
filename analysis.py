from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
from functools import partial

import weights as WEI
import visualisation as VIZ
import global_vars as glob
import pandas as pd

def select(app,args):
	pop_SOM = glob.get("population SOM", [])

	if len(args) != 4 or any(not s.isdigit() for s in args):
		app.write("Please use correct input.\n")
	if not len(pop_SOM):
		app.write("Please train SOM before displaying.\n")
	else:
		coords = [int(coord) for coord in args]
		glob.set("Selected",coords)

		start_x, start_y, end_x, end_y = coords
		selected_data = {}
		for x in range(start_x, end_x + 1):
			for y in range(start_y, end_y + 1):
				for point in pop_SOM[x][y]:
					for dimension, value in point.items():
						selected_data.setdefault(dimension, []).append(value)
		glob.set("Selected data",selected_data)

		VIZ.display_matrix(WEI.counts(pop_SOM),f"population SOM distribution",coords)
		app.write(f"Population SOM displayed.\n")
		app.original_image = Image.open("image.png")
		app.render_image()

def density(app,args):
	data = glob.get("Selected data",[])
	norm_factors = glob.get("normalising factors",{})
	glob_means = glob.get("global means")
	glob_stds = glob.get("global deviations")

	if not len(data):
		app.write("Please select area before analysing density.\n")
	else:
		VIZ.density_func(data)

		dimensions = data.keys()

		for dimension in dimensions:
			norm_range = norm_factors[dimension]['max'] - norm_factors[dimension]['min']
			mean = norm_factors[dimension]['min'] + np.mean(data[dimension]) * norm_range
			diff = mean - glob_means[dimension]
			deviation = diff / glob_stds[dimension]

			app.write(f"{dimension}: mean = {round(mean,2)}; global = {round(diff,2):+} {round(deviation,1)}σ)\n")

		app.write("Will display actual means here.\n")
		app.original_image = Image.open("image.png")
		app.render_image()


comms = {
	"select":(
	 	select,
		"select → select area of SOM for analysis [start x][start y][end x][end y]"
	),

	"density":(
	 	density,
		"density → plot density function of selected area (normalised 0 to 1)"
	)
}
