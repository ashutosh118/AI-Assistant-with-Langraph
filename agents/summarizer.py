from typing import Dict, Any
import streamlit as st
from config.settings import settings
from utils.models import model_manager

class SummarizationAgent:
    """Agent for creating summaries of content"""
    
    def __init__(self):
        self.name = "Summarization Agent"
        self.description = "Creates concise summaries of content"
    
    def summarize_text(self, text: str, summary_type: str = "comprehensive") -> str:
        """Summarize a given text"""
        try:
            if len(text.strip()) < 50:
                return "Text is too short to summarize meaningfully."
            
            # Different summary prompts based on type
            prompts = {
                "brief": f"""Please provide a brief 2-3 sentence summary of the following text:

{text}

Summary:""",
                
                "comprehensive": f"""Please provide a comprehensive summary of the following text, capturing the main points and key details:

{text}

Summary:""",
                
                "bullet_points": f"""Please summarize the following text as bullet points, highlighting the key information:

{text}

Summary (bullet points):""",
                
                "executive": f"""Please provide an executive summary of the following text, focusing on the most important insights and conclusions:

{text}

Executive Summary:"""
            }
            
            prompt = prompts.get(summary_type, prompts["comprehensive"])
            summary = model_manager.azure_llm.invoke(prompt)
            if hasattr(summary, 'content'):
                summary = summary.content
            return summary
            
        except Exception as e:
            st.error(f"Failed to summarize text: {e}")
            return "Sorry, I couldn't summarize the text at the moment."
    
    def summarize_conversation(self, messages: list) -> str:
        """Summarize a conversation history"""
        try:
            conversation = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in messages
            ])
            
            prompt = f"""Please provide a summary of the following conversation, highlighting the main topics discussed and key insights:

{conversation}

Conversation Summary:"""
            
            summary = model_manager.azure_llm.invoke(prompt)
            if hasattr(summary, 'content'):
                summary = summary.content
            return summary
            
        except Exception as e:
            st.error(f"Failed to summarize conversation: {e}")
            return "Sorry, I couldn't summarize the conversation at the moment."
    
    def process_query(self, query: str, content: str = "", summary_type: str = "comprehensive") -> str:
        """Process a summarization query"""
        try:
            if not content:
                return "Please provide content to summarize."
            
            # Check if query specifies a particular summary type
            query_lower = query.lower()
            if "brief" in query_lower or "short" in query_lower:
                summary_type = "brief"
            elif "bullet" in query_lower or "points" in query_lower:
                summary_type = "bullet_points"
            elif "executive" in query_lower:
                summary_type = "executive"
            
            summary = self.summarize_text(content, summary_type)
            
            # Add query-specific context if needed
            if "focus on" in query_lower or "emphasize" in query_lower:
                focus_prompt = f"""Given the following summary and the specific user request: "{query}"

Original Summary:
{summary}

Please adjust the summary to better address the user's specific focus or emphasis."""
                
                summary = model_manager.azure_llm.invoke(focus_prompt)
                if hasattr(summary, 'content'):
                    summary = summary.content
            
            return summary
            
        except Exception as e:
            st.error(f"Failed to process summarization query: {e}")
            return "Sorry, I couldn't process your summarization request at the moment."

# Global summarization agent instance
summarization_agent = SummarizationAgent()
