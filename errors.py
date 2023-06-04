from pathlib import Path


class CommentNotClosedError(Exception):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__(f"Multi-line comment not closed in file ({file}).")

    def __str__(self) -> str:
        return f"Multi-line comment not closed in file ({self.file})."