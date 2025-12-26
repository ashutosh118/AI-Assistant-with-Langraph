from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import streamlit as st

# Import all agents
from agents.web_search import web_search_agent
from agents.web_scraper import web_scraping_agent
from agents.file_reader import file_reader_agent
from agents.summarizer import summarization_agent
from agents.elaborator import elaboration_agent
from agents.calculator import calculator_agent
from agents.predictor import prediction_agent
from utils.models import model_manager

class MultiAgentState(TypedDict):
    """State management for the multi-agent system"""
    query: str
    context: str
    results: Dict[str, Any]
    active_agents: List[str]
    final_response: str
    uploaded_files: List
    urls: List[str]
    data: Any

class MultiAgentOrchestrator:
    """Orchestrates multiple agents using LangGraph"""
    
    def __init__(self):
        self.agents = {
            "web_search": web_search_agent,
            "web_scraper": web_scraping_agent,
            "file_reader": file_reader_agent,
            "summarizer": summarization_agent,
            "elaborator": elaboration_agent,
            "calculator": calculator_agent,
            "predictor": prediction_agent
        }
        
        # Create the graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        def process_query_simple(state: MultiAgentState) -> MultiAgentState:
            """Simple processing that routes and executes agents"""
            query_lower = state["query"].lower()

            # Detect direct data list in query (e.g., [6,7,13,14,27,28,55])
            import re
            data_list_match = re.search(r'\[\s*[-+]?\d+(?:\.\d+)?(?:\s*,\s*[-+]?\d+(?:\.\d+)?)*\s*\]', state["query"])
            if data_list_match:
                # Only use predictor agent, skip all other logic
                state["active_agents"] = ["predictor"]
                try:
                    with st.spinner("Executing Predictor..."):
                        result = self.agents["predictor"].process_query(state["query"])
                        state["results"] = {"predictor": result}
                        state["final_response"] = result
                except Exception as e:
                    st.error(f"Predictor agent failed: {e}")
                    state["results"] = {"predictor": f"Error: {e}"}
                    state["final_response"] = f"Error: {e}"
                return state

            # Determine which agents to activate based on query content
            active_agents = []
            
            # Web search keywords - enhanced detection
            web_search_keywords = [
                'search', 'find information', 'what is', 'tell me about', 
                'latest', 'current', 'news', 'recent', 'update', 'happening',
                'doing', 'what are', 'how is', 'where is', 'when did',
                'today', 'now', 'status', 'situation', 'development',
                'announcement', 'plan', 'strategy', 'market', 'company',
                'business', 'industry', 'technology', 'launch', 'release'
            ]
            
            # Also check for company names, locations, or current events patterns
            if (any(keyword in query_lower for keyword in web_search_keywords) or
                # Check for patterns like "company doing in country"
                (' in ' in query_lower and ('doing' in query_lower or 'plans' in query_lower)) or
                # Check for question patterns about current events
                (query_lower.startswith(('what', 'how', 'where', 'when', 'why', 'who')) and 
                 any(word in query_lower for word in ['tesla', 'google', 'apple', 'microsoft', 'amazon', 'meta', 'india', 'china', 'usa']))):
                active_agents.append("web_search")
            
            # Web scraping keywords
            if any(keyword in query_lower for keyword in [
                'scrape', 'extract from', 'content from url', 'website content'
            ]) or state.get("urls", []):
                active_agents.append("web_scraper")
            
            # File reading keywords
            if any(keyword in query_lower for keyword in [
                'read file', 'analyze file', 'file content', 'document'
            ]) or state.get("uploaded_files", []):
                active_agents.append("file_reader")
            
            # Summarization keywords
            if any(keyword in query_lower for keyword in [
                'summarize', 'summary', 'brief', 'overview', 'tldr'
            ]):
                active_agents.append("summarizer")
            
            # Elaboration keywords
            if any(keyword in query_lower for keyword in [
                'explain', 'elaborate', 'expand', 'detail', 'comprehensive', 'article', 'write'
            ]):
                active_agents.append("elaborator")
            
            # Calculator keywords
            if any(keyword in query_lower for keyword in [
                'calculate', 'compute', 'math', '+', '-', '*', '/', 
                'statistics', 'average', 'mean'
            ]):
                active_agents.append("calculator")
            
            # Prediction keywords
            if any(keyword in query_lower for keyword in [
                'predict', 'forecast', 'trend', 'analyze', 'pattern', 'future'
            ]):
                active_agents.append("predictor")
            
            # If no specific agents identified, use elaborator as default
            if not active_agents:
                active_agents.append("elaborator")
            
            state["active_agents"] = active_agents
            
            # Execute the agents
            results = {}
            
            for agent_name in active_agents:
                try:
                    with st.spinner(f"Executing {agent_name.replace('_', ' ').title()}..."):
                        
                        if agent_name == "web_search":
                            result = self.agents["web_search"].process_query(state["query"])
                        elif agent_name == "web_scraper":
                            result = self.agents["web_scraper"].process_query(state["query"], state.get("urls", []))
                        elif agent_name == "file_reader":
                            result = self.agents["file_reader"].process_query(state["query"], state.get("uploaded_files", []))
                        elif agent_name == "summarizer":
                            content = state.get("context", "")
                            if not content and results:
                                content = "\n\n".join(results.values())
                            result = self.agents["summarizer"].process_query(state["query"], content)
                        elif agent_name == "elaborator":
                            content = state.get("context", "")
                            if not content and results:
                                content = "\n\n".join(results.values())
                            result = self.agents["elaborator"].process_query(state["query"], content)
                        elif agent_name == "calculator":
                            result = self.agents["calculator"].process_query(state["query"])
                        elif agent_name == "predictor":
                            result = self.agents["predictor"].process_query(state["query"], state.get("data"))
                        else:
                            result = f"Unknown agent: {agent_name}"
                        
                        results[agent_name] = result
                        
                except Exception as e:
                    st.error(f"Agent {agent_name} failed: {e}")
                    results[agent_name] = f"Error: {e}"
            
            state["results"] = results
            
            # Synthesize results
            with st.spinner("Synthesizing results..."):
                if not results:
                    state["final_response"] = "No results were generated from the agents."
                elif len(results) == 1:
                    # Single agent result
                    state["final_response"] = list(results.values())[0]
                else:
                    # Multiple agent results - synthesize them
                    combined_results = "\n\n".join([
                        f"**{agent_name.replace('_', ' ').title()}:**\n{result}"
                        for agent_name, result in results.items()
                    ])
                    
                    try:
                        synthesis_prompt = f"""Based on the following results from different AI agents, please provide a comprehensive, well-structured response to the user's query: "{state["query"]}"

Agent Results:
{combined_results}

Please synthesize this information into a coherent, informative response that best addresses the user's needs."""
                        
                        synthesized = model_manager.azure_llm.invoke(synthesis_prompt)
                        if hasattr(synthesized, 'content'):
                            synthesized = synthesized.content
                        state["final_response"] = synthesized
                    except Exception as e:
                        st.error(f"Result synthesis failed: {e}")
                        state["final_response"] = "\n\n".join(results.values())
            
            return state
        
        # Create simple workflow with just one node
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("process", process_query_simple)
        workflow.set_entry_point("process")
        workflow.add_edge("process", END)
        
        return workflow.compile()
    
    def process_query(self, query: str, context: str = "", uploaded_files: List = None, 
                     urls: List[str] = None, data: Any = None) -> str:
        """Process a query through the multi-agent system"""
        try:
            # Create initial state
            initial_state: MultiAgentState = {
                "query": query,
                "context": context,
                "results": {},
                "active_agents": [],
                "final_response": "",
                "uploaded_files": uploaded_files or [],
                "urls": urls or [],
                "data": data
            }
            
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)
            
            return final_state.get("final_response", "No response generated.")
            
        except Exception as e:
            st.error(f"Workflow execution failed: {e}")
            return "Sorry, I encountered an error while processing your query."

# Global orchestrator instance
multi_agent_orchestrator = MultiAgentOrchestrator()
