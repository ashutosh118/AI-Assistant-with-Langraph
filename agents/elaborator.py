from typing import Dict, Any
import streamlit as st
from config.settings import settings
from utils.models import model_manager

class ElaborationAgent:
    """Agent for providing detailed explanations and expansions"""
    
    def __init__(self):
        self.name = "Elaboration Agent"
        self.description = "Provides detailed explanations and expansions"
    
    def elaborate_topic(self, topic: str, context: str = "", focus_areas: list = None) -> str:
        """Elaborate on a given topic"""
        try:
            # Build the elaboration prompt
            prompt_parts = [
                f"Please provide a detailed, comprehensive explanation of: {topic}"
            ]
            
            if context:
                prompt_parts.append(f"\nContext: {context}")
            
            if focus_areas:
                prompt_parts.append(f"\nPlease focus on these areas: {', '.join(focus_areas)}")
            
            prompt_parts.extend([
                "\nPlease include:",
                "1. A clear explanation of the concept",
                "2. Key components or aspects",
                "3. Real-world examples where applicable",
                "4. Benefits, advantages, or importance",
                "5. Any relevant challenges or considerations",
                "6. Related concepts or connections",
                "\nProvide a thorough, informative response:"
            ])
            
            prompt = "\n".join(prompt_parts)
            elaboration = model_manager.azure_llm.invoke(prompt)
            if hasattr(elaboration, 'content'):
                elaboration = elaboration.content
            return elaboration
            
        except Exception as e:
            st.error(f"Failed to elaborate on topic: {e}")
            return "Sorry, I couldn't elaborate on the topic at the moment."
    
    def explain_concept(self, concept: str, audience_level: str = "general") -> str:
        """Explain a concept at different audience levels"""
        try:
            audience_prompts = {
                "beginner": f"Please explain {concept} in simple terms suitable for someone who is completely new to this topic. Use analogies and examples to make it easy to understand.",
                
                "intermediate": f"Please provide a detailed explanation of {concept} for someone with some background knowledge. Include technical details while keeping it accessible.",
                
                "advanced": f"Please provide an in-depth, technical explanation of {concept} for an expert audience. Include technical details, nuances, and advanced considerations.",
                
                "general": f"Please explain {concept} in a way that is informative yet accessible to a general audience. Balance detail with clarity."
            }
            
            prompt = audience_prompts.get(audience_level, audience_prompts["general"])
            explanation = model_manager.azure_llm.invoke(prompt)
            if hasattr(explanation, 'content'):
                explanation = explanation.content
            return explanation
            
        except Exception as e:
            st.error(f"Failed to explain concept: {e}")
            return "Sorry, I couldn't explain the concept at the moment."
    
    def expand_on_points(self, main_points: list, context: str = "") -> str:
        """Expand on a list of main points"""
        try:
            points_text = "\n".join([f"- {point}" for point in main_points])
            
            prompt = f"""Please expand on each of the following points with detailed explanations, examples, and additional context:

Main Points:
{points_text}

{f"Additional Context: {context}" if context else ""}

For each point, provide:
1. Detailed explanation
2. Examples or applications
3. Implications or significance
4. Related considerations

Expanded Analysis:"""
            
            expansion = model_manager.azure_llm.invoke(prompt)
            if hasattr(expansion, 'content'):
                expansion = expansion.content
            return expansion
            
        except Exception as e:
            st.error(f"Failed to expand on points: {e}")
            return "Sorry, I couldn't expand on the points at the moment."
    
    def process_query(self, query: str, content: str = "") -> str:
        """Process an elaboration query"""
        try:
            query_lower = query.lower()
            
            # Determine the type of elaboration needed
            if "explain" in query_lower or "what is" in query_lower:
                # Extract the concept to explain
                concept = query.replace("explain", "").replace("what is", "").strip()
                
                # Determine audience level
                audience_level = "general"
                if "beginner" in query_lower or "simple" in query_lower:
                    audience_level = "beginner"
                elif "advanced" in query_lower or "technical" in query_lower:
                    audience_level = "advanced"
                elif "intermediate" in query_lower:
                    audience_level = "intermediate"
                
                return self.explain_concept(concept, audience_level)
            
            elif "elaborate" in query_lower or "expand" in query_lower:
                topic = query.replace("elaborate on", "").replace("expand on", "").strip()
                return self.elaborate_topic(topic, content)
            
            else:
                # General elaboration approach
                prompt = f"""The user is asking: "{query}"

{f"Relevant context: {content}" if content else ""}

Please provide a comprehensive, detailed response that thoroughly addresses their question. Include explanations, examples, and relevant details to give them a complete understanding."""
                
                response = model_manager.azure_llm.invoke(prompt)
                if hasattr(response, 'content'):
                    response = response.content
                return response
            
        except Exception as e:
            st.error(f"Failed to process elaboration query: {e}")
            return "Sorry, I couldn't process your elaboration request at the moment."

# Global elaboration agent instance
elaboration_agent = ElaborationAgent()
