import pytest
import json
import os

from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from httpretty import HTTPretty, httprettified
from aioresponses import aioresponses

from Wappalyzer.fingerprint import Fingerprint
from Wappalyzer import WebPage, Wappalyzer, analyze_payload
from Wappalyzer.__main__ import get_parser, main
from Wappalyzer.data.update import get_technology_data


class FakeTag:
    def __init__(self, properties=None):
        self.name = "div"
        self.attributes = {}
        self.inner_html = ""
        self.text = ""
        self.properties = properties or {}


class FakeWebPage:
    def __init__(self, url, tags):
        self.url = url
        self.html = ""
        self.headers = {}
        self.scripts = []
        self.meta = {}
        self.text = ""
        self._tags = tags

    def select(self, selector):
        return iter(self._tags.get(selector, []))
@pytest.fixture
def async_mock():
    with aioresponses() as m:
        yield m

@httprettified
def test_new_from_url():
    HTTPretty.register_uri(HTTPretty.GET, 'http://example.com/',
                            body='snerble')

    webpage = WebPage.new_from_url('http://example.com/')

    assert webpage.html == 'snerble'

@pytest.mark.asyncio
async def test_new_from_url_async(async_mock):
    async_mock.get('http://example.com', status=200, body='snerble')

    webpage = await WebPage.new_from_url_async('http://example.com/')

    assert webpage.html == 'snerble'

def test_latest():
    analyzer = Wappalyzer.latest()

    print((analyzer.categories))
    assert analyzer.categories['1'].name == 'CMS'
    assert 'Apache' in analyzer.technologies

# Until https://github.com/chorsley/python-Wappalyzer/pull/66 is merged
@pytest.mark.xfail
def test_latest_update(tmp_path: Path):
    
    # Get the lastest file
    lastest_technologies_dict=get_technology_data()
    
    tmp_file = tmp_path.joinpath('technologies.json')
    # Write the content to a tmp file
    with tmp_file.open('w', encoding='utf-8') as t_file:
        t_file.write(str(lastest_technologies_dict))

    # Create Wappalyzer with this file in argument
    wappalyzer1=Wappalyzer.latest(technologies_file=str(tmp_file))

    wappalyzer2=Wappalyzer.latest(update=True)

    assert wappalyzer1.technologies==wappalyzer2.technologies
    assert wappalyzer1.categories==wappalyzer2.categories

def test_analyze_no_technologies():
    analyzer = Wappalyzer(categories={}, technologies={})
    webpage = WebPage('http://example.com', '<html></html>', {})

    detected_technologies = analyzer.analyze(webpage)

    assert detected_technologies == set()

def test_get_implied_technologies():
    analyzer = Wappalyzer(categories={}, technologies={
        'a': {
            'implies': 'b',
        },
        'b': {
            'implies': 'c',
        },
        'c': {
            'implies': 'a',
        },
    })

    implied_technologies = analyzer._get_implied_technologies('a')

    assert implied_technologies == set(['a', 'b', 'c'])

def test_get_analyze_with_categories():
    webpage = WebPage('http://example.com', '<html>aaa</html>', {})
    categories = {
        "1": {
            "name": "cat1",
            "priority": 1
        },
        "2": {
            "name": "cat2",
            "priority": 1
        }
    }

    technologies = {
        'a': {
            'html': 'aaa',
            'cats': [1],
        },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        }
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_categories(webpage)

    assert result == {"a": {"categories": ["cat1"]}}

def test_get_analyze_with_versions():

    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": "^WordPress ?([\\d.]+)?\\;version:\\1"
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions(webpage)

    assert ("WordPress", {"versions": ["5.4.2"]}) in result.items()

def test_analyze_with_versions_and_categories():
    
    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": "^WordPress ?([\\d.]+)?\\;version:\\1"
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions_and_categories(webpage)
    assert analyzer.get_versions(webpage.url, 'WordPress') == ["5.4.2"], analyzer._detected_technologies[webpage.url]
    assert ("WordPress", {"categories": ["CMS", "Blog"], "versions": ["5.4.2"]}) in result.items()

def test_analyze_with_versions_and_categories_pattern_lists():
    
    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": ["Whatever123", "Whatever456", "^WordPress ?([\\d.]+)?\\;version:\\1", "Whatever"]
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions_and_categories(webpage)

    assert ("WordPress", {"categories": ["CMS", "Blog"], "versions": ["5.4.2"]}) in result.items()

def test_analyze_dom_string():

    webpageA = WebPage('http://example.com', '<html><p class="aaa">webpage a</p></html>', {})
    webpageB = WebPage('http://example.com', '<html><p id="bbb">webpage b</p></html>', {})
    categories = {}
    technologies = {
        'a': { 'dom': '.aaa', },
        'b': {'dom': '#bbb', }
    }
    analyzer = Wappalyzer(categories=categories, technologies=technologies)

    assert analyzer.analyze(webpageA) == {"a"}
    assert analyzer.analyze(webpageB) == {"b"}

def test_analyze_dom_list():
    webpageA = WebPage('http://example.com', '<html><p class="aaa">webpage a</p></html>', {})
    webpageB = WebPage('http://example.com', '<html><p id="bbb">webpage b</p></html>', {})
    categories = {}
    technologies = {
        'a': { 'dom': ['.aaa', '[some-other-css-selector]'], },
        'b': { 'dom': ['[some-other-css-selector]', '#bbb'], }
    }
    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    assert analyzer.analyze(webpageA) == {"a"}
    assert analyzer.analyze(webpageB) == {"b"}

