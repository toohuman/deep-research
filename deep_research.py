import asyncio
import math
import os
from ai.providers import o3_mini_model, trim_prompt, system_prompt, generate_object
from markdown_prompt import markdown_system_prompt
from ai.firecrawl import FirecrawlApp

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
    # Safely extract and filter markdown content
    contents = []
    for item in result.get("data", []):
        if item and isinstance(item, dict) and "markdown" in item and item["markdown"]:
            contents.append(trim_prompt(item["markdown"], 25000))

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
    print(f"Starting write_final_report with {len(learnings)} learnings and {len(visited_urls)} URLs")

    # Prepare learnings string with each learning wrapped in tags.
    # Handle both string and dictionary learnings
    formatted_learnings = []
    for i, learning in enumerate(learnings):
        print(f"Processing learning {i+1}: {type(learning)}")
        if isinstance(learning, dict):
            # Extract the most important fields from the dictionary
            if 'title' in learning and ('details' in learning or 'description' in learning):
                details = learning.get('details', learning.get('description', ''))
                formatted_learning = f"**{learning['title']}**\n\n{details}"
                formatted_learnings.append(formatted_learning)
                print(f"  - Formatted dictionary learning with title: {learning['title']}")
            else:
                # If the dictionary doesn't have the expected structure, convert it to a string
                formatted_learnings.append(str(learning))
                print(f"  - Converted dictionary to string: {str(learning)[:50]}...")
        else:
            # If it's already a string, use it as is
            formatted_learnings.append(learning)
            print(f"  - Using string learning: {learning[:50]}...")

    learnings_string = "\n\n".join([f"<learning>\n{learning}\n</learning>" for learning in formatted_learnings])
    learnings_string = trim_prompt(learnings_string, 150000)
    print(f"Formatted learnings string length: {len(learnings_string)}")

    # Create a numbered list of source URLs for reference with anchor IDs
    sources_list = "\n".join([f"{i+1}. <a id=\"ref{i+1}\"></a>[{url}]({url})" for i, url in enumerate(visited_urls)])

    prompt_text = (
        f"Given the following prompt from the user, write a final report on the topic using the learnings from research. "
        f"Make it as detailed as possible, aim for 3 or more pages, include ALL the learnings from research. "
        f"Format your response as a well-structured Markdown document with proper headings, lists, and formatting. "
        f"Include a numbered Sources section at the end with all the URLs listed.\n\n"
        f"When citing information in the text, use a LaTeX-like citation format by creating a markdown link with a reference number, like this: [[1]](#ref1), [[2]](#ref2), etc. "
        f"Each citation should be a clickable link that jumps to the corresponding entry in the Sources section. "
        f"When multiple pieces of information come from the same source, use the same citation number. "
        f"Place citations at the end of sentences or paragraphs where the information is used.\n\n"
        f"<prompt>{prompt}</prompt>\n\n"
        f"Here are all the learnings from previous research:\n\n"
        f"<learnings>\n{learnings_string}\n</learnings>\n\n"
        f"Here are the source URLs to include in your report (numbered for citation):\n\n"
        f"<sources>\n{sources_list}\n</sources>"
    )
    print(f"Prompt text length: {len(prompt_text)}")

    try:
        print("Calling generate_object...")
        response = await generate_object(
            model=o3_mini_model,
            system=markdown_system_prompt(),
            prompt=prompt_text,
            schema={
                "type": "object",
                "properties": {
                    "reportMarkdown": {
                        "type": "string",
                        "description": "The complete markdown-formatted report including all sections and sources"
                    }
                },
                "required": ["reportMarkdown"]
            }
        )
        print(f"Response from generate_object: {response}")

        # Check if the response has the expected structure
        response_obj = response.get("object", {})
        print(f"Response object keys: {list(response_obj.keys())}")

        # Try to extract the report content from different possible structures
        report = ""

        # Check for content key (one format we're getting)
        if "content" in response_obj:
            print("Found content in response, using as markdown")
            report = response_obj.get("content", "")
        # Check for reportMarkdown key (our expected format)
        elif "reportMarkdown" in response_obj:
            report = response_obj.get("reportMarkdown", "")
        # Check if we have reportTitle (another format we're getting)
        elif "reportTitle" in response_obj:
            print("Found reportTitle in response, converting to markdown")
            title = response_obj.get("reportTitle", "Research Report")
            introduction = response_obj.get("introduction", "")
            conclusion = response_obj.get("conclusion", "")

            # Start with the title
            report = f"# {title}\n\n"

            # Add introduction if present
            if introduction:
                report += f"## Introduction\n\n{introduction}\n\n"

            # Process all other fields that might contain content
            for key, value in response_obj.items():
                if key not in ["reportTitle", "introduction", "conclusion"]:
                    # Convert snake_case or camelCase to Title Case for section headers
                    section_title = key.replace('_', ' ').title()

                    if isinstance(value, str):
                        # If it's a string, add it directly
                        report += f"## {section_title}\n\n{value}\n\n"
                    elif isinstance(value, dict):
                        # If it's a dictionary, process each key as a subsection
                        report += f"## {section_title}\n\n"
                        for sub_key, sub_value in value.items():
                            # Convert snake_case or camelCase to Title Case for subsection headers
                            sub_section_title = sub_key.replace('_', ' ').title()
                            if isinstance(sub_value, str):
                                report += f"### {sub_section_title}\n\n{sub_value}\n\n"
                            elif isinstance(sub_value, dict):
                                # Handle nested dictionaries (up to 2 levels deep)
                                report += f"### {sub_section_title}\n\n"
                                for sub_sub_key, sub_sub_value in sub_value.items():
                                    sub_sub_section_title = sub_sub_key.replace('_', ' ').title()
                                    if isinstance(sub_sub_value, str):
                                        report += f"#### {sub_sub_section_title}\n\n{sub_sub_value}\n\n"
                                    else:
                                        # For any other type, convert to string
                                        report += f"#### {sub_sub_section_title}\n\n{str(sub_sub_value)}\n\n"

            # Add conclusion if present
            if conclusion:
                report += f"## Conclusion\n\n{conclusion}\n\n"
        # Check for final_report key (another format we're getting)
        elif "final_report" in response_obj:
            print("Found final_report object in response, converting to markdown")
            final_report_content = response_obj.get("final_report", "")

            # If final_report is a string, use it directly
            if isinstance(final_report_content, str):
                report = final_report_content
            # If final_report is an object, process it
            elif isinstance(final_report_content, dict):
                report_obj = final_report_content
                title = report_obj.get("title", "Research Report")
                introduction = report_obj.get("introduction", "")
                conclusion = report_obj.get("conclusion", "")

                # Start with the title
                report = f"# {title}\n\n"

                # Add introduction if present
                if introduction:
                    report += f"## Introduction\n\n{introduction}\n\n"

                # Process all other fields that might contain content
                for key, value in report_obj.items():
                    if key not in ["title", "introduction", "conclusion"]:
                        # Convert snake_case or camelCase to Title Case for section headers
                        section_title = key.replace('_', ' ').title()

                        if isinstance(value, str):
                            # If it's a string, add it directly
                            report += f"## {section_title}\n\n{value}\n\n"
                        elif isinstance(value, dict):
                            # If it's a dictionary, process each key as a subsection
                            report += f"## {section_title}\n\n"
                            for sub_key, sub_value in value.items():
                                # Convert snake_case or camelCase to Title Case for subsection headers
                                sub_section_title = sub_key.replace('_', ' ').title()
                                if isinstance(sub_value, str):
                                    report += f"### {sub_section_title}\n\n{sub_value}\n\n"
                                elif isinstance(sub_value, dict):
                                    # Handle nested dictionaries (up to 2 levels deep)
                                    report += f"### {sub_section_title}\n\n"
                                    for sub_sub_key, sub_sub_value in sub_value.items():
                                        sub_sub_section_title = sub_sub_key.replace('_', ' ').title()
                                        if isinstance(sub_sub_value, str):
                                            report += f"#### {sub_sub_section_title}\n\n{sub_sub_value}\n\n"
                                        else:
                                            # For any other type, convert to string
                                            report += f"#### {sub_sub_section_title}\n\n{str(sub_sub_value)}\n\n"

                # Add conclusion if present
                if conclusion:
                    report += f"## Conclusion\n\n{conclusion}\n\n"
            else:
                # Fallback if final_report is neither string nor dict
                report = "# Research Report\n\n"
        # Check for report key (another format we're getting)
        elif "report" in response_obj:
            print("Found report object in response, converting to markdown")
            report_content = response_obj.get("report", "")

            # If report is a string, use it directly
            if isinstance(report_content, str):
                report = report_content
            # If report is an object, process it
            elif isinstance(report_content, dict):
                report_obj = report_content
                title = report_obj.get("title", "Research Report")
                introduction = report_obj.get("introduction", "")
                conclusion = report_obj.get("conclusion", "")

                # Start with the title
                report = f"# {title}\n\n"

                # Add introduction if present
                if introduction:
                    report += f"## Introduction\n\n{introduction}\n\n"

                # Process all other fields that might contain content
                for key, value in report_obj.items():
                    if key not in ["title", "introduction", "conclusion"] and isinstance(value, str):
                        # Convert snake_case or camelCase to Title Case for section headers
                        section_title = key.replace('_', ' ').title()
                        report += f"## {section_title}\n\n{value}\n\n"

                # Add conclusion if present
                if conclusion:
                    report += f"## Conclusion\n\n{conclusion}\n\n"
            else:
                # Fallback if report is neither string nor dict
                report = "# Research Report\n\n"
        # Check for sections key (one format we're getting)
        elif "sections" in response_obj:
            print("Found sections in response, converting to markdown")
            sections = response_obj.get("sections", [])
            title = response_obj.get("title", "Research Report")
            conclusion = response_obj.get("conclusion", "")

            # Convert sections to markdown
            report = f"# {title}\n\n"
            for section in sections:
                section_title = section.get("section_title", "")
                content = section.get("content", "")
                report += f"## {section_title}\n\n{content}\n\n"

            if conclusion:
                report += f"## Conclusion\n\n{conclusion}\n\n"
        # Check for pages key (another format we're getting)
        elif "pages" in response_obj:
            print("Found pages in response, converting to markdown")
            pages = response_obj.get("pages", [])
            title = response_obj.get("title", "Research Report")
            introduction = response_obj.get("introduction", "")
            conclusion = response_obj.get("conclusion", "")

            # Convert pages to markdown
            report = f"# {title}\n\n"

            if introduction:
                report += f"## Introduction\n\n{introduction}\n\n"

            for page in pages:
                page_number = page.get("pageNumber", "")
                content = page.get("content", "")
                report += f"## Page {page_number}\n\n{content}\n\n"

            if conclusion:
                report += f"## Conclusion\n\n{conclusion}\n\n"

        print(f"Report length: {len(report)}")

        # If the report is still empty, generate a simple report directly
        if not report:
            print("Report is empty, generating a simple report")
            simple_report = "# Research Report\n\n"

            # Add a Key Findings section with all learnings
            simple_report += "## Key Findings\n\n"
            for learning in formatted_learnings:
                simple_report += f"{learning}\n\n"

            report = simple_report

        # Check if the report already has a Sources section
        if "## Sources" not in report:
            # Append visited URLs section with numbered references and anchor IDs
            urls_section = "\n\n## Sources\n\n" + "\n".join([f"{i+1}. <a id=\"ref{i+1}\"></a>[{url}]({url})" for i, url in enumerate(visited_urls)])
            report += urls_section

        return report
    except Exception as e:
        print(f"Error in write_final_report: {e}")
        # Generate a simple report as fallback
        simple_report = "# Research Report\n\n"

        # Add a Key Findings section with all learnings
        simple_report += "## Key Findings\n\n"
        for learning in formatted_learnings:
            simple_report += f"{learning}\n\n"

        # Add Sources section with numbered references and anchor IDs
        urls_section = "\n\n## Sources\n\n" + "\n".join([f"{i+1}. <a id=\"ref{i+1}\"></a>[{url}]({url})" for i, url in enumerate(visited_urls)])
        return simple_report + urls_section

