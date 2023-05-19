#!/usr/bin/python3
import logging
from typing import Optional, List
from collections import OrderedDict
import os
import re
import typer
from dataclasses import dataclass

logging.basicConfig()


class BadHeading(ValueError):
    pass


@dataclass
class ArchSection:
    path: str
    relative_path: str
    level: int
    body: str
    title: str


def _check_format(input: str):
    if not input.strip().startswith("# "):
        raise BadHeading()


def _get_readme(file_dir: str, fname: str) -> Optional[str]:
    file_path: str = os.path.join(file_dir, fname)
    logging.debug("Looking for a file at %s", file_path)

    if os.path.isfile(file_path):
        logging.debug("Found a file at %s", file_path)
        with open(file_path, "r") as f:
            logging.debug("Reading file %s", file_path)
            readme_str: str = f.read()
        try:
            _check_format(readme_str)
        except BadHeading:
            print(
                f"WARNING: Readme at {file_path} does not start with a top level heading. Output structure may be malformed."
            )
        return readme_str
    else:
        return None


def _is_dotfile(path: str):
    path_split = path.split("/")

    nonroots: List[str] = path_split[1:]
    for dir in nonroots:
        if dir.startswith("."):
            return True
    return False


def _reformat_readme(input: str, level: int):
    regex = re.compile(r"(?m)(\[[^][]*]\([^()]*\))|^#.*", re.IGNORECASE)
    prefix_levels: str = "#" * (level - 1)
    out: str = regex.sub(
        lambda x: x.group(1) if x.group(1) else f"{prefix_levels}{x.group(0)}", input
    )
    return out


def _create_parents(output: OrderedDict, directory_path: str, root_directory: str):
    relative_path = os.path.relpath(directory_path, root_directory)
    relative_path_split = relative_path.split("/")

    for i, _ in enumerate(relative_path_split):
        parent_relative_path: str = "/".join(relative_path_split[:i])

        parent_absolute_path: str = os.path.join(root_directory, parent_relative_path)

        if parent_relative_path and (parent_absolute_path not in output):
            logging.debug("Creating parent path %s", parent_relative_path)

            parent_name = relative_path_split[i - 1].upper()
            parent_level: str = "#" * (i + 1)

            output[parent_absolute_path] = ArchSection(
                parent_absolute_path,
                parent_relative_path,
                len(relative_path_split),
                f"{parent_level} {parent_name}\n",
                relative_path_split[-1].upper(),
            )


def _get_absolute_path_level(dir_path: str) -> int:
    dir_list: List[str] = dir_path.split("/")
    return len(dir_list)


def _build_doc_dict(
    root_directory: str, readme_filename: str, include_root: bool, title: str
) -> OrderedDict:
    output: OrderedDict = OrderedDict(
        {root_directory: ArchSection(root_directory, "", 0, f"# {title}\n", title)}
    )

    # Store anything needed to operate relative to the project root
    root_path_level = _get_absolute_path_level(root_directory)

    for directory_path, *_ in os.walk(root_directory):
        relative_path = os.path.relpath(directory_path, root_directory)

        # Calculate path level relative to root (starting at 1 for the root)
        path_level = _get_absolute_path_level(directory_path) - root_path_level + 1
        logging.debug(
            "Operating in path %s at path level %i", directory_path, path_level
        )

        # Skip root if includeroot is false, or part of the path is a dotfile
        if (
            directory_path == root_directory
            and not include_root
            and not _is_dotfile(directory_path)
        ):
            pass

        else:
            readme: Optional[str] = _get_readme(directory_path, readme_filename)

            if readme:
                _create_parents(output, directory_path, root_directory)
                output[directory_path] = ArchSection(
                    directory_path,
                    relative_path,
                    path_level,
                    _reformat_readme(readme, path_level),
                    directory_path.split("/")[-1].capitalize(),
                )

    return output


def _make_toc_entry(title: str, level: int, link: str):
    # Invent by level - 2
    # -1 to remove the root ToC level
    # -1 to start at 0, not 1
    return f"{'  ' * (level - 2)}- [{title}](#{link})\n"


def _traverse_readmes(root: str, fname: str, includeroot: bool, title: str) -> str:
    doc_dict: OrderedDict[str, ArchSection] = _build_doc_dict(
        root, fname, includeroot, title
    )

    header: str = doc_dict[root].body
    body: str = ""
    toc: str = "\n"

    for key, section in doc_dict.items():
        if key != root:
            anchorlabel: str = section.relative_path.strip(".").strip("/")
            anchorname: str = anchorlabel.replace("/", "-")

            body += f'\n<a name="{anchorname}"></a>\n\n{section.body}'
            toc += _make_toc_entry(anchorlabel, section.level, anchorname)

    return header + toc + body


app = typer.Typer()


@app.command()
def main(
    path: str = typer.Argument(..., help="Input directory"),
    readme: str = typer.Option("README.md", help="Readme file name"),
    includeroot: bool = typer.Option(False, help="Include root readme in output"),
    out: str = typer.Option("", help="Output file path. Outputs to stdout if empty."),
    title: str = typer.Option("Project Root", help="Output file title"),
):
    output: str = _traverse_readmes(path, readme, includeroot, title)
    if out:
        with open(out, "w") as f:
            f.write(output)
    else:
        typer.echo(output)


if __name__ == "__main__":
    app()
