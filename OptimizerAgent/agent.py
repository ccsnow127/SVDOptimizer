import streamlit as st
from agent_functions import *
from testing_agent import test_code
import time
import json
import pandas as pd

# streamlit styles
st.markdown(
    """
    <style>
    /* Main Background */
    # .css-1aumxhk, .stApp {
    #     background-color: #1F2833;
    # }
    .stMarkdown {
        color: #45A29E;
        text-align: center;
    }
    header {visibility: hidden;}
    
    /* General Button Styling */
    .stButton>button {
        color: black;
        background-color: #45A29E;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
        transition: background-color 0.3s, transform 0.2s;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background-color: #99cfbe;
        color: black;
    }
    .stButton>button:active {
        color: black;
        background-color: #8ccfbb;
    }
    
    /* Code Container Styling */
    .css-1lcbmhc {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Main Title Styling */
    h1 {
        font-size: 2.5em;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 10px;
        color: #45A29E;
        white-space: nowrap;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Subheadings for Optimization Techniques */
    .css-1fv8s86 p {
        font-weight: bold;
        font-size: 1.1em;
    }
    
    /* Slider Styling */
    div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"] {
        background-color: #8ccfbb;
        box-shadow: rgb(14 38 74 / 20%) 0px 0px 0px 0.2rem;
    }
    div.stSlider > div[data-baseweb="slider"] > div > div > div > div {
        color: white;
    }
    div.stSlider > div[data-baseweb="slider"] > div > div > div[data-testid="stTickBar"] > div {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def create_error_message(error: str) -> str:
    """Create a formatted error message for display"""
    return f"""
    ```python
    # An error occurred during code execution
    # {error}
    ```
    """

# ChatGPT style text output
def typewriter_effect_code(text, language="python", speed=0.01):
    displayed_text = ""
    text_placeholder = st.empty()

    for char in text:
        displayed_text += char
        text_placeholder.code(displayed_text, language)  # Preserve syntax highlighting
        time.sleep(speed)

# Change available models, if you want to use something else. Make sure you also add the model to the select_model dict in agent.py
available_models = ["OpenAI o1", "Claude 3.5 Sonnet","OpenAI GPT-4o", "OpenAI o3-mini", "Claude 3.5 Haiku", "OpenAI GPT-4o mini"]
# Initialize session state
if 'viewing_history' not in st.session_state:
    st.session_state.viewing_history = False

# Main content area
st.markdown("<h1>MARCO: Multi-Agent Reactive Code Optimizer</h1>", unsafe_allow_html=True)

# Show input controls
user_code = st.text_area("Enter your prompt or Python code here:", height=200)
not_code = st.toggle("Generate Optimized Code from Prompt")
model_option = st.selectbox("Model used:", available_models)
select_model(model_option)
number_times = st.slider("Number of improvement techniques:", min_value=1, max_value=5, value=3)

async def process_optimization(): 
    # Store results
    results_container = st.container()

    # Show unoptimized code first
    with results_container:
        if not_code:
            st.subheader("Starting Prompt")
            st.text(user_code)
        else:
            st.subheader("Unoptimized Code")
            st.code(user_code, language="python")
    
    # Generate optimization techniques
    with st.spinner("Generating optimization techniques..."):
        optimization_techniques = cached_get_optimization_techniques(user_code, number_times)
        
        if not optimization_techniques:
            st.warning("Failed to generate optimization techniques. Using default improvements.")
            optimization_techniques = ["General improvement"]

    # List to store all code versions (original + optimized)
    if not_code:
        code_versions = list()
    else:
        code_versions = [user_code]
    num_to_adjective = {1:"first", 2:"second", 3:"third", 4:"fourth", 5:"fifth"}

    # Generate optimized versions
    for i, technique in enumerate(optimization_techniques, start=1):
        with st.spinner(f"Trying the {num_to_adjective[i]} optimization technique..."):
            improved_code = cached_improve_code(user_code, [technique])

            if improved_code:
                # Display optimized code
                with results_container:
                    st.subheader(f"Optimization {i}: {technique}")
                    typewriter_effect_code(improved_code)
                
                # Add to code versions for testing
                code_versions.append(improved_code)
            await asyncio.sleep(0)

    # Test all code versions
    with st.spinner("Running performance tests..."):
        # Use testing_agent to test all code versions
        test_results = test_code(code_versions)

        # Prepare data for DataFrame
        results_data = []
        for i, result in enumerate(test_results):
            complexity = json.loads(result['complexity_analysis']) if isinstance(result['complexity_analysis'], str) else result['complexity_analysis']
            results_data.append({
                'Version': f'Optimization {i + 1}' if not_code else f'Optimization {i}' if i != 0 else 'Original',
                'Execution Time (s)': f"{result['execution_time']:.4f}",
                'Memory Usage (KB)': result['memory_usage'],
                'Time Complexity': complexity.get('time_complexity', 'N/A'),
                'Space Complexity': complexity.get('space_complexity', 'N/A'),
                'Output': result['output']
            })
            #'Version': 'Original' if i == 0 else f'Optimization {i}',
            #'Version': f'Optimization {i}' if i != 0 else f'Optimization {i}' if not_code else 'Original',

        # Create and display DataFrame
        df = pd.DataFrame(results_data)
        st.subheader("Performance Comparison")
        st.table(df)

        # Optional: Highlight improvements
        improvements = []
        if len(test_results) > 1 and not not_code:
            original = test_results[0]
            for i, optimized in enumerate(test_results[1:], start=1):
                time_improvement = (original['execution_time'] - optimized['execution_time']) / original['execution_time'] * 100
                memory_improvement = (original['memory_usage'] - optimized['memory_usage']) / original['memory_usage'] * 100
                improvements.append({
                    'Optimization': f'Optimization {i}',
                    'Time Improvement (%)': f"{time_improvement:.2f}",
                    'Memory Improvement (%)': f"{memory_improvement:.2f}"
                })

            if improvements:
                st.subheader("Performance Improvements")
                st.table(pd.DataFrame(improvements))

if st.button("Improve Code", type="primary"):
    if user_code:
        asyncio.run(process_optimization())
    else:
        st.warning("Please enter a prompt or some Python code to improve.")