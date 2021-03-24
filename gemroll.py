import argparse
import csv
import datetime
import ignition
import itertools
import re
import sys
import urllib

class Outputter:
    def __init__(self, args):
        self.output_file = args.output_file
        self.header = (args.header or "").replace("\\n", "\n")
        self.footer = (args.footer or "").replace("\\n", "\n")
        self.n = args.n

    def write_header(self, out):
        out.write(self.header + "\n\n")

    def write_footer(self, out):
        out.write(self.footer + "\n\n")

    def output(self, subscriptions):
        with open(self.output_file, "w") as out:
            self.write_header(out)
            self._output(subscriptions, out)
            self.write_footer(out)

    def _output(self, subscriptions, out):
        raise NotImplementedError("Override!")

class ContinuousOutputter(Outputter):
    def _output(self, subscriptions, out):
        items = [item for sub in subscriptions for item in sub.get_last(self.n)]
        items.sort(key=lambda x: x.date, reverse=True)
        for item in items:
            out.write(item.format() + f" [{item.subscription_header}]\n")

class FeedOutputter(Outputter):
    def _output(self, subscriptions, out):
        for subscription in subscriptions:
            out.write("## " + subscription.header + "\n")
            for item in subscription.get_last(self.n):
                out.write(item.format() + "\n")
            out.write("\n")

class DateOutputter(Outputter):
    def _output(self, subscriptions, out):
        items = [item for sub in subscriptions for item in sub.get_last(self.n)]
        items.sort(key=lambda x: x.date, reverse=True)
        groups = itertools.groupby(items, key=lambda x: x.date.date())
        for group in groups:
            out.write("## " + group[0].isoformat() + "\n")
            for item in group[1]:
                out.write(item.format() + f" [{item.subscription_header}]\n")
            out.write("\n")

class Item:
    def __init__(self, link_line, sub):
        self.main_url = sub.url
        _, self.url, self.header = link_line.split(maxsplit=2)
        self.date = datetime.datetime.strptime(self.header.split()[0], sub.date_format)
        self.subscription_header = sub.header

    def absolute_link(self):
        url = urllib.parse.urlparse(self.main_url)
        if self.url.startswith("gemini://"):
            return self.url
        if self.url.startswith("/"):
            return f"{url.scheme}://{url.netloc}{self.url}"
        if self.main_url.endswith("/"):
            return self.main_url + self.url
        before, _, after = self.main_url.rpartition("/")
        return "{before}/{link}"

    def format(self):
        return f"=> {self.absolute_link()} {self.header.strip()}"

class Subscription:
    def __init__(self, subcription_line, args):
        r = csv.reader([subcription_line], delimiter=" ")
        items = list(r)[0]
        self.url, self.header = items[1:3]
        if len(items) > 3:
            self.date_format = items[3]
        else:
            self.date_format = "%Y-%m-%d"
        self.verbose = args.verbose
        self.errors = []
        self.items = []

    def _log(self, text):
        if self.verbose:
            print(text)

    def _is_feed_entry(self, link_line):
        if not link_line.startswith("=>"):
            return False
        parts = link_line.split(maxsplit=3)
        if len(parts) < 3:
            return False
        try:
            date = datetime.datetime.strptime(parts[2], self.date_format)
            return True
        except ValueError:
            return False

    def fetch(self):
        self._log(f"Reading {self.url}")
        resp = ignition.request(self.url)
        if not resp.success():
            self._log(f"Failed to fetch {self.url}")
            self.errors.append("Failed to fetch")
        self.items = [Item(x, self) for x in resp.data().split("\n") if self._is_feed_entry(x)]

    def get_last(self, n):
        if len(self.items) == 0:
            return self.errors

        self.items.sort(key=lambda x: x.date, reverse=True)
        return self.items[:n]

def create_logroll(args):
    if args.by_date:
        output = DateOutputter(args)
    elif args.by_feed:
        output = FeedOutputter(args)
    else:
        output = ContinuousOutputter(args)
    sub_list = [Subscription(x, args) for x in open(args.input_file).readlines() if x.startswith("=>")]
    for sub in sub_list:
        sub.fetch()
    output.output(sub_list)

def get_parser():
    parser = argparse.ArgumentParser(description='Prepare gemlog roll.')
    parser.add_argument("input_file", help="file with Gemini links to subscribed capsules")
    parser.add_argument("output_file", help="file to put subscriptions to")
    grouping = parser.add_mutually_exclusive_group(required=True)
    grouping.add_argument("-c", "--continuous", action="store_true", help="show all entries sorted by date")
    grouping.add_argument("-f", "--by-feed", action="store_true", help="group entries by feed")
    grouping.add_argument("-d", "--by-date", action="store_true", help="group entries by date")
    parser.add_argument("-H", "--header", default="# My subscriptions", help="header to include in subscription file")
    parser.add_argument("-F", "--footer", help="footer to include in subscription file")
    parser.add_argument("-v", "--verbose", action="store_true", help="display debugging information")
    parser.add_argument("-n", type=int, default=5, help="Number of items from each subscription (default: 5)")

    return parser

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    create_logroll(args)
