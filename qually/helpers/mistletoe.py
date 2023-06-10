import re

from mistletoe.block_token import BlockToken
from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer

from qually.classes import ALL_PROCESSES


class RecordMention(SpanToken):
    pattern = re.compile(r"\w{2,5}-(\d{5,})")
    parse_inner = False
    precedence=100

    def __init__(self, match_obj):
        self.target=match_obj.group(0)

class CustomRenderer(HTMLRenderer):

    def __init__(self, **kwargs):
        super().__init__(
            RecordMention
            )

    def render_record_mention(self, token):

        prefix=token.split('-')[0]

        if prefix.lower() not in 

        return f'<a href="/{token.target}">{token.target}</a>'