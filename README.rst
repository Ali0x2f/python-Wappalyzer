Renewed python-Wappalyzer
-----------------

.. image:: https://travis-ci.org/chorsley/python-Wappalyzer.svg?branch=master
  :target: https://travis-ci.org/chorsley/python-Wappalyzer

.. image:: https://badge.fury.io/py/python-Wappalyzer.svg
  :target: https://pypi.org/project/python-Wappalyzer/

.. image:: https://coveralls.io/repos/github/chorsley/python-Wappalyzer/badge.svg?branch=master
  :target: https://coveralls.io/github/chorsley/python-Wappalyzer?branch=master



Python implementation of the `Wappalyzer <https://github.com/AliasIO/wappalyzer>`_ web application detection utility.  


Install
-------

::

    $ pip install python-Wappalyzer

This also installs a ``wappalyzer`` command line entrypoint.

To enable headless browser rendering with Playwright::

    $ pip install "python-Wappalyzer[browser]"
    $ python -m playwright install chromium

Require Python3.6 or later. 

Usage
-----

The API exposes two objects: ``Wappalyzer.Wappalyzer`` and ``Wappalyzer.WebPage``. 

>>> from Wappalyzer import Wappalyzer, WebPage

First create a WebPage. The following code creates a webpage with the ``request`` module. 

>>> webpage = WebPage.new_from_url('http://example.com')

Then analyze it with Wappalyzer. 

>>> wappalyzer = Wappalyzer.latest()
>>> wappalyzer.analyze(webpage)
{'Docker', 'Azure CDN', 'Amazon Web Services', 'Amazon ECS'}

To download and use the latest technologies file from AliasIO/wappalyzer repository, 
create the Wappalyzer driver with the ``update=True`` parameter. 

>>> wappalyzer = Wappalyzer.latest(update=True)

The Wappalyzer object exposes more methods that returns metatada for the detected technologies. 

>>> wappalyzer.analyze_with_categories(webpage)
{'Amazon ECS': {'categories': ['IaaS']},
 'Amazon Web Services': {'categories': ['PaaS']},
 'Azure CDN': {'categories': ['CDN']},
 'Docker': {'categories': ['Containers']}}

>>> webpage = WebPage.new_from_url('http://wordpress-example.com')
>>> wappalyzer.analyze_with_versions_and_categories(webpage)
{'Font Awesome': {'categories': ['Font scripts'], 'versions': ['5.4.2']},
 'Google Font API': {'categories': ['Font scripts'], 'versions': []},
 'MySQL': {'categories': ['Databases'], 'versions': []},
 'Nginx': {'categories': ['Web servers', 'Reverse proxies'], 'versions': []},
 'PHP': {'categories': ['Programming languages'], 'versions': ['5.6.40']},
 'WordPress': {'categories': ['CMS', 'Blogs'], 'versions': ['5.4.2']},
 'Yoast SEO': {'categories': ['SEO'], 'versions': ['14.6.1']}}

You can also analyze a provided website payload and get structured JSON output.

>>> from Wappalyzer import analyze_payload
>>> analyze_payload({
...     'target_url': 'http://wordpress-example.com',
...     'html': '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>',
...     'headers': {},
... })
{'target_url': 'http://wordpress-example.com',
 'technologies': [{'name': 'WordPress', 'version': '5.4.2', 'confidence': 100, 'matched_on': 'meta'}]}

To persist results in a consolidated database, use the storage helpers with SQLite or any
DB-API compatible connection::

>>> from Wappalyzer import analyze, store_analysis_results_to_sqlite
>>> result = analyze('http://wordpress-example.com')
>>> scan_id = store_analysis_results_to_sqlite('wappalyzer.sqlite', result, url='http://wordpress-example.com')

Read the `API Reference <https://chorsley.github.io/python-Wappalyzer/Wappalyzer.html>`_ for more documentation.

CLI
---

Additionnaly, there is now a CLI interface. It prints the analyzer results (with metatada) as JSON.

Call it with::

    wappalyzer https://example.com

Or with the module entrypoint::

    python -m Wappalyzer https://example.com

positional arguments:
  urls                  URL(s) to analyze

optional arguments:
  -h, --help            show this help message and exit
  --input-file INPUT_FILE
                        Read URLs from a file, one per line
  --update              Use the latest technologies file downloaded from the internet
  --user-agent USERAGENT
                        Request user agent
  --timeout TIMEOUT     Request timeout
  --no-verify           Skip SSL cert verify
  --browser {none,playwright}
                        Rendering engine to use
  --wait-until {load,domcontentloaded,networkidle}
                        Page load state for browser rendering
  --concurrency CONCURRENCY
                        Maximum number of URLs to analyze concurrently
  --pretty              Pretty-print JSON output
  --sqlite-db SQLITE_DB
                        Store results in a consolidated SQLite database

You can scale across multiple websites by passing several URLs or an input file::

    wappalyzer https://example.com https://example.org --concurrency 10
    wappalyzer --input-file urls.txt --concurrency 10
    wappalyzer --input-file urls.txt --sqlite-db ./wappalyzer.sqlite

To render JavaScript-heavy pages before analysis, use Playwright::

    wappalyzer https://example.com --browser playwright --wait-until networkidle

Cannot use lxml in your environment?
------------------------------------

We provide a way to use python-Wappalyzer without ``lxml``.
This should only be used only lxml cannot be installed, 
the standard library DOM parser will fail on broken HTML,
resulting in incomplete results.

It can be used by installing ``python-Wappalyzer`` with ``pip`` 
option ``--no-deps``. Then install the required packages manually 
(``pip install requests aiohttp cached_property dom_query pytest``).

What's new
----------

in development
^^^^^^^^^^^^^^
* Add support for the "dom" key in technologies JSON.
* Fix case sensitivity of the WebPage headers.
* Provide a fallback WebPage class that works without ``lxml``. 
* Add installable ``wappalyzer`` console script.
* Add concurrent multi-site analysis helpers and CLI support.
* Add optional Playwright-based headless browser rendering.

python-Wappalyzer 0.4.0 (unreleased)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Add ``python -m Wappalyzer`` entrypoint.
* Support list of regular expressions in technologies JSON.
* Add auto-update feature (unstable).

python-Wappalyzer 0.3.x
^^^^^^^^^^^^^^^^^^^^^^^
* Python 3 support.
* Async support.
* Add confidence and version parsing.

Note:
    Last version to support Python2 was `0.2.2`.  
