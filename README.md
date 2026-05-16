# Secure Visual Cryptography

![](image.png)


## Overview

This project is an implementation of the visual cryptography system described in article: ***Security of visual cryptography techniques: an overview of
algorithms, their properties, applications, and potential attack
vectors***. It provides a practical realization of the methods and experiments presented in the article, allowing users to reproduce the results and explore the mechanisms in action.

The project includes:

* **Two visual cryptography models: deterministic and probabilistic** 
* **Contrast optimization** 
* **Known-key attacks with mitigation** 
* **Share forgery with verification** 

Using this system, a secret image can be split into multiple shares, with reconstruction only possible from authorized combinations. 

---

## Features
 
 
**Key-based Decryption**

   * Reconstruct a secret image from a single share using a known random key.
   * Supports both deterministic and probabilistic visual cryptography.

**Mitigation Against Attacks**

   * Applies *set expansion* to increase the number of possible subpixel patterns.
   * Protects against known-key attacks.

**Forged Share Generation**

   * Create fake shares from existing shares.
   * Create verification shares for increased security.

---

## Installation

```bash
git clone https://github.com/Flyyy777/SecVC
```

**Dependencies:**

* Python 3.10+
* Pillow
* SciPy
* NumPy

---

## Project Structure

```
SecVC/
│
├── constuctions.py         # Functions for linear program solving and constructing basis matrices for (k, n) schemes
├── encrypt.py              # Functions for encrypting images using visual cryptography and splitting basis matrices into columns
├── decrypt.py              # Functions for decrypting images from visual cryptography shares
├── attacks.py              # Functions for key-based decryption and generating forged shares
├── mitigations.py          # Functions for mitigation during encryption, verification shares, and helper routines
├── tools.py                # Utility functions for calculating γNS, P, and Φ metrics
├── image.png               # Example secret image
├── fake_image.png          # Example target image for forged shares
├── tic.png                 # Example verification image 
└── README.md               # Project documentation
```

For exact details on the implementation, refer to the comments within the code.

---


## How it works



1. **Encryption**

   * Each pixel in the secret image is represented (encrypted) by a block of subpixels across shares.
   * Basis matrices `B0` and `B1` with ***contrast*** and ***security*** properties define patterns for white and black pixels.
   * A random number sequence (the key) is used to select a specific pattern from the basis matrices for each pixel.
   * The selected pattern is split into rows, and each row is assigned to a participant as a subpixel pattern.
   * These subpixel patterns are combined across all pixels to generate the shares.

2. **Decryption**

   * To recover the secret image, at least the threshold number of shares must be correctly superimposed.
   * Superimposition is performed using a logical `OR` operation on corresponding subpixels across all shares.
   * The resulting vector for each pixel expansion has a Hamming weight that indicates the original pixel color.
   * This process reconstructs the original image as interpreted by the human visual system.

3. **Probabilistic Model**

   * The probabilistic model encrypts each secret pixel similarly to the deterministic model, but without expanding the image.
   * Decryption in this model reproduces the secret **globally**, but individual pixels may be incorrect, introducing noise. Pixel recovery is thus probabilistic.
   * Encryption matrices can be derived by transforming deterministic matrices.

4. **Optimal Contrast**

   * The goal is to maximize the visual difference (contrast) between black and white pixels in decrypted images.
   * Basis matrices `B0` and `B1` are optimized to achieve the highest possible `γ` for given `(k, n)` parameters.
   * Linear programming is used to calculate the optimal fractions of columns with specific numbers of ones.
   * Constraints ensure all fractions are non-negative, sum to 1, and satisfy security requirements.
   * The resulting matrices are then scaled to integer sizes for practical use in share generation.

5. **Known Key-attack**

   * In a known key attack, an attacker with access to the encryption key and a subset of shares can potentially recover part or all of the secret image.
   * Some participants may be able to fully reconstruct certain pixels, while others gain no information, depending on their share and the matrix positions.
   * Mitigation reduces the amount of information any single share can reveal, even if the key is known.
   * It works by adding additional matrix permutations so that for any share subset, the chosen matrices do not always disclose the pixel color.
   * This evens out the information leakage across all shares, lowering the maximum probability of successful decryption by an attacker.

6. **Share Forgery**

   * Attacker generates fake shares using one known share or by mimicking share patterns without knowing any real share.
   * When combined with the legitimate shares, the fake shares reveal an attacker-chosen image instead of the original secret.
   * Each participant receives a verification share alongside the encryption share.
   * Overlaying a verification share with any suspicious share reveals whether it is genuine or fake, preventing forgery attacks.





---

## References

* Muszyński, M., & Wodo, W. (2026). *Security of visual cryptography techniques: an overview of
algorithms, their properties, applications, and potential attack
vectors.*

---

## License

MIT License © 2026 Flyyy777

---
