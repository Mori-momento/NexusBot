from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

print("Initializing the AI Triage Agent...")

# 1. Setup the connection to your local LLM
llm = OllamaLLM(model="gemma3:1b", base_url="http://localhost:11435")

# 2. Craft the prompt for the Intelligent Triage task [cite: 73]
# This prompt defines the categories and instructs the model.
prompt = ChatPromptTemplate.from_template("""
You are an intelligent triaging agent for a productivity app.
Your task is to analyze the user's text and classify it into one of three categories:
- Idea: A non-actionable concept or thought. [cite: 73]
- Flexible Task: A short, personal task with no specific deadline. [cite: 74]
- Time-Blocked Task: A work or project-related task that requires a dedicated time slot. [cite: 75]

Analyze the following user text and respond with ONLY the category name.
User Text: "{user_input}"
Category:
""")

# 3. Create the processing chain
chain = prompt | llm | StrOutputParser()

# 4. Define test cases based on the PRD user flow [cite: 64]
test_cases = [
    "idea: a new way to visualize project timelines",
    "remind me to buy milk",
    "Schedule a project sync meeting for Friday at 3pm",
    "a concept for a sci-fi short story",
    "I need to finish the quarterly report by EOD"
]

print("Running classification tests...")
print("-" * 30)

# 5. Run the tests and print the results
for case in test_cases:
    response = chain.invoke({"user_input": case})
    print(f"Input: '{case}'")
    print(f"Output: {response.strip()}")
    print("-" * 30)

print("Tests complete.")