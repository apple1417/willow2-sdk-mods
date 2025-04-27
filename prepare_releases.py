#!/usr/bin/env python3
import itertools
import re
import shutil
import subprocess
import sys
import tomllib
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

CMAKE_LIST_PRESETS_RE = re.compile('  "(.+)"')
CMAKE_BUILD_DIR_BASE = Path(".out") / "build"


@cache
def cmake_get_presets() -> list[str]:
    """
    Gets the presets which may be used.

    Returns:
        A list of presets.
    """
    try:
        proc = subprocess.run(
            ["cmake", "--list-presets"],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf8",
        )
    except FileNotFoundError:
        return []
    return CMAKE_LIST_PRESETS_RE.findall(proc.stdout)


def cmake_configure(preset: str, extra_args: list[str]) -> None:
    """
    Configures the given CMake preset.

    Args:
        preset: The preset to configure.
        extra_args: Extra CMake args to append to the configure command.
    """
    subprocess.check_call(["cmake", ".", "--preset", preset, *extra_args])


def cmake_install(build_dir: Path) -> None:
    """
    Builds and installs a CMake configuration.

    Args:
        build_dir: The preset's build dir.
    """
    subprocess.check_call(["cmake", "--build", build_dir, "--target", "install"])


@cache
def git_is_dirty() -> bool:
    """
    Checks if the current repo is dirty.

    Returns:
        The version string.
    """
    # This command returns the list of modified files, so any output means dirty
    return any(
        subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout,
    )


def git_get_last_commit_in_dir(path: Path) -> str:
    """
    Gets the commit hash of the last commit in a dir.

    Args:
        path: The path to the dir
    """
    return subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%H", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ).stdout.strip()


def iter_mod_files(mod_folder: Path, debug: bool) -> Iterator[Path]:
    """
    Iterates through all files in the given mod folder which are valid to export.

    Args:
        mod_folder: Path to the mod folder to iterate through.
        debug: True if creating a debug zip.
    Yields:
        Valid files to export.
    """
    with (mod_folder / "pyproject.toml").open("rb") as file:
        data = tomllib.load(file)
        file_override = data.get("tool", {}).get("sdkmod_release_script", {}).get("files", [])
        if file_override:
            yield from itertools.chain.from_iterable(
                mod_folder.glob(pattern) for pattern in file_override
            )
            return

    # Obey .gitignore rules
    for filename in subprocess.run(
        ["git", "ls-files", mod_folder],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ).stdout.splitlines():
        file = Path(filename).resolve()
        if not file.exists() or not file.is_file():
            continue

        if file.suffix in {".cpp", ".h", ".hpp"}:
            continue
        if file.name in {"CMakeLists.txt"}:
            continue

        yield file

    # Extra scan for `.pyd`s, which are gitignored
    for file in mod_folder.glob("**/*.pyd"):
        if file.suffix == ".pyd" and file.stem.endswith("_d") != debug:
            continue

        yield file


def get_pyproject_with_git_version(mod_folder: Path) -> str:
    """
    Gets the contents of the given mod's `pyproject.toml`, with the git version added.

    Args:
        mod_folder: The mod folder to check the git version of.
        pyproject: The current pyproject.toml.
    Returns:
        The new contents of the pyproject.toml after injecting the version.
    """
    # tomllib does not support writing, so we'll need to insert the version manually
    # Unfortunately, the TOML spec is kind of dumb and doesn't give us any good way to insert an
    # arbitrary key - duplicate tables aren't allowed, and a root level `tool.sdkmod.version` will
    # conflict with a separate `[tool.sdkmod]` table anywhere else too
    # This means we need to try parse it manually to find the right spot

    with (mod_folder / "pyproject.toml").open("rb") as file:
        # Still use tomllib to make sure we get an accurate base version
        base_version = tomllib.load(file)["project"]["version"]

        # Then read everything out again to manually parse over
        file.seek(0)
        toml_lines = file.read().decode().splitlines()

    git_version = git_get_last_commit_in_dir(mod_folder)[:8] + (", dirty" if git_is_dirty() else "")
    version_key = f'version = "{base_version} ({git_version})"'

    # To simplify things, we'll ignore inline tables, and the possibility of a raw `[tool]` table
    in_sdkmod_region = False
    for idx, line in enumerate(toml_lines):
        stripped_line = line.strip()

        if stripped_line.startswith("version" if in_sdkmod_region else "tool.sdkmod.version"):
            raise ValueError("'pyproject.toml' appears to already contains a display version")

        if stripped_line == "[tool.sdkmod]":
            in_sdkmod_region = True

        if in_sdkmod_region and not stripped_line:
            toml_lines.insert(idx, version_key)
            break

    else:
        if not in_sdkmod_region:
            toml_lines.append("")
            toml_lines.append("[tool.sdkmod]")
        toml_lines.append(version_key)

    return "\n".join(toml_lines)


def dir_path_arg(arg: str) -> Path:
    """
    Argparse type converter which ensures the arg is a valid directory.

    Args:
        arg: The arg to try parse.
    Returns:
        The corresponding path.
    """
    path = Path(arg)
    if not path.is_dir():
        raise ArgumentTypeError(f"'{path}' is not a valid directory")
    return path.resolve()


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare the release zips.")
    parser.add_argument(
        "folders",
        nargs="*",
        type=dir_path_arg,
        help="The mod folders to zip. Leave empty to try all.",
    )

    group = parser.add_argument_group(
        "cmake options",
        description="CMake helpers to run before preparing the release.",
    )
    group.add_argument(
        "--preset",
        choices=cmake_get_presets(),
        metavar="PRESET",
        help="The preset to use.",
    )
    group.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets.",
    )
    group.add_argument(
        "--configure",
        action="store_true",
        help="Configure CMake before building. Requires '--preset' be given.",
    )
    group.add_argument(
        "-C",
        "--configure-extra-args",
        action="append",
        default=[],
        metavar="...",
        help="Extra args to append to the CMake configure call.",
    )
    group.add_argument(
        "--build",
        action="store_true",
        help="Builds the native modules. Requires '--preset' be given.",
    )

    args = parser.parse_args()

    if args.list_presets:
        print("Available presets:")  # noqa: T201
        print()  # noqa: T201
        for preset in cmake_get_presets():
            print(f'  "{preset}"')  # noqa: T201
        sys.exit(0)

    if args.preset:
        if args.configure:
            cmake_configure(args.preset, args.configure_extra_args)
        if args.build:
            cmake_install(CMAKE_BUILD_DIR_BASE / args.preset)

    for mod_folder in args.folders or (x for x in Path(__file__).parent.iterdir() if x.is_dir()):
        if mod_folder.name.startswith("."):
            continue
        if not (mod_folder / "pyproject.toml").exists():
            continue

        output_file = mod_folder.with_suffix(".sdkmod")
        any_pyds = False
        with ZipFile(output_file, "w", ZIP_DEFLATED, compresslevel=9) as zip_file:
            for file in iter_mod_files(mod_folder, debug=False):
                # Will add this later
                if file.name == "pyproject.toml":
                    continue

                if file.suffix == ".pyd":
                    any_pyds = True

                zip_file.write(file, mod_folder.name / file.relative_to(mod_folder))

            zip_file.writestr(
                str(Path(mod_folder.name) / "pyproject.toml"),
                get_pyproject_with_git_version(mod_folder),
            )
            zip_file.write("LICENSE", Path(mod_folder.name) / "LICENSE")

        # Dynamic libraries cannot be loaded from inside a .sdkmod, so rename if needed
        if any_pyds:
            shutil.move(output_file, output_file.with_suffix(".zip"))
