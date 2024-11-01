# Code Context for LLM

A lightweight tool that converts your project structure into a clear XML format, making it easy to provide comprehensive context to Large Language Models.

## Overview

This tool analyzes your project directory and creates a structured XML representation that includes:
- Complete directory tree structure
- Content of all relevant files
- Organized in an LLM-friendly format

## Example Output

Below is a sample output showing how the tool represents a typical project structure:

```xml
<code>
<structure>
project/
├── main.py
├── configs/
│   ├── settings.yml
│   └── env.json
├── src/
│   ├── models/
│   │   ├── user.py
│   │   └── product.py
│   └── utils/
│       ├── helpers.py
│       └── constants.py
├── tests/
│   ├── test_models.py
│   └── test_utils.py
└── README.md
</structure>

<main.py>
here is the content of main.py
</main.py>

<configs/settings.yml>
here is the content of settings.yml
</configs/settings.yml>

<configs/env.json>
here is the content of env.json
</configs/env.json>

<src/models/user.py>
here is the content of user.py
</src/models/user.py>

<src/models/product.py>
here is the content of product.py
</src/models/product.py>

<src/utils/helpers.py>
here is the content of helpers.py
</src/utils/helpers.py>

<src/utils/constants.py>
here is the content of constants.py
</src/utils/constants.py>

<tests/test_models.py>
here is the content of test_models.py
</tests/test_models.py>

<tests/test_utils.py>
here is the content of test_utils.py
</tests/test_utils.py>

<README.md>
here is the content of README.md
</README.md>
</code>
```



## Usage

Basic usage:
```bash
code-context /path/to/your/project
```

This will:
1. Scan your project directory
2. Generate the XML representation
3. Save it to a timestamped file
4. Display the output in the console

## Why Use This?

When working with LLMs such as Claude or GPT-4, providing complete project context can be difficult or time-consuming. This tool solves this problem by
- By creating a standardized representation of the project
- Including both structure and content in a single view
- Using a format that is easy for both humans and LLMs to understand.

## Configuration

The tool can be configured to include/exclude specific file types and directories based on your needs. Default settings include common development files while excluding typical non-essential directories.