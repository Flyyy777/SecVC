from PIL import Image
import numpy as np
import itertools
import math

# ======================================================================================================================================================== #
# Function returning the contrast (in the sense of Naor and Shamir) of a scheme defined by the given matrices, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# k - minimum number of shares required to decrypt the message
def compute_contrast(B0, B1, k):

    n, m = B0.shape
    assert B1.shape == (n, m), "B0 and B1 must have the same dimensions"
    assert 1 <= k <= n, "k must be in the range 1..n"

    def hamming_weight_distribution(A):
        weights = []
        for rows in itertools.combinations(range(n), k):
            result = np.bitwise_or.reduce(A[list(rows), :], axis=0)
            weights.append(np.sum(result))
        return weights

    weights_B0 = hamming_weight_distribution(B0)
    weights_B1 = hamming_weight_distribution(B1)

    l = max(weights_B0)  # white - darkest possible case
    h = min(weights_B1)  # black - brightest possible case

    contrast = (h - l) / m
    return contrast
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the parameter P of the scheme defined by the given matrices, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# probabilistic - deterministic mode (False) or probabilistic mode (True)
def compute_P(i_participant, B0, B1, probabilistic=False):

    if B0.shape != B1.shape:
        raise ValueError("Matrices B0 and B1 must have the same dimensions")

    num_participants, num_columns = B0.shape

    if not (0 <= i_participant < num_participants):
        raise IndexError(f"Participant index out of range 0..{num_participants - 1}")

    if not probabilistic:
        permutations = list(itertools.permutations(range(num_columns)))
        C0_set = [B0[:, p] for p in permutations]
        C1_set = [B1[:, p] for p in permutations]
    else:
        C0_set = [B0[:, [i]] for i in range(num_columns)]
        C1_set = [B1[:, [i]] for i in range(num_columns)]

    x = 0
    y = 0

    for idx in range(len(C0_set)):
        vec_0 = C0_set[idx][i_participant]
        vec_1 = C1_set[idx][i_participant]

        if np.array_equal(vec_0, vec_1):
            x += 1
        else:
            y += 1

    P = y / (x + y) if (x + y) > 0 else 0.0

    return P
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the phi coefficient between two binary images, where:
# image_path_A - path to the first image
# image_path_B - path to the second image
def compute_phi(image_path_A, image_path_B):

    def load_image(path):
        image = Image.open(path).convert("L")
        array = np.array(image)
        binary_image = np.where(array < 128, 1, 0).astype(np.uint8)
        return binary_image

    A = load_image(image_path_A)
    B = load_image(image_path_B)

    if A.shape != B.shape:
        raise ValueError(f"Images must have the same dimensions {A.shape} != {B.shape}")

    a = np.sum((A == 1) & (B == 1))
    b = np.sum((A == 1) & (B == 0))
    c = np.sum((A == 0) & (B == 1))
    d = np.sum((A == 0) & (B == 0))

    numerator = (a * d) - (b * c)
    denominator = math.sqrt((a + b) * (a + c) * (b + d) * (c + d))

    if denominator == 0:
        return 0.0

    phi = numerator / denominator
    return phi
# ======================================================================================================================================================== #
