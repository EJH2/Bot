# coding=utf-8
"""PB pasting"""
import aiohttp
import asyncio
import datetime

from ruamel import yaml

DEFAULT_HOST = 'http://ptpb.pw'


def _url(host: str = DEFAULT_HOST, extra: str = ''):
    if host.endswith('/'):
        return f'{host}{extra}'
    return f'{host}/{extra}'


class Paste:
    """Class representing a paste object."""
    def __init__(self, data):
        self.url = None
        self.long = None
        self.short = None
        self.digest = None
        self.date = None
        self.size = None
        self.uuid = None
        self.label = None
        self.sunset = None
        self.status = None
        self.namespace = None
        self.redirect = None

        _data = {}
        for i in [b for b in [e.split(': ') for e in (data.split('\n'))][:-1]]:
            _data[i[0]] = i[1]

        for k in _data:
            setattr(self, k, _data[k])

    def __repr__(self):
        if self.uuid is None:
            return f'<Paste {self.date}>'
        return f'<Paste {self.uuid}>'


class PB:
    """PB instance"""
    def __init__(self, host: str, loop=None):
        self.host = host or DEFAULT_HOST
        self.session = aiohttp.ClientSession(loop=loop or asyncio.get_event_loop())
        self.formatters = None
        self.lexers = None
        self.styles = None
        asyncio.get_event_loop().run_until_complete(self.get_highlights())

    async def get_highlights(self):
        """Gets the highlights used in the formatting functions."""
        urls = {'lexers': 'l', 'formatters': 'lf', 'styles': 'ls'}
        for k in urls:
            resp = await self._request('get', _url(self.host, urls[k]))
            if k != 'styles':
                formatted = [elem for sublist in yaml.safe_load(resp) for elem in sublist]
            else:
                formatted = yaml.safe_load(resp)
            setattr(self, k, formatted)

    async def _request(self, method: str, url: str, *, payload: dict = None):
        """Main function for requesting the pb api."""
        async with self.session.request(method, url, json=payload) as req:
            assert isinstance(req, aiohttp.ClientResponse)
            resp = (await req.read()).decode()
        return resp

    async def create(self, content: str, **kwargs):
        """Creates a paste."""
        payload = {'content': content}
        if kwargs.get('sunset'):
            kwargs['sunset'] = str(datetime.datetime.utcnow() + datetime.timedelta(seconds=kwargs['sunset']))
        for kw in kwargs:
            if kwargs[kw] is not None:
                payload[kw] = kwargs[kw]
        data = await self._request('post', self.host, payload=payload)
        return Paste(data)

    async def read(self, paste_id: str):
        """Reads a paste."""
        return await self._request('get', _url(self.host, paste_id))

    async def update(self, content: str, uuid: str, **kwargs):
        """Updates a paste."""
        payload = {'content': content}
        if kwargs.get('sunset'):
            kwargs['sunset'] = str(datetime.datetime.utcnow() + datetime.timedelta(seconds=kwargs['sunset']))
        for kw in kwargs:
            if kwargs[kw] is not None:
                payload[kw] = kwargs[kw]
        data = await self._request('put', _url(self.host, uuid), payload=payload)
        return Paste(data)

    async def delete(self, uuid: str):
        """Deletes a paste."""
        data = await self._request('delete', _url(self.host, uuid))
        return Paste(data)

    async def shorten(self, url: str):
        """Create a shortened URL."""
        payload = {'content': url}
        data = await self._request('post', _url(self.host, 'u'), payload=payload)
        return Paste(data)

    async def highlight(self, paste_id: str, lexer: str, *, formatter: str = 'html', style: str = 'default'):
        """Returns formatted url for paste"""
        literals = {'lexers': lexer, 'formatters': formatter, 'styles': style}
        for i in literals:
            if not getattr(self, i) or not literals[i] in getattr(self, i):
                return ValueError(f'{i.title()} {literals[i]} not a valid value.')
        extra = f'{paste_id}/{lexer}/{formatter}?{style}'
        return _url(self.host, extra)

    async def render_id(self, paste_id: str):
        """Renders a pre-created paste's content."""
        extra = f'r/{paste_id}'
        return await self._request('get', _url(self.host, extra))

    async def render_content(self, content: str):
        """Renders passed content without the need for a paste."""
        payload = {'content': content}
        return await self._request('post', _url(self.host, 'r'), payload=payload)

    async def render_terminal_id(self, paste_id: str):
        """Renders a paste containing ascii-cast json v1 into an asciinema-player."""
        extra = f't/{paste_id}'
        return await self._request('get', _url(self.host, extra))

    async def render_terminal_content(self, content: str):
        """Renders passed ascii-cast json v1 content into an asciinema-player."""
        payload = {'content': content}
        return await self._request('post', _url(self.host, 't'), payload=payload)
