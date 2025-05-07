import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
from openai import OpenAIError, RateLimitError
from anthropic import APIError
import nest_asyncio
import time
#from langchain_community.tools import DuckDuckGoSearchRun
#from langchain_community.tools import DuckDuckGoSearchResults
#from langchain_community.tools import TavilySearchResults

from tavily import TavilyClient

from dotenv import load_dotenv
import asyncio
from typing import List, Tuple, Dict

#search = DuckDuckGoSearchRun()
nest_asyncio.apply()
load_dotenv()
llm = None
model_names = {"OpenAI o1":"o1", "Claude 3.5 Sonnet":"claude-3-5-sonnet-latest", "OpenAI GPT-4o":"gpt-4o", "OpenAI o3-mini":"o3-mini",
"Claude 3.5 Haiku":"claude-3-5-haiku-latest", "OpenAI GPT-4o mini":"gpt-4o-mini"}
unavailable_models = list()
selected_model = None

def select_model(option: str):
    global llm
    global selected_model
    selected_model = option
    if option in ["Claude 3.5 Haiku", "Claude 3.5 Sonnet"]:
        llm = ChatAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), model_name=model_names[option])
    elif option in ["OpenAI o1 mini","OpenAI o3-mini"]:
        llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name=model_names[option], temperature=1.0)
    else:
        llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name=model_names[option], temperature=0.7)
        
#llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name='o1-mini') 
#llm = ChatAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), model_name='claude-3-5-sonnet-20241022')
#llm = ChatAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), model_name='claude-3-7-sonnet-latest')
client = TavilyClient(os.getenv('TAVILY_API_KEY'))

if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')

async def invoke_with_fallback(prompt: str) -> str:
    global llm
    global selected_model
    model_fallback = {"OpenAI o1": ["Claude 3.5 Sonnet","OpenAI GPT-4o", "OpenAI o3-mini", "Claude 3.5 Haiku", "OpenAI GPT-4o mini"],
                     "Claude 3.5 Sonnet":["OpenAI GPT-4o", "OpenAI o3-mini", "Claude 3.5 Haiku", "OpenAI GPT-4o mini", "OpenAI o1"],
                     "OpenAI GPT-4o":["Claude 3.5 Sonnet", "OpenAI o3-mini", "Claude 3.5 Haiku", "OpenAI GPT-4o mini", "OpenAI o1"],
                     "OpenAI o3-mini":["Claude 3.5 Haiku", "OpenAI GPT-4o mini", "OpenAI GPT-4o", "Claude 3.5 Sonnet", "OpenAI o1"],
                     "Claude 3.5 Haiku":["OpenAI o3-mini", "OpenAI GPT-4o mini", "OpenAI GPT-4o", "Claude 3.5 Sonnet", "OpenAI o1"],
                     "OpenAI GPT-4o mini":["Claude 3.5 Haiku", "OpenAI o3-mini", "OpenAI GPT-4o", "Claude 3.5 Sonnet", "OpenAI o1"]}
    model_queue = [selected_model] + model_fallback[selected_model]
    for model in model_queue:
        if model in unavailable_models:
            continue
        if model != selected_model:
            if "Claude" in model:
                llm = ChatAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), model_name=model_names[model])
            elif model in ["OpenAI o1", "OpenAI o3-mini"]:
                llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name=model_names[model], temperature=1.0)
            else:
                llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model_name=model_names[model], temperature=0.7)
        try:
            response = await llm.ainvoke(prompt)
            if model != selected_model:
                st.warning(f"The optimization processes will proceed with {model}")
                selected_model = model
            return response
        except OpenAIError:
            if RateLimitError:
                st.warning(f"Rate limit reached for {model}. Trying another model...")
                unavailable_models.append(model)
                continue
            else:
                raise
        except APIError as e:
            if e.status_code == 429:
                st.warning(f"Rate limit reached for {model}. Trying another model...")
                unavailable_models.append(model)
                continue
            else:
                raise
    st.error("All models are currently unavailable. Please try again later.")
    return None
            
"""

OLD PART OF PROMPT - PROCESS NEEDS REFINING

Make sure to add to the existing code, not replace the whole thing.
Each optimization technique should add on to the previous one, and each iteration
should include all the optimizations before it, along with the new one.
If you use numpy, you can move away from using it in later optimizations.
"""

