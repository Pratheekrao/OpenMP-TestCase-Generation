; RUN: %clang_cc1 -fopenmp -emit-llvm %s -o - | FileCheck %s

declare void @__kmpc_for_static_init_4(i32, i32, i32)

define i32 @test_signed_sub() {
  %t1 = sub nsw i32 2147483647, 1
  call void @__kmpc_for_static_init_4(i32 0, i32 2147483647, i32 1)
  ret i32 0
}

define i32 @test_unsigned_sub() {
  %t1 = sub nuw i32 4294967295, 1
  call void @__kmpc_for_static_init_4(i32 0, i32 4294967295, i32 1)
  ret i32 0
}

; CHECK: define i32 @test_signed_sub
; CHECK: sub nsw i32 2147483647, 1
; CHECK: call void @__kmpc_for_static_init_4(i32 0, i32 2147483647, i32 1)

; CHECK: define i32 @test_unsigned_sub
; CHECK: sub nuw i32 4294967295, 1
; CHECK: call void @__kmpc_for_static_init_4(i32 0, i32 4294967295, i32 1)
