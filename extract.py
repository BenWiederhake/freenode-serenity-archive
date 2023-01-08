#!/usr/bin/env python3

import django.utils.html
import re

DEFAULT_FILENAME = "serenityos"
DEFAULT_EXTRACTIONS = [
    # 1-indexed line numbers!
    (83277, "About a different kind of quote, but that's good enough for me! :)"),
    (100995, None),
    (104142, "Fuzzers are even worse than users."),
    (119659, None),
    (122663, "A quote about putting quotes in VC, in VC."),
    (125770, "Apparently I said that once too often."),
    (125768, "\"jk but only a little bit jk\""),
    (125894, "C++ templates will lead you down the rabbithole."),
    (128669, "The IRC notifications are a little bit harsh sometimes, especially if they all seem to spell failure."),
    (132827, "Overflow-correct code is deviously hard. https://github.com/SerenityOS/serenity/commit/183b2e71ba8d85293db493cab27b8adb4af54981"),
]

# Example: 2020-11-14T15:04:17 #serenityos <thakis> kling, niiice
LINE_PARSE_SAYS_RE = re.compile("^(202.-..-..T..:..:..) #serenityos <([^>]+)> (.+)$")
# Example: 2020-11-14T14:13:16 #serenityos * linusg also uses Hetzner
LINE_PARSE_ACTION_RE = re.compile("^(202.-..-..T..:..:..) #serenityos \* ([^ ]+) (.+)$")

COMMON_HEADER = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="format-detection" content="telephone=no">
    <meta name="description" content="Funny quotes from the historic #serenityos freenode channel">
    <meta name="keywords" content="Funny, quotes, SerenityOS">
    <meta name="robots" value="index">
    <title>Serenity Freenode Quotes</title>
    <link rel="author" href="https://github.com/BenWiederhake/">
    <link rel="icon" type="image/png" sizes="32x32" href="favicon.png">
    <link rel="stylesheet" href="x.css">
</head>
"""

AROUND_LINENO_FORMAT = """
<body>
<h1>Quote around line #{lineno}</h1>
<p>
{pre} <br/>
<span class="highlight">{direct}{context}</span><br/>
{epilog}
</p>
<p>See also <a href="index.html">all other quotes</a>.</p>
</body>
</html>
"""

INDEX_FORMAT = """
<body>
<h1>Juicy quotes from the historic <span class="mono">#serenityos</span> Freenode channel</h1>
<p>We can't link to all {line_count} lines individually, so here's the best {extraction_count} of them:</p>
<ul>
{links}
</ul>
<p>You can also download the <a href="serenityos.gz">raw, compressed archive of <code>#serenityos</code></a>.</p>
</body>
</html>
"""


def extract_parts(raw_line):
    the_match = LINE_PARSE_SAYS_RE.match(raw_line)
    if the_match:
        return "says", *the_match.groups()
    the_match = LINE_PARSE_ACTION_RE.match(raw_line)
    if the_match:
        return "action", *the_match.groups()
    print(f">>>{raw_line}<<<")
    raise AssertionError(raw_line)


def format_line(raw_line):
    line_type, time, user, content = extract_parts(raw_line)
    user = django.utils.html.escape(user)
    content = django.utils.html.escape(content)
    if line_type == "says":
        user_mark = f'&lt;<span class="user">{user}</span>&gt;'
    elif line_type == "action":
        user_mark = f'* <span class="user">{user}</span>'
    else:
        raise AssertionError(line_type)
    return f'<span class="mono"><span class="time">{time}</span> {user_mark} <span class="content">{content}</span></span>'


def generate_around_lineno(lines, lineno, context):
    lineno_zero_indexed = lineno - 1
    lines_preamble = lines[max(0, lineno_zero_indexed - 20) : lineno_zero_indexed]
    line_direct = lines[lineno_zero_indexed]
    lines_epilog = lines[lineno_zero_indexed + 1 : lineno_zero_indexed + 21]
    formatted_preamble = "<br/>\n".join(format_line(l) for l in lines_preamble)
    formatted_direct = format_line(line_direct)
    formatted_epilog = "<br/>\n".join(format_line(l) for l in lines_epilog)
    if context is None:
        context_html = ""
    else:
        context_html = f' <span class="context">({context})</span>'
    return COMMON_HEADER + AROUND_LINENO_FORMAT.format(
        pre=formatted_preamble,
        direct=formatted_direct,
        epilog=formatted_epilog,
        context=context_html,
        lineno=lineno,
    )


def format_link(lineno, raw_line, context):
    _line_type, time, user, content = extract_parts(raw_line)
    user = django.utils.html.escape(user)
    content = django.utils.html.escape(content)
    return f'<li>{user}: <a href=\"quote-{lineno}.html\" class="mono">{content}</a> ({time}, line {lineno})</li>'


def generate_index(extractions, lines):
    formatted_links = "\n".join(format_link(lineno, lines[lineno - 1], context) for lineno, context in extractions)
    return COMMON_HEADER + INDEX_FORMAT.format(
        line_count=len(lines),
        extraction_count=len(extractions),
        links=formatted_links,
    )


def run(filename, extractions):
    with open(filename, "r") as fp:
        lines = fp.read().split("\n")
    if lines[-1] == "":
        lines = lines[: -1]
    for lineno, context in extractions:
        with open(f"pages/quote-{lineno}.html", "w") as fp:
            fp.write(generate_around_lineno(lines, lineno, context))
    with open(f"pages/index.html", "w") as fp:
        fp.write(generate_index(extractions, lines))


if __name__ == "__main__":
    run(DEFAULT_FILENAME, DEFAULT_EXTRACTIONS)
