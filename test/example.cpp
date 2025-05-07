#include <iostream>
#include <lapacke.h>

int main() {
    // Define a 3x3 matrix in column-major order
    double A[3*3] = {
        1.0, 4.0, 7.0,  // First column
        2.0, 5.0, 8.0,  // Second column
        3.0, 6.0, 9.0   // Third column
    };

    // Dimensions
    int m = 3; // Number of rows
    int n = 3; // Number of columns
    int lda = m; // Leading dimension of A

    // Allocate space for the singular values and singular vectors
    double s[3];    // Singular values
    double u[3*3];  // Left singular vectors
    double vt[3*3]; // Right singular vectors (transposed)

    // Compute the SVD
    int info = LAPACKE_dgesdd(LAPACK_COL_MAJOR, 'A', m, n, A, lda, s, u, lda, vt, n);

    // Check for convergence
    if (info > 0) {
        std::cerr << "The algorithm computing SVD failed to converge." << std::endl;
        return 1;
    }

    // Output the singular values
    std::cout << "Singular values:" << std::endl;
    for (int i = 0; i < std::min(m, n); i++) {
        std::cout << s[i] << std::endl;
    }

    // Output the left singular vectors (U)
    std::cout << "\nLeft singular vectors (U):" << std::endl;
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < m; j++) {
            std::cout << u[i + j*lda] << " ";
        }
        std::cout << std::endl;
    }

    // Output the right singular vectors (V^T)
    std::cout << "\nRight singular vectors (V^T):" << std::endl;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            std::cout << vt[i + j*n] << " ";
        }
        std::cout << std::endl;
    }

    return 0;
}

// g++ -o example example.cpp -llapacke -llapack -lblas
