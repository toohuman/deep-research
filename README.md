# Deep Research (Python)

A powerful AI-driven research tool that recursively generates queries, processes search results, and produces comprehensive reports on any topic.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/API-OpenAI-green.svg)](https://openai.com/)
[![Firecrawl](https://img.shields.io/badge/Search-Firecrawl-orange.svg)](https://firecrawl.dev/)

## Overview

Deep Research is an advanced research assistant that automates the process of exploring topics in depth. This Python implementation is based on the [original deep-research repository](https://github.com/dzhng/deep-research), with enhancements for Python developers.

The tool works by:
1. Taking an initial research query from the user
2. Generating follow-up questions to clarify research goals
3. Creating multiple search queries based on the research topic
4. Recursively exploring the topic with increasing depth and breadth
5. Processing search results to extract key learnings
6. Compiling a comprehensive, well-structured final report with proper citations

## Features

- **Interactive Research Planning**: Asks clarifying questions to better understand your research needs
- **Recursive Query Generation**: Creates multiple search queries to explore different aspects of your topic
- **Depth and Breadth Control**: Customize how wide and deep your research goes
- **Intelligent Content Processing**: Extracts key learnings from search results
- **Automatic Report Generation**: Creates a well-structured Markdown report with proper citations
- **Progress Tracking**: Shows real-time progress during the research process
- **Flexible Search Integration**: Works with Firecrawl API or can be extended to other search providers

## Architecture

The system consists of several key components:

- **Research Planner**: Generates follow-up questions to clarify research goals
- **Query Generator**: Creates search queries based on the research topic
- **Search Engine Integration**: Connects to Firecrawl for web search capabilities
- **Content Processor**: Extracts key learnings from search results
- **Report Generator**: Compiles findings into a comprehensive final report

## Requirements

- Python 3.12+
- Required packages:
  - `openai`: For AI-powered text generation
  - `httpx`: For asynchronous HTTP requests
  - `python-dotenv`: For environment variable management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Py-deep-research.git
   cd Py-deep-research
   ```

2. Install dependencies:
   ```bash
   pip install openai httpx python-dotenv
   ```

3. Set up environment variables:
   Create a `.env.local` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v1
   ```

## Usage

### Basic Usage

Run the application with default settings:

```bash
python run.py
```

You'll be prompted to:
1. Enter your research topic
2. Specify research breadth (recommended 2-10, default 4)
3. Specify research depth (recommended 1-5, default 2)
4. Answer follow-up questions to clarify your research needs

### Example Session

```
What would you like to research? The impact of quantum computing on cryptography
Enter research breadth (recommended 2-10, default 4): 5
Enter research depth (recommended 1-5, default 2): 3

Creating research plan...

To better understand your research needs, please answer these follow-up questions:

What specific aspects of cryptography are you most interested in (e.g., public key, symmetric, post-quantum)?
Your answer: Public key cryptography and post-quantum cryptography

Are you interested in near-term impacts or long-term theoretical implications?
Your answer: Both, with emphasis on practical implications in the next decade

Do you need technical details or a high-level overview suitable for non-specialists?
Your answer: Technical details are fine, I have a background in computer science

Researching your topic...

Starting research with progress tracking...

Progress: 20%
Progress: 40%
Progress: 60%
Progress: 80%
Progress: 100%

Research completed successfully.

Learnings:
- Shor's algorithm can efficiently factor large numbers, breaking RSA encryption...
- Post-quantum cryptographic algorithms like lattice-based cryptography offer...
- NIST has selected several candidate algorithms for standardization...

Visited URLs (15):
https://en.wikipedia.org/wiki/Post-quantum_cryptography
https://www.nist.gov/news-events/news/2022/07/nist-announces-first-four-quantum-resistant-cryptographic-algorithms
...

Writing final report...

Final Report:

# The Impact of Quantum Computing on Cryptography

## Introduction
Quantum computing represents a paradigm shift in computational capabilities...

...

Report has been saved to output.md
```

### Advanced Configuration

You can modify the following parameters in the code:

- `CONCURRENCY_LIMIT` in `deep_research.py`: Controls the number of concurrent search operations
- Text processing parameters in `ai/text_splitter.py`: Adjust chunk sizes for content processing

## How It Works

### Research Process

1. **Initial Query Processing**:
   - The system takes your initial research query
   - Generates follow-up questions to clarify your needs
   - Combines your answers with the original query

2. **Recursive Research**:
   - Generates multiple search queries based on your topic
   - Performs web searches using Firecrawl API
   - Extracts key learnings from search results
   - Generates follow-up questions for deeper exploration
   - Repeats the process based on the specified depth

3. **Report Generation**:
   - Compiles all learnings into a structured report
   - Organizes information into logical sections
   - Adds proper citations linking to source URLs
   - Formats the report in Markdown for easy reading

### Technical Implementation

- **Asynchronous Processing**: Uses Python's `asyncio` for concurrent operations
- **AI-Powered Text Generation**: Leverages OpenAI's models for query generation and content extraction
- **Recursive Exploration**: Implements a depth-first search approach to topic exploration
- **Text Processing**: Uses recursive character splitting for handling large text chunks
- **Progress Tracking**: Provides real-time feedback during the research process

## Customization

### Using Different AI Models

You can modify the `o3_mini_model` variable in `ai/providers.py` to use different OpenAI models.

### Implementing Alternative Search Providers

The system is designed to work with Firecrawl, but you can implement alternative search providers by:

1. Creating a new class similar to `FirecrawlApp` in `ai/firecrawl.py`
2. Implementing the required methods (`search`, etc.)
3. Updating the `deep_research` function to use your new provider

## Troubleshooting

### Common Issues

- **API Key Errors**: Ensure your OpenAI and Firecrawl API keys are correctly set in `.env.local`
- **Rate Limiting**: Adjust the `CONCURRENCY_LIMIT` if you encounter rate limiting issues
- **Memory Issues**: For very large research projects, you may need to adjust chunk sizes in the text splitter

### Debugging

Enable more detailed logging by modifying the print statements in the code or implementing a proper logging system.

