import os
import json
import httpx
import asyncio
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv('.env.local')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Model configuration
o3_mini_model = "o3-mini"

def system_prompt():
    """
    Returns the system prompt from prompt.py
    This is a stub that will be replaced by the actual implementation
    """
    from prompt import system_prompt as actual_system_prompt
    return actual_system_prompt()

def trim_prompt(prompt: str, max_length: int = 25000) -> str:
    """
    Trims a prompt to a maximum length while preserving whole sentences.

    Args:
        prompt: The text to trim
        max_length: Maximum length in characters

    Returns:
        Trimmed text
    """
    if not prompt:
        return ""

    if len(prompt) <= max_length:
        return prompt

    # Try to trim at sentence boundaries
    sentences = prompt.split('. ')
    result = ""

    for sentence in sentences:
        if len(result) + len(sentence) + 2 <= max_length:  # +2 for ". "
            result += sentence + ". "
        else:
            break

    return result.strip()

async def generate_object(model, system, prompt, schema):
    """
    Generate a structured object using OpenAI.

    Args:
        model: Model name or identifier
        system: System prompt
        prompt: User prompt
        schema: JSON schema for the response

    Returns:
        Generated object
    """
    try:
        print(f"generate_object called with prompt length: {len(prompt)}")
        print(f"Schema: {schema}")

        # Add "json" to the prompt to satisfy the response_format requirement
        modified_prompt = f"{prompt}\n\nPlease provide your response in JSON format according to the schema. Your response must be valid JSON."

        print("Calling OpenAI API...")
        response = client.chat.completions.create(
            model=o3_mini_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": modified_prompt}
            ],
            response_format={"type": "json_object"}
        )

        print(f"OpenAI API response received. Status: {response.choices[0].finish_reason}")

        content = response.choices[0].message.content
        print(f"Response content length: {len(content)}")
        print(f"Response content preview: {content[:200]}...")

        result = json.loads(content)
        print(f"JSON parsed successfully. Keys: {list(result.keys())}")

        return {"object": result}
    except Exception as e:
        print(f"Error generating object: {e}")
        print(f"Error type: {type(e)}")
        # Return a minimal valid object based on the schema
        if schema and "properties" in schema:
            minimal_object = {}
            for key, prop in schema["properties"].items():
                if prop.get("type") == "string":
                    minimal_object[key] = "Error generating content"
                elif prop.get("type") == "array":
                    minimal_object[key] = []
                elif prop.get("type") == "object":
                    minimal_object[key] = {}
            return {"object": minimal_object}
        return {"object": {}}
