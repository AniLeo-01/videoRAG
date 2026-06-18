from openai import AsyncOpenAI
from src.config import SCENE_DESCRIBER_MODEL, SCENE_DESCRIBER_URL
import base64
import asyncio

def encode_base64_content(path: str) -> str:
    with open(path, 'rb') as f:
        content_bytes = f.read()
    return base64.b64encode(content_bytes).decode('utf-8')

async def describer(video_path: str):
    client = AsyncOpenAI(api_key="dummy", base_url=SCENE_DESCRIBER_URL)
    video_b64 = await asyncio.to_thread(encode_base64_content, video_path)
    response = await client.chat.completions.create(
        model=SCENE_DESCRIBER_MODEL,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}
                    },
                    {
                        "type": "text",
                        "text": "Describe the scene present in the given video clip which is a part of a video game trailer. Include all environmental, scenary and action details"
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content
