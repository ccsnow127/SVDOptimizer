#include <stdio.h>
#include <stdlib.h>
#include <lapacke.h>

#define MIN(a, b) (((a) < (b)) ? (a) : (b))


int main() {

    int m = 10000;
    int n = 10000;
    double* a = (double*)malloc(m * n * sizeof(double));

    double* s = (double*)malloc(MIN(m, n) * sizeof(double)); // Singular values
    double* u = (double*)malloc(m * m * sizeof(double));     // Left singular vectors
    double* vt = (double*)malloc(n * n * sizeof(double));    // Right singular vectors (transposed)
    double* superb = (double*)malloc(MIN(m, n) * sizeof(double)); // Superdiagonal elements (for dgesvd)

    int info = LAPACKE_dgesvd(LAPACK_COL_MAJOR, 'A', 'A', m, n, a, m, s, u, m, vt, n, superb);

    
    if (info > 0) {
        printf("The algorithm computing SVD failed to converge.\n");
        exit(1);
    }

    printf("Singular values:\n");
    for (int i = 0; i < MIN(m, n); i++) {
        printf("%f\n", s[i]);
    }
    
    free(a);
    free(s);
    free(u);
    free(vt);
    free(superb);

}
// gcc -pg -o test test.c -llapack -lblas
// gprof -l test gmon.out > analysis.txt
// gcc -pg -o test test.c -llapacke -llapack -lblas -lm
// gcc -g -O1 -o test test.c -llapacke -llapack -lblas -lm


