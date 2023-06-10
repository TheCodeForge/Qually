import re

from mistletoe.block_token import BlockToken
from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer

from flask import g


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

        prefix, number=token.split('-')

        record=g.user.organization.get_record(prefix, number, graceful=True)

        if record:
            return f'<a href="{record.permalink}">{record.name}</a>'
        else:
            return token