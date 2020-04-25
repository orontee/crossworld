from io import StringIO
import logging
from pathlib import Path
import re

from pdfrw import PdfReader, PdfWriter

from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

from .errors import CrosswordNotFoundError, FileAlreadyExistError

LOGGER = logging.getLogger(__name__)


def extract_crossword(file_path: Path, output_path: Path,
                      overwrite: bool = True) -> Path:
    """Save page with crossword.

    Open a PDF document, search for a string identifying Le Monde
    crossword, and save the corresponding page to a file.

    Arguments:
      file_path: Path of the PDF document to process

      output_path: Path of the output directory

      overwrite: Whether to overwrite existing files (default to True)

    Returns:
      Path of the saved file

    """
    LOGGER.debug(f'Processing {file_path}')
    max_extracted_pages = 10
    pattern = 'GRILLE N° ([0-9]{2} - [0-9]{3})'
    rsrcmgr = PDFResourceManager(caching=True)
    crossword_page = None
    m = None
    with open(file_path, 'rb') as f:
        pages = [page for page in PDFPage.get_pages(f)]
        first_checked_pageno = len(pages) - max_extracted_pages
        for i, page in enumerate(pages[first_checked_pageno:]):
            text = StringIO()
            device = TextConverter(rsrcmgr, text, codec='utf-8',
                                   laparams=None,
                                   imagewriter=None)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            if i == max_extracted_pages:
                break
            interpreter.process_page(page)
            m = re.search(pattern, text.getvalue())
            if m:
                crossword_page = first_checked_pageno + i
                msg = f'Crossword found on page {crossword_page}'
                LOGGER.debug(msg)
                break
        if not crossword_page or not m:
            raise CrosswordNotFoundError

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
