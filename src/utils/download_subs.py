from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import os
from youtube_transcript_api import TranscriptsDisabled
from typing import Optional

def fetch_transcript(video_id):
    """
    Returns transcript list:
    [
      {
        'text': ...,
        'start': ...,
        'duration': ...
      }
    ]
    """
    ytt_api = YouTubeTranscriptApi()
    try:
      transcript = ytt_api.fetch(video_id)
      return transcript
    except TranscriptsDisabled:
      print(f"Transcripts disabled for video {video_id}")
      return None

def fetch_transcripts_from_vids_dir(file_path: str, out_file: Optional[str] = None):
  ids = [file.split('.')[0] for file in os.listdir(file_path)]
  transcripts = [{
                  id: [
                        {
                          "text": transcript.text,
                          "start": transcript.start,
                          "duration": transcript.duration
                        } 
                        for transcript in fetch_transcript(id)
                      ]
                  } 
                for id in ids if fetch_transcript(id) is not None]

  if out_file:
    import json
    with open(out_file, "w") as f:
      json.dump(transcripts, f, indent=4)
  return transcripts
  

if __name__ == "__main__":
  fp = "data/videos"
  print(fetch_transcripts_from_vids_dir(fp, "data/transcripts.json"))



  