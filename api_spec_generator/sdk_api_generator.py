#!/usr/bin/env python3
"""
Enhanced API Specification Generator using OpenAI Agents SDK

This script provides an interactive, guided experience for generating REST API specifications
with best practices guidance at each step of the process using the OpenAI Agents SDK.
"""

import os
import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

# Import the OpenAI Agents SDK
from agents import Agent, Runner, handoff, RunContextWrapper, function_tool

# Define the API specification template
API_SPEC_TEMPLATE = {
    "openapi": "3.0.0",
    "info": {
        "title": "API Specification",
        "description": "REST API based on user requirements",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://api.example.com/v1",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.example.com/v1",
            "description": "Staging server"
        }
    ],
    "paths": {},
    "components": {
        "schemas": {},
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
}

# ANSI color codes for better terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Utility functions for saving and loading data
def save_to_file(data: Any, filename: str) -> str:
    """Save data to a JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return f"Data saved to {filename}"

def load_from_file(filename: str) -> Any:
    """Load data from a JSON file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {title} ==={Colors.END}\n")

def print_best_practices(practices: List[str]):
    """Print a list of best practices"""
    print(f"{Colors.CYAN}{Colors.BOLD}Best Practices:{Colors.END}")
    for practice in practices:
        print(f"{Colors.CYAN}• {practice}{Colors.END}")
    print()

