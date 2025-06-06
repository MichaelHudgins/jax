# Copyright 2018 The JAX Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# AMD HIP kernels

load("@rules_python//python:defs.bzl", "py_library")
load(
    "//jaxlib:jax.bzl",
    "if_rocm_is_configured",
    "nanobind_extension",
    "rocm_library",
)

licenses(["notice"])

package(
    default_applicable_licenses = [],
    default_visibility = ["//:__subpackages__"],
)

cc_library(
    name = "hip_vendor",
    hdrs = [
        "//jaxlib/gpu:vendor.h",
    ],
    defines = ["JAX_GPU_HIP=1"],
    deps = [
        "@local_config_rocm//rocm:rocm_headers",
    ],
)

cc_library(
    name = "hip_gpu_kernel_helpers",
    srcs = if_rocm_is_configured(["//jaxlib/gpu:gpu_kernel_helpers.cc"]),
    hdrs = if_rocm_is_configured(["//jaxlib/gpu:gpu_kernel_helpers.h"]),
    copts = [
        "-fexceptions",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":hip_vendor",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ] + if_rocm_is_configured([
        "@local_config_rocm//rocm:rocm_headers",
    ]),
)

rocm_library(
    name = "hip_make_batch_pointers",
    srcs = ["//jaxlib/gpu:make_batch_pointers.cu.cc"],
    hdrs = ["//jaxlib/gpu:make_batch_pointers.h"],
    deps = [
        ":hip_vendor",
        "@local_config_rocm//rocm:rocm_headers",
    ],
)

cc_library(
    name = "hip_blas_handle_pool",
    srcs = ["//jaxlib/gpu:blas_handle_pool.cc"],
    hdrs = ["//jaxlib/gpu:blas_handle_pool.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/synchronization",
        "@local_config_rocm//rocm:hipblas",
        "@local_config_rocm//rocm:rocm_headers",
    ],
)

