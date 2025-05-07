from OptimizerAgent.agent_functions import cached_get_optimization_techniques, cached_improve_code
from OptimizerAgent.testing_agent import test_code
import numpy as np

def svd_example(matrix):
    """Perform SVD using NumPy's LAPACK interface."""
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    return u, s, vh

# Example matrix
matrix = np.random.rand(100, 100)

# Convert the SVD function to a string of code
svd_code = """
import numpy as np

def svd_example(matrix):
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    return u, s, vh

matrix = np.random.rand(100, 100)
svd_example(matrix)
"""

# Generate optimization techniques
optimization_techniques = cached_get_optimization_techniques(svd_code, 3)

# Apply optimization techniques
optimized_versions = [svd_code]
for technique in optimization_techniques:
    improved_code = cached_improve_code(svd_code, [technique])
    if improved_code:
        optimized_versions.append(improved_code)

# Test all versions
test_results = test_code(optimized_versions)

# Display results
for i, result in enumerate(test_results):
    print(f"Version {i}: Execution Time = {result['execution_time']}, Memory Usage = {result['memory_usage']}")