```
// RUN: %clang_cc1 -fopenmp -fsyntax-only -verify %s

void test1() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test2() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(static, 2)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test3() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(dynamic, 2)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test4() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(runtime)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test5() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(auto)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test6() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(static)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test7() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(dynamic)
  for (i = 0; i < 10; i++) {
    x += i;
  }
}

void test8() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(static, 2) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}

void test9() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(dynamic, 2) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}

void test10() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(runtime) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}

void test11() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(auto) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}

void test12() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(static) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}

void test13() {
  int i, x = 5;
#pragma omp parallel for reduction(+:x) schedule(dynamic) collapse(2)
  for (i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
      x += i + j;
    }
  }
}
```