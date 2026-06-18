import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

_client = QdrantClient(url="http://localhost:6333")

def embeddings_to_points(embeddings:list[float], documents: list[dict]):
  points = []
  for doc, vector in zip(documents, embeddings):
      # `clip` is the unique per-scene key; `id` is the (shared) source video id.
      point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc["clip"]))
      point = PointStruct(
          id=point_id,
          vector=vector,
          payload={
              "video_id": doc["id"],
              "scene": doc["scene"],
              "transcript": doc.get('transcript')
          },
      )
      points.append(point)
  return points

def upsert_to_qdrant(collection_name: str, points: list[PointStruct]):
  if not _client.collection_exists(collection_name):
    _client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=3072,
                distance=Distance.COSINE,
            ),
        )
  _client.upsert(
      collection_name=collection_name,
      points=points,
  )

def search(collection_name: str, query_vector: list[float], limit: int = 5):
  hits = _client.query_points(
      collection_name=collection_name,
      query=query_vector,
      limit=5,
  )
  return [
      {"ID": point.payload.get('video_id'), "score": point.score, "scene": point.payload.get("scene"), "transcript": point.payload.get("transcript")}
      for point in hits.points
  ]