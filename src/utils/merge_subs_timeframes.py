import json
from pathlib import Path


def merge_sub_timeframes_into_scenes(sub_frames: list[dict]) -> list[dict]:
  """
  Merge fragmented subtitles into contextual scenes based on subtitle timeframe overlaps.

  Two consecutive subtitle frames belong to the same scene when the earlier frame is
  still on screen as the next one begins, i.e. its end time (start + duration) falls
  after the next frame's start. Overlapping frames are collapsed into a single scene
  whose text is the merged frames' text joined by whitespace, whose start is the first
  frame's start, and whose duration spans up to the latest end time in the group.
  """
  scenes: list[dict] = []

  for frame in sorted(sub_frames, key=lambda f: f['start']):
    start = frame['start']
    end = start + frame['duration']
    text = frame['text']

    if scenes and start < scenes[-1]['_end']:
      # Overlaps the current scene -> same scene, extend it.
      scene = scenes[-1]
      scene['text'] = f"{scene['text']} {text}".strip()
      scene['_end'] = max(scene['_end'], end)
    else:
      # No overlap -> start a new scene.
      scenes.append({'text': text, 'start': start, '_end': end})

  # Convert the tracked end times back into durations.
  for scene in scenes:
    scene['duration'] = round(scene.pop('_end') - scene['start'], 3)

  return scenes


def merge_transcripts(transcripts: dict[str, list[dict]]) -> dict[str, list[dict]]:
  """Apply scene merging to every video in a transcripts mapping."""
  return {
    video_id: merge_sub_timeframes_into_scenes(frames)
    for video_id, frames in transcripts.items()
  }


if __name__ == "__main__":
  data_dir = Path(__file__).resolve().parents[2] / "data"
  src = data_dir / "transcripts.json"
  dst = data_dir / "transcripts_merged.json"

  with open(src) as f:
    transcripts = json.load(f)

  merged = merge_transcripts(transcripts)

  with open(dst, "w") as f:
    json.dump(merged, f, indent=2)

  print(f"Wrote merged scenes to {dst}")
