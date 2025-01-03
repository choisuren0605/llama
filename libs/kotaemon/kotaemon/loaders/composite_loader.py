from typing import Callable, List, Optional, Type

from llama_index.core.readers.base import BaseReader as LIBaseReader

from .base import BaseReader, LIReaderMixin


class DirectoryReader(LIReaderMixin, BaseReader):
    """
        llama-index SimpleDirectoryReader
    """

    input_dir: Optional[str] = None
    input_files: Optional[List] = None
    exclude: Optional[List] = None
    exclude_hidden: bool = True
    errors: str = "ignore"
    recursive: bool = False
    encoding: str = "utf-8"
    filename_as_id: bool = False
    required_exts: Optional[list[str]] = None
    file_extractor: Optional[dict[str, "LIBaseReader"]] = None
    num_files_limit: Optional[int] = None
    file_metadata: Optional[Callable[[str], dict]] = None

    def _get_wrapped_class(self) -> Type["LIBaseReader"]:
        from llama_index.core import SimpleDirectoryReader

        return SimpleDirectoryReader
