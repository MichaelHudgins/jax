#!/usr/bin/python
# A cli using argparse that accepts the enums defined in matrix.py as options
import asyncio
import argparse
import sys
import logging
from helpers import matrix, command, tools, output

logger = logging.getLogger()


def add_python_argument(parser: argparse.ArgumentParser):
  parser.add_argument(
    "--python-version",
    type=matrix.PythonVersion.parse_cli,
    choices=list(matrix.PythonVersion),
    default=matrix.PythonVersion.default_version(),
    help="Python version to use",
  )


def add_system_argument(parser: argparse.ArgumentParser):
  parser.add_argument(
    "--system",
    type=matrix.System,
    choices=list(matrix.System),
    default=matrix.System.default_version(),
    help="System to use",
  )


def add_cuda_argument(parser: argparse.ArgumentParser):
  # TODO: should probably make this naming agnostic to allow for amd or intel
  parser.add_argument(
    "--cuda-version",
    type=matrix.CUDAVersion,
    choices=list(matrix.CUDAVersion),
    default=matrix.CUDAVersion.default_version(),
    help="CUDA version to use",
  )


def add_gloabl_arguments(parser: argparse.ArgumentParser):
  # These are seperate simply because subcommands with argparse do not allow for
  # intermixed parsing.  Arg parse will require any top level optional arguments
  # to come before the command (which at least to me is not intuative) for example
  # the default behavior for verbose requires
  # cli.py --verbose jaxlib --python 3.10
  # instead of
  # cli.py jaxlib --python 3.10 --verbose
  # by adding them as sub commands we restore it to looking for it at the end
  parser.add_argument(
    "--release",
    action="store_true",
    help="""
        Flags as requesting a release or release like build.  Setting this flag will assume
        multiple settings expected in release and CI builds. 
        These are set by the release options in .bazelrc. To see best how this flag resolves
        you can run the artifact of choice with "--release -dry-run" to get the commands issued
        to bazel for that artifact
    """,
  )
  parser.add_argument("--dry-run", action="store_true", help="Dry run")
  parser.add_argument("--verbose", action="store_true", help="Verbose output")
  parser.add_argument("--bazel_options", nargs="?")


async def main():
  parser = argparse.ArgumentParser(
    description="Helper script for building/testing JAX, jaxlib, plugins, and pjrt",
  )

  # add subcommands that build either jax, jaxlib, plugin, pjrt
  subparsers = parser.add_subparsers(dest="command")

  jax_parser = subparsers.add_parser("jax")

  jaxlib_parser = subparsers.add_parser("jaxlib")
  add_python_argument(jaxlib_parser)
  add_system_argument(jaxlib_parser)

  plugin_parser = subparsers.add_parser("plugin")
  pjrt_parser = subparsers.add_parser("pjrt")

  # Add global options, see "add_global_arguments" for why we do this
  for _, subparser in subparsers.choices.items():
    add_gloabl_arguments(subparser)

  args = parser.parse_args()

  # First configure our logger
  level = logging.DEBUG if args.verbose else logging.INFO
  # TODO: add the file option
  output.configure_logger(logger=logger, min_level=level, file_path=None)

  # Find the bazel command, we will be needing it

  # Find clang unless "--use-clang" is false.

  # If "--clang-path" is specified, we use that, if --release is set, we will defer to the release .bazelrc value for now.
  # Otherwise we look for it
  # TODO: this interaction is  akward, can this be fixed by use of platforms instead of TF's janky toolchains?

  # Find what version of clang this is.  We use it in a few places to determine extra flags

  if args.command == "jax":
    logger.info("Building jax")
  elif args.command == "jaxlib":
    logger.info(
      f"Building jaxlib with python version {args.python_version} for system {args.system}"
    )
    # Check if args.python_version and args.system are in the matrix: matrix.ci_supported_jaxlib
    if not matrix.is_jaxlib_supported(
      system=args.system, python_version=args.python_version
    ):
      logger.error(
        f"{args.python_version} and {args.system} are not supported for jaxlib"
      )
  elif args.command == "plugin":
    logger.info("Building plugin")
  elif args.command == "pjrt":
    logger.info("Building pjrt")
  else:
    logger.info("Invalid command")
    # print help and exit
    parser.print_help()
    sys.exit(1)

  # Just testing command
  # Give the user the option to install it into the current python bin path
  #   check_package_is_installed(python_bin_path, python_version, "wheel")
  #   check_package_is_installed(python_bin_path, python_version, "build")
  #   check_package_is_installed(python_bin_path, python_version, "setuptools")

  executor = command.SubprocessExecutor()
  await executor.run('for i in {1..2}; do echo "Iteration $i"; sleep 1; done')
  # Clang it
  clang = tools.get_clang_path()

  bazel_command = command.CommandBuilder("bazelisk run")
  bazel_command.append("--config=linux_release_x86")
  # If clang
  bazel_command.append(f"--action_env CLANG_COMPILER_PATH={clang}")
  bazel_command.append(f"--repo_env CC={clang}")
  bazel_command.append(f"--repo_env BAZEL_COMPILER={clang}")
  # Things that really should be in an rc option
  bazel_command.append("--")
  bazel_command.append("//jaxlib/tools:build_wheel")
  # Next 3 are not required for the build but are for the run, probably check with yash on why these are two seperate steps in ci
  bazel_command.append("--output_path=dist/")  # Optional field to replace
  bazel_command.append("--cpu=x86_64")  # Replace with architecture
  bazel_command.append(
    '--jaxlib_git_hash="$(git rev-parse HEAD)"'
  )  # Figure out if needed and if so make it a tool call to get this hash

  await executor.run(bazel_command.command)

  # wheel_command = command.CommandBuilder("bazel-bin/jaxlib/tools/build_wheel")
  # wheel_command.append("--output_path=dist/") # Optional field to replace
  # wheel_command.append("--cpu=x86_64") # Replace with architecture
  # wheel_command.append("--jaxlib_git_hash=\"$(git rev-parse HEAD)\"") # Figure out if needed and if so make it a tool call to get this hash
  # await executor.run(wheel_command.command, dry_run=True)


if __name__ == "__main__":
  asyncio.run(main())