async def get_optimization_techniques(user_code: str, number_times: int) -> List[str]:
    try:
        prompt = f"""You are an expert in performance optimization. Generate a list of {number_times} code optimization techniques for the following code:
{user_code}
Each technique should be specific and actionable.
Consider creative and advanced optimizations to improve its performance. 
The optimizations should go beyond basic NumPy usage and incorporate techniques such as cache locality exploitation, 
loop blocking, vectorization, register tiling, instruction-level parallelism, and hardware-specific optimizations. 
Consider factors such as memory access patterns, minimizing cache misses, reducing data movement, 
and optimizing for different architectures (e.g., CPU vs. GPU). Feel free
to import libraries that can also improve performance, especially new and interesting ones.
Return only the list of techniques, one per line, with no additional text."""
        
        #response = await llm.ainvoke(prompt)
        response = None
        if not response or not response.content:
            
            summary = await user_code_summary(user_code) 
            
            summary = summary.content.strip().split('\n')[0]
            
            print("llm summary response: ", summary)
            techniques = await search_techniques(user_code, number_times, summary)
            web_prompt = f""" {techniques} I have gathered multiple search snippets on advanced optimization. For {number_times}
            snippets, return only the list of techniques, one per line, with only a one sentence description of the optimization."""
            response = await invoke_with_fallback(web_prompt)
            #response = await llm.ainvoke(web_prompt)
            #return ["Basic optimization"]  # Fallback default
            
        techniques = response.content.strip().split('\n')
        techniques = [technique.strip('- ').strip().lstrip('0123456789. ')
                    for technique in techniques if technique.strip()]
        
        print("techniques[0]", techniques[0])
        
        #techniques = techniques[1:] # get rid of "i'll analyze 3 key snippets... response from LLM"
        
        return techniques[:number_times] 
    
    except Exception as e:
        print(f"Error generating optimization techniques: {str(e)}")
        return ["Basic optimization"]

async def search_techniques(user_code: str, number_times: int, user_code_summary: str) -> List[str]:
    
    query = f"detailed and in-depth {user_code_summary} optimization techniques"
    
    try:
        response = client.search(
        max_results=number_times,
        query=query,
        search_depth="advanced",
        include_answer="advanced",
        include_domains=["acm.org","ieee.org", "arxiv.org", "researchgate.net"]
        )
        
        results_list = response
        answer = results_list.get('answer', '')
        content_list = [result.get('content', '') for result in results_list.get('results', []) if result.get('content')]
        final_results = [answer] + content_list
        
        print("Tavily Search Results:", final_results)
    except Exception as e:
        print(f"Error invoking Tavily search: {str(e)}")

    return final_results


async def user_code_summary(user_code: str) -> str:
    
    try:
        prompt = f"""Summarize the following code snippet: {user_code} 
        only give a brief, few word description of what the code is doing. For example, 
        if the user were to input a matrix multiplication code, the summary would be "matrix multiplication"."""
        
        response = await invoke_with_fallback(prompt)
        #response = await llm.ainvoke(prompt)
        #print("llm summary response: ", response)
        
    except Exception as e:
        print(f"Error generating code summary: {str(e)}")
        
    return response
    

async def improve_code(code: str, technique_subset: List[str]) -> str:
    techniques = ', '.join(technique_subset)
    
    print("techniques: ", techniques)
    print("\n")
    
    prompt = f"""
Please improve the following code using the following optimization technique(s): {techniques}. If the technique
does not describe an implementation of the optimization, use that information to come up with one and implement it
into the code.
Make sure the code is complete and can run independently if put into a temporary file and executed using subprocess.
Include all necessary variable definitions. Do not add any example usage or testing in your code.
Do not add any example function calls or variable definitions and do not write any comments.
Do not define any matricies or structures that are used as parameters in the function, including numpy arrays, unless it is
part of the functionality of the code. Do not include a main method, unless one was already given.
Feel free to import libraries that can also improve performance, especially new and interesting ones.

{code}

ONLY RETURN CODE, NO OTHER TEXT.
ONLY RETURN THE RAW CODE WITHOUT ANY MARKDOWN, AND NOTHING ELSE.
Ensure all variables are properly defined before use.
Keep any print statements or output generation from the original code.
Only return optimized code in the language the original code was given in.
"""
    response = await invoke_with_fallback(prompt)
    #response = await llm.ainvoke(prompt)
    parser = StrOutputParser()
    improved_code = parser.invoke(response.content)
    return improved_code

def run_async_func(_async_func, *args, **kwargs):
    return asyncio.run(_async_func(*args, **kwargs))

@st.cache_data
def cached_improve_code(code: str, technique_subset: List[str]) -> str:
    #start = time.perf_counter()
    #time.sleep(4)
    #end = time.perf_counter()
    #print(f"Execution time: {end - start:.6f} seconds")
    #print(f"test test test") 
    return run_async_func(improve_code, code, technique_subset)

@st.cache_data
def cached_get_optimization_techniques(user_code: str, number_times: int) -> List[str]:
    return run_async_func(get_optimization_techniques, user_code, number_times)