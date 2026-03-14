#from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

##For generating study plans##
def generate_study_plan(task_name, task_category, days_left, description):
    """Uses LangChain to construct a prompt and call the Gemini API."""
    ##This Securely loads the API Key##
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return "Error: API Key missing. Please add GEMINI_API_KEY to .streamlit/secrets.toml"

    ##Initializing the Gemini Model##
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=api_key,
        temperature=0.3 # Low temperature keeps the plan focused and structured
    )

    ##Prompt Engineering##
    template = """
    You are an expert academic tutor and productivity coach helping a university student.
    The student needs a study plan for the following task:
    
    - Task Name: {task_name}
    - Category: {task_category}
    - Days Remaining: {days_left}
    - Additional Details: {description}

    Please generate a realistic step-by-step and day-by-day, actionable study plan that is easy to understand to help them complete this task on time.
    Suggest stricly relevant and existing online resources based on the task with links to these online resources.
    Keep it concise, encouraging, and format it in clean Markdown with bullet points or checkboxes.
    If the days remaining are very few (e.g., less than 3 days), provide an emergency prioritization plan.
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    #For Building the LangChain pipeline (Prompt -> LLM -> String Output)##
    chain = prompt | llm | StrOutputParser()

    ##For Executing the chain##
    try:
        response = chain.invoke({
            "task_name": task_name,
            "task_category": task_category,
            "days_left": days_left,
            "description": description if description else "No additional details provided."
        })
        return response
    except Exception as e:
        return f"AI Generation Error: {str(e)}"
    
##For a Gatekeeper for input validation##
def validate_academic_task(task_name, task_description, task_category):
    """
    Acts as a gatekeeper to ensure the user is only adding academic/productivity tasks.
    Returns True if valid, False if invalid.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return True  # If API key is missing, skip validation to avoid blocking users
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=api_key,
        temperature=0.0 # Deterministic output for validation (Strict Yes or No) Don't want any creativity here
    )

    ##Prompt Engineering for validation##
    template = """
    You are a strict data validation bot for a university student's planner app.
    Your job is to read a task name, description, and category and determine if it is relevant to academics, university life, studying, or student productivity.
    
    Examples of VALID tasks: "Math homework", "Read chapter 4", "Pay tuition", "Group meeting", "Buy textbooks".
    Examples of INVALID tasks: "Play video games", "Go to the club", "Walk the dog", "Buy groceries", "Watch Netflix".
    
    Task Name: {task_name}
    Description: {description}
    Category: {category}
    
    Is this an academically relevant task? Reply STRICTLY with the word YES or NO.
    """

    prompt = ChatPromptTemplate.from_template(template) 
    chain = prompt | llm | StrOutputParser()
    try:
        response = chain.invoke({
            "task_name": task_name,
            "description": task_description if task_description else "",
            "category": task_category
        })
        #Create clean response to ensure we only get YES or NO
        response = response.strip().upper()
        if "YES" in response:
            return True
        else:
            return False
        
    except Exception as e:
        # If for some reason, the AI fails to validate, this allows the task to be saved anyway
        return True 
