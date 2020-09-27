from io import StringIO
import logging
from pathlib import Path
import re
from typing import AnyStr, Match, Optional

from pdfrw import PdfReader, PdfWriter

from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

from .errors import CrosswordNotFoundError, FileAlreadyExistError

LOGGER = logging.getLogger(__name__)

_PATTERN = '[^ ]GRILLE N° ([0-9]{2} - [0-9]{3})'


def _search_in_page(page: PDFDocument,
                    rsrcmgr: PDFResourceManager) -> Optional[Match[AnyStr]]:
    text = StringIO()
    device = TextConverter(rsrcmgr, text, codec='utf-8',
                           laparams=None,
                           imagewriter=None)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    interpreter.process_page(page)
    m = re.search(_PATTERN, text.getvalue())
    return m


def extract_crossword(file_path: Path, output_path: Path,
                      overwrite: bool = True) -> Path:
    """Save page with crossword.

    Open a PDF document, search for a string identifying Le Monde
    crossword, and save the corresponding page to a file.

    Args:
      file_path: Path of the PDF document to process

      output_path: Path of the output directory

      overwrite: Whether to overwrite existing files (default to True)

    Returns:
      Path of the saved file

    """
    LOGGER.debug(f'Processing {file_path}')
    max_extracted_pages = 15
    rsrcmgr = PDFResourceManager(caching=True)
    crossword_page = None
    m = None
    with open(file_path, 'rb') as f:
        pages = [page for page in PDFPage.get_pages(f)]
        LOGGER.debug(f'Found {len(pages)} pages')
        first_checked_pageno = max(0, len(pages) - max_extracted_pages)
        LOGGER.debug(f'Searching last {max_extracted_pages} pages first')
        for i, page in enumerate(pages[first_checked_pageno:]):
            m = _search_in_page(page, rsrcmgr)
            if m:
                crossword_page = first_checked_pageno + i
                break

        if not crossword_page:
            LOGGER.debug(f'Extending search to all pages')
            for i, page in enumerate(pages[:first_checked_pageno]):
                m = _search_in_page(page, rsrcmgr)
                if m:
                    crossword_page = i
                    break

    if not crossword_page or not m:
        raise CrosswordNotFoundError

    LOGGER.debug(f'Crossword found on page {crossword_page}')

    path = output_path / '{}.pdf'.format(m.group(1))
    if path.exists() and not overwrite:
        LOGGER.debug(f'File already exist ${path}')
        raise FileAlreadyExistError

    x = PdfReader(file_path)
    page = x.pages[crossword_page]
    y = PdfWriter()
    y.addpage(page)
    y.write(path)

    return path
