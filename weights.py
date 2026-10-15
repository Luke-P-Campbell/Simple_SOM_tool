import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from functools import partial
import neighbourhood as NBH
import visualisation as VIZ
import global_vars as glob

#-------------------------------------------------------------------
# code ref 3.1 - Randomised weight matrices
#-------------------------------------------------------------------
def random_weights(SOM_width, SOM_height, dimensions):
	weights = {}

	empty = [[0] * SOM_height for _ in range(SOM_width)]

	for name in dimensions:
		weights[name] = [row[:] for row in empty]

	for name in dimensions:
		for x in range(0, SOM_width):
			for y in range(0, SOM_height):
				weights[name][x][y] = random.random()

	return(weights)

#-------------------------------------------------------------------
# code ref 3.2 - Training function
#-------------------------------------------------------------------

def train(neighbourhood_func,weights,data,initial_learning_rate,epochs,initial_reactivation,reactivation_decay,epoch_half_life,penalty_strength):
	dimensions = list(weights.keys())
	SOM_width = len(weights[dimensions[0]])
	SOM_height = len(weights[dimensions[0]][0])
	ideal_contribution = 100/len(dimensions)

	#Python list of lists -> NP matrices
	np_format_weights = {}
	for dimension in dimensions:
		np_format_weights[dimension] = np.array(weights[dimension])

	#Neighbourhood matrices are divided into layers, this assigns layers -> epoch %
	epoch_layers = [100 * i / epochs for i in range(epochs)]

	# Win tracker
	decaying_wins = np.zeros((SOM_width, SOM_height))

	indices = list(data.keys())
	for epoch_perc in epoch_layers:
		# Adjust learning rate so later epochs do fine tuning
		learning_rate = initial_learning_rate * (1 - 0.0095 * epoch_perc)

		#Shuffle indices so order doesn't create unwanted patterns
		random.shuffle(indices)

		#Initialise trackers for dead neurons and poorly represented data points
		activations = np.zeros((SOM_width, SOM_height))
		BMU_distances = {key: 0 for key in data}

		#Tracks distance to BMU for each dimension
		var_weights = {dimension:[] for dimension in dimensions}

		for index in indices:
			datum = data[index]
			distance_matrix = np.zeros((SOM_width, SOM_height))

			#Calculate win penalty
			penalty = penalty_strength * np.log((decaying_wins + 0.01) / (1/(SOM_width*SOM_height) + 0.01))

			#Calculate weighted difference matrix
			WD_matrices = {}
			for dimension in dimensions:
				input_value = datum[dimension]
				weight_matrix = np_format_weights[dimension]
				WD_matrices[dimension] = (weight_matrix - input_value)**2
			WD_matrix = np.sum(list(WD_matrices.values()), axis=0) + penalty

			#Extract BMU
			flat_idx = np.argmin(WD_matrix)
			bmu_x, bmu_y = np.unravel_index(flat_idx, WD_matrix.shape)

			#Update dead neuron and poor represented points trackers
			BMU_distances[index] = np.min(WD_matrix)
			activations[bmu_x][bmu_y] += 1

			#Extract relevnat neighbourhood matrix
			neighbourhood = np.array(neighbourhood_func(winning_x = bmu_x, winning_y = bmu_y, layer = int(epoch_perc)))

			#Update weights
			for dimension in dimensions:
				input_value = datum[dimension]
				weight_matrix = np_format_weights[dimension]
				if neighbourhood.shape == weight_matrix.shape:
					np_format_weights[dimension] = weight_matrix + neighbourhood * (input_value - weight_matrix) * learning_rate

		decaying_wins = decaying_wins * 2**(-1/epoch_half_life)

		#Reactivate dead neuron to weight values of least represented datapoint
		temp_activations = activations.copy()
		temp_distances = BMU_distances.copy()
		n_reactivations = max([1,int(initial_reactivation * SOM_width * SOM_height * (1 - epoch_perc/100)**reactivation_decay)])
		for i in range(0,n_reactivations):
			LRD_i = min(temp_distances, key=temp_distances.get) #Least Represented Datum index
			LRNs_x, LRNs_y = np.where(activations == np.min(temp_activations)) #Least Represented Neuron(s) coordinates
			LRN_i = np.random.choice(len(LRNs_x))
			LRN_x = LRNs_x[LRN_i]
			LRN_y = LRNs_y[LRN_i]
			for dimension in dimensions:
				np_format_weights[dimension][LRN_x][LRN_y] = data[LRD_i][dimension]
			temp_activations[LRN_x, LRN_y] = np.inf
			temp_distances.pop(LRD_i)


	#Move from numpy matrices -> python list of lists
	for dimension in dimensions:
		weights[dimension] = np_format_weights[dimension].tolist()

	return weights

