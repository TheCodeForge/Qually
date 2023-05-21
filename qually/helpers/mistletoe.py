import re

from mistletoe.block_token import BlockToken
from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer


class RecordMention(SpanToken):
    pattern = re.compile(r"[A-Z]{4}-(\d{5,})")
    parse_inner = False

    def __init__(self, match_obj):
        self.target=match_obj.group(0)

class CustomRenderer(HTMLRenderer):

    def __init__(self, **kwargs):
        super().__init__(
            NcmrMention
            )

    def render_record_mention(self, token):

        return f'<a href="/{token.target}">{token.target}</a>'