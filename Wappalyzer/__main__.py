import argparse
import json
from .Wappalyzer import analyze, analyze_batch
from .storage import store_analysis_results_to_sqlite

def get_parser() -> argparse.ArgumentParser:
    """Get the CLI `argparse.ArgumentParser`"""
    parser = argparse.ArgumentParser(description="python-Wappalyzer CLI", prog="wappalyzer")
    parser.add_argument('urls', nargs='*', help='URL(s) to analyze')
    parser.add_argument('--input-file', help='Read URLs from a file, one per line')
    parser.add_argument('--update', action='store_true', help='Use the latest technologies file downloaded from the internet')
    parser.add_argument('--user-agent', help='Request user agent', dest='useragent')
    parser.add_argument('--timeout', help='Request timeout', type=int, default=10)
    parser.add_argument('--no-verify', action='store_true', help='Skip SSL cert verify', dest='noverify')
    parser.add_argument('--browser', choices=('none', 'playwright'), default='none', help='Rendering engine to use')
    parser.add_argument('--wait-until', choices=('load', 'domcontentloaded', 'networkidle'), default='networkidle', help='Page load state for browser rendering')
    parser.add_argument('--concurrency', help='Maximum number of URLs to analyze concurrently', type=int, default=5)
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    parser.add_argument('--sqlite-db', help='Store results in a consolidated SQLite database')
    return parser

def _read_urls(args) -> list:
    urls = list(args.urls)
    if args.input_file:
        with open(args.input_file, 'r', encoding='utf-8') as handle:
            urls.extend(
                line.strip()
                for line in handle
                if line.strip() and not line.lstrip().startswith('#')
            )
    if not urls:
        raise SystemExit("At least one URL or --input-file is required")
    return urls

def main(args) -> None:
    """Entrypoint
    :param args: `Namespace` returned by `argparse.ArgumentParser.parse_args`. 
    """
    urls = _read_urls(args)
    kwargs = dict(
        update=args.update,
        useragent=args.useragent,
        timeout=args.timeout,
        verify=not args.noverify,
        browser=args.browser,
        wait_until=args.wait_until,
    )
    if len(urls) == 1:
        result = analyze(urls[0], **kwargs)
    else:
        result = analyze_batch(urls, concurrency=args.concurrency, **kwargs)
    if args.sqlite_db:
        store_analysis_results_to_sqlite(args.sqlite_db, result, url=urls[0] if len(urls) == 1 else None)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=args.pretty))

def run(argv=None) -> int:
    main(get_parser().parse_args(argv))
    return 0

if __name__ == '__main__':
    raise SystemExit(run())
