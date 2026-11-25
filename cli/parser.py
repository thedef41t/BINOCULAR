import argparse

def args_parser(argv: list[str] | None = None) -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        prog="binocular",
        description="Python Web Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 binocular.py -u https://example.com\n"
            "  python3 binocular.py -u https://example.com -d 3 --subs"
        ),
    )
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Target starting URL (e.g. https://example.com)"
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=2,
        help="Maximum crawl depth (default: 2)"
    )
    parser.add_argument(
        "--subs",
        action="store_true",
        help="Include subdomains in crawl scope"
    )

    return parser.parse_args(argv)