from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyAtQRjgBV8CJsLGlXc5ODMTaV-DgoDdOWc"

# Mise à jour du modèle vers Gemini
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")  # Utilise "gemini-pro" ou "gemini-pro-vision" selon tes besoins

# Template du prompt
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}."
    "Please follow these instructions carefully:"
    "1. **Extract Information**: Only extract the information that directly matches the provided description: {parse_description}."
    "2. **No Extra Content**: Do not include any additional text, comments, or explanations in your response."
    "3. **Empty Response**: If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only**: Your output should contain only the data explicitly requested, with no additional text."
)

def parse_with_gemini(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []

    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i} of {len(dom_chunks)}")

        # Check if the response has a 'text' or 'content' attribute and call it as a method
        if hasattr(response, 'text'):
            parsed_results.append(str(response.text()))  # Call text() to get the content
        elif hasattr(response, 'content'):
            parsed_results.append(str(response.content))  # If content, use it directly
        else:
            parsed_results.append(str(response))  # Otherwise, convert the response to a string

    # Ensure parsed_results contains only strings before joining
    return "\n".join(parsed_results)
