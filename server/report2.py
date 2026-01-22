import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify keys exist to prevent runtime errors
if not os.getenv("PINECONE_API_KEY"):
    raise ValueError("PINECONE_API_KEY not found in .env file")
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file")

from google import genai
from google.genai import types
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

def report(embedding_model, organ, age, clinical_history, disease, features=None):
    
    # Initialize Pinecone explicitly to ensure connection
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    index_name = organ.lower()
    print("Defining index...")
    
    # Connect to the VectorStore
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embedding_model)
    
    # Initialize Google GenAI Client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

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
    
    # Filter for complete metadata
    for result in results:
        metadata = result.metadata
        # Check if all required metadata fields are present and not empty
        if (metadata.get("blood_tests") and 
            metadata.get("possible_causes") and 
            metadata.get("prescriptions") and 
            metadata.get("treatment_recommendations")):
            
            print("Retrieved data found.")
            result_str = result
            break    
    
    # Fallback if no perfect match found
    retrieved_texts = [result_str.page_content] if result_str else [result.page_content for result in results]

    print("Restructuring using LLM...")
    prompt = f"""
    Based on the following medical data:
    {retrieved_texts}

    Provide:
    1. Treatment Recommendations where format is [Recommendation title: Short Description, ... ].
    2. Possible Causes where format is [Possible Cause title: Short Description, ...].
    3. Blood Tests where format is [Test title : Short Description, ... ].
    4. Prescriptions where format is [Medicine title : short reason/description, ... ] 
    Do not provide any other information like Dosage.

    Give only output in JSON file or a dictionary format.
    """

    print("Generating response...")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=500
        )   
    )
    
    print("Structured output generated.")
    
    # Clean up response text (remove markdown code blocks if present)
    output_text = response.text.strip()
    if output_text.startswith("```json"):
        output_text = output_text[7:-3].strip()
    elif output_text.startswith("```"):
        output_text = output_text[3:-3].strip()

    print(output_text)
    return output_text