def test_analyze_dom_dict_text():
    webpageA = WebPage('http://example.com', '<html><p class="aaa">webpage a</p></html>', {})
    webpageB = WebPage('http://example.com', '<html><p id="bbb">webpage b</p></html>', {})
    categories = {}
    get_dom_val = lambda cat: {
                '#bbb': { 'text': f"webpage\\ {cat}", },
                '.aaa': { 'text': f"webpage\\ {cat}", }
            }
    technologies = {
        'a': { 'dom': get_dom_val('a') },
        'b': { 'dom': get_dom_val('b'), }
    }
    analyzer = Wappalyzer(categories=categories, technologies=technologies)

    assert analyzer.analyze(webpageA) == {"a"}
    assert analyzer.analyze(webpageB) == {"b"}

def test_analyze_dom_dict_exists():
    webpageA = WebPage('http://example.com', '<html><p class="aaa">webpage a</p></html>', {})
    webpageB = WebPage('http://example.com', '<html><p id="bbb">webpage b</p></html>', {})
    categories = {}
    get_dom_val = lambda cat: {
                f'#{cat*3}': { 'exists': "", },
                f'.{cat*3}': { 'exists': "", }
            }
    technologies = {
        'a': { 'dom': get_dom_val('a') },
        'b': { 'dom': get_dom_val('b'), }
    }
    analyzer = Wappalyzer(categories=categories, technologies=technologies)

    assert analyzer.analyze(webpageA) == {"a"}
    assert analyzer.analyze(webpageB) == {"b"}

def test_analyze_dom_dict_attributes():
    webpageA = WebPage('http://example.com', '<html><p class="aaa" onclick="webpageAScript()">webpage a</p></html>', {})
    webpageB = WebPage('http://example.com', '<html><p id="bbb" onclick="webpageBScript()">webpage b</p></html>', {})
    categories = {}
    get_dom_val = lambda cat: {
                f'#{cat*3}': { 'attributes': {'onclick': f'webpage{cat.upper()}Script.*'}, },
                f'.{cat*3}': { 'attributes': {'onclick': f'webpage{cat.upper()}Script.*'}, }
            }
    technologies = {
        'a': { 'dom': get_dom_val('a') },
        'b': { 'dom': get_dom_val('b'), }
    }
    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    assert analyzer.analyze(webpageA) == {"a"}
    assert analyzer.analyze(webpageB) == {"b"}

def test_analyze_scriptSrc():
    webpage = WebPage(
        'http://example.com',
        '<html><head><script src="/static/app.js"></script></head></html>',
        {},
    )
    analyzer = Wappalyzer(categories={}, technologies={
        'a': {'scriptSrc': 'app\\.js'},
    })

    assert analyzer.analyze(webpage) == {"a"}

def test_analyze_text():
    webpage = WebPage('http://example.com', '<html><body>Hello text detection</body></html>', {})
    analyzer = Wappalyzer(categories={}, technologies={
        'a': {'text': 'hello\\ text\\ detection'},
    })

    assert analyzer.analyze(webpage) == {"a"}

def test_analyze_dom_dict_properties():
    webpage = FakeWebPage('http://example.com', {
        'body > div': [FakeTag({'_reactRootContainer': ''})],
    })
    analyzer = Wappalyzer(categories={}, technologies={
        'React': {
            'dom': {
                'body > div': {
                    'properties': {
                        '_reactRootContainer': '',
                    }
                }
            }
        }
    })

    assert analyzer.analyze(webpage) == {"React"}

def test_fingerprint():
    tech_fingerprint = Fingerprint(name='WordPress', **{
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": ["Whatever123", "Whatever456", "^WordPress ?([\\d.]+)?\\;version:\\1", "Whatever"]
            },
            "website": "https://wordpress.org"
            })
    assert tech_fingerprint.meta['generator'][-2].version == '\\1'
    assert tech_fingerprint.meta['generator'][-2].regex.pattern == '^WordPress ?([\d.]+)?'

def cli(*args):
    """Wrap python-Wappalyzer CLI exec"""

    with StringIO() as stream:
        with redirect_stdout(stream):
            main(get_parser().parse_args(args))
        result = json.loads(stream.getvalue())
    return result

@pytest.mark.skipif(os.getenv('GITHUB_ACTIONS') is not None, reason="This test fails on the github CI, python3.9 for some reason.")
def test_cli():
    r = cli('http://exemple.com', '--update', '--user-agent', 'Mozilla/5.0', '--timeout', '30')
    assert len(r) > 2
    assert "Bootstrap" in r

def test_analyze_payload():
    technologies_file = Path(__file__).resolve().parents[1] / 'Wappalyzer' / 'data' / 'technologies.json'
    result = analyze_payload({
        'target_url': 'http://wordpress-example.com',
        'html': '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>',
        'headers': {},
    }, technologies_file=str(technologies_file))

    assert result['target_url'] == 'http://wordpress-example.com'
    assert {
        'name': 'WordPress',
        'version': '5.4.2',
        'confidence': 100,
        'matched_on': 'meta',
    } in result['technologies']
