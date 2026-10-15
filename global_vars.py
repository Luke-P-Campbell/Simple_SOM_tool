import os, shutil, pickle

FILE = "data.pkl"

#-----------------------------------------------------
# Code ref 1.2 - internal functions
#-----------------------------------------------------

def _load():
    """Load all stored variables from the pickle file."""
    if not os.path.exists(FILE):
        return {}

    with open(FILE, "rb") as f:
        return pickle.load(f)


def _save(data):
    """Save all variables to the pickle file."""
    with open(FILE, "wb") as f:
        pickle.dump(data, f)


def get(name, default=None):
    """Get a stored variable."""
    data = _load()
    return data.get(name, default)


def set(name, value):
    """Create or update a stored variable."""
    data = _load()
    data[name] = value
    _save(data)


def delete(name):
    """Delete a stored variable.

    Returns True if the variable existed, otherwise False.
    """
    data = _load()

    if name not in data:
        return False

    del data[name]
    _save(data)
    return True


def show_all():
    """Return all stored variables as a dictionary."""
    return _load()


def exists(name):
    """Check whether a variable exists."""
    return name in _load()


def clear():
    """Delete all stored variables."""
    _save({})

#-----------------------------------------------------
# Code ref 1.2 - user side functions
#-----------------------------------------------------

def EXPORT(app, args):
	if len(args) == 1:
		filename = args[0]
		if not ".pkl" == filename[-4:]:
			filename = filename + ".pkl"
		shutil.copyfile("data.pkl", filename)
		app.write(f"Exported workspace to {filename}\n")
	else:
		app.write("Please enter the correct number of arguments (1 - filename)")

def IMPORT(app, args):
	if len(args) == 1:
		filename = args[0]
		if not ".pkl" == filename[-4:]:
			filename = filename + ".pkl"
		if os.path.exists(filename):
			shutil.copyfile(filename,"data.pkl")
			app.write(f"Imported {filename} to workspace\n")
		else:
			app.write(f"Could not find file {filename}\n")
	else:
		app.write("Please enter the correct number of arguments (1 - filename)")

def BLANK(app, args):
	with open("data.pkl", "wb") as f:
		pickle.dump({},f)

	set("save",True)

	app.write(f"Blank workspace established\n")

#-----------------------------------------------------
# Code ref 1.3 - exposed functions and descriptions
#-----------------------------------------------------

comms = {
    "export_workspace":(
        EXPORT,
        "export_workspace → export all matrices to file [filename]"
    ),

    "import_workspace":(
        IMPORT,
        "import_workspace → import previously exported workspace [filename]"
    ),

    "blank_workspace":(
        BLANK,
        "blank_workspace → establish blank workspace"
    )
}
