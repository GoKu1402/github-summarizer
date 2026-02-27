"""
LLM Client
Handles communication with LLM APIs (Nebius, Anthropic, OpenAI)
"""

import os
import json
import requests
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with various LLM APIs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider = self._detect_provider()
        
    def _detect_provider(self) -> str:
        """Detect which LLM provider to use based on available API keys"""
        if os.getenv("NEBIUS_API_KEY"):
            return "nebius"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        else:
            # Default to Nebius if key provided but no env var set
            return "nebius"
    
    def _build_prompt(self, repo_context: Dict) -> str:
        """Build a comprehensive prompt for the LLM"""
        owner = repo_context['owner']
        repo = repo_context['repo']
        tree = repo_context['tree_structure']
        files = repo_context['files']
        
        prompt = f"""Analyze this GitHub repository and provide a comprehensive summary.

Repository: {owner}/{repo}

## Directory Structure
{tree}

## File Contents
"""
        
        for file_info in files:
            prompt += f"\n### {file_info['path']}\n```\n{file_info['content']}\n```\n"
        
        prompt += """

Based on the above repository contents, provide a detailed analysis in the following JSON format:

{
  "summary": "A thorough description of what this project does, its purpose, goals, and who it is for (4-6 sentences)",
  "technologies": ["Every technology, language, framework, library, and tool used"],
  "structure": "Detailed explanation of how the project is organized: main directories, key files, and how they relate to each other",
  "key_features": ["Bullet list of the main features and capabilities of the project"],
  "architecture": "Explanation of the architectural patterns, design decisions, and how data flows through the system",
  "getting_started": "How someone would run or use this project: entry points, setup steps, main commands",
  "use_cases": ["Concrete examples of what this project can be used for"]
}

Important:
- Be specific and accurate based on the actual code and files
- For technologies, list concrete items (e.g., "Python", "FastAPI", "PostgreSQL", not vague terms)
- For structure, reference actual file and directory names you see
- Return ONLY valid JSON, no additional text or markdown
"""
        
        return prompt
    
    def _call_nebius(self, prompt: str) -> str:
        """Call Nebius Token Factory API"""
        url = "https://api.studio.nebius.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing software projects. You provide accurate, concise summaries of code repositories based on their structure and contents."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to call Nebius API: {e}")
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to call Anthropic API: {e}")
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4-turbo-preview",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing software projects. You provide accurate, concise summaries of code repositories."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to call OpenAI API: {e}")
    
    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response and extract JSON"""
        try:
            # Try to find JSON in the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```'):
                lines = response.split('\n')
                # Remove first and last lines (```)
                response = '\n'.join(lines[1:-1])
                # Remove language identifier if present
                if response.startswith('json'):
                    response = response[4:].strip()
            
            data = json.loads(response)

            required = {'summary', 'technologies', 'structure', 'key_features', 'architecture', 'getting_started', 'use_cases'}
            if not required.issubset(data.keys()):
                raise ValueError("Response missing required fields")

            # Ensure list fields are actually lists
            for field in ('technologies', 'key_features', 'use_cases'):
                if not isinstance(data[field], list):
                    data[field] = [data[field]]
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            return {
                "summary": "Unable to parse repository summary from LLM response.",
                "technologies": ["Unknown"],
                "structure": "Unable to determine project structure.",
                "key_features": ["Unknown"],
                "architecture": "Unable to determine architecture.",
                "getting_started": "Unable to determine.",
                "use_cases": ["Unknown"]
            }
    
    def generate_summary(self, repo_context: Dict) -> Dict:
        """
        Generate repository summary using LLM
        
        Args:
            repo_context: Repository information from analyzer
            
        Returns:
            Dictionary with summary, technologies, and structure
        """
        logger.info(f"Generating summary using {self.provider}")
        
        prompt = self._build_prompt(repo_context)

        if self.provider == "nebius":
            response = self._call_nebius(prompt)
        elif self.provider == "anthropic":
            response = self._call_anthropic(prompt)
        elif self.provider == "openai":
            response = self._call_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        result = self._parse_response(response)
        
        logger.info("Summary generated successfully")
        return result
