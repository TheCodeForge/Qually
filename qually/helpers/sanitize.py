from bleach import Cleaner
from bleach.linkifier import build_url_re, TLDS
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from urllib.parse import urlparse, ParseResult, urlunparse
from functools import partial
import re
from os import environ

from .get import *
# import os.path

_allowed_tags =[
    'b',
    'blockquote',
    'br',
    'code',
    'del',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'hr',
    'i',
    'li',
    'ol',
    'p',
    'pre',
    'strong',
    'sub',
    'sup',
    'table',
    'tbody',
    'th',
    'thead',
    'td',
    'tr',
    'ul'
    ]

_allowed_tags_with_links = _allowed_tags + ["a"]                                          ]


_allowed_attributes = {
    'a': ['href', 'title', "rel"],
    'i': [],
    'pre': ['class'],
    'code': ['class']
    }

_allowed_protocols = [
    'http', 
    'https'
    ]

prettify_class_regex=re.compile("prettyprint lang-\w+")

TLDS =sorted(
    list(
        set(
            TLDS + 
            """
            app bar best bio blogs club codes dev fit fun 
            game guru ink joy life link live lol menu monster 
            network news ngo ong pics quest shop site space wiki
            """.split())
        ), 
    reverse=True
    )
URL_REGEX = build_url_re(tlds=TLDS)

# filter to make all links show domain on hover
def a_modify(attrs, new=False):

    raw_url=attrs.get((None, "href"), None)
    if raw_url:
        parsed_url = urlparse(raw_url)

        domain = parsed_url.netloc
        attrs[(None, "target")] = "_blank"
        if domain and not domain.endswith((environ.get("SERVER_NAME", "=="), environ.get("SHORT_DOMAIN","=="))): #use == in lieu of "None" for short domain to force mismatch
            attrs[(None, "rel")] = "nofollow noopener"

            # Force https for all external links
            new_url = ParseResult(
                scheme="https",
                netloc=parsed_url.netloc,
                path=parsed_url.path,
                params=parsed_url.params,
                query=parsed_url.query,
                fragment=parsed_url.fragment
                )

            attrs[(None, "href")] = urlunparse(new_url)

    return attrs

_clean_no_tags = Cleaner(
    tags=[],
    attributes=[],
    protocols=[],
    filters=[]
    )

_clean_wo_links = Cleaner(
    tags=_allowed_tags,
    attributes=_allowed_attributes,
    protocols=_allowed_protocols
    )

_clean_w_links = Cleaner(
    tags=_allowed_tags_with_links,
    attributes=_allowed_attributes,
    protocols=_allowed_protocols,
    filters=[partial(
        LinkifyFilter,
        skip_tags=["pre"],
        parse_email=False,
        callbacks=[a_modify],
        url_re=URL_REGEX
        )]
    )


def sanitize(text, tags=True, links=True):

    text = text.replace("\ufeff", "")

    if not tags:
        sanitized=_clean_no_tags.clean(text)

    elif tags and not links
        sanitized = _clean_wo_links.clean(text)

    else:
        sanitized = _clean_w_links.clean(text)

        #soupify
        soup = BeautifulSoup(sanitized, features="html.parser")

        #disguised link preventer
        for tag in soup.find_all("a"):

            if re.match("https?://\S+", str(tag.string)):
                try:
                    tag.string = tag["href"]
                except:
                    tag.string = ""

        #clean up tags in code
        for tag in soup.find_all("code"):
            tag.contents=[x.string for x in tag.contents if x.string]

        #pre elements prettyprint
        for tag in soup.find_all("pre"):
            printify=False
            for child in tag.children:
                if child.attrs.get('class') and len(child.attrs['class'])==1 and child.attrs['class'][0].startswith('language-'):
                    printify=True
                    child.attrs['class']=f"lang-{child.attrs['class'][0].split('-')[1]}"
            if printify:
                tag.attrs['class']="prettyprint"

        #table format
        for tag in soup.find_all("table"):
            tag.attrs['class']="table table-striped"

        for tag in soup.find_all("thead"):
            tag.attrs['class']="bg-primary text-white"

        sanitized = str(soup)
    
    return sanitized