#-------------------------------------------------------------------
# Code ref 3.3 - SOM feeding
#-------------------------------------------------------------------
def feed(weights,data,existing_weights = {}):
	dimensions = list(weights.keys())
	SOM_width = len(weights[dimensions[0]])
	SOM_height = len(weights[dimensions[0]][0])

	if not len(existing_weights.keys()):
		existing_weights = {dimension:1 for dimension in dimensions}

	np_format_weights = {}
	for dimension in dimensions:
		np_format_weights[dimension] = np.array(weights[dimension])

	population_matrix = [ [[] for _ in range(SOM_height)] for _ in range(SOM_width)]

	var_weights = {dimension:[] for dimension in dimensions}

	topographic_error = 0
	quantisation_error = 0

	for datum in data.values():
		distance_matrix = np.zeros((SOM_width, SOM_height))

		distance_matrices = {}

		for dimension in dimensions:
			input_value = datum[dimension]
			weight_matrix = np_format_weights[dimension]
			distance_matrices[dimension] = existing_weights[dimension] * (weight_matrix - input_value)**2

		distance_matrix = np.sum(list(distance_matrices.values()), axis=0)
		DM_copy = distance_matrix.copy()

		flat_idx = np.argmin(distance_matrix)

		bmu_x, bmu_y = np.unravel_index(flat_idx, distance_matrix.shape)

		#Distance to BMU
		distances_per_dimension = []
		for dimension in dimensions:
			distances_per_dimension.append(np_format_weights[dimension][bmu_x, bmu_y] - datum[dimension])
		quantisation_error += np.sqrt(sum([dist**2 for dist in distances_per_dimension]))

		#Find second bmu and calculate if adds to TE
		DM_copy[bmu_x,bmu_y] = np.inf
		bmu2_x, bmu2_y = np.unravel_index(np.argmin(DM_copy), DM_copy.shape)
		are_adjacent = (abs(bmu_x - bmu2_x) + abs(bmu_y - bmu2_y)) == 1
		topographic_error += not are_adjacent

		for dimension in dimensions:
			mat = distance_matrices[dimension]
			var_weights[dimension].append(mat[bmu_x, bmu_y])

		population_matrix[bmu_x][bmu_y].append(datum)

	topographic_error = topographic_error/len(data.values())
	quantisation_error = quantisation_error/len(data.values())

	contribution_means = {dimension:float(np.mean(var_weights[dimension])) for dimension in dimensions}
	normalise_factor = 100/sum(list(contribution_means.values()))
	contribution_means = {dimension:val*normalise_factor for dimension,val in contribution_means.items()}

	return population_matrix, contribution_means, topographic_error, quantisation_error

def counts(SOM):
	return [
		[len(SOM[x][y]) for y in range(len(SOM[x]))]
		for x in range(len(SOM))
	]

#-------------------------------------------------------------------
# Code ref 3.4 - User side functions
#-------------------------------------------------------------------

def TRAIN(app, args):
	weights = glob.get("weights", [])
	data = glob.get("input data", [])

	neighbourhood_matrix = glob.get("neighbourhood_matrix", [])

	if len(args)>6:
		app.write("Please enter the correct number of arguments.\nInitial learning rate (default 0.4 - 40%)];\nn. of epochs (default 150);\ninitial reactivation (default 0.02 - 2%/epoch);\nreactivation decay (default 2 - quadratic);\nPenalty decay (10 - 10 epoch half life);\nPenalty strength (default 0.5 - medium penalty)")

	elif not len(neighbourhood_matrix):
		app.write(f"Please set SOM parameters before training.\n")

	elif not (len(weights) and len(data)):
		app.write(f"Please import data before training.\n")

	else:
		defaults = [0.4, 150, 0.02, 2, 10, 0.5]
		args = (args + defaults[len(args):])[:len(defaults)]

		initial_learning_rate = float(args[0])
		epochs = int(args[1])
		initial_reactivation = float(args[2])
		reactivation_decay = float(args[3])
		penalty_half_life = float(args[4])
		penalty_strength = float(args[5])

		neighbourhood_func = partial(NBH.SNAPSHOT, matrices = neighbourhood_matrix)
		app.write("Training...\n")
		trained_weights = train(neighbourhood_func,
			weights,
			data,
			initial_learning_rate,
			epochs,
			initial_reactivation,
			reactivation_decay,
			penalty_half_life,
			penalty_strength)
		glob.set("weights",trained_weights)
		app.write("Finished training.\n")

