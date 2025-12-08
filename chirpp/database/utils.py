import numpy as np


def find_elbow_index(scores: np.ndarray) -> int:
    """
    find the elbow of knee of the scoores to have a dynamic cutoff point for semantic search
    :params vector: the scores returned by the semantic search from the database, the kind of the score is determined by the
    model but it does not matter for this function whether it's a similarity or a distance score
    : return: the index of the elbow point this is the cutoff point for the semantic search
    """
    n_points = len(scores)
    x_values = np.arange(n_points)

    P1 = np.array([x_values[0], scores[0]])
    PN = np.array([x_values[-1], scores[-1]])

    # A = yN - y1
    A = PN[1] - P1[1]
    # B = -(xN - x1)
    B = -(PN[0] - P1[0])
    # C = xN*y1 - yN*x1
    C = PN[0] * P1[1] - PN[1] * P1[0]

    # Calculate the denominator for the distance formula
    denominator = np.sqrt(A ** 2 + B ** 2)

    # Initialize distances array
    distances = np.zeros(n_points)

    # 4. Calculate the perpendicular distance for every point P_i = (x_i, y_i)
    # Distance d = |Ax_i + By_i + C| / sqrt(A^2 + B^2)
    for i in range(n_points):
        x_i, y_i = x_values[i], scores[i]

        # Calculate numerator
        numerator = np.abs(A * x_i + B * y_i + C)

        # Avoid division by zero, though this should only happen if P1=PN
        if denominator == 0:
            distances[i] = 0
        else:
            distances[i] = numerator / denominator

    # 5. The elbow point is the index with the maximum distance
    # We exclude the first and last points since their distance is always 0
    # The max distance will occur between the start and end points.
    # Note: We use argmax on the whole array as P1 and PN should have 0 distance,
    # but the elbow will be one of the intermediate points with the largest non-zero distance.
    elbow_index = np.argmax(distances)+1
    return elbow_index