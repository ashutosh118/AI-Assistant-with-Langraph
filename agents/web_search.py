import requests
from typing import List, Dict, Any
import streamlit as st
from config.settings import settings
from utils.models import model_manager

class WebSearchAgent:
    """Agent for web searching capabilities"""
    
    def __init__(self):
        self.name = "Web Search Agent"
        self.description = "Searches the web for relevant information"
    
    def search_duckduckgo_html(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform web search using DuckDuckGo HTML search (more reliable)
        """
        max_results = max_results or settings.MAX_SEARCH_RESULTS
        
        try:
            # Use DuckDuckGo HTML search
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Search URL
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                results = []
                # Find search result links
                result_links = soup.find_all('a', class_='result__a')[:max_results]
                
                for i, link in enumerate(result_links):
                    title = link.get_text().strip()
                    url = link.get('href', '')
                    
                    # Get snippet from the result
                    result_div = link.find_parent('div', class_='result')
                    snippet = ""
                    if result_div:
                        snippet_elem = result_div.find('a', class_='result__snippet')
                        if snippet_elem:
                            snippet = snippet_elem.get_text().strip()
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'content': snippet or f"Search result {i+1} for: {query}",
                            'url': url,
                            'source': 'DuckDuckGo Search'
                        })
                
                return results
            
        except Exception as e:
            st.warning(f"DuckDuckGo HTML search failed: {e}")
        
        return []

    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform web search using multiple methods
        """
        max_results = max_results or settings.MAX_SEARCH_RESULTS
        
        # Try DuckDuckGo instant answer API first
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Get instant answer if available
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('Heading', 'DuckDuckGo Answer'),
                    'content': data.get('AbstractText'),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo Instant Answer'
                })
            
            # Get related topics
            for topic in data.get('RelatedTopics', [])[:max_results-1]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ').title(),
                        'content': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo'
                    })
            
            # If we got good results, return them
            if results and any(len(r['content']) > 50 for r in results):
                return results[:max_results]
            
        except Exception as e:
            st.warning(f"DuckDuckGo API search failed: {e}")
        
        # If instant answer didn't work well, try HTML search
        html_results = self.search_duckduckgo_html(query, max_results)
        if html_results:
            return html_results
        
        # If no search results found, return empty list
        return []
    
    def process_query(self, query: str) -> str:
        """Process a search query and return formatted results"""
        try:
            # Get search results
            results = self.search(query)
            
            if not results:
                # If no search results found, use LLM knowledge instead
                fallback_prompt = f"""I couldn't find specific web search results for the query: "{query}"

Based on your general knowledge, please provide a helpful and informative response to this query. If this is about recent events or current affairs, please mention that you might not have the most up-to-date information and suggest alternative ways to find current information.

Please provide a comprehensive response:"""

                response = model_manager.azure_llm.invoke(fallback_prompt)
                if hasattr(response, 'content'):
                    response = response.content
                response += "\n\n*Note: This response is based on general knowledge as current web search results were not available. For the most current information, please check recent news sources.*"
                return response
            
            # Use LLM to synthesize the search results
            context = "\n\n".join([
                f"**{result['title']}**\n{result['content']}\nSource: {result['url']}"
                for result in results
            ])
            
            prompt = f"""Based on the following search results, provide a comprehensive answer to the query: "{query}"

Search Results:
{context}

Please synthesize this information into a clear, informative response that addresses the user's query. Include relevant sources where appropriate."""

            response = model_manager.azure_llm.invoke(prompt)
            if hasattr(response, 'content'):
                response = response.content
            # Add search results metadata
            sources = [f"- [{result['title']}]({result['url']})" for result in results if result['url']]
            if sources:
                response += "\n\n**Sources:**\n" + "\n".join(sources)
            return response
            
        except Exception as e:
            st.error(f"Failed to process search query: {e}")
            return "Sorry, I couldn't process your search query at the moment."

# Global web search agent instance
web_search_agent = WebSearchAgent()
