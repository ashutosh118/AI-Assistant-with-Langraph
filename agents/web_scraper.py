import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import streamlit as st
from config.settings import settings
from utils.models import model_manager

class WebScrapingAgent:
    """Agent for web scraping capabilities"""
    
    def __init__(self):
        self.name = "Web Scraping Agent"
        self.description = "Extracts content from web pages"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a single URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract main content
            content_selectors = ['main', 'article', '.content', '#content', '.post', '.entry']
            content = None
            
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                content = soup.find('body')
            
            if content:
                # Get text content
                text_content = content.get_text(separator='\n', strip=True)
                
                # Clean up the text
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                cleaned_content = '\n'.join(lines)
                
                return {
                    'url': url,
                    'title': title_text,
                    'content': cleaned_content[:5000],  # Limit content length
                    'status': 'success'
                }
            else:
                return {
                    'url': url,
                    'title': title_text,
                    'content': '',
                    'status': 'no_content'
                }
                
        except Exception as e:
            return {
                'url': url,
                'title': '',
                'content': '',
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape content from multiple URLs"""
        results = []
        max_urls = min(len(urls), settings.MAX_SCRAPING_PAGES)
        
        for i, url in enumerate(urls[:max_urls]):
            with st.spinner(f"Scraping URL {i+1}/{max_urls}: {url}"):
                result = self.scrape_url(url)
                results.append(result)
        
        return results
    
    def process_query(self, query: str, urls: List[str] = None) -> str:
        """Process a scraping query"""
        try:
            if not urls:
                return "Please provide URLs to scrape."
            
            # Scrape the URLs
            scraped_data = self.scrape_urls(urls)
            
            # Filter successful scrapes
            successful_scrapes = [
                data for data in scraped_data 
                if data['status'] == 'success' and data['content']
            ]
            
            if not successful_scrapes:
                return "Could not successfully scrape any content from the provided URLs."
            
            # Combine content
            combined_content = "\n\n".join([
                f"**From {data['title']} ({data['url']}):**\n{data['content']}"
                for data in successful_scrapes
            ])
            
            # Use LLM to analyze the scraped content
            prompt = f"""Based on the following scraped web content, please answer the query: "{query}"

Scraped Content:
{combined_content}

Please provide a comprehensive response based on the scraped content. If the content doesn't directly answer the query, provide the most relevant information available."""

            response = model_manager.azure_llm.invoke(prompt)
            if hasattr(response, 'content'):
                response = response.content
            # Add metadata
            sources = [f"- [{data['title']}]({data['url']})" for data in successful_scrapes]
            response += f"\n\n**Scraped from {len(successful_scrapes)} pages:**\n" + "\n".join(sources)
            return response
            
        except Exception as e:
            st.error(f"Failed to process scraping query: {e}")
            return "Sorry, I couldn't process your scraping request at the moment."

# Global web scraping agent instance
web_scraping_agent = WebScrapingAgent()
