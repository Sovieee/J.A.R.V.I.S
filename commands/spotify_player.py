import base64
import hashlib
import json
import os
import secrets
import time
import webbrowser
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_DEFAULT_REDIRECT_URI = "http://127.0.0.1:5000/spotify/callback"
SPOTIFY_TOKEN_FILE = "spotify_tokens.json"
SPOTIFY_SCOPES = (
    "user-read-playback-state",
    "user-modify-playback-state",
)
SPOTIFY_TOP_HITS_URI = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
GENERIC_MUSIC_REQUESTS = {
    "",
    "a song",
    "song",
    "some song",
    "some songs",
    "music",
    "some music",
    "a music",
    "playlist",
    "a playlist",
    "spotify",
    "something",
    "something good",
}

_pending_pkce = {}


class SpotifyPlaybackError(RuntimeError):
    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


def _client_id():
    return os.getenv("SPOTIFY_CLIENT_ID", "").strip()


def _redirect_uri():
    return os.getenv("SPOTIFY_REDIRECT_URI", SPOTIFY_DEFAULT_REDIRECT_URI).strip()


def _token_path():
    return os.path.join(os.getcwd(), SPOTIFY_TOKEN_FILE)


def _load_tokens():
    token_path = _token_path()
    if not os.path.exists(token_path):
        return {}

    try:
        with open(token_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_tokens(tokens):
    with open(_token_path(), "w", encoding="utf-8") as file:
        json.dump(tokens, file, indent=2)


def _clear_tokens():
    token_path = _token_path()
    if os.path.exists(token_path):
        os.remove(token_path)


def _base64_url_encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def _generate_code_verifier():
    return secrets.token_urlsafe(64)[:96]


def _generate_code_challenge(code_verifier):
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return _base64_url_encode(digest)


def _build_login_url():
    redirect = _redirect_uri()
    parts = urlsplit(redirect)
    return urlunsplit((parts.scheme, parts.netloc, "/spotify/login", "", ""))


def spotify_is_configured():
    return bool(_client_id())


def spotify_is_authorized():
    tokens = _load_tokens()
    if tokens.get("refresh_token"):
        return True

    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at", 0)
    return bool(access_token and time.time() < expires_at)


def get_spotify_status():
    return {
        "configured": spotify_is_configured(),
        "authorized": spotify_is_authorized(),
        "redirect_uri": _redirect_uri(),
        "login_url": _build_login_url(),
    }


def _http_request(url, method="GET", headers=None, params=None, form_data=None, json_data=None):
    if params:
        query = urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    body = None
    request_headers = dict(headers or {})

    if form_data is not None:
        body = urlencode(form_data).encode("utf-8")
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=request_headers, method=method)

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read()
            text = raw.decode("utf-8") if raw else ""
            return response.status, text
    except HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8") if raw else ""
        raise SpotifyPlaybackError(
            f"Spotify request failed with status {exc.code}.",
            status=exc.code,
            payload=_try_parse_json(text),
        ) from exc
    except URLError as exc:
        raise SpotifyPlaybackError("Spotify is unreachable right now.") from exc


def _try_parse_json(text):
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def create_spotify_authorize_url():
    if not spotify_is_configured():
        raise SpotifyPlaybackError(
            "Spotify is not configured yet. Add SPOTIFY_CLIENT_ID to your .env first."
        )

    state = secrets.token_urlsafe(24)
    code_verifier = _generate_code_verifier()
    _pending_pkce[state] = {
        "code_verifier": code_verifier,
        "created_at": time.time(),
    }

    params = {
        "client_id": _client_id(),
        "response_type": "code",
        "redirect_uri": _redirect_uri(),
        "scope": " ".join(SPOTIFY_SCOPES),
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": _generate_code_challenge(code_verifier),
    }

    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def open_spotify_authorization():
    auth_url = create_spotify_authorize_url()
    webbrowser.open(auth_url)
    return auth_url


def complete_spotify_authorization(code, state, error=None):
    if error:
        raise SpotifyPlaybackError(f"Spotify authorization failed: {error}.")

    pending = _pending_pkce.pop(state, None)
    if not pending:
        raise SpotifyPlaybackError("Spotify authorization state expired. Please try again.")

    status, text = _http_request(
        SPOTIFY_TOKEN_URL,
        method="POST",
        form_data={
            "client_id": _client_id(),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _redirect_uri(),
            "code_verifier": pending["code_verifier"],
        },
    )

    if status != 200:
        raise SpotifyPlaybackError("Spotify authorization did not return a token.")

    payload = _try_parse_json(text)
    payload["expires_at"] = time.time() + int(payload.get("expires_in", 3600)) - 60
    _save_tokens(payload)
    return payload


def _refresh_access_token():
    tokens = _load_tokens()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise SpotifyPlaybackError("Spotify is not authorized yet.")

    status, text = _http_request(
        SPOTIFY_TOKEN_URL,
        method="POST",
        form_data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": _client_id(),
        },
    )

    if status != 200:
        raise SpotifyPlaybackError("Spotify token refresh failed.")

    payload = _try_parse_json(text)
    tokens["access_token"] = payload["access_token"]
    tokens["expires_in"] = payload.get("expires_in", tokens.get("expires_in", 3600))
    tokens["expires_at"] = time.time() + int(tokens["expires_in"]) - 60
    if payload.get("refresh_token"):
        tokens["refresh_token"] = payload["refresh_token"]

    _save_tokens(tokens)
    return tokens["access_token"]


