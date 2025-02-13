# Deep Research (Python)

This repository is a Python translation of the [deep-research](https://github.com/dzhng/deep-research) repository.

## Overview

Deep Research is a tool that recursively generates research queries, processes search results, and produces a comprehensive final report on a given topic. This Python version implements similar functionality using OpenAI API for query generation and content extraction, and integrates with Firecrawl for performing search operations. When Firecrawl is not available, dummy responses are used for testing.

## Requirements

- Python 3.12+
- Required packages can be installed via `pip install -r requirements.txt`
- Environment Variables:
  - `OPENAI_API_KEY` (or `OPENAI_KEY`): A valid API key for accessing the OpenAI API.
  - `FIRECRAWL_KEY`: API key for Firecrawl (if available).
  - `FIRECRAWL_BASE_URL` (optional): The base URL for the Firecrawl API. If not provided, dummy responses are used.

## Usage

To run the deep research application, execute:

```
python run.py
```

You will be prompted to enter a research query along with parameters for breadth and depth. The tool will generate follow-up questions, process SERP results, and ultimately produce a final report stored in `output.md`.



