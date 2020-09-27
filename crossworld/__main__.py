import argparse
import logging
from pathlib import Path
import re
import sys
from typing import List

from tqdm import tqdm

from .download import download_newspapers
from .errors import ApplicationError, CrosswordNotFoundError
from .extract import extract_crossword

LOGGER = logging.getLogger(__name__)


def is_valid_path(p: Path) -> bool:
    """Whether it's a valid path."""
    pattern = '[0-9]{8}_Le Monde\\.pdf'
    return re.match(pattern, p.name) is not None


def get_parser() -> argparse.ArgumentParser:
    desc = 'Extract crossword from Le Monde newspaper'
    parser = argparse.ArgumentParser(description=desc,
                                     prog='python -m crossworld')

    parser.add_argument('files', type=str, nargs='*',
                        help='Files or directories to process '
                        '(disable newspapers download when specified)')

    parser.add_argument('--max-download', type=int, default=10,
                        dest='max_download',
                        help='Max number of newspapers to download')

    output_help = 'Output directory (default to current directory)'
    parser.add_argument('-o', '--output', type=Path, default=Path.cwd(),
                        dest='output_path', help=output_help)

    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logs')

    parser.add_argument('--no-headless', action='store_true',
                        help='Don\'t use a headless web browser')

    return parser


def configure_logger(args):
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    level = logging.DEBUG if args.debug is True else logging.INFO
    ch.setLevel(level)
    logger = logging.getLogger('crossworld')
    logger.setLevel(level)
    logger.addHandler(ch)


def collect_pdf_paths(input_files: List[str]) -> List[Path]:
    paths = []
    extension = '.pdf'
    pattern = f'**/*{extension}'
    for f in input_files:
        p = Path(f)
        if not p.exists():
            raise ApplicationError(f'Path doesn\'t exists {p}')
        if p.is_dir():
            paths += [q for q in p.glob(pattern)]
        else:
            if not p.suffix == extension:
                msg = f'Expecting files with {extension} extension'
                raise ApplicationError(msg)
            paths.append(p)
    return paths


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    configure_logger(args)
    files = args.files if args.files \
        else download_newspapers(limit=args.max_download,
                                 headless=not args.no_headless)

    paths = collect_pdf_paths(files)
    if not len(paths):
        LOGGER.debug('Nothing to process')
        sys.exit(1)

    LOGGER.debug(f'Found {len(paths)} files to process')

    output_path = args.output_path

    not_found = []
    generated = []
    bar_format = '{bar}| {n_fmt}/{total_fmt} {postfix[0]} {postfix[1][value]}'
    try:
        with tqdm(total=len(paths),
                  bar_format=bar_format,
                  postfix=['Processing', dict(value=str(paths[0]))],
                  leave=False) as t:
            for p in paths:
                if not is_valid_path(p):
                    raise ApplicationError(f'Unexpected file {p}')
                try:
                    crossword_path = extract_crossword(p, output_path)
                    generated.append(crossword_path)
                except IOError:
                    msg = f'Failed to extract crossword from {p}'
                    raise ApplicationError(msg)
                except CrosswordNotFoundError:
                    not_found.append(p)
                t.postfix[1]['value'] = str(p)
                t.update()
    except ApplicationError as err:
        print(err)
        sys.exit(1)

    print()

    if len(generated):
        print('Available crosswords: ',
              ', '.join([str(p) for p in generated]))

    if len(not_found):
        print('No crossword found in: ',
              ', '.join([str(p) for p in not_found]))
