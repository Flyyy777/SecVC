from PIL import Image
import numpy as np
import itertools
import math
import os

# ======================================================================================================================================================== #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  KEY PROTECTION  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  #
# ======================================================================================================================================================== #

# ======================================================================================================================================================== #
# Function returning a permutation of matrix columns according to a given sequence, where:
# matrix - input matrix to be permuted
# sequence - pattern used to reorder the matrix columns
def permute_columns(matrix, sequence):
    return matrix[:, list(sequence)]
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning sets of matrices with applied mitigation, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# Zm - set of maximal forbidden sets
def apply_set_expansion(B0, B1, Zm):

    C0 = []
    C1 = []

    permutations = list(itertools.permutations(range(B0.shape[1])))

    for F in Zm:

        B1_prime = B1.copy()
        found = False

        for perm in permutations:

            if np.array_equal(B1_prime[F, :], B0[F, :]):
                found = True

            if not found:
                B1_prime = permute_columns(B1_prime, perm)

            else:
                for perm_ in permutations:
                    C0.append(permute_columns(B0, perm_))
                    C1.append(permute_columns(B1_prime, perm_))
                break

            if np.array_equal(B1_prime[F, :], B0[F, :]):
                found = True
                for perm_ in permutations:
                    C0.append(permute_columns(B0, perm_))
                    C1.append(permute_columns(B1_prime, perm_))
                break

        if not found:
            print("No valid permutation found for set:", F)

    return C0, C1
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning encrypted shares with applied key mitigation, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# image_path - path to the input image
# key - random value used as the RNG seed
# output_dir - directory where the generated shares will be saved
def encrypt_with_key_mitigation(basis_matrices, image_path, key, output_dir):

    image = Image.open(image_path).convert('L')
    image = np.array(image)
    binary_image = np.where(image == 0, 1, 0).astype(np.uint8)

    B0, B1 = basis_matrices
    permutations = list(itertools.permutations(range(B0.shape[1])))

    C0 = [B0[:, p] for p in permutations]
    C1 = [B1[:, p] for p in permutations]

    forbidden_sets = [[0], [1]]
    C0, C1 = apply_set_expansion(B0, B1, forbidden_sets)

    height, width = binary_image.shape
    num_matrices = len(C0)
    bits_per_choice = math.ceil(math.log2(num_matrices))
    key_length_bits = height * width * bits_per_choice

    rng = np.random.default_rng(key)
    key_bits = ''.join(rng.choice(['0', '1'], size=key_length_bits))

    num_shares = B0.shape[0]
    output_height = height * B0.shape[1]
    shares = [np.zeros((output_height, width), dtype=int) for _ in range(num_shares)]

    key_index = 0

    for y in range(height):
        for x in range(width):

            fragment = key_bits[key_index:key_index + bits_per_choice]
            key_index += bits_per_choice
            matrix_index = int(fragment, 2) % num_matrices

            M = C1[matrix_index] if binary_image[y, x] == 1 else C0[matrix_index]

            for i in range(num_shares):
                shares[i][y * M.shape[1]:(y + 1) * M.shape[1], x] = M[i]

    os.makedirs(output_dir, exist_ok=True)

    for i, share in enumerate(shares, start=1):
        share_image = Image.fromarray(((1 - share) * 255).astype(np.uint8)).convert('L')
        path = os.path.join(output_dir, f"share_{i}.png")
        share_image.save(path)
        print(f"Share saved to: {path}")

    print(f"\nFinished generating {num_shares} shares in directory: {output_dir}")

    return shares
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || VERIFICATION ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  #
# ======================================================================================================================================================== #

# ======================================================================================================================================================== #
# Function returning extended basis matrices together with permutations of two additional columns, where:
# B - input basis matrix
def add_verification_columns(B):

    k, m = B.shape

    column_A = np.ones((k, 1), dtype=np.uint8)
    column_B = np.zeros((k, 1), dtype=np.uint8)

    extended_matrix = np.hstack([B, column_A, column_B])

    labels = [f"orig{i}" for i in range(m)] + ["A", "B"]

    permutations = list(itertools.permutations(range(m + 2)))

    matrices_list = []
    labels_list = []

    for perm in permutations:
        matrices_list.append(extended_matrix[:, perm])
        labels_list.append([labels[i] for i in perm])

    return matrices_list, labels_list
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning encrypted shares and verification shares, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# image_path_O - path to the original image
# image_path_VO - path to the validation image
# output_dir - directory where the shares will be saved
def encrypt_with_verification(B0, B1, image_path_O, image_path_VO, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    C0, W0 = add_verification_columns(B0)
    C1, W1 = add_verification_columns(B1)

    image_O = Image.open(image_path_O).convert("L")
    image_O = (np.array(image_O) < 128).astype(np.uint8)
    height, width = image_O.shape

    image_VO = Image.open(image_path_VO).convert("L")
    image_VO = image_VO.resize((width, height), Image.NEAREST)
    image_VO = (np.array(image_VO) < 128).astype(np.uint8)

    n, m = B0.shape
    new_m = m + 2

    shares_S = [np.zeros((height * new_m, width), dtype=np.uint8)
                for _ in range(n)]
    shares_VS = [np.zeros((height * new_m, width), dtype=np.uint8)
                for _ in range(n)]

    rng = np.random.default_rng()

    for y in range(height):
        for x in range(width):

            if image_O[y, x] == 0:
                index = rng.integers(0, len(C0))
                M = C0[index]
                L = W0[index]
            else:
                index = rng.integers(0, len(C1))
                M = C1[index]
                L = W1[index]

            idx_A = L.index("A")
            idx_B = L.index("B")

            y_start = y * new_m
            y_end = (y + 1) * new_m

            for i in range(n):
                shares_S[i][y_start:y_end, x] = M[i]

            if image_VO[y, x] == 0:
                pair = (1, 0)
            else:
                pair = (0, 1)

            for i in range(n):
                shares_VS[i][y_start + idx_A, x] = pair[0]
                shares_VS[i][y_start + idx_B, x] = pair[1]

    for i in range(n):
        img_S = Image.fromarray((255 * (1 - shares_S[i])).astype(np.uint8))
        img_VS = Image.fromarray((255 * (1 - shares_VS[i])).astype(np.uint8))

        img_S.save(os.path.join(output_dir, f"S_{i + 1}.png"))
        img_VS.save(os.path.join(output_dir, f"VS_{i + 1}.png"))

    print(f"\nFinished generating {n} shares in directory: {output_dir}")
# ======================================================================================================================================================== #