def FEED(app, args):
	weights = glob.get("weights", [])
	data = glob.get("input data", [])

	if not (len(weights) and len(data)):
		app.write("Please import data before training")
	else:
		pop_SOM, contributions, topo_error, quant_error = feed(weights,data)
		glob.set("population SOM",pop_SOM)
		VIZ.display_matrix(counts(pop_SOM),f"population SOM distribution")

		app.write("\n".join({f"contribution of {dimension} = {contribution}%" for dimension,contribution in contributions.items()}))
		app.write(f"\nTopographic error = {int(100*topo_error)}%\n")
		app.write(f"Quantisation error = {round(quant_error,2)}\n")
		app.original_image = Image.open("image.png")
		app.render_image()

def TWEAK(app,args):
	weights = glob.get("weights",[])
	data = glob.get("input data",[])

	dimensions = list(weights.keys())

	if not (len(weights) and len(data)):
		app.write("Please import data before tweaking")
	else:
		max_deviation = 100
		pop_SOM, contributions, topo_error, quant_error = feed(weights,data)
		i = 0
		adjustments = {dimension:1 for dimension in dimensions}
		while i < 20 and max_deviation > 0.5:
			ideal_contribution = 100/len(dimensions)
			max_deviations = max([abs(contributions[dimension] - ideal_contribution) for dimension in dimensions])
			adjustments = {dimension:adjustments[dimension] * ideal_contribution/contribution for dimension,contribution in contributions.items()}

			pop_SOM, contributions, topo_error, quant_error = feed(weights,data,adjustments)
			i += 1
		app.write("tweaking complete \n\n")

		glob.set("population SOM",pop_SOM)
		VIZ.display_matrix(counts(pop_SOM),f"population SOM distribution")

		app.write("\n".join({f"contribution of {dimension} = {contribution}%" for dimension,contribution in contributions.items()}) + "\n")
		app.write(f"\nTopographic error = {int(100*topo_error)}%\n")
		app.write(f"Quantisation error = {round(quant_error,2)}\n")
		app.original_image = Image.open("image.png")
		app.render_image()

def LIST_DIMENSIONS(app,args):
	dimensions = glob.get("dimensions",[])
	if len(dimensions):
		for dimension in dimensions:
			app.write(f"     - {dimension}\n")
	else:
		app.write("Please import data to establish dimensions.\n")

def SHOW_DIMENSION(app,args):
	if len(args) == 1:
		dimension = args[0].strip().lower()
		weights = glob.get("weights",{})
		dimensions = [string.strip().lower() for string in weights.keys()]

	if len(args) != 1:
		app.write("Please enter the correct number of arguments (1 - dimension).\n")
	elif not len(dimensions):
		app.write("Please import data to establish dimensions.\n")
	elif not dimension in dimensions:
		app.write("Please select a valid dimension.\n")
	else:
		VIZ.display_matrix(weights[dimension],f"Weights for {dimension}")
		app.write(f"Weights for {dimension} displayed.\n")
		app.original_image = Image.open("image.png")
		app.render_image()

#-------------------------------------------------------------------
# Code ref 3.5 - user side functions and descriptions
#-------------------------------------------------------------------

comms = {
	"train":(
		TRAIN,
		"train → run SOM training algorithm on import data [learning rate (0.4)] [n. of epochs (150)] [initial dead neuron reactivation (0.02)] [dead neuron reactivation decay (2)] [penalty decay (10)] [penalty strength (0.5)]"
	),

	"feed":(
		FEED,
		"feed → feed entire population through SOM"
	),

	"tweak":(
		TWEAK,
		"tweak → adjust weighted sum until all variables contribute equally"
	),

	"list_dimensions":(
		LIST_DIMENSIONS,
		"list_dimensions → show dimensions of currently loaded data"
	),

	"show_dimension":(
		SHOW_DIMENSION,
		"show_dimension → show the weight matrix for a particular dimension [dimension]"
	)
}


