from PIL import Image, ImageDraw, ImageFont
import visualisation as VIZ
import global_vars as glob
import math

#-------------------------------------------------------------------
# Code ref 2.1 - neighbourhood functions
#-------------------------------------------------------------------

def gaussian(distance, sigma, epoch_perc):
	sigma = (1 - 0.95 * epoch_perc) * sigma
	return math.exp(-(distance ** 2) / (2 * sigma ** 2))

def bubble(distance, radius, epoch_perc):
	radius = (1 - 0.95 * epoch_perc) * radius
	return 1.0 if distance <= radius else 0.0

def triangular(distance, radius, epoch_perc):
	radius = (1 - 0.95 * epoch_perc) * radius
	return max(0.0, 1.0 - distance / radius)

def parabolic(distance, radius, epoch_perc):
	radius = (1 - 0.95 * epoch_perc) * radius
	return max(0.0, 1.0 - (distance / radius) ** 2)

def mexican_hat(distance, sigma, epoch_perc):
	sigma = (1 - 0.95 * epoch_perc) * sigma
	x = distance / sigma
	return (1.0 - x ** 2) * math.exp(-x ** 2 / 2)

neighbourhood_functions = {
	"gaussian":gaussian,
	"bubble":bubble,
	"triangular":triangular,
	"parabolic":parabolic,
	"mexican_hat":mexican_hat
}

#-------------------------------------------------------------------
# Code ref 2.2 - matrix creation
#-------------------------------------------------------------------

def MATRIX(SOM_x,SOM_y,func_name, param):
	func = neighbourhood_functions[func_name]

	matrices = []

	for epoch in [i / 100 for i in range(101)]:
		NEIGHBOURHOOD_x = SOM_x * 2 - 1
		NEIGHBOURHOOD_y = SOM_y * 2 - 1
		matrix = [ [0] * NEIGHBOURHOOD_y for _ in range(NEIGHBOURHOOD_x)]

		for x in range(0,NEIGHBOURHOOD_x):
			dist_x = abs(x - SOM_x + 1)
			for y in range(0,NEIGHBOURHOOD_y):
				dist_y = abs(y - SOM_y + 1)
				matrix[x][y] = func((dist_x**2 + dist_y**2)**0.5, param, epoch)

		matrices.append(matrix)

	return(matrices)

def SNAPSHOT(winning_x,winning_y,matrices,layer):
	matrix = matrices[layer]

	x_max = len(matrix)
	y_max = len(matrix[0])

	x_start = (x_max + 1)//2 - winning_x
	x_end = x_max - winning_x
	y_start = (y_max + 1)//2 - winning_y
	y_end = y_max - winning_y

	portion = [
		row[y_start:y_end + 1]
		for row in matrix[x_start:x_end + 1]
	]

	return(portion)

#-------------------------------------------------------------------
# Code ref 2.3 - User side functions
#-------------------------------------------------------------------

def SET(app, args):
        if len(args) == 4:
                x,y,func_name,func_param = list(args)
                x = int(x)
                y = int(y)
                func_param = int(func_param)

                neighbourhood_matrix = MATRIX(x,y,func_name,func_param)

                glob.set("SOM_width",x)
                glob.set("SOM_height",y)
                glob.set("neighbourhood_matrix",neighbourhood_matrix)

                VIZ.display_matrix(neighbourhood_matrix[0],"Neighbourhood matrix")

                app.original_image = Image.open("image.png")
                app.render_image()
                app.write(f"Established a {x} x {y} SOM and set the neighbourhood funciton to {func_name}.\n")
        else:
                app.write("Please enter the correct number of arguments. (4 - SOM width; SOM height; neihbourhood function; neighbourhood function parameter.)\n")

def SHOW(app, args):
        neighbourhood_matrix = glob.get("neighbourhood_matrix",[]) #returns [] if neighbourhood_matrix not yet set

        if len(args) and int(args[0]) <= 100:
                layer = int(args[0])-1
        else:
                layer = 0

        if len(neighbourhood_matrix):
                VIZ.display_matrix(neighbourhood_matrix[layer],"Neighbourhood matrix")
                app.original_image = Image.open("image.png")
                app.render_image()
                app.write(f"Neighbourhood matrix displayed.\n")
        else:
                app.write(f"Please set the parameters first.\n")

#-------------------------------------------------------------------
# Code ref 2.4 - exposed functions and descriptions
#-------------------------------------------------------------------

comms = {
	"set_neighbourhood":(
		SET,
		"set_neighbourhood → set parameters for SOM [SOM width][SOM height][neighbourhood function][neighbourhood function parameter] \n neighbourhood functions: 'gaussian'; 'bubble';'triangular';'parabolic';'mexican_hat'"
	),

	"show_neighbourhood":(
		SHOW,
		"show_neighbourhood → display the neighbourhood matrix on screen [epoch % (default 0)]"
	)
}
