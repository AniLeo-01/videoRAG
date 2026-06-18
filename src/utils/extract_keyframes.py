import subprocess
from scenedetect import detect, ContentDetector
from scenedetect import split_video_ffmpeg
import os

def extract_keyframes(video_path: str, output_dir: str):
  scene_list = detect(video_path, ContentDetector())
  split_video_ffmpeg(video_path, scene_list, output_dir=output_dir)


def split_video_by_timeframe(input_video: str, start_time: float, end_time: float, output_path: str):
  """Split a single clip from input_video between start_time and end_time (seconds)."""
  cmd = [
    "ffmpeg", "-y",
    "-ss", str(start_time),
    "-i", input_video,
    "-to", str(end_time - start_time),
    "-c", "copy",
    output_path,
  ]
  subprocess.run(cmd, check=True)


def extract_keyframe_clips_by_timeframe(video_path: str, output_dir: str, id: str, timeframes: list[dict]):
  filepath = video_path
  for i in range(len(timeframes)):
    output_path = os.path.join(output_dir, f"{id}-Scene-{i}.mp4")
    if i == len(timeframes)-1:
      start_time, end_time = timeframes[i]['start'], timeframes[i]['start']+timeframes[i]['duration']
      split_video_by_timeframe(filepath, start_time, end_time, output_path)
      break
    start_time, end_time = timeframes[i]['start'], timeframes[i+1]['start']
    split_video_by_timeframe(filepath, start_time, end_time, output_path)


def keyframe_clip_extraction(video_dir: str, transcription_path: str, output_dir: str):
  with open(f'{transcription_path}', 'r') as f:
    transcription = json.load(f)
  for vid in os.listdir(video_dir):
    id = vid.split(".")[0]
    if id in transcription:
      extract_keyframe_clips_by_timeframe(os.path.join(video_dir, vid), output_dir, id, transcription[id])
    else:
      extract_keyframes(os.path.join(video_dir, vid), output_dir)
      
if __name__ == "__main__":
  import json 
  from src.config import VIDEO_OUTPUT_DIR, PROCESSED_VIDEO_OUTPUT_DIR
  keyframe_clip_extraction(VIDEO_OUTPUT_DIR, 'data/transcripts_merged.json', PROCESSED_VIDEO_OUTPUT_DIR)