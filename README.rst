==========
Crossworld
==========

A python package for downloading and extracting crossword from `Le
Monde`_ website.

Prerequisites
-------------

Interaction with `Le Monde`_ website is done using Selenium_. It's
required to install Chrome and a compatible version of ChromeDriver.

Usage
-----

First install dependencies::

     poetry install

Then run the following commands::

     poetry shell
     python -m crossworld --output ~/Documents/Mots\ croisés

The default is to download at most 10 newspapers. It can be changed
using the ``--max-download`` option.

Credentials
-----------

Access to the web site `Le Monde`_ requires using credentials; Those
credentials are read from Freedesktop `Secret Service API`_.

To store your credentials, you can use the following command::

     $ secret-tool store --label='crossworld credentials' \
                   uri https://secure.lemonde.fr \
                   username USERNAME

.. _Le Monde: https://journal.lemonde.fr/
.. _Selenium: https://www.selenium.dev/
.. _Secret Service API: https://specifications.freedesktop.org/secret-service/latest/
