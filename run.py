#!/usr/bin/env python3
import asyncio

from deep_research import deep_research, write_final_report
from feedback import generate_feedback

async def ask_question(prompt: str) -> str:
    """
    Asynchronously ask the user for input.
    This runs the built-in input() in a thread to avoid blocking the event loop.
    """
    return await asyncio.get_event_loop().run_in_executor(None, lambda: input(prompt))

async def main():
    # Get initial query
    initial_query = await ask_question("What would you like to research? ")

    # Get research breadth parameter (default 4)
    breadth_input = await ask_question("Enter research breadth (recommended 2-10, default 4): ")
    try:
        breadth = int(breadth_input)
    except ValueError:
        breadth = 4

    # Get research depth parameter (default 2)
    depth_input = await ask_question("Enter research depth (recommended 1-5, default 2): ")
    try:
        depth = int(depth_input)
    except ValueError:
        depth = 2

    print("Creating research plan...")

    # Generate follow-up questions
    follow_up_questions = await generate_feedback(query=initial_query)

    print("\nTo better understand your research needs, please answer these follow-up questions:")

    # Collect answers to follow-up questions
    answers = []
    for question in follow_up_questions:
        answer = await ask_question(f"\n{question}\nYour answer: ")
        answers.append(answer)

    # Combine all information for deep research
    combined_query = f"Initial Query: {initial_query}\nFollow-up Questions and Answers:\n"
    for q, a in zip(follow_up_questions, answers):
        combined_query += f"Q: {q}\nA: {a}\n"

    print("\nResearching your topic...")
    print("\nStarting research with progress tracking...\n")

    # Define a simple progress callback
    def on_progress(progress):
        print(f"Progress: {progress}%")

    # Perform deep research (assumes deep_research supports an on_progress callback)
    result = await deep_research(query=combined_query, breadth=breadth, depth=depth)
    learnings = result.get("learnings", [])
    visited_urls = result.get("visitedUrls", [])

    print("\n\nLearnings:\n")
    print("\n".join(learnings))
    print(f"\n\nVisited URLs ({len(visited_urls)}):\n")
    print("\n".join(visited_urls))
    print("Writing final report...")

    # Write the final report
    report = await write_final_report(prompt=combined_query, learnings=learnings, visited_urls=visited_urls)

    # Save report to file
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n\nFinal Report:\n\n{report}")
    print("\nReport has been saved to output.md")

if __name__ == '__main__':
    asyncio.run(main())
