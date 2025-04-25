from typing import List, Dict, Any, Annotated, TypedDict, Literal
import operator
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from utils import gemini_flash


# Define the state schema
class ChainOfThoughtState(TypedDict):
    query: str
    messages: List[BaseMessage]
    reasoning: List[str]
    should_continue: bool
    output: str


# Initialize the reasoning model
def get_reasoning_model():
    return gemini_flash


# Node to perform reasoning
def reason(state: ChainOfThoughtState) -> ChainOfThoughtState:
    """
    Perform a step of chain-of-thought reasoning based on the query and previous reasoning.
    """
    # Get the current state
    query = state["query"]
    messages = state["messages"]
    reasoning_history = state["reasoning"]
    
    # Prepare the prompt for the reasoning step
    system_message = SystemMessage(
        content="You are an advanced reasoning agent. Your task is to think step by step about the query. "
                "Build on your previous reasoning to go deeper or explore new angles. "
                "Be thorough and analytical in your approach."
    )
    
    # Construct the prompt with the query and reasoning history
    reasoning_context = "\n\n".join([
        f"Reasoning step {i+1}: {reasoning}" 
        for i, reasoning in enumerate(reasoning_history)
    ])
    
    if reasoning_history:
        human_message = HumanMessage(
            content=f"Query: {query}\n\nPrevious reasoning:\n{reasoning_context}\n\n"
                    f"Continue reasoning about this query. Provide the next step in your chain of thought."
        )
    else:
        human_message = HumanMessage(
            content=f"Query: {query}\n\nBegin reasoning about this query. Think step by step."
        )
    
    # Include previous conversation messages for context
    all_messages = [system_message] + messages + [human_message]
    
    # Get the model's response
    model = get_reasoning_model()
    ai_message = model.invoke(all_messages)
    print("AI Message:")
    print(ai_message.content)
    
    # Extract the reasoning from the response
    new_reasoning = ai_message.content
    
    # Update the state with the new reasoning
    updated_reasoning = reasoning_history + [new_reasoning]
    
    return {
        "query": query,
        "messages": messages,
        "reasoning": updated_reasoning,
        "should_continue": True,  # Default to continue, will be evaluated in the next node
        "output": ""  # Will be populated when reasoning is complete
    }


# Node to decide whether to continue reasoning
def should_continue_reasoning(state: ChainOfThoughtState) -> ChainOfThoughtState:
    """
    Decide whether to continue the reasoning process or finalize the output.
    """
    # Get the current state
    query = state["query"]
    messages = state["messages"]
    reasoning_history = state["reasoning"]
    
    # Prepare the prompt for the decision
    system_message = SystemMessage(
        content="You are a decision-making agent. Your task is to decide whether further reasoning is needed "
                "on the given query. Consider the depth and completeness of the reasoning so far. "
                "If the reasoning is thorough and addresses the query comprehensively, decide to stop. "
                "Otherwise, recommend continuing the reasoning process."
    )
    
    # Construct the prompt with the query and reasoning history
    reasoning_context = "\n\n".join([
        f"Reasoning step {i+1}: {reasoning}" 
        for i, reasoning in enumerate(reasoning_history)
    ])
    
    human_message = HumanMessage(
        content=f"Query: {query}\n\nReasoning so far:\n{reasoning_context}\n\n"
                f"Should I continue reasoning or is this sufficient? Respond with CONTINUE if more reasoning is needed "
                f"or STOP if the reasoning is sufficient. Explain your decision briefly."
    )
    
    # Include previous conversation messages for context
    all_messages = [system_message] + messages + [human_message]
    
    # Get the model's response
    model = get_reasoning_model()
    ai_message = model.invoke(all_messages)
    
    # Determine if we should continue based on the response
    response = ai_message.content.upper()
    should_continue = "CONTINUE" in response
    
    return {
        "query": query,
        "messages": messages,
        "reasoning": reasoning_history,
        "should_continue": should_continue,
        "output": ""  # Will be populated when reasoning is complete
    }


# Node to generate the final output
def generate_output(state: ChainOfThoughtState) -> ChainOfThoughtState:
    """
    Generate the final output based on the complete reasoning process.
    """
    # Get the current state
    query = state["query"]
    messages = state["messages"]
    reasoning_history = state["reasoning"]
    
    # Prepare the prompt for generating the final output
    system_message = SystemMessage(
        content="You are a summarization agent. Your task is to synthesize the chain-of-thought reasoning "
                "into a clear, concise, and comprehensive answer to the original query. "
                "Incorporate the key insights from the reasoning process."
    )
    
    # Construct the prompt with the query and reasoning history
    reasoning_context = "\n\n".join([
        f"Reasoning step {i+1}: {reasoning}" 
        for i, reasoning in enumerate(reasoning_history)
    ])
    
    human_message = HumanMessage(
        content=f"Query: {query}\n\nComplete reasoning process:\n{reasoning_context}\n\n"
                f"Based on this chain-of-thought reasoning, provide a final answer to the query."
    )
    
    # Include previous conversation messages for context
    all_messages = [system_message] + messages + [human_message]
    
    # Get the model's response
    model = get_reasoning_model()
    ai_message = model.invoke(all_messages)
    
    # Extract the final output
    final_output = ai_message.content
    
    return {
        "query": query,
        "messages": messages,
        "reasoning": reasoning_history,
        "should_continue": False,  # We're done reasoning
        "output": final_output
    }


# Define the edges of the graph
def define_edges(state: ChainOfThoughtState) -> str:
    """
    Define the edges of the graph based on the current state.
    """
    if state["should_continue"]:
        return "reason"
    else:
        return END


# Create the chain of thought graph
def create_chain_of_thought_graph():
    """
    Create and return the chain of thought reasoning graph.
    """
    # Initialize the graph
    workflow = StateGraph(ChainOfThoughtState)
    
    # Add the nodes
    workflow.add_node("reason", reason)
    workflow.add_node("continue_decision", should_continue_reasoning)
    workflow.add_node("generate_output", generate_output)
    
    # Add the edges
    workflow.add_edge("reason", "continue_decision")
    workflow.add_conditional_edges(
        "continue_decision",
        define_edges,
        {
            "reason": "reason",
            END: "generate_output"
        }
    )
    workflow.add_edge("generate_output", END)
    
    # Set the entry point
    workflow.set_entry_point("reason")
    
    # Compile the graph
    return workflow.compile()


# Function to run the chain of thought reasoning
def run_chain_of_thought(query: str, messages: List[BaseMessage] = None) -> Dict[str, Any]:
    """
    Run the chain of thought reasoning on the given query.
    
    Args:
        query: The query to reason about
        messages: Optional list of previous conversation messages for context
        
    Returns:
        The final state containing the reasoning process and output
    """
    if messages is None:
        messages = []
    
    # Initialize the state
    initial_state = {
        "query": query,
        "messages": messages,
        "reasoning": [],
        "should_continue": True,
        "output": ""
    }
    
    # Create and run the graph
    graph = create_chain_of_thought_graph()
    result = graph.invoke(initial_state)
    
    return result


# Example usage
if __name__ == "__main__":
    query = """On average Joe throws 25 punches per minute. A fight lasts 5 rounds of 3 minutes. How many punches did he throw?"""
    result = run_chain_of_thought(query)
    
    print("\nQuery:", result["query"])
    # print("\nReasoning Process:")
    # for i, reasoning in enumerate(result["reasoning"]):
    #     print(f"\nStep {i+1}:\n{reasoning}")
    
    print("\nFinal Output:\n", result["output"])
