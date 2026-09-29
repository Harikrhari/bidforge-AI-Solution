"""Document parser adapter using Docling."""
import tempfile

from docling.document_converter import DocumentConverter


class DoclingParser:
    def __init__(self):
        self.converter = DocumentConverter()

    async def parse(self, data: bytes, suffix: str = ".pdf") -> str:
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            f.write(data)
            f.flush()
            return self.converter.convert(f.name).document.export_to_markdown()
