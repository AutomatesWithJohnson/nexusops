"""NexusOps Monitoring Dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# Page config
st.set_page_config(
    page_title="NexusOps Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #2e2e2e;
    }
    .stCard {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #2e2e2e;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Mock data generators
def get_mock_events():
    """Generate mock event data."""
    events = []
    for i in range(50):
        events.append({
            "task_id": f"task_{i:04d}",
            "event_type": ["email", "webhook", "api"][i % 3],
            "classification": ["sales_inquiry", "support_ticket", "complaint", "follow_up"][i % 4],
            "agent_chain": f"['classifier', '{['responder', 'quoter', 'scheduler'][i % 3]}']",
            "latency_ms": 500 + (i * 100),
            "escalated": i % 10 == 0,
            "timestamp": datetime.now() - timedelta(minutes=i * 15),
        })
    return pd.DataFrame(events)


def get_mock_agent_stats():
    """Generate mock agent statistics."""
    return {
        "classifier": {"tasks_completed": 245, "errors": 3, "avg_latency_ms": 120, "status": "idle"},
        "responder": {"tasks_completed": 180, "errors": 8, "avg_latency_ms": 2500, "status": "working"},
        "quoter": {"tasks_completed": 95, "errors": 2, "avg_latency_ms": 3200, "status": "idle"},
        "scheduler": {"tasks_completed": 67, "errors": 1, "avg_latency_ms": 1800, "status": "idle"},
        "escalator": {"tasks_completed": 23, "errors": 0, "avg_latency_ms": 4100, "status": "waiting_human"},
    }


def get_mock_memory_stats():
    """Generate mock memory statistics."""
    return {
        "redis_keys": 1247,
        "postgres_entries": 8934,
        "avg_similarity_score": 0.82,
        "memory_hits": 5421,
        "memory_misses": 312,
    }


# Sidebar
st.sidebar.title("🤖 NexusOps")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Agents", "Memory", "Events", "Human Queue"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Track 4:** Autopilot Agent")
st.sidebar.markdown("**Powered by:** Qwen Cloud")
st.sidebar.markdown("**Status:** 🟢 Running")

# Main content
if page == "Overview":
    st.title("📊 System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Events Processed", "1,247", "+12%")
    with col2:
        st.metric("Avg Latency", "1.8s", "-5%")
    with col3:
        st.metric("Success Rate", "98.2%", "+0.3%")
    with col4:
        st.metric("Human Escalations", "23", "-8%")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Events by Classification")
        events_df = get_mock_events()
        classification_counts = events_df["classification"].value_counts()
        fig = px.pie(
            values=classification_counts.values,
            names=classification_counts.index,
            hole=0.4,
        )
        fig.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Latency Distribution")
        fig = px.histogram(
            events_df,
            x="latency_ms",
            nbins=20,
            title="Response Time Distribution",
        )
        fig.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent events
    st.subheader("Recent Events")
    st.dataframe(
        events_df.head(10)[["task_id", "classification", "latency_ms", "escalated", "timestamp"]],
        use_container_width=True,
        hide_index=True,
    )

elif page == "Agents":
    st.title("🤖 Agent Performance")
    
    agent_stats = get_mock_agent_stats()
    
    # Agent cards
    for agent_name, stats in agent_stats.items():
        with st.container():
            st.markdown(f"### {agent_name.title()} Agent")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Tasks Completed", stats["tasks_completed"])
            with col2:
                st.metric("Errors", stats["errors"])
            with col3:
                st.metric("Avg Latency", f"{stats['avg_latency_ms']}ms")
            with col4:
                status_emoji = {"idle": "🟢", "working": "🟡", "waiting_human": "🔵"}.get(stats["status"], "⚪")
                st.metric("Status", f"{status_emoji} {stats['status'].title()}")
            st.markdown("---")

elif page == "Memory":
    st.title("🧠 Memory System")
    
    mem_stats = get_mock_memory_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Redis Keys (Short-term)", f"{mem_stats['redis_keys']:,}")
    with col2:
        st.metric("PostgreSQL Entries (Long-term)", f"{mem_stats['postgres_entries']:,}")
    with col3:
        st.metric("Avg Similarity Score", f"{mem_stats['avg_similarity_score']:.2f}")
    
    st.markdown("---")
    
    # Memory search demo
    st.subheader("Memory Search")
    search_query = st.text_input("Search memories", placeholder="Enter search query...")
    
    if search_query:
        st.info(f"Searching for: '{search_query}'")
        # Mock search results
        results = [
            {"id": "mem_001", "content": "Customer prefers email communication", "score": 0.92, "category": "preference"},
            {"id": "mem_002", "content": "Previous quote for 50 units at $120 each", "score": 0.87, "category": "interaction"},
            {"id": "mem_003", "content": "Customer complained about delivery delay", "score": 0.81, "category": "interaction"},
        ]
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

elif page == "Events":
    st.title("📨 Event Log")
    
    events_df = get_mock_events()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        event_type_filter = st.multiselect("Event Type", ["email", "webhook", "api"], default=["email", "webhook", "api"])
    with col2:
        classification_filter = st.multiselect(
            "Classification",
            ["sales_inquiry", "support_ticket", "complaint", "follow_up"],
            default=["sales_inquiry", "support_ticket", "complaint", "follow_up"],
        )
    
    # Filter dataframe
    filtered_df = events_df[
        (events_df["event_type"].isin(event_type_filter)) &
        (events_df["classification"].isin(classification_filter))
    ]
    
    st.dataframe(
        filtered_df[["task_id", "event_type", "classification", "latency_ms", "escalated", "timestamp"]],
        use_container_width=True,
        hide_index=True,
    )

elif page == "Human Queue":
    st.title("👤 Human Review Queue")
    
    st.info("Tasks requiring human approval")
    
    # Mock human queue
    queue_items = [
        {
            "task_id": "task_0010",
            "agent": "responder",
            "summary": "High-value complaint from gold tier customer",
            "confidence": 0.65,
            "urgency": "high",
            "created_at": datetime.now() - timedelta(minutes=15),
        },
        {
            "task_id": "task_0020",
            "agent": "quoter",
            "summary": "Quote over $10,000 requires manager approval",
            "confidence": 0.72,
            "urgency": "medium",
            "created_at": datetime.now() - timedelta(minutes=45),
        },
    ]
    
    for item in queue_items:
        with st.container():
            st.markdown(f"### Task: {item['task_id']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Agent:** {item['agent'].title()}")
            with col2:
                st.write(f"**Confidence:** {item['confidence']:.2f}")
            with col3:
                urgency_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(item["urgency"], "⚪")
                st.write(f"**Urgency:** {urgency_color} {item['urgency'].title()}")
            
            st.write(f"**Summary:** {item['summary']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{item['task_id']}"):
                    st.success("Approved!")
            with col2:
                if st.button("❌ Reject", key=f"reject_{item['task_id']}"):
                    st.error("Rejected!")
            
            st.markdown("---")
