# VideoRAG

A RAG based approach on videos to search and filter across a collection of YouTube videos (movies, trailers, documentaries, etc), using structured filter and semantic filter.
In this case, we are going to use year as the structural filter and prompt as the semantic filter.

## Goals
The system should output the most relevant movies ranked according to the prompt relevance and given year.

## High Level Architecture
```
        ┌──────────────┐
        │ User Query   │
        └──────┬───────┘
               │
               ▼
      ┌─────────────────────┐
      │ Query Service       │
      └─────────┬───────────┘
                │
   ┌────────────┴────────────┐
   │                         │
   ▼                         ▼
Metadata Filter          Vector Search
(Year)                  (Prompt)
   ▼                         ▼
   └────────────┬────────────┘
                ▼
          Ranked Results
                |
                ▼
          Response Builder      
                |
                ▼
               User
```

## Ingestion Architecture
```
 YouTube links (data/video_links.txt)
            │
            ▼
   yt-dlp download ──────────────► data/videos/<id>.mp4
            │
            ▼
 youtube-transcript-api ─────────► data/transcripts.json
            │
            ▼
 merge subtitle timeframes ──────► data/transcripts_merged.json
            │
            ▼
 PySceneDetect / ffmpeg split ───► data/videos_processed/<id>-Scene-<n>.mp4
            │
            ▼
 scene description (VLM) + clip embedding (Gemini)
            │
            ▼
        Qdrant (collection: game_trailers)
```

## Component Design
### Video Downloader
We will use `yt-dlp` library to download youtube videos and metadata (`src/utils/download_vids.py`).
A `cookies.txt` next to the videos directory is picked up automatically to bypass bot checks.

### Transcript Service
We will extract the subtitles/transcripts from the video using `youtube-transcript-api` (`src/utils/download_subs.py`).

### Scene Segmentation
Subtitle fragments are merged into contextual scenes by timeframe overlap (`src/utils/merge_subs_timeframes.py`),
and the source video is split into per-scene clips with PySceneDetect + ffmpeg (`src/utils/extract_keyframes.py`).

### Scene Describer
Each clip is described by a vision-language model over an OpenAI-compatible endpoint (`src/embedder/describe_scene.py`).

### Embedder
The scene description + dialogue and the raw clip bytes are embedded with Gemini embeddings (`src/embedder/embed_clips.py`).
Embedding is checkpointed to `data/embedding_checkpoint.jsonl` so an interrupted run resumes where it stopped.

### Vector Store
Embeddings are upserted into a local Qdrant collection (`src/utils/qdrant_utils.py`).

### Retriever / Generator
A query is embedded, the top-k clips are fetched from Qdrant (`src/retriever/search.py`),
and a generator model selects the relevant video IDs (`src/retriever/generate.py`).
`src/pipeline.py` turns those IDs into `https://www.youtube.com/watch?v={ID}` links.

## Project Layout
```
src/
├── config.py                  # loads env vars
├── pipeline.py                # query → relevant IDs → YouTube links
├── ingestion.py               # embed clips + upsert to Qdrant
├── utils/
│   ├── download_vids.py       # yt-dlp video download
│   ├── download_subs.py       # transcript fetch
│   ├── merge_subs_timeframes.py
│   ├── extract_keyframes.py   # scene splitting
│   └── qdrant_utils.py        # Qdrant points / upsert / search
├── embedder/
│   ├── describe_scene.py      # VLM scene description
│   └── embed_clips.py         # Gemini embeddings + query embedding
└── retriever/
    ├── search.py              # vector search
    └── generate.py            # LLM relevance filter
```

## Prerequisites
- Python `>=3.11`
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (used for scene splitting)
- A running [Qdrant](https://qdrant.tech/) instance on `http://localhost:6333`
- API keys for the embedding, scene-describer and generator models (see `.env.example`)

## Setup

1. **Install dependencies** (using [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync
   ```
   or with pip:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment.** Copy the example and fill in your own values:
   ```bash
   cp .env.example .env
   ```
   Key variables:

   | Variable | Description |
   | --- | --- |
   | `YT_LINKS` | Path to the file of YouTube URLs (default `data/video_links.txt`) |
   | `VIDEO_OUTPUT_DIR` | Where downloaded videos are stored (`data/videos`) |
   | `PROCESSED_VIDEO_OUTPUT_DIR` | Where per-scene clips are written (`data/videos_processed`) |
   | `EMBEDDING_MODEL` / `EMBEDDING_MODEL_API_KEY` | Gemini embedding model + key |
   | `SCENE_DESCRIBER_MODEL` / `SCENE_DESCRIBER_URL` | VLM model + OpenAI-compatible endpoint |
   | `GENERATOR_MODEL` / `GENERATOR_MODEL_URL` / `GENERATOR_MODEL_API_KEY` | LLM that selects relevant IDs |
   | `QDRANT_COLLECTION_NAME` | Qdrant collection name (`game_trailers`) |

3. **Start Qdrant** (Docker), persisting data to `./qdrant_storage`:
   ```bash
   docker run -p 6333:6333 -p 6334:6334 \
     -v "$(pwd)/qdrant_storage:/qdrant/storage" \
     qdrant/qdrant
   ```

## Steps to Recreate

Run everything as modules from the repo root so the `src.` imports resolve (`python -m src...`).

1. **Add video links.** Put one YouTube URL per line in `data/video_links.txt`.

2. **Download the videos** → `data/videos/`:
   ```bash
   python -m src.utils.download_vids
   ```

3. **Fetch transcripts** → `data/transcripts.json`:
   ```bash
   python -m src.utils.download_subs
   ```

4. **Merge subtitles into scenes** → `data/transcripts_merged.json`:
   ```bash
   python -m src.utils.merge_subs_timeframes
   ```

5. **Split videos into per-scene clips** → `data/videos_processed/`:
   ```bash
   python -m src.utils.extract_keyframes
   ```

6. **Describe, embed and index the clips into Qdrant:**
   ```bash
   python -m src.ingestion
   ```

7. **Query the system.** Enter a prompt and get back ranked YouTube links:
   ```bash
   python -m src.pipeline
   ```
   Example:
   ```
   Enter your query: Horror action with guns and monsters
   Relevant videos:
   https://www.youtube.com/watch?v=<ID1>
   https://www.youtube.com/watch?v=<ID2>
   ```

## Notes
- `.env.example` is only a template — replace the placeholder credentials with your own and never commit real secrets.
