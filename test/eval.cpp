#include <iostream>
#include <vector>

extern "C" {
    void dgsvd_(char *JOBU, char *JOBV, char *JOBQ, int *M, int *N, int *P,
                int *K, int *L, double *A, int *LDA, double *B, int *LDB, 
                double *ALPHA, double *BETA, double *U, int *LDU, double *V, 
                int *LDV, double *Q, int *LDQ, double *WORK, int *IWORK, int *INFO);
}

int main() {
    // Define matrix sizes
    int M = 3, N = 3, P = 3;
    int K, L;
    int INFO;

    // Example matrices A and B
    std::vector<double> A = {1.0, 2.0, 3.0,
                             4.0, 5.0, 6.0,
                             7.0, 8.0, 9.0};  // MxN matrix

    std::vector<double> B = {9.0, 8.0, 7.0,
                             6.0, 5.0, 4.0,
                             3.0, 2.0, 1.0};  // PxN matrix

    int LDA = M, LDB = P;
    
    std::vector<double> ALPHA(N), BETA(N);
    std::vector<double> U(M*M, 0), V(P*P, 0), Q(N*N, 0);
    int LDU = M, LDV = P, LDQ = N;

    std::vector<double> WORK(10 * N);
    std::vector<int> IWORK(N);

    char JOBU = 'U', JOBV = 'V', JOBQ = 'Q';  // Compute all U, V, and Q

    // Call LAPACK's dgsvd
    dgsvd_(&JOBU, &JOBV, &JOBQ, &M, &N, &P, &K, &L, A.data(), &LDA, B.data(), &LDB,
           ALPHA.data(), BETA.data(), U.data(), &LDU, V.data(), &LDV, Q.data(), &LDQ,
           WORK.data(), IWORK.data(), &INFO);

    if (INFO == 0) {
        std::cout << "GSVD computed successfully.\n";
    } else {
        std::cerr << "dgsvd failed with INFO = " << INFO << "\n";
    }

    return 0;
}


// g++ -o eval eval.cpp -llapacke -llapack -lblas
