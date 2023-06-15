from bleach import Cleaner
from bleach.linkifier import build_url_re, TLDS
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from urllib.parse import urlparse, ParseResult, urlunparse
from functools import partial
from mistletoe import Document
import re

from .mistletoe import CustomRenderer

_allowed_tags =[
    'a',
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

_clean_no_tags = Cleaner(
    tags=[],
    attributes=[],
    protocols=[]
    )

_clean_links_only = Cleaner(
    tags=['a'],
    attributes=[],
    protocols=_allowed_protocols,
    filters=[partial(
        LinkifyFilter,
        skip_tags=["pre"],
        parse_email=False,
        url_re=URL_REGEX
        )]
    )

_clean_w_tags = Cleaner(
    tags=_allowed_tags,
    attributes=_allowed_attributes,
    protocols=_allowed_protocols,
    filters=[partial(
        LinkifyFilter,
        skip_tags=["pre"],
        parse_email=False,
        url_re=URL_REGEX
        )]
    )



def txt(raw_text, kind="plain"):

    if kind not in ['plain','links','tags']:
        raise ValueError('`kind` must be one of "plain", "links", "tags"')

    #Part 1: Clean up whitespace and garbage characters

    text=raw_text.lstrip().rstrip()
    text = text.replace("\ufeff", "")
    #text=re.sub("(\n\r?\w+){3,}", "\n\n", text)
    text=re.sub("(\u200b|\u200c|\u200d)",'', text)

    #Part 2: Process markdown
    if kind in ['links','tags']:
        with CustomRenderer() as renderer:
            text = renderer.render(Document(text))

    #Part 3: Bleach; this also linkifies!
    if kind=="links":
        text=_clean_links_only.clean(text)
    elif kind=="plain":
        text=_clean_no_tags.clean(text)
    else:
        text=_clean_w_tags.clean(text)

    #part 4: Parse with BS4 for post-bleach polish
    if kind in ['tags','links']:
        soup=BeautifulSoup(text, features="html.parser")

        #Disguised link preventer
        for tag in soup.find_all('a'):
            if re.match("https?://\S+", str(tag.string)):
                try:
                    tag.string = tag["href"]
                except:
                    tag.string = ""

        #clean up tags in code
        for tag in soup.find_all("code"):
            tag.contents=[x.string for x in tag.contents if x.string]

        #table format
        for tag in soup.find_all("table"):
            tag.attrs['class']="table table-striped"

        for tag in soup.find_all("thead"):
            tag.attrs['class']="bg-primary text-white"

        text=str(soup)

    return text

def html(text):
    return txt(text, kind="tags")