import os
import json
import pandas as pd
from typing import Dict, Any, List
import streamlit as st
from config.settings import settings
from utils.models import model_manager
from utils.vector_store import vector_store

class FileReaderAgent:
    """Agent for reading and processing various file formats"""
    
    def __init__(self):
        self.name = "File Reader Agent"
        self.description = "Processes and reads various file formats"
        self.supported_extensions = settings.SUPPORTED_FILE_TYPES
    
    def read_text_file(self, file_content: bytes, filename: str) -> str:
        """Read plain text file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except Exception as e:
                return f"Error reading text file: {e}"
    
    def read_csv_file(self, file_content: bytes, filename: str) -> str:
        """Read CSV file and return summary"""
        try:
            import io
            df = pd.read_csv(io.BytesIO(file_content))
            
            summary = f"""CSV File Analysis for {filename}:
            
**Basic Information:**
- Rows: {len(df)}
- Columns: {len(df.columns)}
- Column Names: {', '.join(df.columns.tolist())}

**Data Types:**
{df.dtypes.to_string()}

**Sample Data (first 5 rows):**
{df.head().to_string()}

**Statistical Summary:**
{df.describe().to_string()}
"""
            return summary
            
        except Exception as e:
            return f"Error reading CSV file: {e}"
    
    def read_json_file(self, file_content: bytes, filename: str) -> str:
        """Read JSON file"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            # Format JSON data nicely
            formatted_json = json.dumps(data, indent=2)
            
            summary = f"""JSON File Analysis for {filename}:

**Structure:**
- Type: {type(data).__name__}
- Size: {len(str(data))} characters

**Content:**
```json
{formatted_json[:2000]}{"..." if len(formatted_json) > 2000 else ""}
```
"""
            return summary
            
        except Exception as e:
            return f"Error reading JSON file: {e}"
    
    def process_uploaded_file(self, uploaded_file) -> str:
        """Process an uploaded file"""
        try:
            filename = uploaded_file.name
            file_extension = os.path.splitext(filename)[1].lower()
            
            if file_extension not in self.supported_extensions:
                return f"Unsupported file type: {file_extension}"
            
            # Read file content
            file_content = uploaded_file.read()
            
            # Process based on file type
            if file_extension == '.txt':
                content = self.read_text_file(file_content, filename)
            elif file_extension == '.csv':
                content = self.read_csv_file(file_content, filename)
            elif file_extension == '.json':
                content = self.read_json_file(file_content, filename)
            else:
                content = f"File type {file_extension} is supported but not yet implemented."
            
            # Add to vector store for future retrieval
            try:
                vector_store.add_documents(
                    [content],
                    [{"filename": filename, "type": "uploaded_file", "extension": file_extension}]
                )
            except Exception as e:
                st.warning(f"Could not add file to vector store: {e}")
            
            return content
            
        except Exception as e:
            return f"Error processing file: {e}"
    
    def process_query(self, query: str, uploaded_files: List = None) -> str:
        """Process a file reading query"""
        try:
            if not uploaded_files:
                # Try to search in vector store for existing files
                search_results = vector_store.similarity_search(query, k=3)
                
                if search_results:
                    context = "\n\n".join([
                        f"**From {result[2].get('filename', 'Unknown file')}:**\n{result[0]}"
                        for result in search_results
                    ])
                    
                    prompt = f"""Based on the following file content, please answer the query: "{query}"

File Content:
{context}

Please provide a comprehensive response based on the file data."""

                    response = model_manager.azure_llm.invoke(prompt)
                    if hasattr(response, 'content'):
                        response = response.content
                    return response
                else:
                    return "No files found. Please upload files to analyze."
            
            # Process uploaded files
            results = []
            for uploaded_file in uploaded_files:
                file_content = self.process_uploaded_file(uploaded_file)
                results.append(f"**{uploaded_file.name}:**\n{file_content}")
            
            combined_content = "\n\n".join(results)
            
            # Use LLM to analyze the files in context of the query
            prompt = f"""Based on the following file analysis, please answer the query: "{query}"

File Analysis:
{combined_content}

Please provide insights and answer the query based on the file content."""

            response = model_manager.azure_llm.invoke(prompt)
            if hasattr(response, 'content'):
                response = response.content
            return response
            
        except Exception as e:
            st.error(f"Failed to process file reading query: {e}")
            return "Sorry, I couldn't process your file reading request at the moment."

# Global file reader agent instance
file_reader_agent = FileReaderAgent()
