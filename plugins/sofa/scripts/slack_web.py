"""slack_web: the Slack Web API calls of sofa-slack and sofa-people.

The base URL is SOFA_SLACK_API (default https://slack.com/api/), so a test can use a fake API.
The bot token goes to that URL, so only https://slack.com/api/ and an http address on this
computer (127.0.0.1, localhost, ::1) are allowed, and a redirect stops the call. slack_pages
follows next_cursor and stops with a failure after MAX_PAGES pages or a repeated cursor.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

SLACK_API = "https://slack.com/api/"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


class Fail(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def api_base():
    """The base URL of the Slack API. The token goes to this URL, so only Slack or this computer is allowed."""
    base = os.environ.get("SOFA_SLACK_API", SLACK_API)
    try:
        url = urllib.parse.urlsplit(base)
        host, port = url.hostname, url.port
    except ValueError:
        raise Fail(f"SOFA_SLACK_API is not a valid URL: {base!r}", 2)
    if base.rstrip("/") == SLACK_API.rstrip("/") and port is None:
        return SLACK_API
    if url.scheme == "http" and host in LOOPBACK_HOSTS and not url.username:
        return base
    raise Fail("SOFA_SLACK_API must be https://slack.com/api/ or an http address on this computer "
               "(127.0.0.1, localhost or ::1), because the bot token goes to it", 2)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib keeps the Authorization header on a redirect, so a redirect would send the token to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Fail(f"Slack answered with a redirect (HTTP {code}). The call stops, because the bot token must go to 1 host only")


SETUP_FIX = "Fix: type /sofa:setup, and do step 5 item 6 (it installs the app again with the new scopes)"


class SlackError(Fail):
    """Slack answered with ok false. error is the error code of Slack."""

    def __init__(self, method, error, needed=""):
        if error == "missing_scope":
            needed_text = f" (needed: {needed})" if needed else ""
            super().__init__(f"{method}: {error}{needed_text}. {SETUP_FIX}")
        else:
            super().__init__(f"{method}: {error}")
        self.error = error


def slack_call(token, method, params=None, headers=None):
    """Call a Slack method with the bot token and return the JSON of the reply. When headers is a dict, the
    headers of the reply go into it, with lower case names."""
    base = api_base()
    req = urllib.request.Request(base.rstrip("/") + "/" + method, data=urllib.parse.urlencode(params or {}).encode(),
                                 method="POST", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=20) as resp:
            data = json.load(resp)
            if headers is not None:
                headers.update({k.lower(): v for k, v in resp.headers.items()})
    except (urllib.error.URLError, ValueError) as e:
        raise Fail(f"{method}: no answer from Slack ({type(e).__name__})")
    if not data.get("ok"):
        raise SlackError(method, data.get("error", "unknown error"), str(data.get("needed", "")))
    return data


MAX_PAGES = 50


def slack_pages(token, method, params, key):
    """Yield the items of the list KEY of each page of METHOD, and follow next_cursor. Stop with a failure after
    MAX_PAGES pages, and when Slack gives a cursor that was sent already."""
    cursor, sent = "", set()
    for _ in range(MAX_PAGES):
        page = slack_call(token, method, dict(params, cursor=cursor) if cursor else params)
        yield from page.get(key, [])
        cursor = (page.get("response_metadata") or {}).get("next_cursor", "")
        if not cursor:
            return
        if cursor in sent:
            raise Fail(f"{method}: Slack gave the same cursor 2 times; the search stops")
        sent.add(cursor)
    raise Fail(f"{method}: more than {MAX_PAGES} pages; the search stops")
