"""
Line Counter

WARNING: The counter will not count a blank line at the end of the file. This is due to the way that the file is read,
and is not a bug.
"""
from errors import CommentNotClosedError
from dataclasses import dataclass
from typing import List, Literal
from pathlib import Path
import os

Detail = Literal["minimal", "basic", "full"]


PYTHON_FILE_EXTENSIONS = [".py"]


def _zero_safe_division(numerator: int, denominator: int) -> float:
    """Zero safe division"""
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


@dataclass
class Settings:
    """Settings information payload"""
    path: Path
    ignoreNames: List[str]
    ignorePaths: List[Path]
    recursive: bool
    outputDetail: Detail


@dataclass
class FileData:
    """File data"""
    file: Path
    totalLines: int
    commentLines: int
    codeLines: int
    blankLines: int


def get_arbitrary_settings() -> Settings:
    """Get settings from user"""
    return Settings(
        Path(os.getcwd()),
        ["venv", ".git", ".env", ".vscode", ".idea", "__pycache__"],
        [],
        True
    )


class LineCounter:
    def __init__(self, settings: Settings) -> None:
        self._settings: Settings = settings
        self._fileDatas: list[FileData] = []

    def count_file(self, file: Path) -> None:
        """
        Get file data, and append to LineCounter.fileDatas
        :raises FileNotFoundError: If file does not exist
        :raises CommentNotClosedError: If multi-line comment is not closed
        """

        fileData = FileData(file, 0, 0, 0, 0)

        # Open the file
        with open(file, "r") as f:
            # Get the lines
            lines = f.read().splitlines()

        inMultiLineComment = False

        # loop through the lines
        for line in lines:
            fileData.totalLines += 1

            # strip the line for whitespace
            strippedLine = line.strip()

            # check if the line is a comment
            if strippedLine.startswith("#"):
                fileData.commentLines += 1
                continue

            elif strippedLine.startswith("'''") or strippedLine.startswith('"""'):

                # Check if the line ends with '''
                if strippedLine.endswith("'''") or strippedLine.endswith('"""'):
                    fileData.commentLines += 1

                else:
                    inMultiLineComment = not inMultiLineComment
                    fileData.commentLines += 1

                continue

            elif inMultiLineComment:
                fileData.commentLines += 1
                continue

            # check if the line is blank
            elif strippedLine == "":
                fileData.blankLines += 1
                continue
            else:
                # if the line is not a comment or blank, it is probably code.
                fileData.codeLines += 1

        # raise if inMultiLineComment is True
        if inMultiLineComment:
            raise CommentNotClosedError(file)

        assert fileData.totalLines == fileData.commentLines + fileData.codeLines + fileData.blankLines

        self._fileDatas.append(fileData)

    def get_py_files(self, path: Path) -> list[Path]:
        """
        Get all python files in a path.
        :raises ValueError: If path is not a directory or a python file
        """

        if path.is_file():
            # Check if it is a python file, and return it if it is
            if path.suffix in PYTHON_FILE_EXTENSIONS:
                return [path]

            else:
                raise ValueError(f"Path '{path}' is not a directory or a python file.")

        files = []

        for file in path.iterdir():
            if file.is_dir():
                if file.name in self._settings.ignoreNames:
                    continue

                if file in self._settings.ignorePaths:
                    continue

                if not self._settings.recursive:
                    continue

                # If file is directory, and it's not in the ignoreNames list and ignorePaths list, then get the files
                # in the directory

                files += self.get_py_files(file)

            elif file.is_file():

                if file.suffix not in PYTHON_FILE_EXTENSIONS:
                    continue

                if file.name in self._settings.ignoreNames:
                    continue

                if file in self._settings.ignorePaths:
                    continue

                # If file is a file, and it's not in the ignoreNames list and ignorePaths list, then append it to the
                # files list

                files.append(file)

        return files

    def count_files(self, files: list[Path]) -> None:
        """
        Count all the files provided.
        :raises FileNotFoundError: If file does not exist
        :raises CommentNotClosedError: If multi-line comment is not closed
        """

        for file in files:
            if not file.exists():
                raise FileNotFoundError(
                    f"File '{file}' does not exist. Please check that the file exists, and try again."
                )

            self.count_file(file)

    def print_file_data(self) -> None:
        """Print the file data"""
        if len(self._fileDatas) == 0:
            print("No files to print.")
            return

        for file in self._fileDatas:
            print(f"{file.file}")
            print(f"    total lines:    {file.totalLines}")
            print(f"    comment lines:  {file.commentLines}")
            print(f"    code lines:     {file.codeLines}")
            print(f"    blank lines:    {file.blankLines}")
            print(f"    blank-code ratio: {_zero_safe_division(file.blankLines, file.codeLines) * 100:.2f}%")
            print(f"    comment-code ratio: {_zero_safe_division(file.commentLines, file.codeLines) * 100:.2f}%")

        print("Total:")

        totalLines = sum([file.totalLines for file in self._fileDatas])
        commentLines = sum([file.commentLines for file in self._fileDatas])
        codeLines = sum([file.codeLines for file in self._fileDatas])
        blankLines = sum([file.blankLines for file in self._fileDatas])

        print(f"    total lines:    {totalLines}")
        print(f"    comment lines:  {commentLines}")
        print(f"    code lines:     {codeLines}")
        print(f"    blank lines:    {blankLines}")
        print(f"    blank-code ratio: {_zero_safe_division(blankLines, codeLines) * 100:.2f}%")
        print(f"    comment-code ratio: {_zero_safe_division(commentLines, codeLines) * 100:.2f}%")

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def fileDatas(self) -> list[FileData]:
        return self._fileDatas