cc_library(
    name = "miopen_rnn_kernels",
    srcs = ["//jaxlib/gpu:rnn_kernels.cc"],
    hdrs = ["//jaxlib/gpu:rnn_kernels.h"],
    deps = [
        ":ffi_wrapper",
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib:kernel_helpers",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_rocm//rocm:miopen",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_rnn",
    srcs = ["//jaxlib/gpu:rnn.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_rnn",
    deps = [
        ":hip_vendor",
        ":miopen_rnn_kernels",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/strings:str_format",
        "@nanobind",
    ],
)

cc_library(
    name = "hip_solver_handle_pool",
    srcs = ["//jaxlib/gpu:solver_handle_pool.cc"],
    hdrs = ["//jaxlib/gpu:solver_handle_pool.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/synchronization",
        "@local_config_rocm//rocm:hipsolver",
        "@local_config_rocm//rocm:rocm_headers",
    ],
)

cc_library(
    name = "hipsolver_interface",
    srcs = ["//jaxlib/gpu:solver_interface.cc"],
    hdrs = ["//jaxlib/gpu:solver_interface.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_rocm//rocm:hipblas",
        "@local_config_rocm//rocm:hipsolver",
    ],
)

cc_library(
    name = "hipsolver_kernels_ffi",
    srcs = ["//jaxlib/gpu:solver_kernels_ffi.cc"],
    hdrs = ["//jaxlib/gpu:solver_kernels_ffi.h"],
    deps = [
        ":hip_blas_handle_pool",
        ":hip_gpu_kernel_helpers",
        ":hip_make_batch_pointers",
        ":hip_solver_handle_pool",
        ":hip_vendor",
        ":hipsolver_interface",
        "//jaxlib:ffi_helpers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_rocm//rocm:hipblas",
        "@local_config_rocm//rocm:hipsolver",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_solver",
    srcs = ["//jaxlib/gpu:solver.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_solver",
    deps = [
        ":hip_vendor",
        ":hipsolver_kernels_ffi",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_rocm//rocm:hipblas",
        "@local_config_rocm//rocm:hipsolver",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
    ],
)

cc_library(
    name = "ffi_wrapper",
    hdrs = ["//jaxlib/gpu:ffi_wrapper.h"],
    deps = [
        ":hip_vendor",
        "//jaxlib:ffi_helpers",
        "@xla//xla/ffi/api:ffi",
    ],
)

cc_library(
    name = "hipsparse_kernels",
    srcs = ["//jaxlib/gpu:sparse_kernels.cc"],
    hdrs = ["//jaxlib/gpu:sparse_kernels.h"],
    deps = [
        ":ffi_wrapper",
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "//jaxlib/gpu:handle_pool",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_rocm//rocm:hipsparse",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_sparse",
    srcs = ["//jaxlib/gpu:sparse.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_sparse",
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        ":hipsparse_kernels",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/hash",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@local_config_rocm//rocm:hipsparse",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
        "@xla//xla/tsl/python/lib/core:numpy",
    ],
)

cc_library(
    name = "hip_linalg_kernels",
    srcs = ["//jaxlib/gpu:linalg_kernels.cc"],
    hdrs = ["//jaxlib/gpu:linalg_kernels.h"],
    features = ["-use_header_modules"],
    deps = [
        ":hip_blas_handle_pool",
        ":hip_gpu_kernel_helpers",
        ":hip_linalg_kernels_impl",
        ":hip_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "@com_google_absl//absl/strings:str_format",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

rocm_library(
    name = "hip_linalg_kernels_impl",
    srcs = ["//jaxlib/gpu:linalg_kernels.cu.cc"],
    hdrs = ["//jaxlib/gpu:linalg_kernels.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_linalg",
    srcs = ["//jaxlib/gpu:linalg.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_linalg",
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_linalg_kernels",
        ":hip_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
    ],
)

cc_library(
    name = "hip_prng_kernels",
    srcs = ["//jaxlib/gpu:prng_kernels.cc"],
    hdrs = ["//jaxlib/gpu:prng_kernels.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_prng_kernels_impl",
        ":hip_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib:kernel_helpers",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/status",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:c_api",
        "@xla//xla/ffi/api:ffi",
    ],
)

rocm_library(
    name = "hip_prng_kernels_impl",
    srcs = ["//jaxlib/gpu:prng_kernels.cu.cc"],
    hdrs = ["//jaxlib/gpu:prng_kernels.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib:kernel_helpers",
        "@local_config_rocm//rocm:rocm_headers",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_prng",
    srcs = ["//jaxlib/gpu:prng.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_prng",
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_prng_kernels",
        ":hip_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
    ],
)

cc_library(
    name = "hip_hybrid_kernels",
    srcs = ["//jaxlib/gpu:hybrid_kernels.cc"],
    hdrs = ["//jaxlib/gpu:hybrid_kernels.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib:ffi_helpers",
        "//jaxlib/cpu:lapack_kernels",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/types:span",
        "@xla//xla/ffi/api:ffi",
    ],
)

nanobind_extension(
    name = "_hybrid",
    srcs = ["//jaxlib/gpu:hybrid.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_hybrid",
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_hybrid_kernels",
        ":hip_vendor",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/cpu:lapack_kernels",
        "@com_google_absl//absl/base",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
        "@xla//xla/ffi/api:ffi",
    ],
)

cc_library(
    name = "triton_kernels",
    srcs = ["//jaxlib/gpu:triton_kernels.cc"],
    hdrs = ["//jaxlib/gpu:triton_kernels.h"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        ":triton_utils",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/synchronization",
        "@xla//xla/service:custom_call_status",
        "@xla//xla/tsl/platform:env",
        "@xla//xla/tsl/platform:errors",
        "@xla//xla/tsl/util:env_var",
    ],
)

cc_library(
    name = "triton_utils",
    srcs = ["//jaxlib/gpu:triton_utils.cc"],
    hdrs = ["//jaxlib/gpu:triton_utils.h"],
    visibility = ["//visibility:public"],
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@zlib",
    ],
)

nanobind_extension(
    name = "_triton",
    srcs = ["//jaxlib/gpu:triton.cc"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    module_name = "_triton",
    deps = [
        ":hip_gpu_kernel_helpers",
        ":hip_vendor",
        ":triton_kernels",
        ":triton_utils",
        "//jaxlib:absl_status_casters",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/gpu:triton_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
        "@nanobind",
    ],
)

py_library(
    name = "rocm_gpu_support",
    deps = [
        ":_hybrid",
        ":_linalg",
        ":_prng",
        ":_rnn",
        ":_solver",
        ":_sparse",
        ":_triton",
    ],
)

cc_library(
    name = "py_client_gpu",
    srcs = ["//jaxlib/gpu:py_client_gpu.cc"],
    hdrs = ["//jaxlib/gpu:py_client_gpu.h"],
    copts = [
        "-fexceptions",
        "-fno-strict-aliasing",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":hip_vendor",
        "//jaxlib:ffi",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base",
        "@com_google_absl//absl/container:inlined_vector",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/types:span",
        "@dlpack",
        "@nanobind",
        "@xla//third_party/python_runtime:headers",  # buildcleaner: keep
        "@xla//xla:comparison_util",
        "@xla//xla:shape_util",
        "@xla//xla:util",
        "@xla//xla:xla_data_proto_cc",
        "@xla//xla/ffi:ffi_api",
        "@xla//xla/ffi/api:ffi",
        "@xla//xla/pjrt:host_callback",
        "@xla//xla/pjrt:transpose",
        "@xla//xla/python:nb_numpy",
        "@xla//xla/python:types",
        "@xla//xla/service:platform_util",
    ],
)

nanobind_extension(
    name = "rocm_plugin_extension",
    srcs = ["rocm_plugin_extension.cc"],
    module_name = "rocm_plugin_extension",
    deps = [
        ":py_client_gpu",
        "//jaxlib:kernel_nanobind_helpers",
        "//jaxlib/gpu:gpu_plugin_extension",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/strings",
        "@local_config_rocm//rocm:hip",
        "@local_config_rocm//rocm:rocm_headers",
        "@nanobind",
    ],
)

py_library(
    name = "gpu_only_test_deps",
    # `if_rocm_is_configured` will default to `[]`.
    deps = if_rocm_is_configured([
        ":rocm_gpu_support",
        ":rocm_plugin_extension",
    ]),
)
