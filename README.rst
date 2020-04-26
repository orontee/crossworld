==========
Crossworld
==========

A python package for downloading and extracting crossword from Le
Monde newspaper.

Usage
-----

First install dependencies::

     poetry install

Then run the following command::

     python -m crossworld --output Mots\ croisés

The default is to download at most 10 newspapers. It can be changed
using the ``--max-download`` option.

Credentials
-----------

Access to the web site https://journal.lemonde.fr is done using
credentials read from Freedesktop SecretService standard.

To store your credentials, you can use the following command::

     $ secret-tool store --label='crossworld credentials' \
                   uri https://secure.lemonde.fr \
                   username USERNAME
