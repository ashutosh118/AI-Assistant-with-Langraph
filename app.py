import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
import os
from typing import List, Dict, Any

# Import components
from config.settings import settings
from utils.models import model_manager
from utils.vector_store import vector_store
from graph.multi_agent_graph import multi_agent_orchestrator

# Configure Streamlit page
st.set_page_config(
    page_title=settings.PAGE_TITLE,
    page_icon=settings.PAGE_ICON,
    layout=settings.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        background: #f1f3f4;
    }
    
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vector_store_stats' not in st.session_state:
        st.session_state.vector_store_stats = vector_store.get_stats()
    if 'ollama_status' not in st.session_state:
        st.session_state.ollama_status = None

def display_main_header():
    """Display the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Multi-Agent AI Assistant</h1>
        <p>Powered by LangGraph • Azure OpenAI GPT-4o • FAISS Vector Store</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display the sidebar with configuration and stats"""
    with st.sidebar:
        st.header("🛠️ Configuration")
        st.subheader("Model Settings")
        st.write("Current Model: `gpt-4o (Azure OpenAI)`")
        st.write(f"Embedding Model: `{settings.EMBEDDING_MODEL}`")
        # Vector Store Stats
        st.subheader("📊 Vector Store")
        stats = vector_store.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", stats["total_documents"])
        with col2:
            st.metric("Index Size", stats["index_size"])
        if st.button("Clear Vector Store"):
            vector_store.clear()
            st.rerun()
        if st.button("Save Vector Store"):
            vector_store.save_index()
        # Agent Information
        st.subheader("🤖 Available Agents")
        agents_info = [
            ("🔍", "Web Search", "Searches web for information"),
            ("🕷️", "Web Scraper", "Extracts content from URLs"),
            ("📄", "File Reader", "Processes uploaded files"),
            ("📝", "Summarizer", "Creates concise summaries"),
            ("📖", "Elaborator", "Provides detailed explanations"),
            ("🧮", "Calculator", "Performs calculations"),
            ("📈", "Predictor", "Makes predictions and analysis")
        ]
        for icon, name, desc in agents_info:
            with st.expander(f"{icon} {name}"):
                st.write(desc)

def display_chat_interface():
    """Display the main chat interface"""
    st.header("💬 Chat with AI Assistant")

    # Display chat history (above input)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "metadata" in message:
                with st.expander("Response Details"):
                    st.json(message["metadata"])

    # Chat input at the bottom
    prompt = st.chat_input("Ask me anything...")
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    uploaded_files = st.session_state.get('uploaded_files', [])
                    urls = st.session_state.get('urls', [])
                    response = multi_agent_orchestrator.process_query(
                        query=prompt,
                        uploaded_files=uploaded_files,
                        urls=urls
                    )
                    st.write(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
        st.rerun()

def display_file_upload():
    """Display file upload interface"""
    st.header("📁 File Upload")
    
    uploaded_files = st.file_uploader(
        "Upload files for analysis",
        type=[ext.replace('.', '') for ext in settings.SUPPORTED_FILE_TYPES],
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(settings.SUPPORTED_FILE_TYPES)}"
    )
    
    if uploaded_files:
        st.session_state['uploaded_files'] = uploaded_files
        st.success(f"Uploaded {len(uploaded_files)} file(s)")
        
        for file in uploaded_files:
            st.write(f"📄 {file.name} ({file.size} bytes)")

def display_url_input():
    """Display URL input interface"""
    st.header("🌐 Web URLs")
    
    urls_input = st.text_area(
        "Enter URLs to scrape (one per line)",
        height=100,
        placeholder="https://example.com\nhttps://another-site.com"
    )
    
    if urls_input:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state['urls'] = urls
        st.success(f"Added {len(urls)} URL(s)")
        
        for url in urls:
            st.write(f"🔗 {url}")

def display_analytics():
    """Display analytics and insights"""
    st.header("📊 Analytics & Insights")
    
    if not st.session_state.messages:
        st.info("Start chatting to see analytics!")
        return
    
    # Message statistics
    total_messages = len(st.session_state.messages)
    user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
    assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Messages", total_messages)
    with col2:
        st.metric("User Messages", user_messages)
    with col3:
        st.metric("Assistant Messages", assistant_messages)
    
    # Message length analysis
    if st.session_state.messages:
        message_lengths = [len(m["content"]) for m in st.session_state.messages]
        
        # Create a simple bar chart
        df = pd.DataFrame({
            'Message': range(1, len(message_lengths) + 1),
            'Length': message_lengths,
            'Role': [m["role"] for m in st.session_state.messages]
        })
        
        fig = px.bar(df, x='Message', y='Length', color='Role', 
                    title="Message Lengths Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Export conversation
    if st.button("Export Conversation"):
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "stats": {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages
            }
        }
        
        st.download_button(
            label="Download JSON",
            data=json.dumps(conversation_data, indent=2),
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display main header
    display_main_header()
    
    # Display sidebar
    display_sidebar()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📁 Files", "🌐 URLs", "📊 Analytics"])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_file_upload()
    
    with tab3:
        display_url_input()
    
    with tab4:
        display_analytics()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Multi-Agent AI Assistant • Built with Streamlit, LangGraph & Azure OpenAI GPT-4o</p>
        <p>• Developed by Ashutosh Srivastava</p>
        <p>🤖 Powered by Open Source AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
