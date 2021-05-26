#!/usr/bin/python3
from typing import Optional, List
from collections import OrderedDict
import os
import re
import typer
from dataclasses import dataclass


class BadHeading(ValueError):
    pass


@dataclass
class ArchSection:
    path: str
    level: int
    body: str
    title: str


def _check_format(input: str):
    if not input.strip().startswith("# "):
        raise BadHeading()


def _get_readme(path: str, fname: str) -> Optional[str]:
    path: str = os.path.join(path, fname)
    if os.path.isfile(path):
        with open(path, "r") as f:
            readme_str: str = f.read()
        try:
            _check_format(readme_str)
        except BadHeading:
            print(
                f"WARNING: Readme in {path} does not start with a top level heading. Output structure may be malformed."
            )
        return readme_str
    else:
        return None


def _is_dotfile(dirlist: List[str]):
    nonroots: List[str] = dirlist[1:]
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


def _create_parents(output: OrderedDict, dirlist: List[str]):
    for i, _ in enumerate(dirlist):
        parent_path: str = "/".join(dirlist[:i])
        if parent_path and (parent_path not in output):
            parent_name = dirlist[i - 1].upper()
            parent_level: str = "#" * i
            output[parent_path] = ArchSection(
                parent_path,
                len(dirlist),
                f"{parent_level} {parent_name}\n",
                dirlist[-1].upper(),
            )


def _build_doc_dict(
    root: str, fname: str, includeroot: bool, title: str
) -> OrderedDict:
    output: OrderedDict = OrderedDict(
        {root: ArchSection(root, 0, f"# {title}\n", title)}
    )

    for dirpath, *_ in os.walk(root):
        dirlist: List[str] = dirpath.split("/")
        pathlevel: int = len(dirlist)

        readme: Optional[str]
        if dirpath == root and not includeroot:
            pass
        elif not _is_dotfile(dirlist):
            readme = _get_readme(dirpath, fname)

            if readme:
                _create_parents(output, dirlist)
                output[dirpath] = ArchSection(
                    dirpath,
                    pathlevel,
                    _reformat_readme(readme, pathlevel),
                    dirlist[-1].upper(),
                )

    return output


def _make_toc_entry(title: str, level: int, link: str):
    return f"{'  ' * (level)}- [{title}](#{link})\n"


def _traverse_readmes(root: str, fname: str, includeroot: bool, title: str) -> str:
    doc_dict: OrderedDict = _build_doc_dict(root, fname, includeroot, title)

    header: str = doc_dict[root].body
    body: str = ""
    toc: str = "\n"

    for key, section in doc_dict.items():
        if key != root:
            anchorlabel: str = key.strip(".").strip("/")
            anchorname: str = anchorlabel.replace("/", "-")
            
            body += f'\n<a name="{anchorname}"></a>\n\n{section.body}'
            toc += _make_toc_entry(anchorlabel, section.level - 1, anchorname)

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
