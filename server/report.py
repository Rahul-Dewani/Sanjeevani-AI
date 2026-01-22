import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for keys immediately to avoid errors later
if not os.getenv("PINECONE_API_KEY"):
    raise ValueError("PINECONE_API_KEY not found in .env file")
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in .env file")

import openai
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

def report(organ, age, clinical_history, disease, features=None):
    # Set OpenAI Key from environment
    openai.api_key = os.getenv("OPENAI_API_KEY")

    print("Loading embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="abhinand/MedEmbed-large-v0.1")
    
    # Initialize Pinecone using the env variable
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    index_name = organ.lower()
    print("Defining index...")
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embedding_model)
    
    # Construct Query
    if (organ in ["Liver", "Brain"]) or disease == "stone":
        query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}, Features: {features} "
    else:
        query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}"
    
    print("Processing query:")
    print(query)

    # Handle "healthy" case immediately
    if disease == "healthy":
        print("Structured output (Healthy)")
        dic = {
            "Treatment Recommendations": ["none"], 
            "Possible Causes": ["none"], 
            "Blood Tests": ["none"], 
            "Prescriptions": ["none"]
        }
        return json.dumps(dic)

    print("Retrieving data from Pinecone...")
    results = vectorstore.similarity_search(query, k=2)
    
    result_str = None
    
    # Filter results based on metadata completeness
    for result in results:
        metadata = result.metadata
        if (metadata.get("blood_tests") and 
            metadata.get("possible_causes") and 
            metadata.get("prescriptions") and 
            metadata.get("treatment_recommendations")):
            
            print("Retrieved data found.")
            result_str = result
            # print(result_str) # Optional: Print raw result
            break    
    
    # Fallback if no perfect match found in the loop
    retrieved_texts = [result_str.page_content] if result_str else [result.page_content for result in results]

    print("Restructuring using LLM...")
    prompt = f"""
    Based on the following medical data:
    {retrieved_texts}

    Provide:
    1. Treatment Recommendations where format is [Recommendation title: Short Description, ... ].
    2. Possible Causes where format is [Possible Cause title: Short Description, ...].
    3. Blood Tests where format is [Test title : Short Description, ... ].
    4. Prescriptions where format is [Medicine title : short reason/description, ... ] Do not provide any other information like Dosage.

    Give only output in JSON file or a dictionary format.
    """
    
    print("Generating response...")
    
    # Call GPT-4 (Ensure your openai library version supports this syntax)
    # If using OpenAI Python SDK v1.0+, you might need client.chat.completions.create
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7,
    )
    
    content = response.choices[0].message["content"].strip()
    print("Structured output generated.")
    return content