async def deep_research(query, breadth, depth, learnings=None, visited_urls=None):
    learnings = learnings or []
    visited_urls = visited_urls or []

    serp_queries = await generate_serp_queries(query, num_queries=breadth, learnings=learnings)

    # Get API key and base URL from environment variables
    api_key = os.getenv("FIRECRAWL_API_KEY")
    api_url = os.getenv("FIRECRAWL_BASE_URL")

    print(f"FireCrawl API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
    print(f"FireCrawl Base URL: {api_url}")

    if not api_key:
        print("ERROR: FireCrawl API key is not set. Cannot perform search.")
        return {"learnings": learnings, "visitedUrls": []}

    try:
        firecrawl = FirecrawlApp(api_key=api_key, api_url=api_url)
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    except Exception as e:
        print(f"ERROR: Failed to initialize FireCrawl API: {e}")
        return {"learnings": learnings, "visitedUrls": []}

    async def process_query(serp_query):
        async with semaphore:
            try:
                print(f"Searching for: {serp_query['query']}")
                result = await firecrawl.search(serp_query["query"], timeout=15000, limit=5, scrapeOptions={"formats": ["markdown"]})
                print(f"Search result status: {result.get('status', 'unknown')}")

                # Collect URLs from the search results.
                data_items = result.get("data", [])
                print(f"Found {len(data_items)} data items")

                # Make sure we're extracting URLs correctly
                new_urls = []
                for item in data_items:
                    if item and isinstance(item, dict) and "url" in item and item["url"]:
                        new_urls.append(item["url"])

                print(f"Extracted {len(new_urls)} URLs: {new_urls}")

                if not new_urls:
                    print(f"WARNING: No URLs found in search results for query: {serp_query['query']}")
                    # Add a dummy URL for debugging purposes if needed
                    # new_urls = [f"https://example.com/search?q={serp_query['query']}"]

                new_breadth = math.ceil(breadth / 2)
                new_depth = depth - 1

                new_learnings_obj = await process_serp_result(serp_query["query"], result, num_follow_up_questions=new_breadth)

                # Process learnings to ensure they are strings
                new_learnings = new_learnings_obj.get("learnings", [])
                processed_learnings = []

                for learning in new_learnings:
                    if isinstance(learning, str):
                        processed_learnings.append(learning)
                    elif isinstance(learning, dict):
                        # Convert dictionary to string representation
                        if 'title' in learning and ('details' in learning or 'description' in learning):
                            details = learning.get('details', learning.get('description', ''))
                            processed_learning = f"{learning['title']}: {details}"
                        else:
                            processed_learning = str(learning)
                        processed_learnings.append(processed_learning)
                    else:
                        # For any other type, convert to string
                        processed_learnings.append(str(learning))

                all_learnings = learnings + processed_learnings
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
                print(f"ERROR: Failed to run query '{serp_query['query']}': {e}")
                return {"learnings": [], "visitedUrls": []}

    tasks = [process_query(q) for q in serp_queries]
    results = await asyncio.gather(*tasks)
    # Flatten the learnings and URLs
    all_learnings = [l for r in results for l in r.get("learnings", [])]
    all_urls = [u for r in results for u in r.get("visitedUrls", [])]

    # Remove duplicates from URLs (which are hashable)
    final_urls = list(set(all_urls))

    # For learnings (which may be dictionaries and unhashable), we need a different approach
    # If learnings are strings, we can use a set
    if all_learnings and isinstance(all_learnings[0], str):
        final_learnings = list(set(all_learnings))
    else:
        # If learnings are dictionaries, we need to keep them all for now
        # A more sophisticated deduplication could be implemented if needed
        final_learnings = all_learnings
    return {"learnings": final_learnings, "visitedUrls": final_urls}

if __name__ == "__main__":
    # For debugging purposes
    asyncio.run(deep_research("test", 2, 1))
