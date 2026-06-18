from src.config import VIDEO_OUTPUT_DIR
from yt_dlp import YoutubeDL
from urllib.parse import urlparse

def download_video(url: str):
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(VIDEO_OUTPUT_DIR / "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        # tv_embedded bypasses the n-challenge and supports cookies;
        # ios also bypasses it but is skipped when a cookiefile is present
        "extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios", "web"]}},
    }
    cookies_path = VIDEO_OUTPUT_DIR.parent / "cookies.txt"
    if cookies_path.exists():
        ydl_opts["cookiefile"] = str(cookies_path)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_id = info["id"]

    video_path = None
    for ext in ["mp4", "mkv", "webm"]:
        p = VIDEO_OUTPUT_DIR / f"{video_id}.{ext}"
        if p.exists():
            video_path = p
            break

    return {
        "video_id": video_id,
        "title": info.get("title"),
        "upload_date": info.get("upload_date"),
        "video_path": str(video_path)
    }

def is_valid_url_format(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme in ("http", "https"), parsed.netloc])

def download_vids_from_file(file_path: str):
    failed = []
    with open(file_path) as f:
        for line in f:
            url = line.strip()
            if not url or not is_valid_url_format(url):
                continue
            try:
                download_video(url)
            except Exception as e:
                print(f"Failed to download {url}: {e}")
                failed.append(url)
    if failed:
        print(f"\n{len(failed)} video(s) failed:")
        for u in failed:
            print(f"  {u}")

if __name__ == "__main__":
    fp = "data/video_links.txt"
    download_vids_from_file(fp)
