import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Rectangle

def display_matrix(matrix, name, coords=[]):
    matrix = np.asarray(matrix)

    fig, ax = plt.subplots()

    # matrix[x][y] -> imshow expects [y][x]
    im = ax.imshow(
        matrix.T,
        cmap="coolwarm",
        origin="lower",
        aspect="auto"
    )

    # Limit the number of x/y ticks for large matrices
    ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))

    # Outline selected area
    if len(coords):
        start_x,start_y,end_x,end_y = coords
        # Put a rectangular outline around coords

        # Normalise the corners, allowing selection in either direction
        x0, x1 = sorted((start_x, end_x))
        y0, y1 = sorted((start_y, end_y))

        # Validate coordinates
        if not (
            0 <= x0 <= x1 < matrix.shape[0]
            and 0 <= y0 <= y1 < matrix.shape[1]
        ):
            raise ValueError("Selection coordinates are outside the matrix")

        rect = Rectangle(
            (x0 - 0.5, y0 - 0.5),
            x1 - x0 + 1,
            y1 - y0 + 1,
            fill=False,
            edgecolor="lime",
            linewidth=2.0
        )
        ax.add_patch(rect)

    # Colour bar showing the value range
    fig.colorbar(im, ax=ax, label="Value")

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(name)

    plt.tight_layout()
    plt.savefig("image.png")

    plt.close("all")

def density_func(data):
    # Plot all dimensions on the same axes
    fig, ax = plt.subplots(figsize=(10, 6))

    for dimension, values in data.items():
        sns.kdeplot(
            x=values,
            ax=ax,
            fill=False,
            clip=(0, 1),
            label=dimension
        )

    ax.set_xlim(0, 1)
    ax.set_xlabel("Normalised value")
    ax.set_ylabel("Density")
    ax.set_title("Density distributions of all dimensions")
    ax.legend(title="Dimension")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("image.png")

    plt.close("all")
