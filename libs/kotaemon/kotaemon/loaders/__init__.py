from .base import AutoReader, BaseReader
from .composite_loader import DirectoryReader
from .docx_loader import DocxReader
from .excel_loader import ExcelReader, PandasExcelReader
from .html_loader import HtmlReader, MhtmlReader
from .ocr_loader import ImageReader, OCRReader
from .pdf_loader import PDFThumbnailReader
from .txt_loader import TxtReader
from .unstructured_loader import UnstructuredReader
from .web_loader import WebReader

__all__ = [
    "AutoReader",
    "BaseReader",
    "PandasExcelReader",
    "ExcelReader",
    "ImageReader",
    "OCRReader",
    "DirectoryReader",
    "UnstructuredReader",
    "DocxReader",
    "HtmlReader",
    "MhtmlReader",
    "AdobeReader",
    "TxtReader",
    "PDFThumbnailReader",
    "WebReader",
]
