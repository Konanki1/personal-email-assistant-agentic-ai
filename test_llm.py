from llm import llm


response = llm.invoke(
    "Hello! Explain what an email assistant does in one sentence."
)

print(response.content)