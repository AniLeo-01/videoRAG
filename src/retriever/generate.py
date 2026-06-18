from openai import OpenAI
from src.config import GENERATOR_MODEL_API_KEY, GENERATOR_MODEL, GENERATOR_MODEL_URL, EMBEDDING_MODEL_API_KEY
from src.retriever.search import fetch_relevant_documents

_client = OpenAI(api_key=EMBEDDING_MODEL_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

GENERATOR_PROMPT = """Given the following video game trailer snippets, check which of the following is relevant to the user query and output the IDs:
SNIPPETS:
{snippets}

## NOTES:
STRICTLY output only the unique IDs of the relevant snippets in a comma-separated list of strings like this: ["ID1", "ID2", ...].
If None of the snippets are relevant and answers the query, output -1
DO NOT ASSUME information that are outside the given query.
"""

def generate(query: str):
  limits = [3,5,10]
  limit_counter = 0
  while limit_counter<len(limits):
    rel_docs = fetch_relevant_documents(query, limits[limit_counter])
    # format the ID and scene of docs into strings
    rel_docs = "\n".join([f"ID: {doc['ID']}, Context: {doc['scene']}" for doc in rel_docs])
    response = _client.chat.completions.create(
      model="gemini-3.5-flash",
      messages=[
        {"role": "system", "content": GENERATOR_PROMPT.format(snippets=rel_docs)},
        {"role": "user", "content": query},
      ],
      reasoning_effort="medium",
      temperature=0.7
    )
    output = response.choices[0].message.content
    output = format_thinking_strings(output)
    if output == -1:
      limit_counter += 1
    else:
      try:
        import ast
        ids = ast.literal_eval(output)
        return ids
      except Exception:
        print(output)
        return
  return "Not Found"

def format_thinking_strings(input: str):
  """Remove thinking context from input: <thought></thought>"""
  input = input.split("</thought>")[-1]
  return input
    
      
if __name__ == "__main__":
  query = "Horror action with guns and monsters"
  query = "Side-scrolling video game"
  query = "racing game"
  output = generate(query)
  print("OUTPUT:", output)
  