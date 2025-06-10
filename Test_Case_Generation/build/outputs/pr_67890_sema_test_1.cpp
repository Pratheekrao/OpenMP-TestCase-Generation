// RUN: %clang_cc1 -fopenmp -fsyntax-only -verify %s

void test1() {
  int a = 5;
  int b = 10;
  #pragma omp parallel for reduction(+:a:b)
  for (int i = 0; i < 10; i++) {
    a = a + b;
  }
  // expected-error{{reduction variable 'a' in '#pragma omp parallel for' has invalid initializer}}
}

void test2() {
  int a = 5;
  int b = 10;
  #pragma omp parallel for reduction(+:a:b)
  for (int i = 0; i < 10; i++) {
    a = a + b;
  }
  // expected-error{{reduction variable 'a' in '#pragma omp parallel for' has invalid initializer}}
}

void test3() {
  int a = 5;
  int b = 10;
  #pragma omp parallel for reduction(+:a:)
  for (int i = 0; i < 10; i++) {
    a = a + b;
  }
  // expected-error{{reduction variable 'a' in '#pragma omp parallel for' has invalid initializer}}
}

void test4() {
  int a = 5;
  int b = 10;
  #pragma omp parallel for reduction(+:a:b:c)
  for (int i = 0; i < 10; i++) {
    a = a + b;
  }
  // expected-error{{reduction variable 'c' in '#pragma omp parallel for' has invalid initializer}}