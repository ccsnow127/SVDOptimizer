import os
import time
import subprocess
import tempfile
import json
import tracemalloc
import re
from typing import List, Dict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name='gpt-4o-mini')

def estimate_complexity(code: str) -> str:
    """Estimate time and space complexity of a given code snippet."""
    prompt = f"""Analyze the following Python Function:
        
        {code}
        
        Now:
        - **Time Complexity**: Start this section with "The time complexity is" and then estimate the worst case Big-O TIME complexity and do not write anything else, no reasoning in this section
        - **Space Complexity**: Start this section with "The space complexity is" and estimate the worst case Big-O SPACE complexity and do not write anything else, no reasoning in this section
        - **Justification**: Explain the reasoning for both in a separate section that is labeled "Justification"

        Do not include ```json or ``` in the output
        **Format**:  Respond in JSON format:
        {{
            "time_complexity": "O(...)",
            "space_complexity": "O(...)",
            "justification": "..."
        }}
    """
    response = llm.invoke(prompt)
    return response.content.strip()

def create_sample(code: str) -> str:
    """Create a sample input for testing the given code."""
    prompt = f"""Analyze the following Python Function:
        {code}
        
        Now:
        - **Runnable Sample Input**: Generate the most computationally expensive input that still runs in reasonable time that would work on any optimized version of this same code:
            Ensuring that the input:
            1. Maximizes execution time and space usage.
            2. Covers as many edge cases as possible.
            3. Can be used for optimization technique evaluation.
            4. Defines sample inputs
            5. Calls the functions needed with those inputs
            6. Prints those results clearly
        - Format the input as a **runnable Python script** (fully executable if appended to the function).
        - Output only the generated code, **without any additional text**.
        Ensure that when this code is appended to any function it does not cause indentation errors
        Do not include ```python or ``` in the output
    """
    response = llm.invoke(prompt)
    return response.content.strip()

def get_metrics(temp_file_path: str) -> tuple:
    """Execute the code and collect performance metrics."""
    process = None
    output = ""
    execution_time = 0.0
    peak_memory = 0.0

    try: 
        tracemalloc.start()

        start_time = time.time()

        process = subprocess.Popen(
                ['python', temp_file_path], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        stdout, stderr = process.communicate()
        execution_time = time.time() - start_time

        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if process.returncode == 0:
            output = stdout.strip()
        else:
            output = f"Error:\n{stderr.strip()}"
    
    except Exception as e:
        output = f"Exception occurred: {str(e)}"

    finally:
        # Kill process if needed
        if process:
            try:
                process.stdout.close()
                process.stderr.close()
                if process.poll() is None:
                    process.kill()
            except:
                pass
        
        # Clear space of tempFile
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

    # **Cap Execution Output Length**
    MAX_CHARACTERS = 500  # Adjust as needed
    MAX_LINES = 15  # Adjust as needed

    output_lines = output.split("\n")[:MAX_LINES]  # Limit lines
    output = "\n".join(output_lines)

    if len(output) > MAX_CHARACTERS:
        output = output[:MAX_CHARACTERS] + "...\n"

    return output, execution_time, peak_memory

def generate_report(code_output: str, execution_time: float, peak_memory: float, complexity_analysis: str) -> Dict:
    """Generate a comprehensive report for the code execution."""
    return {
        'output': code_output,
        'execution_time': execution_time,
        'memory_usage': peak_memory // 1024,
        'complexity_analysis': complexity_analysis
    }

def test_code(code: List[str]) -> List[Dict]:
    """Main function to test multiple code snippets."""
    reports = []

    # Generate a single sample input for the first code snippet
    sample_input = create_sample(code[0])

    for i, c in enumerate(code):
        # Estimate complexity for each code snippet
        complexity_analysis = estimate_complexity(c)

        # Combine code with sample input
        full_code = f"{c}\n\n{sample_input}"

        # Create a temporary file with the full code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(full_code)
            temp_file_path = temp_file.name 

        # Get metrics for the code
        code_output, execution_time, peak_memory = get_metrics(temp_file_path)
        
        # Generate report
        report = generate_report(code_output, execution_time, peak_memory, complexity_analysis)
        
        reports.append(report)

    return reports