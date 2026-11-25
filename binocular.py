from cli.starter import header
from cli.parser import args_parser
from crawler.endpoint_analyzer import crawl
import asyncio

def main():
    header()
    args = args_parser()
    for endpoint in asyncio.run(crawl(args.url, max_depth=args.depth, allow_subs=args.subs)):
        print(endpoint)

if __name__ == "__main__":
    main()