"""Analyse des liens vidéo (YouTube, Vimeo) pour des intégrations respectueuses de la vie privée."""

import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtube-nocookie.com"}
VIMEO_HOSTS = {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}


def parse_video(url):
    """Retourne ``{"provider", "id", "embed", "thumbnail", "url"}`` ou ``None``."""
    if not url:
        return None
    parsed = urlparse(str(url).strip())
    host = (parsed.hostname or "").lower()
    video_id = None
    if host in YOUTUBE_HOSTS:
        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/")[0]
        elif parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        else:
            match = re.match(r"^/(?:embed|shorts|live|v)/([\w-]{6,})", parsed.path)
            video_id = match.group(1) if match else None
        if video_id and re.fullmatch(r"[\w-]{6,20}", video_id):
            return {
                "provider": "youtube",
                "id": video_id,
                "embed": f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&rel=0",
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
    if host in VIMEO_HOSTS:
        match = re.search(r"/(?:video/)?(\d{5,})", parsed.path)
        if match:
            video_id = match.group(1)
            return {
                "provider": "vimeo",
                "id": video_id,
                "embed": f"https://player.vimeo.com/video/{video_id}?autoplay=1&dnt=1",
                "thumbnail": "",
                "url": f"https://vimeo.com/{video_id}",
            }
    return None
