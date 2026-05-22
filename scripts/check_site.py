#!/usr/bin/env python3
"""Project-specific quality checks for the static website."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = ["index.html", "publications.html"]
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class SiteParser(HTMLParser):
    def __init__(self, filename):
        super().__init__(convert_charrefs=True)
        self.filename = filename
        self.stack = []
        self.links = []
        self.images = []
        self.stylesheets = []
        self.scripts = []
        self.h2 = []
        self.summaries = []
        self.titles = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in VOID_TAGS:
            self.stack.append(tag)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "img":
            self.images.append(attrs.get("src", ""))
            if not attrs.get("alt"):
                raise AssertionError(f"{self.filename}: image is missing alt text")
        elif tag == "link" and attrs.get("rel") == "stylesheet":
            self.stylesheets.append(attrs.get("href", ""))
        elif tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            raise AssertionError(f"{self.filename}: unexpected closing tag </{tag}>")
        opened = self.stack.pop()
        if opened != tag:
            raise AssertionError(
                f"{self.filename}: expected </{opened}> before </{tag}>"
            )

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text or not self.stack:
            return
        current = self.stack[-1]
        if current == "h2":
            self.h2.append(text)
        elif current == "summary":
            self.summaries.append(text)
        elif current == "title":
            self.titles.append(text)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def normalize(text):
    return " ".join(text.split())


def check_html_structure():
    for name in HTML_FILES:
        parser = SiteParser(name)
        content = read(name)
        parser.feed(content)
        require(not parser.stack, f"{name}: unclosed tags: {parser.stack}")

        for path in parser.images + parser.stylesheets + parser.scripts:
            require(path, f"{name}: empty local asset reference")
            require((ROOT / path).exists(), f"{name}: missing asset {path}")

        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("mailto:") or href.startswith("#"):
                continue
            target = href.split("#", 1)[0] or name
            require((ROOT / target).exists(), f"{name}: missing linked file {target}")

        require(
            "Website designed and built with" in content,
            f"{name}: missing footer credit",
        )
        require(
            "Last updated: <span data-last-updated>May 22, 2026</span>." in content,
            f"{name}: missing automatic last-updated footer fallback",
        )
        require(
            '<script src="scripts/site.js"></script>' in content,
            f"{name}: missing shared footer update script",
        )


def check_homepage_spec():
    html = read("index.html")
    text = normalize(html)

    required = [
        "bilingualism and multilingualism, early literacy development, multimodal literacies, heritage language maintenance, and posthuman/post-qualitative methodologies.",
        "everyday practices in language and literacy acquisition.",
        "Biliteracy and Heritage Language Maintenance",
        "Early Literacy Education",
        "Literacy Environment and Resources within Immigrant Families",
        "Socio-material, Multimodal, and Posthuman Literacies",
        "Post-qualitative and Qualitative Research Methodologies",
        "Courses Taught and Supported",
        "<summary>The University of British Columbia</summary>",
        "<summary>Western University</summary>",
        "<summary>Selected journal publications</summary>",
    ]
    for item in required:
        require(item in text or item in html, f"index.html: missing required text: {item}")

    forbidden = [
        "biliteracy learning, language acquisition, and literacy acquisition",
        "Qufu Normal University",
        "Linyi Experimental Secondary School",
        "Course A-Chinese",
        "Course B-Comprehensive",
        "Grade 7-English",
        "Academic writing, L2 writing",
        "Chinese-Canadian children and families</li>",
        "<h2>Teaching</h2>",
    ]
    for item in forbidden:
        require(item not in html, f"index.html: forbidden text found: {item}")

    require(html.count('<details class="fold">') == 3, "index.html: expected 3 folds")


def check_publications_spec():
    html = read("publications.html")
    expected_sections = {
        "Refereed Journal Publications (N=17)": 17,
        "Refereed Book Chapters (N=8)": 8,
        "Non-Refereed Publications (N=4)": 4,
        "Refereed Conference Presentations (N=31)": 31,
        "Non-Refereed Conference Presentations (N=1)": 1,
    }
    require(
        html.count('<details class="fold">') == len(expected_sections),
        "publications.html: unexpected number of collapsible sections",
    )
    for title, count in expected_sections.items():
        pattern = (
            rf"<summary>{re.escape(title)}</summary>.*?"
            rf"<ol class=\"pubs\">(.*?)</ol>"
        )
        match = re.search(pattern, html, flags=re.S)
        require(match, f"publications.html: missing section {title}")
        actual = match.group(1).count("<li>")
        require(
            actual == count,
            f"publications.html: {title} expected {count} items, found {actual}",
        )


def main():
    checks = [check_html_structure, check_homepage_spec, check_publications_spec]
    for check in checks:
        check()
    print("site quality checks passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
