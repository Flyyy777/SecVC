from PIL import Image
import numpy as np
import os

# ======================================================================================================================================================== #
# Function returning an image reconstructed from Visual Cryptography shares, where:
# share_paths - list of paths to PNG files containing shares
# output_dir - directory where the decrypted image will be saved
def decrypt(share_paths, output_dir):
    shares = []
    for path in share_paths:
        image = Image.open(path).convert('L')
        image_array = np.array(image)
        binary_array = (image_array < 128).astype(np.uint8)
        shares.append(binary_array)
        print(f"Loaded share: {path}")

    reconstruction = shares[0]
    for share in shares[1:]:
        reconstruction = np.logical_or(reconstruction, share).astype(np.uint8)

    os.makedirs(output_dir, exist_ok=True)
    result = Image.fromarray((1 - reconstruction) * 255).convert('L')
    result_path = os.path.join(output_dir, "decrypted.png")
    result.save(result_path)

    print(f"\nDecrypted image saved to: {result_path}")
    return result
# ======================================================================================================================================================== #
