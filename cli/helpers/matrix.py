# This file contains enums and artifact names for current supported build matrix in CI

from enum import Enum

# TODO: need to add the concept of "experimental" or other non ci builds, will let us log an indicate it may not be supported

# Enum for current supported python versions
class PythonVersion(str, Enum):
    PYTHON_3_9 = "3.9"
    PYTHON_3_10 = "3.10"
    PYTHON_3_11 = "3.11"
    PYTHON_3_12 = "3.12"

    # print the python version to match the bazel flag used
    def __str__(self):
        return "python" + self.value

    # default_version will return the current python version if it is supported, otherwise None
    @staticmethod
    def default_version():
        import sys
        # TODO: just string concat and see if the value works, if not return None (will remove this extra 9,10,11,12)
        if sys.version_info.major == 3 and sys.version_info.minor in [9, 10, 11, 12]:
            return PythonVersion(str(sys.version_info.major) + "." + str(sys.version_info.minor))
        else:
            return None

    # parse_cli allows for several variants of possible user input to cut back on annoying errors
    @staticmethod
    def parse_cli(user_string: str):
        # replace any occurances of "_" with "." in user_string
        user_string = user_string.replace("_", ".")
        return PythonVersion(user_string)


# Enum current supported CUDA versions
class CUDAVersion(str, Enum):
    CUDA_12_1 = "12_1"
    CUDA_12_3 = "12_3"

    # print the CUDA version to match the bazel flag used
    def __str__(self):
        return "cuda_" + self.value
    
    # The default_verion for cuda is 12.3
    @staticmethod
    def default_version():
        return CUDAVersion.CUDA_12_3

# Enum for current supported systems
class System(str, Enum):
    LINUX_X86_64 = "linux_x86_64"
    LINUX_AARCH64 = "linux_aarch64"
    WINDOWS_X86_64 = "windows_x86_64"
    MACOS_X86_64 = "macos_x86_64"
    MACOS_ARM64 = "macos_arm64"

    # print the system version to match the bazel flag used
    def __str__(self):
        return str(self.value)

    # TODO: do system detection with platform to determine current system as default if it is supported
    @staticmethod
    def default_version():
        return System.LINUX_X86_64


# ci_supported_jaxlib is a matrix containing all values of system and python version combinations
ci_supported_jaxlib = [
    (system, python_version)
    for system in System
    for python_version in PythonVersion
]
def is_jaxlib_supported(system: System, python_version: PythonVersion):
    return (system, python_version) in ci_supported_jaxlib


# ci_supported_cuda_systems is a list of cuda supported systems
ci_supported_cuda_systems = [
    System.LINUX_X86_64,
    System.LINUX_AARCH64,
]

# ci_supported_jax_plugins is a matrix of all supported jax plugin combinations
ci_supported_jax_plugins = [
    (python_version, cuda_version, system)
    for python_version in PythonVersion
    for cuda_version in CUDAVersion
    for system in ci_supported_cuda_systems
]
def is_jax_plugin_supported(python_version: PythonVersion, cuda_version: CUDAVersion, system: System):
    return (python_version, cuda_version, system) in ci_supported_jax_plugins


# ci_supported_jax_pjrt is a matrix of all cuda versions and ci_supported_cuda_systems
ci_supported_jax_pjrt = [
    (cuda_version, system)
    for cuda_version in CUDAVersion
    for system in ci_supported_cuda_systems
]
def is_jax_pjrt_supported(cuda_version: CUDAVersion, system: System):
    return (cuda_version, system) in ci_supported_jax_pjrt

