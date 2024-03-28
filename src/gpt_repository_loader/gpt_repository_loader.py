#!/usr/bin/env python3

import argparse
import fnmatch
import os
import sys

import pyperclip

HERE = os.path.dirname(os.path.abspath(__file__))


def get_ignore_list(ignore_file_path):
    ignore_list = []
    with open(ignore_file_path, "r") as ignore_file:
        for line in ignore_file:
            if sys.platform == "win32":
                line = line.replace("/", "\\")
            ignore_list.append(line.strip())
    return ignore_list


def should_ignore(file_path, ignore_list):
    for pattern in ignore_list:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def process_repository(repo_path, ignore_list, output_file):
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_file_path = os.path.relpath(file_path, repo_path)

            if not should_ignore(relative_file_path, ignore_list):
                with open(file_path, "r", errors="ignore") as file:
                    contents = file.read()
                output_file.write("----!@#$----" + "\n")
                output_file.write(f"{relative_file_path}\n")
                output_file.write(f"{contents}\n")


def main() -> int:  # pylint: disable=too-many-statements
    # copy this but using argparse
    parser = argparse.ArgumentParser(
        description="Process a git repository into a single file for chat gpt."
    )
    parser.add_argument(
        "repo_path", help="path to the git repository", type=str, nargs="?"
    )
    parser.add_argument(
        "-p", "--preamble", help="path to the preamble file", type=str, nargs="?"
    )
    parser.add_argument(
        "--clipboard", help="copy the output to the clipboard", action="store_true"
    )
    parser.add_argument(
        "--openfile", help="open output file after creation", action="store_true"
    )
    parser.add_argument(
        "--write-config",
        help="Write a default config file to the target directory.",
        type=str,
        nargs="?",
    )
    args = parser.parse_args()

    repo_path = args.repo_path or os.getcwd()
    ignore_file_path = os.path.join(repo_path, ".gptignore")
    if sys.platform == "win32":
        ignore_file_path = ignore_file_path.replace("/", "\\")

    if not os.path.exists(ignore_file_path):
        # try and use the .gptignore file in the current directory as a fallback.
        ignore_file_path = os.path.join(HERE, ".gptignore")
        assert os.path.exists(ignore_file_path)
        with open(ignore_file_path, "r") as ignore_file:
            contents = ignore_file.read()
        with open(ignore_file_path, "w") as ignore_file:
            ignore_file.write(contents)

    preamble_file = args.preamble
    if os.path.exists(ignore_file_path):
        ignore_list = get_ignore_list(ignore_file_path)
    else:
        ignore_list = []
    outfile = os.path.abspath("gptrepo_output.txt")
    with open(outfile, "w") as output_file:
        if preamble_file:
            with open(preamble_file, "r") as pf:
                preamble_text = pf.read()
                output_file.write(f"{preamble_text}\n")
        else:
            output_file.write(
                "The following text is a Git repository with code. The structure of the text are sections that begin with ----!@#$----, followed by a single line containing the file path and file name, followed by a variable amount of lines containing the file contents. The text representing the Git repository ends when the symbols --END-- are encounted. Any further text beyond --END-- are meant to be interpreted as instructions using the aforementioned Git repository as context.\n"
            )
        process_repository(repo_path, ignore_list, output_file)
    outfile = os.path.abspath("gptrepo_output.txt")
    with open(outfile, "a") as output_file:
        output_file.write("--END--")
    if not args.clipboard:
        print(f"Repository contents written to {outfile}")
        if args.openfile:
            if sys.platform == "win32":
                os.startfile(outfile)
            elif sys.platform == "darwin":
                os.system(f"open {outfile}")
            else:
                try:
                    os.system(f"xdg-open {outfile}")
                except Exception:  # pylint: disable=broad-except
                    pass
        return 0
    with open(outfile, "r") as output_file:
        contents = output_file.read()
    pyperclip.copy(contents)
    os.remove(outfile)
    print("Copied to clipboard")
    return 0
