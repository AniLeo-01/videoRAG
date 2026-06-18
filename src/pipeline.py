from src.retriever.generate import generate

YOUTUBE_URL_TEMPLATE = "https://www.youtube.com/watch?v={ID}"


def run_pipeline(query: str):
  """Take a user query, fetch relevant video IDs and build YouTube links."""
  ids = generate(query)
  if ids in ("Not Found", None) or not isinstance(ids, list):
    return []
  return [YOUTUBE_URL_TEMPLATE.format(ID=id) for id in ids]


if __name__ == "__main__":
  query = input("Enter your query: ")
  links = run_pipeline(query)
  if links:
    print("Relevant videos:")
    for link in links:
      print(link)
  else:
    print("No relevant videos found.")