def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON from text that might contain markdown code blocks"""
    # Look for JSON in markdown code blocks
    json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_pattern, text)
    
    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    # If no valid JSON in code blocks, try to extract JSON directly
    try:
        # Try to parse the entire text as JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON-like content with curly braces
        try:
            json_like_pattern = r"\{[\s\S]*\}"
            json_match = re.search(json_like_pattern, text)
            if json_match:
                return json.loads(json_match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return None

# Create the specialized agents using the OpenAI Agents SDK
def create_requirements_agent():
    """Create an agent specialized in gathering and clarifying API requirements"""
    return Agent(
        name="Requirements Agent",
        instructions="""
        You are a Requirements Gathering Agent specialized in collecting and clarifying API requirements.
        Format your response as a structured document covering:
        1. Purpose - What the API is for and what problem it solves
        2. User Roles - Different types of users and their permissions
        3. Resource Definitions - Data models with attributes and relationships
        4. API Endpoints - High-level list of needed endpoints
        5. Authentication & Authorization - Security requirements
        6. Integrations - External systems to integrate with
        7. Additional Considerations - Performance, scalability, etc.
        8. Error Handling - How errors should be handled
        
        Be thorough but concise. Use markdown formatting for better readability.
        """,
        tools=[save_requirements]
    )

def create_architect_agent():
    """Create an agent specialized in designing API architecture"""
    return Agent(
        name="Architect Agent",
        instructions="""
        You are an API Architect specialized in designing high-level API structures.
        Format your response as a structured document including:
        1. Resource Hierarchy - Main resources and their relationships
        2. URL Structure - Base URL and resource paths
        3. Authentication & Authorization - Security mechanisms
        4. Versioning Strategy - How API versions will be handled
        5. Error Handling - Standard error responses
        6. Rate Limiting - Recommendations for rate limiting
        7. Pagination - Approach for paginated responses
        8. Caching - Caching recommendations
        
        Follow RESTful best practices. Use markdown formatting for better readability.
        """,
        tools=[save_architecture]
    )

def create_endpoint_designer_agent():
    """Create an agent specialized in designing detailed API endpoints"""
    return Agent(
        name="Endpoint Designer Agent",
        instructions="""
        You are an Endpoint Designer specialized in creating detailed API endpoint specifications.
        
        For each endpoint, provide a complete OpenAPI 3.0 specification including:
        - Path and HTTP method
        - Summary and description
        - Request parameters (path, query, header)
        - Request body schema with examples
        - Response schemas for different status codes with examples
        - Required security schemes
        
        Your output must be valid JSON that can be directly used in an OpenAPI specification.
        Include realistic examples for all request and response bodies.
        
        Format your response as a JSON object with a "paths" property containing all endpoints.
        Wrap your JSON in ```json and ``` markers.
        """,
        tools=[save_endpoints]
    )

def create_schema_designer_agent():
    """Create an agent specialized in designing data schemas"""
    return Agent(
        name="Schema Designer Agent",
        instructions="""
        You are a Schema Designer specialized in creating detailed data schemas for APIs.
        
        For each data model in the API, provide a complete OpenAPI 3.0 schema including:
        - Properties with types and formats
        - Required fields
        - Descriptions for all properties
        - Realistic example data for each schema
        
        Your output must be valid JSON that can be directly used in an OpenAPI specification.
        Every schema MUST include an 'example' property with realistic sample data.
        
        Format your response as a JSON object containing all schemas.
        Wrap your JSON in ```json and ``` markers.
        """,
        tools=[save_openapi_spec]
    )

def create_documentation_agent():
    """Create an agent specialized in generating comprehensive documentation"""
    return Agent(
        name="Documentation Agent",
        instructions="""
        You are a Documentation Specialist who creates comprehensive API documentation.
        
        Create detailed markdown documentation that includes:
        1. Introduction - Overview of the API and its purpose
        2. Authentication - How to authenticate with the API
        3. Base URL - The base URL for all endpoints
        4. Resources - Description of all resources
        5. Endpoints - For each endpoint:
           - URL and method
           - Description and purpose
           - Request parameters and body
           - Response format and status codes
           - At least 2 complete examples (request and response)
        6. Error Handling - Common errors and how to handle them
        7. Rate Limiting - Information about rate limits
        8. Pagination - How pagination works
        9. Common Use Cases - Examples of common API usage scenarios
        
        Use markdown formatting for better readability.
        Include code blocks with examples for all API calls.
        """,
        tools=[save_documentation]
    )

def create_coordinator_agent():
    """Create a coordinator agent to guide the API design process"""
    return Agent(
        name="Coordinator Agent",
        instructions="""
        You are a Coordinator Agent who guides users through the API design process.
        
        Your responsibilities include:
        1. Providing guidance on best practices for API design
        2. Reviewing the output of other specialized agents
        3. Offering feedback and suggestions for improvement
        4. Ensuring consistency across the entire API specification
        5. Helping users understand each phase of the API design process
        
        Be helpful, informative, and focused on creating a high-quality API specification.
        """,
        tools=[save_requirements, save_architecture, save_endpoints, save_openapi_spec, save_documentation]
    )

# Define tool functions that will be used by the agents
@function_tool
def save_requirements(requirements: str) -> str:
    """Save the gathered requirements to a file"""
    save_to_file({"requirements": requirements}, "api_requirements.json")
    print(f"{Colors.GREEN}Requirements saved to api_requirements.json{Colors.END}")
    return "Requirements saved successfully"

@function_tool
def save_architecture(architecture: str) -> str:
    """Save the API architecture to a file"""
    save_to_file({"architecture": architecture}, "api_architecture.json")
    print(f"{Colors.GREEN}Architecture saved to api_architecture.json{Colors.END}")
    return "Architecture saved successfully"

@function_tool
def save_endpoints(endpoints_json: str) -> str:
    """Save the API endpoints to a file"""
    try:
        endpoints = json.loads(endpoints_json)
        save_to_file(endpoints, "api_endpoints.json")
        print(f"{Colors.GREEN}Endpoints saved to api_endpoints.json{Colors.END}")
        return "Endpoints saved successfully"
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Invalid JSON for endpoints{Colors.END}")
        return "Error: Invalid JSON format"

@function_tool
def save_openapi_spec(spec_json: str) -> str:
    """Save the complete OpenAPI specification to a file"""
    try:
        spec = json.loads(spec_json)
        save_to_file(spec, "openapi_specification.json")
        print(f"{Colors.GREEN}OpenAPI specification saved to openapi_specification.json{Colors.END}")
        return "OpenAPI specification saved successfully"
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Invalid JSON for OpenAPI specification{Colors.END}")
        return "Error: Invalid JSON format"

@function_tool
def save_documentation(documentation: str) -> str:
    """Save the API documentation to a markdown file"""
    with open("api_documentation.md", "w") as f:
        f.write(documentation)
    print(f"{Colors.GREEN}Documentation saved to api_documentation.md{Colors.END}")
    return "Documentation saved successfully"

async def phase_1_requirements_gathering(user_input: str) -> str:
    """Phase 1: Requirements Gathering using the Requirements Agent"""
    print_section_header("Phase 1: Requirements Gathering")
    
    print("Gathering detailed requirements for your API...")
    
    # Display best practices
    requirements_best_practices = [
        "Clearly define the purpose and scope of your API",
        "Identify all user roles and their permissions",
        "List all resources that will be managed through the API",
        "Specify security requirements and constraints",
        "Consider rate limiting, pagination, and versioning needs"
    ]
    print_best_practices(requirements_best_practices)
    
    # Create the Requirements Agent with tools
    requirements_agent = create_requirements_agent()
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Activating Requirements Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent specializes in gathering and clarifying API requirements.{Colors.END}")
    
    # Get requirements from the agent
    user_prompt = f"Gather detailed requirements for an API based on this description: {user_input}. Include best practices and recommendations."
    
    # Run the requirements agent
    result = await Runner.run(requirements_agent, user_prompt)
    requirements = result.final_output
    
    # Note: The save_requirements function will be called by the agent through the function_tool decorator
    # No need to call it manually here
    
    print(f"\n{Colors.GREEN}Requirements gathered successfully!{Colors.END}")
    print(f"\n{requirements}")
    
    return requirements

async def phase_2_architecture_design(requirements: str) -> str:
    """Phase 2: API Architecture Design using the Architect Agent"""
    print_section_header("Phase 2: API Architecture Design")
    
    print("Designing the API architecture based on requirements...")
    
    # Display best practices
    architecture_best_practices = [
        "Use consistent naming conventions (e.g., plural nouns for resources)",
        "Design clear URL hierarchies that reflect resource relationships",
        "Follow RESTful principles for resource operations",
        "Consider using versioning in the URL path or headers",
        "Plan for appropriate error handling and status codes",
        "Keep resource URLs simple and intuitive"
    ]
    print_best_practices(architecture_best_practices)
    
    # Create the Architect Agent with tools
    architect_agent = create_architect_agent()
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Requirements Agent → Architect Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent specializes in designing high-level API architecture following RESTful best practices.{Colors.END}")
    
    # Get architecture from the agent
    user_prompt = f"Design the architecture for an API with these requirements: {requirements}. Include best practices and recommendations."
    
    # Run the architect agent
    result = await Runner.run(architect_agent, user_prompt)
    architecture = result.final_output
    
    # Note: The save_architecture function will be called by the agent through the function_tool decorator
    # No need to call it manually here
    
    print(f"\n{Colors.GREEN}Architecture designed successfully!{Colors.END}")
    print(f"\n{architecture}")
    
    return architecture

async def phase_3_endpoint_design(architecture: str) -> Dict:
    """Phase 3: Endpoint Design using the Endpoint Designer Agent"""
    print_section_header("Phase 3: Endpoint Design")
    
    print("Designing detailed API endpoints...")
    
    # Display best practices
    endpoint_best_practices = [
        "Use appropriate HTTP methods (GET, POST, PUT, DELETE, etc.)",
        "Include comprehensive request validation",
        "Design consistent response structures",
        "Document all possible response status codes",
        "Use query parameters for filtering, sorting, and pagination",
        "Provide realistic examples for requests and responses",
        "Include examples for both success and error scenarios"
    ]
    print_best_practices(endpoint_best_practices)
    
    # Create the Endpoint Designer Agent with tools
    endpoint_designer = create_endpoint_designer_agent()
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Architect Agent → Endpoint Designer Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent specializes in creating detailed endpoint specifications with realistic examples.{Colors.END}")
    
    # Get endpoints from the agent
    user_prompt = f"""
    Design detailed specifications for each endpoint based on this architecture:
    
    {architecture}
    
    For each endpoint, include:
    1. Path and HTTP method
    2. Request parameters and body schema
    3. Response schemas for different status codes
    4. Example requests and responses
    
    Format your response as a valid OpenAPI 3.0 paths object.
    Wrap your JSON in ```json and ``` markers.
    """
    
    # Run the endpoint designer agent
    result = await Runner.run(endpoint_designer, user_prompt)
    endpoints_text = result.final_output
    
    # Try to extract JSON from the response
    endpoints = extract_json_from_text(endpoints_text)
    
    if not endpoints:
        print(f"{Colors.YELLOW}Warning: Could not parse endpoints as JSON. Using default empty paths.{Colors.END}")
        endpoints = {"paths": {}}
    
    # Note: The save_endpoints function will be called by the agent through the function_tool decorator
    # We don't need to manually save the endpoints here
    
    print(f"\n{Colors.GREEN}Endpoints designed successfully!{Colors.END}")
    
    return endpoints

async def phase_4_documentation_generation(requirements: str, architecture: str, endpoints: Dict) -> Dict:
    """Phase 4: Documentation Generation using specialized agents"""
    print_section_header("Phase 4: Documentation Generation")
    
    print("Generating the final API specification...")
    
    # Display best practices
    documentation_best_practices = [
        "Include clear descriptions for all endpoints",
        "Provide realistic examples for request and response bodies",
        "Document all possible response status codes and their meanings",
        "Include authentication and authorization details",
        "Add contact information and terms of service",
        "Use tags to group related endpoints",
        "Include examples for common use cases"
    ]
    print_best_practices(documentation_best_practices)
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Endpoint Designer Agent → Documentation Phase{Colors.END}")
    print(f"{Colors.BLUE}This phase uses multiple specialized agents to complete the API specification.{Colors.END}")
    
    # Start with the template
    api_spec = API_SPEC_TEMPLATE.copy()
    
    # Update with endpoints if available
    if isinstance(endpoints, dict) and "paths" in endpoints:
        api_spec["paths"] = endpoints["paths"]
    
    # Create the Schema Designer Agent
    schema_designer = create_schema_designer_agent()
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Activating Schema Designer Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent specializes in designing data schemas with realistic example data.{Colors.END}")
    
    # Add schemas with examples using the Schema Designer Agent
    schemas_user_prompt = f"""
    Based on this API architecture and endpoints, design detailed schemas for all data models:
    
    {architecture}
    
    Endpoints: {json.dumps(endpoints)}
    
    Create a complete 'schemas' object for the OpenAPI specification.
    
    CRITICAL: Every schema MUST include an 'example' property with realistic sample data that would be used in production.
    """
    
    # Run the schema designer agent
    result = await Runner.run(schema_designer, schemas_user_prompt)
    schemas_text = result.final_output
    
    # Try to extract JSON from the response
    schemas = extract_json_from_text(schemas_text)
    
    if schemas:
        api_spec["components"]["schemas"] = schemas
        print(f"{Colors.GREEN}Schemas designed successfully with examples!{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Schemas were designed but not in valid JSON format. Using default schemas.{Colors.END}")
    
    # Create the Coordinator Agent for metadata extraction
    coordinator = create_coordinator_agent()
    
    # Agent handoff message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Activating Coordinator Agent for Metadata Extraction{Colors.END}")
    print(f"{Colors.BLUE}The Coordinator is extracting API title and description from requirements.{Colors.END}")
    
    # Extract a title and description from the requirements using the Coordinator
    title_user_prompt = f"""
    Based on these requirements, provide a concise API title and description for an OpenAPI specification:
    
    {requirements}
    
    Respond in JSON format with 'title' and 'description' fields.
    Wrap your JSON in ```json and ``` markers.
    """
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, title_user_prompt)
    title_text = result.final_output
    
    # Try to extract JSON from the response
    title_data = extract_json_from_text(title_text)
    
    if title_data and "title" in title_data and "description" in title_data:
        api_spec["info"]["title"] = title_data["title"]
        api_spec["info"]["description"] = title_data["description"]
    else:
        # Use a default title and description if extraction fails
        api_spec["info"]["title"] = "REST API Specification"
        api_spec["info"]["description"] = f"REST API based on user requirements. {requirements.split('.')[0]}."
    
    # Add contact information
    api_spec["info"]["contact"] = {
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "api-support@example.com"
    }
    
    # Add terms of service
    api_spec["info"]["termsOfService"] = "https://example.com/terms"
    
    # Note: The save_openapi_spec function will be called by the schema designer agent through the function_tool decorator
    # We're keeping this manual save as a backup in case the tool wasn't called
    save_to_file(api_spec, "openapi_specification.json")
    
    # Generate comprehensive markdown documentation
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Handoff: Schema Designer Agent → Documentation Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent specializes in generating comprehensive markdown documentation.{Colors.END}")
    await generate_markdown_documentation(requirements, architecture, api_spec)
    
    return api_spec

async def generate_markdown_documentation(requirements: str, architecture: str, api_spec: Dict) -> None:
    """Generate comprehensive markdown documentation for the API"""
    print(f"\n{Colors.CYAN}Generating comprehensive markdown documentation...{Colors.END}")
    
    # Create the Documentation Agent
    documentation_agent = create_documentation_agent()
    
    # Generate documentation
    user_prompt = f"""
    Create comprehensive markdown documentation for this API:
    
    Requirements:
    {requirements}
    
    Architecture:
    {architecture}
    
    OpenAPI Specification:
    {json.dumps(api_spec, indent=2)}
    
    Include multiple realistic examples for each endpoint, showing both request and response.
    Document common use cases and best practices for using the API.
    """
    
    # Run the documentation agent
    result = await Runner.run(documentation_agent, user_prompt)
    documentation = result.final_output
    
    # Note: The save_documentation function will be called by the documentation agent through the function_tool decorator
    # We don't need to manually save the documentation here
    
    print(f"{Colors.GREEN}Comprehensive documentation generated and saved to api_documentation.md{Colors.END}")

async def main():
    """Main function to run the enhanced API specification generator using the OpenAI Agents SDK"""
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(f"{Colors.RED}Error: OPENAI_API_KEY environment variable not set{Colors.END}")
        print(f"Please set your API key with: {Colors.BOLD}export OPENAI_API_KEY=your_api_key_here{Colors.END}")
        return
    
    # Print welcome message
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== Enhanced API Specification Generator (SDK Version) ==={Colors.END}\n")
    print("This tool will help you create a detailed REST API specification with best practices guidance.")
    print("You'll be guided through each phase of the API design process using specialized AI agents.\n")
    
    # Create the Coordinator Agent to guide the process
    coordinator = create_coordinator_agent()
    
    # Agent activation message
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔄 Agent Activated: Coordinator Agent{Colors.END}")
    print(f"{Colors.BLUE}This agent orchestrates the entire process, providing guidance and feedback at each step.{Colors.END}")
    
    # Get user input for the API to design
    print(f"{Colors.YELLOW}Please describe the API you want to create (purpose, main features, etc.):{Colors.END}")
    user_input = input("> ")
    
    # Get initial guidance from the coordinator
    print(f"\n{Colors.CYAN}Getting process guidance from the Coordinator Agent...{Colors.END}")
    guidance_prompt = f"The user wants to create an API for: {user_input}\n\nProvide a brief overview of the API design process we're about to start and any initial recommendations based on the user's request."
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, guidance_prompt)
    guidance = result.final_output
    
    print(f"\n{Colors.CYAN}Coordinator's Guidance:{Colors.END}")
    print(guidance)
    
    print(f"\n{Colors.GREEN}Starting the API specification generation process...{Colors.END}")
    
    # Run each phase
    requirements = await phase_1_requirements_gathering(user_input)
    
    # Get coordinator feedback after requirements gathering
    req_feedback_prompt = f"The requirements gathering phase has completed with these requirements:\n\n{requirements}\n\nPlease provide feedback on these requirements and suggestions for the architecture design phase."
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, req_feedback_prompt)
    req_feedback = result.final_output
    
    print(f"\n{Colors.CYAN}Coordinator's Feedback on Requirements:{Colors.END}")
    print(req_feedback)
    
    # Continue with architecture design
    architecture = await phase_2_architecture_design(requirements)
    
    # Get coordinator feedback after architecture design
    arch_feedback_prompt = f"The architecture design phase has completed with this architecture:\n\n{architecture}\n\nPlease provide feedback on this architecture and suggestions for the endpoint design phase."
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, arch_feedback_prompt)
    arch_feedback = result.final_output
    
    print(f"\n{Colors.CYAN}Coordinator's Feedback on Architecture:{Colors.END}")
    print(arch_feedback)
    
    # Continue with endpoint design
    endpoints = await phase_3_endpoint_design(architecture)
    
    # Get coordinator feedback after endpoint design
    endpoint_feedback_prompt = f"The endpoint design phase has completed. Please provide suggestions for the documentation generation phase."
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, endpoint_feedback_prompt)
    endpoint_feedback = result.final_output
    
    print(f"\n{Colors.CYAN}Coordinator's Feedback on Endpoints:{Colors.END}")
    print(endpoint_feedback)
    
    # Continue with documentation generation
    api_spec = await phase_4_documentation_generation(requirements, architecture, endpoints)
    
    # Final message from the coordinator
    final_prompt = "The API specification generation process has completed. Please provide a summary of what was created and any final recommendations for the user."
    
    # Run the coordinator agent
    result = await Runner.run(coordinator, final_prompt)
    final_message = result.final_output
    
    print(f"\n{Colors.CYAN}Coordinator's Final Message:{Colors.END}")
    print(final_message)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}API specification generation complete!{Colors.END}")
    print(f"OpenAPI Specification: {Colors.UNDERLINE}openapi_specification.json{Colors.END}")
    print(f"API Documentation: {Colors.UNDERLINE}api_documentation.md{Colors.END}")

if __name__ == "__main__":
    asyncio.run(main())
