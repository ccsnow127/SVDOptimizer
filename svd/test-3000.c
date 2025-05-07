
#include <stdio.h>
#include <stdlib.h>
#include <lapacke.h>
#include <unistd.h> // Include this for the sleep function

#define MIN(a, b) (((a) < (b)) ? (a) : (b))

void read_csv(const char* filename, int** ms, int** ns, int* count) {
    // sleep(1);
    FILE* file = fopen(filename, "r");
    if (!file) {
        perror("Error opening file");
        exit(EXIT_FAILURE);
    }
    
    // Skip the header
    fscanf(file, "%*[^\n]\n");
    
    // Count the number of lines
    *count = 0;
    while (!feof(file)) {
        int m, n;
        if (fscanf(file, "%d,%d\n", &m, &n) == 2) {
            (*count)++;
        }
    }
    
    // Allocate memory for m and n arrays
    *ms = (int*)malloc(*count * sizeof(int));
    *ns = (int*)malloc(*count * sizeof(int));
    
    // Rewind file and skip header again
    rewind(file);
    fscanf(file, "%*[^\n]\n");
    
    // Read m and n values
    for (int i = 0; i < *count; i++) {
        fscanf(file, "%d,%d\n", &(*ms)[i], &(*ns)[i]);
    }
    
    fclose(file);
}

int lapack(int m, int n, double* a, double* s, double* u, double* vt, double* superb) {
    // Call LAPACKE_dgesvd with correct parameters
    return LAPACKE_dgesvd(LAPACK_COL_MAJOR, 'A', 'A', m, n, a, m, s, u, m, vt, n, superb);
}

int main() {
    const char* filename = "datasets/svd_dataset_3000.csv";
    int* ms, *ns, count;
    
    read_csv(filename, &ms, &ns, &count);
    
    for (int i = 0; i < count; i++) {
        int m = ms[i];
        int n = ns[i];
        // int m = 100;
        // int n = 100;
        
        double* a = (double*)malloc(m * n * sizeof(double));
        // Initialize matrix 'a' with random values or specific data
        for (int j = 0; j < m * n; j++) {
            a[j] = (double)rand() / RAND_MAX; // Example: random values
        }

        double* s = (double*)malloc(MIN(m, n) * sizeof(double)); // Singular values
        double* u = (double*)malloc(m * m * sizeof(double));     // Left singular vectors
        double* vt = (double*)malloc(n * n * sizeof(double));    // Right singular vectors (transposed)
        double* superb = (double*)malloc(MIN(m, n) * sizeof(double)); // Superdiagonal elements

        // int info = lapack(m, n, a, m, s, u, m, vt, n, superb);
        int info = lapack(m, n, a, s, u, vt, superb);
        
        if (info > 0) {
            printf("The algorithm computing SVD failed to converge for dataset %d.\n", i);
            exit(EXIT_FAILURE);
        }

        printf("Singular values for dataset %d:\n", i);
        for (int j = 0; j < MIN(m, n); j++) {
            printf("%f\n", s[j]);
        }
        
        free(a);
        free(s);
        free(u);
        free(vt);
        free(superb);
    }
    
    free(ms);
    free(ns);
    
    return 0;
}
// gcc -pg -o test test.c -llapacke -llapack -lblas
//  valgrind ./test
//    gprof my_program gmon.out > profile.txt