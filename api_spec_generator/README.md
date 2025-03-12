# SDK API Generator

A powerful multi-agent system for generating comprehensive REST API specifications using the OpenAI Agents SDK framework.

## Overview

The SDK API Generator leverages a true multi-agent architecture to create detailed, production-ready API specifications in OpenAPI 3.0 format. Each phase of the API design process is handled by a specialized agent, ensuring high-quality results with proper guidance and best practices.

## Features

- **True Multi-Agent Architecture** - Each agent maintains its own memory and context
- **Specialized Agents** - Purpose-built agents for each phase of API design
- **Clear Agent Handoffs** - Transparent transitions between agents
- **Comprehensive Documentation** - Generates both OpenAPI specification and markdown documentation
- **Best Practices Guidance** - Expert recommendations at each step

## Agent Roles

The system uses six specialized agents, each with a specific role:

1. **RequirementsAgent** - Gathers and clarifies API requirements from user input
2. **ArchitectAgent** - Designs high-level API architecture following RESTful best practices
3. **EndpointDesignerAgent** - Creates detailed endpoint specifications with realistic examples
4. **SchemaDesignerAgent** - Designs data schemas with realistic example data
5. **DocumentationAgent** - Generates comprehensive markdown documentation
6. **CoordinatorAgent** - Orchestrates the entire process, providing guidance and feedback

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rcapers/open-ai-agents.git
   cd open-ai-agents/api_spec_generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

### Running the Generator

Use the convenience script:
```bash
./run_sdk_generator.sh
```

Or run the Python script directly:
```bash
python sdk_api_generator.py
```

## Usage Guide

1. **Start the Generator** - Run the script as shown above
2. **Describe Your API** - Provide a detailed description of the API you want to create
3. **Follow the Prompts** - Each agent will guide you through its specific phase
4. **Review the Output** - Check the generated files for completeness and accuracy

## Output Files

The SDK API Generator produces the following output files:

- `api_requirements.json` - Detailed requirements gathered during phase 1
- `api_architecture.json` - High-level API architecture designed during phase 2
- `api_endpoints.json` - Detailed endpoint specifications created during phase 3
- `openapi_specification.json` - Complete OpenAPI 3.0 specification
- `api_documentation.md` - Comprehensive markdown documentation

## Example

Here's an example interaction with the SDK API Generator:

```
=== Enhanced API Specification Generator (SDK Version) ===

This tool will help you create a detailed REST API specification with best practices guidance.
You'll be guided through each phase of the API design process using specialized AI agents.

🔄 Agent Activated: Coordinator Agent
This agent orchestrates the entire process, providing guidance and feedback at each step.

Please describe the API you want to create (purpose, main features, etc.):
> I need an API for a blog management system that allows users to create, edit, and publish blog posts.

[The system will then guide you through the entire process with specialized agents for each phase]
```

## Customization

You can customize the behavior of each agent by modifying their system prompts in the `sdk_api_generator.py` file. Look for the `create_*_agent()` functions to adjust the instructions for each agent.

## Troubleshooting

- **API Key Issues**: Ensure your OpenAI API key is correctly set as an environment variable
- **Dependency Problems**: Make sure all requirements are installed with `pip install -r requirements.txt`
- **Generation Errors**: If you encounter errors during generation, check the console output for specific error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
