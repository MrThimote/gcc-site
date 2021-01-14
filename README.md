Girls Can Code! website
=======================

[![Build Status](https://travis-ci.com/prologin/gcc-site.svg?branch=master)](https://travis-ci.com/prologin/gcc-site)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

This repository contains the source of the website of GCC!:
<https://gcc.prologin.org>.

GCC! is a free computer science summer camp for girls under 18 organised by the
association [Prologin](https://prologin.org) since 2014.

Table of Contents
-----------------

* [Table of Contents](#table-of-contents)
* [Installation](#installation)
* [Hacking on the website](#hacking-on-the-website)
* [Contributing](#Contributing)
* [Troubleshooting](#troubleshooting)

Installation
------------

### Requirements

Running the GCC! website requires the following dependencies:

* Git
* Python 3
* NPM (for Javascript & CSS assets)
* PostgreSQL
* A running version of the [Prologin website](https://github.com/prologin/site)
  in order to interact with its OAuth server.

Theses requirements are a subset of the requirements of the Prologin website
itself, you may refer to the README of [the corresponding
repository](https://github.com/prologin/site) for details about there setup.

### Cloning

Clone the website and, optionally, the other Prologin repositories needed for
the different modules of the website:

```bash
git clone git@github.com:prologin/gccsite
git clone git@github.com:prologin/archives   # Edition archives (private)
```

Then, enter the website directory:

```
cd gccsite
```

### Python virtualenv & dependencies

Use a [virtual environment](https://docs.python.org/3/library/venv.html) to
install the Python dependencies of the website:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Web dependencies

Download the web dependencies from NPM:

```bash
( cd assets && npm install )
```

### Configuration

Copy the sample configuration to a file of your choice. I recommend to use
`dev.py` for a development environment:

```bash
cp gccsite/gccsite/settings/{conf.sample,dev}.py
```

The default settings should work by default if you are following this guide,
but if needed, you can edit `gccsite/gccsite/settings/dev.py` to adjust some
settings.

### Creating the database

Create the `gcc` PostgreSQL database, and run the migrations :

```bash
createdb gcc
./gccsite/manage.py migrate
```

### OAuth

If you followed this guide, the connection through the website of Prologin
should work by default, you can however modify this configuration if you
please:

dev.py on the Prologin website:
```python3
AUTH_TOKEN_CLIENTS = {
    'gcc': AuthTokenClient('SECRET', '//localhost:8001/user/auth/callback'),
}
```

dev.py on the GCC! website:
```python3
OAUTH_ENDPOINT = 'http://localhost:8000/user/auth'
OAUTH_SECRET = 'SECRET'
```

### Creating the minimal context

(**Note**: If you would rather work with an **anonymized database dump** of the
website, ask one of the Prologin roots to provide you one.)

```bash
python manage.py edition create
```

Hacking on the website
----------------------

Every time you need to work on the website:

1. Enter the virtualenv:
    ```bash
    source .venv/bin/activate
    ```
2. Launch the local dev server:
    ```bash
    make runserver
    ```

Contributing
----------------------
In order to contribute, please follow this guide

 1. Create a branch for the issue/functionnality you wish to implement
 2. Commit all your changes in the new branch and then create a Merge Request
 3. Format the code as follows

#### Formatting

All of the python codebase needs to be formatted using [black](https://github.com/python/black)
by running `black .` at the root of the project before any commit.

You can automate the process by installing the recommended pre-commit hooks:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Translations

The website user-facing strings are internationalized through Django's internal
i18n framework.

You can translate the strings locally by editing the `.po` files in your editor
or using a dedicated software such as [poedit](https://poedit.net/).

To ease the *community* translation process, it is possible to upload the
untranslated (English) strings to Transifex, ask people to translate them (eg.
using the Transifex web app) and download them back to the repository.
To that end, use the provided `make` commands:

```bash
# I've created/update source (English) strings, let's push them
# (we pull before to update local strings just in case)
make tx-pull tx-push
# ... translate on Transifex ...
# Get back the translated strings
make tx-pull
# Commit
git commit gccsite/locale -m 'locale: update for <feature>'
```
