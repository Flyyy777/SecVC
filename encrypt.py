from PIL import Image
import numpy as np
import itertools
import os

# ======================================================================================================================================================== #
# Function returning sets of single-column matrices for two colors, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
def split_into_columns(B0, B1):
    C0 = [B0[:, [i]] for i in range(B0.shape[1])]
    C1 = [B1[:, [i]] for i in range(B1.shape[1])]
    return C0, C1
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning an encrypted image using Visual Cryptography, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# image_path - path to the input image
# seed - random value used as the RNG seed
# output_dir - directory where the generated shares will be saved
# probabilistic - deterministic mode (False) or probabilistic mode (True)
def encrypt(B0, B1, image_path, seed, output_dir, probabilistic=False):

    image = Image.open(image_path).convert('L')
    image_array = np.array(image)
    binary_image = np.where(image_array == 0, 1, 0).astype(np.uint8)

    if not probabilistic:
        permutations = list(itertools.permutations(range(B0.shape[1])))
        C0 = [B0[:, p] for p in permutations]
        C1 = [B1[:, p] for p in permutations]
    else:
        C0, C1 = split_into_columns(B0, B1)

    num_matrices = len(C0)

    rng = np.random.default_rng(seed)

    n = C0[0].shape[0]
    height, width = binary_image.shape

    if not probabilistic:
        output_height = height * C0[0].shape[1]
    else:
        output_height = height

    shares = [np.zeros((output_height, width), dtype=int) for _ in range(n)]

    for y in range(height):
        for x in range(width):

            index = rng.integers(0, num_matrices)

            M = C1[index] if binary_image[y, x] == 1 else C0[index]

            for i in range(n):
                shares[i][y * M.shape[1]:(y + 1) * M.shape[1], x] = M[i]

    os.makedirs(output_dir, exist_ok=True)

    for i, share in enumerate(shares, start=1):
        share_image = Image.fromarray(((1 - share) * 255).astype(np.uint8)).convert('L')
        path = os.path.join(output_dir, f"share_{i}.png")
        share_image.save(path)
        print(f"Share saved to: {path}")

    print(f"\nFinished generating {n} shares in directory: {output_dir}")

    return shares
# ======================================================================================================================================================== #
