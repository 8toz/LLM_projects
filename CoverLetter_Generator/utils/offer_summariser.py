from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
# Store it into a ChromaDB database
from langchain_openai import OpenAIEmbeddings

import os
import json


PERSIST_DIR = './chroma/'

job_offer_prompt = PromptTemplate(
    input_variables=["job_description"],
    template="""
    You are a professional job offer analyzer. Your task is to extract every tool, technology, and skill mentioned in the job description, grouping them into tech stack and soft skills categories. Follow these instructions carefully:

    1. Use ONLY the EXACT WORDS and phrases from the job description.
    2. Define the role
    3. Group related technologies or skills, separating them with commas if they appear separately in the text.
    4. Assign relevancy points always 10
    5. Do not invent or infer any skills or technologies not explicitly mentioned.
    6. Return the results in the following JSON format:

    {{
      "company": Company name or if missing Industry, 
      "role": "Role definition here",
      "tech_stack": {{
        "Technology/Tool 1": Points (1-100),
        "Technology/Tool 2, Related Technology": Points (1-100),
        ...
      }},
      "soft_skills": {{
        "Soft Skill 1": Points (1-100),
        "Soft Skill 2": Points (1-100),
        ...
      }}
    }}

    Job Description: {job_description}
    """
)

def extract_job_requirements(job_description, api_key):
    # Use ChatOpenAI as the LLM for Langchain
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=api_key)
    # Create an LLMChain
    chain = LLMChain(llm=llm, prompt=job_offer_prompt)
    # Run the chain with the job description
    result = chain.run(job_description)
    # Parse the result as JSON
    try:
        parsed_result = json.loads(result)
        return parsed_result
    except json.JSONDecodeError:
        return {"error": "Failed to parse the result as JSON"}



def generate_cover_letter(processed_job_offer, api_key):
    
    embedding = OpenAIEmbeddings(api_key=api_key)

    # Load the existing vector database
    vectordb = Chroma(
        embedding_function=embedding,
        persist_directory='path/to/existing/persist_directory'  # Specify the directory where the database is stored
    )

    question = f"""
    Use the following pieces of context to create a cover letter for the job offer below:
    {processed_job_offer}

    Instructions:
    1. Create a concise, semi-formal cover letter with a maximum of three paragraphs.
    3. Relate the strongest skills of the candidate with the requirements of the job.
    2. Address any knowledge or technical gap between the applicant's skills and the job requirements:
    a. If possible, compare missing skills to similar ones the applicant possesses.
    b. Exclude skills with no similar counterparts from the cover letter.
    c. For remaining skill gaps, briefly mention the applicant's willingness to learn or adapt.
    3. Keep the language clear and avoid excessive use of adjectives.
    4. Do not fabricate information not provided in the context.

    Return the result as a string with the cover letter.

    """

    # Build prompt
    template = """Use the following pieces of context to answer the question
    {context}
    Question: {question}
    Cover letter: Fill in the letter here
    """
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)


    llm = ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=0, api_key = os.getenv("OPENAI_TEST_KEY"))
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    result = qa_chain({"query": question})

    return result["result"]