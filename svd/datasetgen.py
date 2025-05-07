import csv
import random
import os

def generate_dataset(filename, num_samples, m_range=(10, 200), n_range=(10, 200)):
    """Generate a dataset of (m, n) pairs and save it as a CSV file."""
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["m", "n"])  # Write header
        
        for _ in range(num_samples):
            m = random.randint(*m_range)
            n = random.randint(*n_range)
            writer.writerow([m, n])

if __name__ == "__main__":
    os.makedirs("datasets", exist_ok=True)  # Ensure the directory exists

    for i, exponent in enumerate(range(2, 7)):  
        num_samples = 1000 * exponent
        filename = f"datasets/svd_dataset_{num_samples}.csv"
        print(f"Generating {filename} with {num_samples} samples...")
        generate_dataset(filename, num_samples)

    print("All datasets have been generated.")
