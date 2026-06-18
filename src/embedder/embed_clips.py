import asyncio
import glob
import json
import os
from tqdm.asyncio import tqdm_asyncio
from google import genai
from google.genai import types
from src.config import EMBEDDING_MODEL, EMBEDDING_MODEL_API_KEY
from src.embedder.describe_scene import describer

EMBEDDING_PROMPT = """
VIDEO DESCRIPTION:
{scene_description}

DIALOGUE:
{transcript_text}
"""

EMBEDDING_PROMPT_WITHOUT_DIALOGUE = """
VIDEO DESCRIPTION:
{scene_description}
"""

_client = genai.Client(api_key=EMBEDDING_MODEL_API_KEY)

def embed_query(query: str):
    result = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query]
    )
    return result.embeddings[0].values

async def embed_video_clips(video_path: str, scene_desc: str | None = None, transcription: str | None = None):
    video_bytes = await asyncio.to_thread(lambda: open(video_path, 'rb').read())
    result = await _client.aio.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[
            EMBEDDING_PROMPT.format(
                scene_description=scene_desc,
                transcript_text=transcription
            ) if transcription else EMBEDDING_PROMPT_WITHOUT_DIALOGUE.format(
                scene_description=scene_desc
            ),
            types.Part.from_bytes(
                data=video_bytes,
                mime_type="video/mp4"
            )
        ]
    )
    return result.embeddings[0].values

DEFAULT_CHECKPOINT_PATH = "data/embedding_checkpoint.jsonl"

def _load_checkpoint(path: str) -> dict:
    """Map each already-processed clip filepath to its (doc, embedding)."""
    done = {}
    if not os.path.exists(path):
        return done
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            done[rec["key"]] = (rec["doc"], rec["embedding"])
    return done

def _append_checkpoint(path: str, key: str, doc: dict, embedding: list):
    with open(path, "a") as f:
        f.write(json.dumps({"key": key, "doc": doc, "embedding": embedding}) + "\n")

async def _process_clip(filepath: str, id: str, transcription: str | None,
                        checkpoint_path: str, lock: asyncio.Lock):
    scene_desc = await describer(filepath)
    embedding = await embed_video_clips(filepath, scene_desc, transcription)
    # `clip` is the unique per-scene key; `id` is the (shared) source video id.
    doc = {"id": id, "clip": filepath, "scene": scene_desc}
    if transcription:
        doc["transcript"] = transcription
    # Persist as soon as this clip finishes so a halt can resume from here. The
    # lock serializes appends across concurrent clips to keep the file intact.
    async with lock:
        await asyncio.to_thread(_append_checkpoint, checkpoint_path, filepath, doc, embedding)
    return doc, embedding

async def video_embedder(video_path: str, transcripts: dict, processed_video_clips_path: str,
                         checkpoint_path: str = DEFAULT_CHECKPOINT_PATH):
    # Collect every clip as (unique filepath key, id, transcription).
    clips = []
    for files in os.listdir(video_path):
        id = files.split('.')[0]
        transcription = transcripts.get(id)
        if transcription:
            for i in range(len(transcription)):
                filepath = os.path.join(processed_video_clips_path, f"{id}-Scene-{i}.mp4")
                clips.append((filepath, id, transcription[i]))
        else:
            for filepath in glob.glob(os.path.join(processed_video_clips_path, f"{id}-Scene-*")):
                clips.append((filepath, id, None))

    done = _load_checkpoint(checkpoint_path)
    pending = [c for c in clips if c[0] not in done]

    lock = asyncio.Lock()
    tasks = [_process_clip(fp, id, tr, checkpoint_path, lock) for fp, id, tr in pending]

    # Seed the bar at the already-done count so a resume continues from e.g.
    # 92/418 instead of restarting at 0.
    new_results = await tqdm_asyncio.gather(
        *tasks, desc="Embedding clips", initial=len(done), total=len(clips)
    )

    results = list(done.values()) + list(new_results)
    docs = [r[0] for r in results]
    embeddings = [r[1] for r in results]

    # All clips finished — the checkpoint was only needed to resume a halt, so
    # remove it. A future failed run will leave its own checkpoint behind.
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    return docs, embeddings
