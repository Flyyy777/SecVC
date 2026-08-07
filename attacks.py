from mitigations import apply_set_expansion
from PIL import Image
import numpy as np
import itertools
import random
import math
import os

# ======================================================================================================================================================== #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  KEY ATTACKS ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  #
#  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  #
# ======================================================================================================================================================== #

# ======================================================================================================================================================== #
# Function returning the decryption result of a share using a key, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# share_path - path to the participant's share image
# participant_index - index of the participant (0-based)
# key - random value used as RNG seed
# output_dir - directory where the decrypted image will be saved
# probabilistic - deterministic mode (False) or probabilistic mode (True)
def decrypt_with_key(B0, B1, share_path, participant_index, key, output_dir, probabilistic=False):

    image = Image.open(share_path).convert('L')
    share = (np.array(image) < 128).astype(np.uint8)

    if not probabilistic:
        m = B0.shape[1]
        permutations = list(itertools.permutations(range(m)))
        C0_set = [B0[:, p] for p in permutations]
        C1_set = [B1[:, p] for p in permutations]
        block_height = C0_set[0].shape[1]
    else:
        C0_set = [B0[:, [i]] for i in range(B0.shape[1])]
        C1_set = [B1[:, [i]] for i in range(B1.shape[1])]
        block_height = 1

    D0 = [c[participant_index] for c in C0_set]
    D1 = [c[participant_index] for c in C1_set]

    num_matrices = len(D0)
    share_height, width = share.shape
    secret_height = share_height // block_height

    rng = np.random.default_rng(key)
    secret = np.zeros((secret_height, width), dtype=np.uint8)

    for y in range(secret_height):
        for x in range(width):
            start = y * block_height
            end = start + block_height
            block = share[start:end, x]

            index = rng.integers(0, num_matrices)

            if np.array_equal(block, D0[index]) and np.array_equal(block, D1[index]):
                secret[y, x] = np.random.randint(0, 2)
            elif np.array_equal(block, D0[index]):
                secret[y, x] = 0
            elif np.array_equal(block, D1[index]):
                secret[y, x] = 1

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_image = Image.fromarray((1 - secret) * 255).convert('L')
        path = os.path.join(output_dir, f"decrypted_participant_{participant_index + 1}.png")
        output_image.save(path)

    return secret
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# Function returning the reconstructed secret for a given share encrypted with mitigation, where:
# B0 - basis matrix for the white pixel
# B1 - basis matrix for the black pixel
# share_path - path to the participant's share image
# participant_index - index of the participant (0-based)
# key - random value used as RNG seed
# output_dir - directory where the decrypted image will be saved
# probabilistic - deterministic mode (False) or probabilistic mode (True)
def decrypt_with_key_mitigation(B0, B1, share_path, participant_index, key, output_dir, probabilistic=0):

    image = Image.open(share_path).convert('L')
    image_array = (np.array(image) < 128).astype(np.uint8)

    ZM = [[0], [1]]

    if not probabilistic:
        m = B0.shape[1]
        permutations = list(itertools.permutations(range(m)))
        C0 = [B0[:, p] for p in permutations]
        C1 = [B1[:, p] for p in permutations]
        C0, C1 = apply_set_expansion(B0, B1, ZM)
    else:
        m = 1
        C0 = [B0[:, [i]] for i in range(B0.shape[1])]
        C1 = [B1[:, [i]] for i in range(B1.shape[1])]
        C0, C1 = apply_set_expansion(B0, B1, ZM)

    D0 = [c[participant_index] for c in C0]
    D1 = [c[participant_index] for c in C1]

    num_matrices = len(D0)
    bits_per_choice = math.ceil(math.log2(num_matrices))

    height_out, width = image_array.shape
    height = height_out // m

    key_bits_length = height * width * bits_per_choice

    rng = np.random.default_rng(key)
    key_bits = ''.join(rng.choice(['0', '1'], size=key_bits_length))

    secret = np.zeros((height, width), dtype=np.uint8)
    key_index = 0

    for y in range(height):
        for x in range(width):
            start = y * m
            end = start + m
            block = image_array[start:end, x]

            bits = key_bits[key_index:key_index + bits_per_choice]
            key_index += bits_per_choice

            r = int(bits, 2) % num_matrices

            if np.array_equal(block, D0[r]) and np.array_equal(block, D1[r]):
                secret[y, x] = np.random.randint(0, 2)
            elif np.array_equal(block, D0[r]):
                secret[y, x] = 0
            elif np.array_equal(block, D1[r]):
                secret[y, x] = 1
            else:
                secret[y, x] = np.random.randint(0, 2)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_image = Image.fromarray(((1 - secret) * 255).astype(np.uint8))
        path = os.path.join(
            output_dir,
            f"decrypted_seed_participant_{participant_index + 1}.png"
        )
        output_image.save(path)

    return secret
# ======================================================================================================================================================== #


# ======================================================================================================================================================== #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || FORGED SHARES ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  ||  || #
# \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/ #
# ======================================================================================================================================================== #

# ======================================================================================================================================================== #
# Function returning a forged share based on a genuine share and a target fake image, where:
# share_path - path to the original share image
# output_path - path where the forged share will be saved
# m - number of subpixels in a single encoding block
# fake_image_path - path to the target fake image
def create_forged_share(share_path, output_path, m, fake_image_path):

    fake_image = Image.open(fake_image_path).convert("L")
    fake_array = np.array(fake_image)

    FO = np.where(fake_array < 128, 1, 0).astype(np.uint8)

    share = Image.open(share_path).convert("L")
    share_array = np.array(share)

    S = np.where(share_array < 128, 1, 0).astype(np.uint8)

    subpixel_height, width = S.shape

    if subpixel_height % m != 0:
        raise ValueError(
            f"Share height {subpixel_height} is not divisible by m={m}"
        )

    height = subpixel_height // m

    if FO.shape != (height, width):
        raise ValueError(
            f"FO has size {FO.shape}, "
            f"while share corresponds to {height}x{width}"
        )

    forged_share = np.zeros_like(S, dtype=np.uint8)

    for y in range(height):
        for x in range(width):

            block = S[y*m:(y+1)*m, x]

            black_count = int(np.sum(block))

            if FO[y, x] == 0:
                forged_share[y*m:(y+1)*m, x] = block

            else:
                new_block = np.zeros(m, dtype=np.uint8)

                positions = random.sample(
                    range(m),
                    black_count
                )

                for position in positions:
                    new_block[position] = 1

                forged_share[y*m:(y+1)*m, x] = new_block

    output_array = ((1 - forged_share) * 255).astype(np.uint8)

    output_image = Image.fromarray(output_array).convert("L")

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    output_image.save(output_path)

    print(
        f"Forged share saved: {output_path}"
    )

    return forged_share
# ======================================================================================================================================================== #
