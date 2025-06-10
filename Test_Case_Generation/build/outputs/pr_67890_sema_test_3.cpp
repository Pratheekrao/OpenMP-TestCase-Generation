```
// RUN: %clang_cc1 -fopenmp -fsyntax-only -verify %s

void foo() {
  int x, y;
  #pragma omp parallel for reduction(+:x)
    for (int i = 0; i < 10; i++) {
      x += i;
    }
  // expected-error{{reduction variable 'x' must be shared in enclosing context}}
  #pragma omp parallel {
    #pragma omp for reduction(+:x)
    for (int i = 0; i < 10; i++) {
      x += i;
    }
  }
}

void bar() {
  int x, y;
  #pragma omp parallel for reduction(+:x) reduction(*:y)
    for (int i = 0; i < 10; i++) {
      x += i;
      y *= i;
    }
  // expected-error{{reduction variable 'x' must be shared in enclosing context}}
  #pragma omp parallel {
    #pragma omp for reduction(+:x) reduction(*:y)
    for (int i = 0; i < 10; i++) {
      x += i;
      y *= i;
    }
  }
}
```