def get_valid_spotify_access_token():
    if not spotify_is_configured():
        raise SpotifyPlaybackError(
            "Spotify is not configured yet. Add SPOTIFY_CLIENT_ID to your .env first."
        )

    tokens = _load_tokens()
    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at", 0)

    if access_token and time.time() < expires_at:
        return access_token

    return _refresh_access_token()


def _spotify_api_request(path, method="GET", params=None, json_data=None):
    access_token = get_valid_spotify_access_token()
    status, text = _http_request(
        f"{SPOTIFY_API_BASE}{path}",
        method=method,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        json_data=json_data,
    )

    payload = _try_parse_json(text)
    return status, payload


def _launch_spotify_desktop():
    os.system("start spotify:")


def _find_controllable_device(devices):
    playable = [device for device in devices if not device.get("is_restricted")]
    if not playable:
        return None

    active = next((device for device in playable if device.get("is_active")), None)
    if active:
        return active

    preferred_types = ("computer", "smartphone", "speaker")
    for device_type in preferred_types:
        match = next((device for device in playable if device.get("type", "").lower() == device_type), None)
        if match:
            return match

    return playable[0]


def _get_available_devices():
    _, payload = _spotify_api_request("/me/player/devices")
    return payload.get("devices", [])


def _wait_for_device():
    _launch_spotify_desktop()

    for _ in range(15):
        devices = _get_available_devices()
        device = _find_controllable_device(devices)
        if device:
            return device
        time.sleep(1)

    return None


def _transfer_playback(device_id):
    _spotify_api_request(
        "/me/player",
        method="PUT",
        json_data={
            "device_ids": [device_id],
            "play": False,
        },
    )


def _start_playback(device_id, *, context_uri=None, uris=None):
    body = {}
    if context_uri:
        body["context_uri"] = context_uri
    if uris:
        body["uris"] = uris

    _spotify_api_request(
        "/me/player/play",
        method="PUT",
        params={"device_id": device_id},
        json_data=body,
    )


def _search_spotify_item(query):
    _, payload = _spotify_api_request(
        "/search",
        params={
            "q": query,
            "type": "track,playlist,album",
            "limit": 5,
        },
    )

    tracks = payload.get("tracks", {}).get("items", [])
    playlists = payload.get("playlists", {}).get("items", [])
    albums = payload.get("albums", {}).get("items", [])

    if tracks:
        track = tracks[0]
        return {
            "kind": "track",
            "uri": track["uri"],
            "name": track["name"],
        }

    if playlists:
        playlist = playlists[0]
        return {
            "kind": "context",
            "uri": playlist["uri"],
            "name": playlist["name"],
        }

    if albums:
        album = albums[0]
        return {
            "kind": "context",
            "uri": album["uri"],
            "name": album["name"],
        }

    return None


def extract_spotify_query(command):
    import re

    match = re.search(r"\b(?:play|put on)\b\s+(.+)$", command)
    if not match:
        return None

    query = match.group(1).strip(" .?!,")
    query = re.sub(r"\bon spotify\b", "", query)
    query = re.sub(r"\bfrom spotify\b", "", query)
    query = re.sub(r"\bfor me\b", "", query)
    query = re.sub(r"\bright now\b", "", query)
    query = re.sub(r"\bnow\b", "", query)
    query = re.sub(r"\s+", " ", query).strip(" .?!,")

    if query in GENERIC_MUSIC_REQUESTS:
        return None

    if query.startswith("a song ") or query.startswith("some music "):
        query = re.sub(r"^(a song|some music|music)\s+", "", query).strip()

    return query or None


def play_spotify_request(command):
    if not spotify_is_configured():
        return (
            "Spotify is not configured yet. Add SPOTIFY_CLIENT_ID to your .env and "
            f"register {_redirect_uri()} as a redirect URI in your Spotify app."
        )

    if not spotify_is_authorized():
        open_spotify_authorization()
        return (
            "I opened Spotify sign-in in your browser. Approve access, then ask me to play it again."
        )

    try:
        device = _wait_for_device()
        if not device:
            return (
                "I could not find a controllable Spotify device. Open the Spotify desktop app and try again."
            )

        if not device.get("is_active"):
            _transfer_playback(device["id"])

        query = extract_spotify_query(command)
        if not query:
            _start_playback(device["id"], context_uri=SPOTIFY_TOP_HITS_URI)
            return "Playing Today's Top Hits on Spotify."

        item = _search_spotify_item(query)
        if not item:
            return f"I could not find anything on Spotify for {query}."

        if item["kind"] == "track":
            _start_playback(device["id"], uris=[item["uri"]])
        else:
            _start_playback(device["id"], context_uri=item["uri"])

        return f"Playing {item['name']} on Spotify."

    except SpotifyPlaybackError as exc:
        if exc.status == 401:
            _clear_tokens()
            open_spotify_authorization()
            return "Your Spotify session expired. I opened sign-in again; please approve access and retry."

        if exc.status == 403:
            return (
                "Spotify playback control needs Spotify Premium and a controllable active device."
            )

        return str(exc)


def spotify_callback_page(success, message):
    title = "Spotify Connected" if success else "Spotify Connection Failed"
    color = "#16a34a" if success else "#dc2626"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #020617;
      color: #e2e8f0;
      font-family: Consolas, monospace;
    }}
    .card {{
      max-width: 540px;
      padding: 28px;
      border: 1px solid rgba(148, 163, 184, 0.25);
      background: rgba(15, 23, 42, 0.92);
      box-shadow: 0 18px 60px rgba(2, 6, 23, 0.45);
    }}
    h1 {{
      margin-top: 0;
      color: {color};
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <p>{message}</p>
    <p>You can close this tab and go back to JARVIS.</p>
  </div>
</body>
</html>"""
