import os
# import pinecone
import openai
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import json


def report(organ,age,clinical_history,disease,features=None):
    # os.environ["PINECONE_API_KEY"] = "pcsk_kPX7Z_7uouP3ZtasKTnxdxmv1Xq78CbDFgHi7X1d5NKbAAYs2MjanRU87uLujvaVAFTde"
    os.environ["PINECONE_API_KEY"] = "pcsk_76sA86_9DeHgRYds1BXvcndMbEyvKKtUrqPTeuUfbnVsdTm3PHQGi1yjix16aEvWRpHuQj"
    print("Loading embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="abhinand/MedEmbed-large-v0.1")
    print(embedding_model)
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    # index = pc.Index("mdb1")
    index_name = organ.lower()
    # print(index_name)
    print("Defining index")
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embedding_model)
    
    openai.api_key = "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"

    if (organ in ["Liver", "Brain"]) or disease=="stone":
        query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}, Features: {features} "
        print("Processing query")
        print(query)
    else:
        query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}"
        print("Processing query")
        print(query)
    print("Retrieving data from pinecone...")
    if disease =="healthy":
        print("Structured output")
        dic={"Treatment Recommendations": ["none"], "Possible Causes": ["none"], "Blood Tests": ["none"], "Prescriptions": ["none"]}
        return (json.dumps(dic))
    # Perform similarity search
    results = vectorstore.similarity_search(query, k=2)
    for result in results:
        # print(f"Text: {result.page_content}")
        # print(f"Metadata: {result.metadata}")
        if result.metadata["blood_tests"] != "" and result.metadata["possible_causes"] != "" and  result.metadata["prescriptions"] != "" and  result.metadata["treatment_recommendations"] != "":
            print("Retrieved data: ")
            result_str=result
            print(result_str)
            break    
    # results_str = "\n\n".join([
    # f"Clinical Data:\n{doc.page_content}\n"
    # f"Possible Causes: {doc.metadata.get('possible_causes', 'N/A')}\n"
    # f"Treatment Recommendations: {doc.metadata.get('treatment_recommendations', 'N/A')}\n"
    # f"Blood Tests: {doc.metadata.get('blood_tests', 'N/A')}\n"
    # f"Prescriptions: {doc.metadata.get('prescriptions', 'N/A')}"
    # for doc in results
    # ])
    print("Restructuring using LLM...")
    retrieved_texts = [result_str.page_content] if result_str else [result.page_content for result in results]
    prompt = f"""
Based on the following medical data:
{retrieved_texts}

Provide:
1.⁠ ⁠Treatment Recommendations where format is [Recommendation title: Short Description, Recommendation title: Short Description, ... ].
2.⁠ ⁠Possible Causes where format is [Possible Cause title: Short Description, Possible Cause title: Short Description, ...].
3.⁠ ⁠Blood Tests where format is [Test title : Short Description, Test title : Short Description, ... ].
4.⁠ ⁠Prescriptions where format is [Medicine title : short reason/description ,  Medicine title : short reason / description, ...  ] Do not provide any other information like Dosage.

Give only output in JSON file or a dictonary format.
"""
    print("generating response")
    # Call GPT-4
    response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=500,
    temperature=0.7,
)
    print("Structured output")
    print(response.choices[0].message["content"].strip())
    return(response.choices[0].message["content"].strip())

# #

# import os
# # import pinecone
# import openai
# from pinecone import Pinecone
# from langchain_pinecone import PineconeVectorStore
# # from langchain.embeddings import HuggingFaceEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
# from google import genai

# def report(organ,age,clinical_history,disease,features=None):
#     os.environ["PINECONE_API_KEY"] = "pcsk_kPX7Z_7uouP3ZtasKTnxdxmv1Xq78CbDFgHi7X1d5NKbAAYs2MjanRU87uLujvaVAFTde"
#     print("x")
#     embedding_model = HuggingFaceEmbeddings(model_name="abhinand/MedEmbed-large-v0.1")
#     print(embedding_model)
#     pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
#     print("x")
#     # index = pc.Index("mdb1")
#     index_name = organ.lower()
#     print(index_name)
#     vectorstore = PineconeVectorStore(index_name=index_name, embedding=embedding_model)
#     print("x")
    
#     # Get API Key
#     API_key = ''

#     if API_key is None:  # Check if the API key is set
#         raise ValueError("API key not found. Please set the GROQ_API_KEY environment variable.")

    


#     if (organ in ["Liver", "Brain"]) or disease=="stone":
#         query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}, Features: {features} "
#         print(query)
#     else:
#         query = f"Age Range: {age}, Clinical History: {clinical_history}, Disease: {disease}"
#         print(query)
#     # Perform similarity search
#     results = vectorstore.similarity_search(query, k=10)
#     for result in results:
#         # print(f"Text: {result.page_content}")
#         # print(f"Metadata: {result.metadata}")
#         if result.metadata["blood_tests"] != "" and result.metadata["possible_causes"] != "" and  result.metadata["prescriptions"] != "" and  result.metadata["treatment_recommendations"] != "":
#             result_str=result
#             print(result_str)
#             break    
#     # results_str = "\n\n".join([
#     # f"Clinical Data:\n{doc.page_content}\n"
#     # f"Possible Causes: {doc.metadata.get('possible_causes', 'N/A')}\n"
#     # f"Treatment Recommendations: {doc.metadata.get('treatment_recommendations', 'N/A')}\n"
#     # f"Blood Tests: {doc.metadata.get('blood_tests', 'N/A')}\n"
#     # f"Prescriptions: {doc.metadata.get('prescriptions', 'N/A')}"
#     # for doc in results
#     # ])

#     retrieved_texts = [result_str.page_content] if result_str else [result.page_content for result in results]
#     prompt = f"""
# Based on the following medical data:
# {retrieved_texts}

# Provide:
# 1.⁠ ⁠Treatment Recommendations where format is [Recommendation title: Short Description, Recommendation title: Short Description, ... ].
# 2.⁠ ⁠Possible Causes where format is [Possible Cause title: Short Description, Possible Cause title: Short Description, ...].
# 3.⁠ ⁠Blood Tests where format is [Test title : Short Description, Test title : Short Description, ... ].
# 4.⁠ ⁠Prescriptions where format is [Medicine title : short reason/description ,  Medicine title : short reason / description, ...  ] Do not provide any other information like Dosage.

# Give only output in JSON file or a dictonary format.
# """
#     print("generating response")
#     # Call GPT-4
# #     response = openai.ChatCompletion.create(
# #     model="gpt-4o-mini",
# #     messages=[{"role": "user", "content": prompt}],
# #     max_tokens=500,
# #     temperature=0.7,
# # )


#     client = genai.Client(api_key="AIzaSyDdprIaWEpn6TgWvFdlGDpO4zlkfDiQ0kU")

#     response = client.models.generate_content(
#         model="gemini-2.0-flash",
#         contents="prompt",
# )

#     print(response.text)


#     print(response.choices[0].message["content"].strip())
#     return(response.choices[0].message["content"].strip())

