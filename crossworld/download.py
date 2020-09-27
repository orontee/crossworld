from collections import namedtuple
from contextlib import closing
from datetime import date
import logging
from pathlib import Path
import re
from time import sleep

import secretstorage

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from .errors import CredentialsNotFound

LOGGER = logging.getLogger(__name__)

Credentials = namedtuple('Credentials', 'mail, password')

_month_names = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre',
                'décembre')

_download_base_path = Path('~/Téléchargements').expanduser()


def _read_credentials() -> Credentials:
    """Read credentials from Freedesktop.org SecretService standard."""
    with closing(secretstorage.dbus_init()) as conn:
        collection = secretstorage.get_default_collection(conn)
        items = collection.search_items({'uri': 'https://secure.lemonde.fr'})
        try:
            item = next(items)
        except StopIteration:
            LOGGER.debug('Credentials not found!')
            raise CredentialsNotFound

        attributes = item.get_attributes()
        mail = attributes['username']
        LOGGER.debug(f'Will use credentials for {mail}')
        return Credentials(mail, item.get_secret().decode('utf-8'))


def _connect(driver: WebDriver, creds: Credentials):
    LOGGER.debug('Connecting to lemonde.fr')
    driver.get('https://journal.lemonde.fr')
    elements = driver.find_elements_by_class_name('access-login')
    elements[0].click()

    mail_input = driver.find_element_by_id('connection_mail')
    mail_input.send_keys(creds.mail)

    password_input = driver.find_element_by_id('connection_password')
    password_input.send_keys(creds.password)

    connect_button = driver.find_element_by_id('connection_save')
    connect_button.click()


def _get_file_path(newspaper_date: date) -> Path:
    prefix = newspaper_date.strftime('%Y%m%d')
    return _download_base_path / f'{prefix}_Le Monde.pdf'


def download_newspapers(*, limit: int, headless: bool):
    """Download newspapers in PDF format.

    Args:
        limit: Max number of newspaper to download

        headless: Whether to use a headless web browser

    """
    options = webdriver.ChromeOptions()
    if headless:
        LOGGER.debug('Configuring web browser to be headless')
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('window-size=1400,2100')
        prefs = {}
        prefs['profile.default_content_settings.popups'] = 0
        prefs['download.default_directory'] = str(_download_base_path)
        options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(15)

    creds = _read_credentials()
    _connect(driver, creds)

    pattern = '([0-9]{1,2}) (' + '|'.join(_month_names) + ') ([0-9]{4})'
    downloaded = []
    try:
        for i in range(limit):
            sleep(5)
            elements = driver.find_elements_by_class_name('subTitle')
            element = None
            for e in elements:
                m = re.match(pattern, e.text)
                if not m:
                    continue

                month = _month_names.index(m.group(2)) + 1
                newspaper_date = date(int(m.group(3)), month, int(m.group(1)))
                file_path = _get_file_path(newspaper_date)
                if file_path.exists():
                    continue

                element = e
                break

            if not element:
                LOGGER.debug('No new newspaper to download')
                break

            sleep(2)
            element.click()
            download_button = driver.find_element_by_id('download-publication')
            sleep(2)
            download_button.click()
            full_button = [e for e in
                           driver.find_elements_by_class_name('download-item')
                           if e.get_attribute('data-download') == 'fullPdf'][0]

            sleep(2)
            full_button.click()

            msg = f'Downloading {newspaper_date} newspaper to {file_path}…'
            LOGGER.info(msg)
            for i in range(4):
                if file_path.exists():
                    break

                sleep(15)
            if not file_path.exists():
                LOGGER.debug(f'Failed to download {file_path}')
            else:
                downloaded.append(file_path)

            driver.back()
    except Exception as err:
        LOGGER.debug('Failed to download newspaper', err)
    finally:
        driver.quit()

    return downloaded
