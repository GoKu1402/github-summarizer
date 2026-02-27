"""
Repository Analyzer
Handles fetching, filtering, and processing GitHub repository contents
"""

import os
import requests
import base64
from typing import Dict, List, Optional, Set
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Analyzes GitHub repositories and extracts relevant information"""
    
    # File extensions to skip (binary files, media, compiled files)
    SKIP_EXTENSIONS = {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp',
        # Videos
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        # Audio
        '.mp3', '.wav', '.ogg', '.flac',
        # Archives
        '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
        # Binaries
        '.exe', '.dll', '.so', '.dylib', '.bin',
        # Fonts
        '.ttf', '.woff', '.woff2', '.eot', '.otf',
        # Database
        '.db', '.sqlite', '.sqlite3',
        # Others
        '.pdf', '.pyc', '.pyo', '.class', '.o', '.a'
    }
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '__pycache__', '.git', '.svn', '.hg',
        'venv', 'env', '.venv', 'virtualenv',
        'dist', 'build', 'target', 'bin', 'obj',
        '.pytest_cache', '.mypy_cache', '.tox',
        'coverage', '.coverage', 'htmlcov',
        '.idea', '.vscode', '.vs',
        'vendor', 'packages', 'bower_components'
    }
    
    # Files to skip
    SKIP_FILES = {
        'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock',
        'Gemfile.lock', 'composer.lock', 'cargo.lock',
        '.DS_Store', 'thumbs.db', 'desktop.ini',
        '.gitignore', '.dockerignore', '.npmignore',
        'LICENSE', 'LICENSE.txt', 'LICENSE.md',
    }
    
    # High priority files (always include if they exist)
    PRIORITY_FILES = {
        'README.md', 'README.rst', 'README.txt', 'README',
        'CONTRIBUTING.md', 'ARCHITECTURE.md', 'DESIGN.md',
        'package.json', 'setup.py', 'pyproject.toml', 'requirements.txt',
        'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
        'Dockerfile', 'docker-compose.yml', '.dockerignore',
        'Makefile', 'CMakeLists.txt',
        'tsconfig.json', '.eslintrc', 'jest.config.js'
    }
    
    def __init__(self, github_url: str):
        self.github_url = github_url
        self.owner, self.repo = self._parse_github_url(github_url)
        self.base_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        
    def _parse_github_url(self, url: str) -> tuple:
        """Extract owner and repo name from GitHub URL"""
        parsed = urlparse(url)
        if parsed.netloc not in ['github.com', 'www.github.com']:
            raise ValueError("Invalid GitHub URL. Must be a github.com URL")
        
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")
        
        return path_parts[0], path_parts[1]
    
    def _should_skip_file(self, path: str, name: str) -> bool:
        """Determine if a file should be skipped"""
        path_parts = path.split('/')
        if any(part in self.SKIP_DIRS for part in path_parts):
            return True

        if name in self.SKIP_FILES:
            return True

        ext = '.' + name.split('.')[-1] if '.' in name else ''
        if ext.lower() in self.SKIP_EXTENSIONS:
            return True
        
        return False
    
    def _is_priority_file(self, name: str) -> bool:
        """Check if file is high priority"""
        return name in self.PRIORITY_FILES or name.lower() in {f.lower() for f in self.PRIORITY_FILES}
    
    def _get_file_content(self, file_info: Dict) -> Optional[str]:
        """Fetch file content from GitHub API"""
        try:
            # GitHub API returns base64 encoded content
            if 'content' in file_info:
                content = base64.b64decode(file_info['content']).decode('utf-8', errors='ignore')
                return content
            
            # If content not in response, fetch it
            response = requests.get(file_info['url'], headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            return content
            
        except Exception as e:
            logger.warning(f"Failed to fetch content for {file_info.get('path', 'unknown')}: {e}")
            return None
    
    def _fetch_tree(self) -> List[Dict]:
        """Fetch repository tree structure"""
        try:
            repo_info = requests.get(self.base_api_url, headers=self.headers, timeout=10)
            repo_info.raise_for_status()
            default_branch = repo_info.json().get('default_branch', 'main')

            tree_url = f"{self.base_api_url}/git/trees/{default_branch}?recursive=1"
            response = requests.get(tree_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            tree = response.json().get('tree', [])
            return tree
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError("Repository not found or is private")
            raise ConnectionError(f"Failed to fetch repository: {e}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Network error while fetching repository: {e}")
    
    def _build_tree_structure(self, tree: List[Dict]) -> str:
        """Build a visual tree structure of the repository"""
        relevant_items = []
        for item in tree:
            if item['type'] == 'tree':
                continue
            path = item['path']
            name = path.split('/')[-1]
            if not self._should_skip_file(path, name):
                relevant_items.append(path)
        
        # Limit to reasonable number
        if len(relevant_items) > 100:
            relevant_items = relevant_items[:100]
        
        return '\n'.join(relevant_items)
    
    def _select_files_to_analyze(self, tree: List[Dict]) -> List[Dict]:
        """Select most relevant files for analysis"""
        priority_files = []
        source_files = []
        config_files = []
        
        for item in tree:
            if item['type'] != 'blob':  # Only files
                continue
            
            path = item['path']
            name = path.split('/')[-1]
            
            if self._should_skip_file(path, name):
                continue

            if self._is_priority_file(name):
                priority_files.append(item)
            elif any(path.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h']):
                source_files.append(item)
            elif any(name.endswith(ext) for ext in ['.json', '.yml', '.yaml', '.toml', '.xml', '.ini', '.cfg']):
                config_files.append(item)
        
        selected = priority_files.copy()

        root_source = [f for f in source_files if '/' not in f['path'] or f['path'].count('/') <= 1]
        selected.extend(root_source[:10])

        selected.extend(config_files[:5])

        remaining_source = [f for f in source_files if f not in root_source]
        selected.extend(remaining_source[:15])
        
        return selected
    
    def analyze(self) -> Dict:
        """
        Analyze repository and return structured context for LLM
        
        Returns:
            Dictionary with repository information
        """
        logger.info(f"Analyzing repository: {self.owner}/{self.repo}")
        
        tree = self._fetch_tree()
        logger.info(f"Repository has {len(tree)} items")

        tree_structure = self._build_tree_structure(tree)

        selected_files = self._select_files_to_analyze(tree)
        logger.info(f"Selected {len(selected_files)} files for analysis")

        file_contents = []
        total_chars = 0
        max_chars = 100000  # Limit total characters
        
        for file_info in selected_files:
            if total_chars >= max_chars:
                break
            
            content = self._get_file_content(file_info)
            if content:
                # Limit individual file size
                if len(content) > 5000:
                    content = content[:5000] + "\n... (truncated)"
                
                file_contents.append({
                    'path': file_info['path'],
                    'content': content
                })
                total_chars += len(content)
        
        return {
            'owner': self.owner,
            'repo': self.repo,
            'tree_structure': tree_structure,
            'files': file_contents
        }
