
# Helper tools such as
import shutil
import pathlib
import subprocess

# Get current python version as a matrix enum

# Get current system cuda version (if present) as a matrix enum

# Get current system data as a matrix enum

# Get current system bazel version

# Get current system clang information (path and version)
def get_clang_path():
  which_clang_output = shutil.which("clang")
  if which_clang_output:
    # If we've found a clang on the path, need to get the fully resolved path
    # to ensure that system headers are found.
    return str(pathlib.Path(which_clang_output).resolve())
  else:
    raise Exception("Clang cannot be found in path")

def get_clang_major_version(clang_path: str):
  clang_version_proc = subprocess.run(
      [clang_path, "-E", "-P", "-"],
      input="__clang_major__",
      check=True,
      capture_output=True,
      text=True,
  )
  major_version = int(clang_version_proc.stdout)

  return major_version

# Download bazel or bazelisk 



