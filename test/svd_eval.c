#include <stdio.h>
#include <stdlib.h>
#include <lapacke.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <unistd.h>

#define MIN(a, b) (((a) < (b)) ? (a) : (b))

// Function to read an npy file (assuming double-precision, row-major order)
void read_npy(const char *filename, double *matrix, int size) {
    FILE *file = fopen(filename, "rb");
    if (!file) {
        printf("Error: Cannot open %s\n", filename);
        exit(1);
    }
    fseek(file, 128, SEEK_SET);  // Skip .npy header
    fread(matrix, sizeof(double), size, file);
    fclose(file);
}

// Function to create output directory if it doesn't exist
void create_directory(const char *dir) {
    struct stat st = {0};
    if (stat(dir, &st) == -1) {
        mkdir(dir, 0700);
    }
}

// Function to get peak memory usage (Resident Set Size in KB)
long get_peak_memory_usage() {
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    return usage.ru_maxrss;  // Peak memory usage in KB
}

// Function to get file size
long get_file_size(const char *filename) {
    struct stat st;
    if (stat(filename, &st) == 0)
        return st.st_size;
    return -1;
}

int main() {
    int m = 100, n = 100;
    char *input_files[] = {
        "svd_dataset/random_matrix.npy",
        "svd_dataset/diagonal_matrix.npy",
        "svd_dataset/low_rank_matrix.npy",
        "svd_dataset/perturbed_identity.npy",
        "svd_dataset/noisy_matrix.npy"
    };
    char *output_folder = "svd_results";
    create_directory(output_folder);

    for (int file_idx = 0; file_idx < 5; file_idx++) {
        char *input_file = input_files[file_idx];
        printf("Processing: %s\n", input_file);

        double *a = (double *)malloc(m * n * sizeof(double));
        double *s = (double *)malloc(MIN(m, n) * sizeof(double));
        double *u = (double *)malloc(m * m * sizeof(double));
        double *vt = (double *)malloc(n * n * sizeof(double));
        double *superb = (double *)malloc(MIN(m, n) * sizeof(double));

        read_npy(input_file, a, m * n);  // Load dataset

        // Get initial CPU usage
        struct rusage usage_before;
        getrusage(RUSAGE_SELF, &usage_before);

        // Get peak memory usage before computation
        long peak_memory_before = get_peak_memory_usage();

        // Start execution timing
        clock_t start = clock();
        int info = LAPACKE_dgesvd(LAPACK_COL_MAJOR, 'A', 'A', m, n, a, m, s, u, m, vt, n, superb);
        clock_t end = clock();

        // Get peak memory usage after computation
        long peak_memory_after = get_peak_memory_usage();

        // Get final CPU usage
        struct rusage usage_after;
        getrusage(RUSAGE_SELF, &usage_after);

        double elapsed_time = ((double)(end - start)) / CLOCKS_PER_SEC;

        // Calculate CPU usage in seconds
        double user_cpu_time = (usage_after.ru_utime.tv_sec - usage_before.ru_utime.tv_sec) +
                               (usage_after.ru_utime.tv_usec - usage_before.ru_utime.tv_usec) / 1e6;
        double system_cpu_time = (usage_after.ru_stime.tv_sec - usage_before.ru_stime.tv_sec) +
                                 (usage_after.ru_stime.tv_usec - usage_before.ru_stime.tv_usec) / 1e6;

        if (info > 0) {
            printf("SVD failed to converge for %s\n", input_file);
            exit(1);
        }

        // Save singular values
        char output_singular_file[256];
        snprintf(output_singular_file, sizeof(output_singular_file), "%s/singular_values_%d.txt", output_folder, file_idx);
        FILE *s_file = fopen(output_singular_file, "w");
        for (int i = 0; i < MIN(m, n); i++) {
            fprintf(s_file, "%f\n", s[i]);
        }
        fclose(s_file);

        // Get file size of singular values
        long singular_file_size = get_file_size(output_singular_file);

        // Save performance metrics
        char output_perf_file[256];
        snprintf(output_perf_file, sizeof(output_perf_file), "%s/performance_log.txt", output_folder);
        FILE *perf_file = fopen(output_perf_file, "a");
        fprintf(perf_file, "File: %s, Time: %f sec, User CPU Time: %f sec, System CPU Time: %f sec, Peak Mem Before: %ld KB, Peak Mem After: %ld KB, Output File Size: %ld bytes\n",
                input_file, elapsed_time, user_cpu_time, system_cpu_time, peak_memory_before, peak_memory_after, singular_file_size);
        fclose(perf_file);

        // Cleanup
        free(a);
        free(s);
        free(u);
        free(vt);
        free(superb);
    }

    printf("Results stored in %s/\n", output_folder);
    return 0;
}
