# gemroll
Create a list of subscribed Gemini capsules.

# Usage

```
usage: gemroll.py [-h] (-d | -f) [-H HEADER] [-F FOOTER] [-v] [-n N] input_file output_file

Prepare gemlog roll.

positional arguments:
  input_file            file with Gemini links to subscribed capsules
  output_file           file to put subscriptions to

optional arguments:
  -h, --help            show this help message and exit
  -d, --by-date         show all entries sorted by date
  -f, --by-feed         show entries grouped by feed
  -H HEADER, --header HEADER
                        header to include in subscription file
  -F FOOTER, --footer FOOTER
                        footer to include in subscription file
  -v, --verbose         display debugging information
  -n N                  Number of items from each subscription (default: 5)
```

`gemroll` creates a file with last `N` items from each subscribed capsule. The links are grouped by capsule (`-f`) or sorted by date (`-d`).

The input file has the following format:

```
=> gemini://a.gemini.capsule "Description of the feed" optional-date-format
```

If date format is not given, the default for the Gemini subscription recommendation is used (`%Y-%m-%d`). Gemroll uses Python's `strptime` to parse the date.
