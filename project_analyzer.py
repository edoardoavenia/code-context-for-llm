import os
from pathlib import Path
from typing import List, Set
from datetime import datetime

class ProjectStructureGenerator:
   """
   Generates XML representation of a project's structure and content.
   Used to provide context to Large Language Models (LLMs).
   """
   
   # File extensions to include in XML content
   SHOW_CONTENT_EXTENSIONS = {
       '.py',    # Python files
       '.txt',   # Text files
       '.md',    # Markdown
       '.json',  # JSON configs
       '.yml',   # YAML configs
       '.yaml',  # YAML configs
       '.js',    # JavaScript
       '.ts',    # TypeScript 
       '.html',  # HTML
       '.css'    # CSS
   }
   
   # Patterns for files/directories to ignore
   IGNORE_PATTERNS = {
       '__pycache__',
       '.git',
       '.env',
       '*.pyc',
       '.vscode',
       '.idea',
       'venv',
       'node_modules',
       '*.log',
       '*.cache',
       'build',
       'dist'
   }

   def __init__(self, root_path: str):
       """
       Initialize generator with root project path.
       
       Args:
           root_path (str): Path to the root of the project to analyze
       """
       self.root_path = Path(root_path)
       self.output = []

   def generate_tree(self, path: Path, prefix: str = "", is_last: bool = True) -> List[str]:
       """
       Generate a tree representation of the directory structure.
       
       Args:
           path (Path): Current path being processed
           prefix (str): Prefix for current line
           is_last (bool): If current item is last in its list
           
       Returns:
           List[str]: Lines of the tree structure
       """
       if self._should_ignore(path):
           return []

       tree_lines = []
       if path != self.root_path:
           connector = "└── " if is_last else "├── "
           tree_lines.append(f"{prefix}{connector}{path.name}")
           prefix += "    " if is_last else "│   "

       # Sort directories first, then files
       items = sorted(list(path.iterdir()), key=lambda x: (x.is_file(), x.name))
       items = [item for item in items if not self._should_ignore(item)]

       for index, item in enumerate(items):
           is_last_item = index == len(items) - 1
           if item.is_dir():
               tree_lines.extend(self.generate_tree(item, prefix, is_last_item))
           else:
               connector = "└── " if is_last_item else "├── "
               tree_lines.append(f"{prefix}{connector}{item.name}")

       return tree_lines

   def _should_ignore(self, path: Path) -> bool:
       """
       Check if a path should be ignored based on patterns.
       
       Args:
           path (Path): Path to check
           
       Returns:
           bool: True if path should be ignored
       """
       name = path.name
       
       # Ignore hidden files and directories
       if name.startswith('.'):
           return True
           
       # Ignore exact pattern matches    
       if name in self.IGNORE_PATTERNS:
           return True
           
       # Ignore wildcard pattern matches
       for pattern in self.IGNORE_PATTERNS:
           if pattern in str(path):
               return True
               
       return False

   def get_file_content(self, file_path: Path) -> str:
       """
       Read content of file if it has a supported extension.
       
       Args:
           file_path (Path): Path to the file
           
       Returns:
           str: File content or error message
       """
       if file_path.suffix in self.SHOW_CONTENT_EXTENSIONS:
           try:
               with open(file_path, 'r', encoding='utf-8') as f:
                   return f.read()
           except Exception as e:
               return f"# Error reading file: {str(e)}"
       return ""

   def generate_xml(self) -> str:
       """
       Generate complete XML representation of project.
       
       Returns:
           str: XML string containing project structure and file contents
       """
       output = ["<code>"]
       
       # Add tree structure
       output.append("<structure>")
       output.extend(self.generate_tree(self.root_path))
       output.append("</structure>\n")

       # Add file contents
       for path in Path(self.root_path).rglob('*'):
           if path.is_file() and not self._should_ignore(path):
               relative_path = path.relative_to(self.root_path)
               content = self.get_file_content(path)
               if content:
                   tag_name = str(relative_path)
                   output.append(f"<{tag_name}>")
                   output.append(content)
                   output.append(f"</{tag_name}>\n")

       output.append("</code>")
       return "\n".join(output)

   def save_to_file(self, content: str) -> str:
       """
       Save generated XML content to a timestamped file.
       
       Args:
           content (str): XML content to save
           
       Returns:
           str: Success/error message
       """
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       project_name = self.root_path.name
       filename = f"project_structure_{project_name}_{timestamp}.txt"
       
       try:
           with open(filename, 'w', encoding='utf-8') as f:
               f.write(content)
           return f"File saved successfully: {filename}"
       except Exception as e:
           return f"Error saving file: {str(e)}"

def main():
   """Entry point for the command line interface."""
   import argparse
   parser = argparse.ArgumentParser(
       description="Generate XML representation of a project for LLM context"
   )
   parser.add_argument(
       "path", 
       nargs="?", 
       default=".", 
       help="Path to the project root directory"
   )
   args = parser.parse_args()

   # Generate and save content
   generator = ProjectStructureGenerator(args.path)
   content = generator.generate_xml()
   print(content)
   result = generator.save_to_file(content)
   print("\n" + result)

if __name__ == "__main__":
   main()