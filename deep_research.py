import asyncio
import math
import os
from ai.providers import o3_mini_model, trim_prompt, system_prompt, generate_object, FirecrawlApp

# Increase this if you have higher API rate limits
CONCURRENCY_LIMIT = 4

async def generate_serp_queries(query, num_queries=3, learnings=None):
    learnings = learnings or []
    prompt_text = (
        f"Given the user's prompt: <prompt>{query}</prompt>, generate a valid JSON object with a field 'queries' which is an array of up to {num_queries} unique SERP queries. "
        "Each element in this array should be an object with two string keys: 'query' (the search query) and 'researchGoal' (a brief description of the intended research outcome). "
        "Ensure the output is in strict JSON format without any additional text."
    )
    if learnings:
        prompt_text += " Use the following learnings to refine the queries: " + "\n".join(learnings)

    response = await generate_object(
        model=o3_mini_model,
        system=system_prompt(),
        prompt=prompt_text,
        schema={
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "researchGoal": {"type": "string"}
                        },
                        "required": ["query", "researchGoal"]
                    }
                }
            },
            "required": ["queries"]
        }
    )
    queries = response.get("object", {}).get("queries", [])
    print(f"Created {len(queries)} queries: {queries}")
    return queries[:num_queries]

async def process_serp_result(query, result, num_learnings=3, num_follow_up_questions=3):
    # Filter out null/empty markdown content and trim them
    contents = [trim_prompt(item["markdown"], 25000) for item in result.get("data", []) if item.get("markdown")]
    print(f"Ran {query}, found {len(contents)} contents")

    # If no contents found, return empty learnings and followUpQuestions immediately.
    if not contents:
        print(f"No contents found for query {query}. Returning empty learnings and follow-up questions.")
        return {"learnings": [], "followUpQuestions": []}

    # Build the prompt from scraped contents (each wrapped in <content> tags)
    contents_text = "\n".join([f"<content>\n{content}\n</content>" for content in contents])
    prompt_text = (
        f"Given the following contents from a SERP search for the query <query>{query}</query>, generate a list of learnings from the contents. "
        f"Return a maximum of {num_learnings} learnings, but feel free to return less if the contents are clear. "
        f"Ensure each learning is unique and provide concise, detailed information. "
        f"Include any entities (such as people, places, companies, products) and any exact metrics, numbers, or dates mentioned.\n\n"
        f"<contents>{contents_text}</contents>"
    )

    response = await generate_object(
        model=o3_mini_model,
        system=system_prompt(),
        prompt=prompt_text,
        schema={
            "type": "object",
            "properties": {
                "learnings": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "followUpQuestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["learnings", "followUpQuestions"]
        }
    )
    learnings = response.get("object", {}).get("learnings", [])
    print(f"Created {len(learnings)} learnings: {learnings}")
    return response.get("object", {})

async def write_final_report(prompt, learnings, visited_urls):
    # Prepare learnings string with each learning wrapped in tags.
    learnings_string = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])
    learnings_string = trim_prompt(learnings_string, 150000)

    prompt_text = (
        f"Given the following prompt from the user, write a final report on the topic using the learnings from research. "
        f"Make it as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:\n\n"
        f"<prompt>{prompt}</prompt>\n\n"
        f"Here are all the learnings from previous research:\n\n"
        f"<learnings>\n{learnings_string}\n</learnings>"
    )
    response = await generate_object(
        model=o3_mini_model,
        system=system_prompt(),
        prompt=prompt_text,
        schema={
            "type": "object",
            "properties": {
                "reportMarkdown": {"type": "string"}
            },
            "required": ["reportMarkdown"]
        }
    )
    report = response.get("object", {}).get("reportMarkdown", "")
    # Append visited URLs section
    urls_section = "\n\n## Sources\n\n" + "\n".join([f"- {url}" for url in visited_urls])
    return report + urls_section

async def deep_research(query, breadth, depth, learnings=None, visited_urls=None):
    learnings = learnings or []
    visited_urls = visited_urls or []

    serp_queries = await generate_serp_queries(query, num_queries=breadth, learnings=learnings)
    firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_KEY"), api_url=os.getenv("FIRECRAWL_BASE_URL"))
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def process_query(serp_query):
        async with semaphore:
            try:
                result = await firecrawl.search(serp_query["query"], timeout=15000, limit=5, scrapeOptions={"formats": ["markdown"]})
                # Collect URLs from the search results.
                new_urls = [item["url"] for item in result.get("data", []) if item.get("url")]
                new_breadth = math.ceil(breadth / 2)
                new_depth = depth - 1

                new_learnings_obj = await process_serp_result(serp_query["query"], result, num_follow_up_questions=new_breadth)
                all_learnings = learnings + new_learnings_obj.get("learnings", [])
                all_urls = visited_urls + new_urls

                if new_depth > 0:
                    print(f"Researching deeper, breadth: {new_breadth}, depth: {new_depth}")
                    next_query = (
                        f"Previous research goal: {serp_query['researchGoal']}\n"
                        f"Follow-up research directions:" + "".join(f"\n{q}" for q in new_learnings_obj.get("followUpQuestions", []))
                    )
                    return await deep_research(next_query, new_breadth, new_depth, all_learnings, all_urls)
                else:
                    return {"learnings": all_learnings, "visitedUrls": all_urls}
            except Exception as e:
                print(f"Error running query: {serp_query['query']}: {e}")
                return {"learnings": [], "visitedUrls": []}

    tasks = [process_query(q) for q in serp_queries]
    results = await asyncio.gather(*tasks)
    # Flatten and remove duplicates by converting to set
    final_learnings = list(set([l for r in results for l in r.get("learnings", [])]))
    final_urls = list(set([u for r in results for u in r.get("visitedUrls", [])]))
    return {"learnings": final_learnings, "visitedUrls": final_urls}

if __name__ == "__main__":
    # For debugging purposes
    asyncio.run(deep_research("test", 2, 1))
