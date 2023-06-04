"""
CLI
"""

from counter import Settings, LineCounter
from pathlib import Path
import argparse

from errors import CommentNotClosedError


def init_argument_parser() -> argparse.ArgumentParser:
    """
    Initialize the argument parser
    :return: The argument parser
    """

    class StoreBoolAction(argparse.Action):
        def __call__(self,
                     parser_: argparse.ArgumentParser,
                     namespace: argparse.Namespace,
                     values: str,
                     option_string: str = None
                     ) -> None:
            if values.lower() in ('yes', 'true', 't', 'y', '1'):
                setattr(namespace, self.dest, True)
            elif values.lower() in ('no', 'false', 'f', 'n', '0'):
                setattr(namespace, self.dest, False)
            else:
                parser_.error("Invalid value for boolean argument")

    parser = argparse.ArgumentParser(
        description="CountMyLines is a command line tool that counts the number of lines in a project, "
                    "with some extra features.",
        usage="countmylines [options]",
    )

    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        required=False,
        help="The path to the directory or file to count the lines of. Defaults to current directory.",
        default=Path.cwd()
    )

    # -r
    # not specified: True
    # -r: True
    # -r False: False
    # -r True: True

    parser.add_argument(
        "-r",
        "--recursive",
        action=StoreBoolAction,  # NOQA - ignore ide warning
        required=False,
        help="Whether to count the lines of the subdirectories.",
        default=True
    )

    parser.add_argument(
        "-i",
        "--ignore",
        type=Path,
        help="The path to the exact directory or file to ignore.",
        action="append",  # Allows multiple arguments
        default=[]
    )

    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        help="Will exclude all files and directories with the given name, regardless of location.",
        required=False,
        action="append",  # Allows multiple arguments
        default=["venv", ".git", ".env", ".vscode", ".idea", "__pycache__"]
    )

    # Argument for how detailed the output stats should be
    parser.add_argument(
        "-d",
        "--detail",
        type=str,
        help="How detailed the output statistics should be.",
        required=False,
        default="basic",
        choices=["minimal", "basic", "full"]
    )

    parser.add_argument(
        "-pe",
        "--persistent",
        action=StoreBoolAction,  # NOQA - ignore ide warning
        required=False,
        help="Whether to require user input before exiting.",
        default=False
    )

    return parser


def validate_settings(settings: Settings) -> bool:
    """
    Validate the settings
    :param settings: The settings to validate
    :raises FileNotFoundError: If the path does not exist
    """

    # Check if path exists
    if not settings.path.exists():
        print(f"ERROR: Path '{settings.path}' does not exist.")
        return False

    for path in settings.ignorePaths:
        if not path.exists():
            print(f"ERROR: Path in ignore paths '{path}' does not exist.")
            return False

    if settings.outputDetail not in ("minimal", "basic", "full"):
        print(f"ERROR: Invalid output detail '{settings.outputDetail}'.")
        return False

    return True


def count_lines(settings: Settings) -> LineCounter | None:
    """
    Count the lines
    :param settings: The settings configured by the user.
    """

    print(f"Counting lines in '{settings.path}'...")
    lineCounter = LineCounter(settings=settings)

    # Get the files
    try:
        files = lineCounter.get_py_files(settings.path)
    except ValueError:
        # Path is a file that is not a python file,
        # 'If path is not a directory or a python file'

        print(f"ERROR: Path '{settings.path}' is not a directory or a python file.")
        return

    try:
        lineCounter.count_files(files)
    except FileNotFoundError as e:
        print(f"ERROR: Couldn't open file during counting: {e.args[0]} ")
        return
    except CommentNotClosedError as e:
        print(f"ERROR: .py file {e.args[0]} contains invalid code. Couldn't count comments because multi-line "
              f"comment does not finish.")
        return

    print("Done!")

    return lineCounter


def print_table(lineCounter: LineCounter) -> None:
    """
    Print the table
    """
    header = ["file", "lines", "comments", "code", "blank"]
    rows: list[list[str]] = []

    # Create rows
    for fileData in lineCounter.fileDatas:
        rows.append([
            str(fileData.file.name),
            str(fileData.totalLines),
            str(fileData.commentLines),
            str(fileData.codeLines),
            str(fileData.blankLines),
        ])

    # Print table
    print()

    string = ""
    paddingString = ""

    for i, head in enumerate(header):
        longestRowLength = max(
            [len(row[i]) for row in rows] + [len(head)]
        )

        string += head.ljust(longestRowLength) + "  |  "
        paddingString += " " * longestRowLength + "  |  "

    print("_" * len(string.rstrip()))
    print(string)
    print(paddingString)

    for row in rows:
        string = ""

        for i, cell in enumerate(row):
            longestRowLength = max(
                [len(row[i]) for row in rows] + [len(header[i])]
            )

            string += cell.ljust(longestRowLength) + "  |  "

        print(string)


def print_statistics(lineCounter: LineCounter) -> None:
    totalLines = sum([fileData.totalLines for fileData in lineCounter.fileDatas])
    totalComments = sum([fileData.commentLines for fileData in lineCounter.fileDatas])
    totalCode = sum([fileData.codeLines for fileData in lineCounter.fileDatas])
    totalBlank = sum([fileData.blankLines for fileData in lineCounter.fileDatas])

    averageLines = f"{totalLines / len(lineCounter.fileDatas):.2f}"
    averageComments = f"{totalComments / len(lineCounter.fileDatas):.2f}"
    averageCode = f"{totalCode / len(lineCounter.fileDatas):.2f}"
    averageBlank = f"{totalBlank / len(lineCounter.fileDatas):.2f}"

    print(f"average per file ({len(lineCounter.fileDatas)} files):")
    print(f"    lines:            {averageLines}")
    print(f"    comments:         {averageComments}")
    print(f"    code:             {averageCode}")
    print(f"    blank lines:      {averageBlank}")
    print()

    print()
    print(f"blank percent:        {(totalBlank / totalLines) * 100:.2f}%")
    print(f"comment percent:      {(totalComments / totalLines) * 100:.2f}%")
    print(f"code percent:         {(totalCode / totalLines) * 100:.2f}%")
    print()


def print_data(lineCounter: LineCounter) -> None:
    # Print the stats total

    totalLines = sum([fileData.totalLines for fileData in lineCounter.fileDatas])
    totalComments = sum([fileData.commentLines for fileData in lineCounter.fileDatas])
    totalCode = sum([fileData.codeLines for fileData in lineCounter.fileDatas])
    totalBlank = sum([fileData.blankLines for fileData in lineCounter.fileDatas])

    print()

    print(f"overall:")
    print(f"    files counted:    {len(lineCounter.fileDatas)}")
    print(f"    total lines:      {totalLines}")
    print(f"    comments:         {totalComments}")
    print(f"    code:             {totalCode}")
    print(f"    blank lines:      {totalBlank}")

    if lineCounter.settings.outputDetail == "minimal":
        return

    print_table(lineCounter)

    print()

    if lineCounter.settings.outputDetail == "basic":
        return

    # Print statistics
    print_statistics(lineCounter)


def main() -> None:
    """
    Main function
    """

    parser = init_argument_parser()
    args = parser.parse_args()

    settings = Settings(
        args.path,
        args.exclude,
        args.ignore,
        args.recursive,
        args.detail
    )

    result: bool = validate_settings(settings)

    if not result:
        return

    countLinesResult: LineCounter | None = count_lines(settings)

    if countLinesResult is None:
        return

    print_data(countLinesResult)

    if args.persistent:
        input("Press enter to exit...")
        return


if __name__ == '__main__':
    main()
