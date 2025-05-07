import numpy as np
import os

# Directory to save dataset
dataset_dir = "svd_dataset"
os.makedirs(dataset_dir, exist_ok=True)

# Dataset settings
m, n = 100, 100  # Matrix size

# 1. Random Matrix (Standard Case)
random_matrix = np.random.randn(m, n)
np.save(os.path.join(dataset_dir, "random_matrix.npy"), random_matrix)

# 2. Diagonal Dominant Matrix
diagonal_values = np.linspace(1, 100, min(m, n))  # Spread singular values
diagonal_matrix = np.diag(diagonal_values)
np.save(os.path.join(dataset_dir, "diagonal_matrix.npy"), diagonal_matrix)

# 3. Low-Rank Matrix (Rank 10)
U = np.random.randn(m, 10)
V = np.random.randn(10, n)
low_rank_matrix = U @ V  # Construct a rank-10 matrix
np.save(os.path.join(dataset_dir, "low_rank_matrix.npy"), low_rank_matrix)

# 4. Perturbed Identity Matrix
identity_matrix = np.eye(m, n)
perturbed_identity = identity_matrix + 0.01 * np.random.randn(m, n)  # Small noise
np.save(os.path.join(dataset_dir, "perturbed_identity.npy"), perturbed_identity)

# 5. Noisy Matrix (Diagonal + Random Noise)
noise = 0.05 * np.random.randn(m, n)
noisy_matrix = diagonal_matrix + noise
np.save(os.path.join(dataset_dir, "noisy_matrix.npy"), noisy_matrix)

print(f"Dataset created in {dataset_dir}")
