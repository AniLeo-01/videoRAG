import asyncio
from src.config import VIDEO_OUTPUT_DIR, PROCESSED_VIDEO_OUTPUT_DIR, QDRANT_COLLECTION_NAME
from src.embedder.embed_clips import video_embedder
import json
from src.utils.qdrant_utils import embeddings_to_points, upsert_to_qdrant

with open('data/transcripts_merged.json', 'r') as f:
  transcripts = json.load(f)

# generate the embeddings of the video clips
docs, embeddings = asyncio.run(video_embedder(
                    video_path= VIDEO_OUTPUT_DIR,
                    transcripts= transcripts,
                    processed_video_clips_path= PROCESSED_VIDEO_OUTPUT_DIR
                  ))

# upsert them to qdrant
vectors = embeddings_to_points(embeddings, docs)
upsert_to_qdrant(QDRANT_COLLECTION_NAME, vectors)
