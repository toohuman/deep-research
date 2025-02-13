import asyncio
from ai.providers import o3_mini_model, system_prompt, generate_object

async def generate_feedback(query, num_questions=3):
    prompt_text = (
        f"Given the following query from the user, ask some follow up questions to clarify the research direction. "
        f"Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear: <query>{query}</query>"
    )
    response = await generate_object(
        model=o3_mini_model,
        system=system_prompt(),
        prompt=prompt_text,
        schema={
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["questions"]
        }
    )
    questions = response.get("object", {}).get("questions", [])
    return questions[:num_questions]

if __name__ == "__main__":
    asyncio.run(generate_feedback("What is AI?"))
