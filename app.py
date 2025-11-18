import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from tools import save_report_to_file

# --- INITIAL SETUP ---
load_dotenv()
app = Flask(__name__)

# --- Pydantic Models for Structured Output ---
class CompanyProfile(BaseModel):
    """Structured data for a single company."""
    company_name: str = Field(description="The official name of the company.")
    company_description: str = Field(description="A detailed paragraph describing the company's business and mission.")
    industry_type: str = Field(description="The primary industry the company operates in.")
    company_size: str = Field(description="The approximate number of employees.")
    specialties: list[str] = Field(description="A list of the company's key specialties, services, or products.")

class AnalysisReport(BaseModel):
    """Structured data for the final business match report."""
    match_score: str = Field(description="The final matching score: 'Strong', 'Common', or 'Weak'.")
    summary: str = Field(description="A detailed summary explaining the rationale behind the matching score.")
    similarities: list[str] = Field(description="A bulleted list of key similarities between the two companies.")
    differences: list[str] = Field(description="A bulleted list of key differences between the two companies.")

# --- AGENT LOGIC ---
def get_upgraded_agent():
    """Creates a reusable LangChain agent."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set.")
    llm = ChatDeepSeek(
        model="deepseek-chat",
        api_key=SecretStr(api_key),
        temperature=0.1
    )
    tools = [DuckDuckGoSearchRun()]
    return llm, tools

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/fetch-and-analyze', methods=['POST'])
def fetch_and_analyze():
    """
    New single endpoint to handle both fetching company data and running the analysis.
    """
    data = request.get_json()
    user_url = data.get('user_url')
    target_url = data.get('target_url')
    if not user_url or not target_url:
        return jsonify({'status': 'error', 'message': 'Missing URLs'}), 400

    try:
        llm, tools = get_upgraded_agent()

        # --- PHASE 1: Research and Auto-fill Data ---
        print(f"🤖 Researching URLs: {user_url} and {target_url}")

        structured_llm = llm.with_structured_output(CompanyProfile)

        user_profile_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert business researcher. Your task is to visit the provided URL and extract key information about the company. Fill in all fields of the CompanyProfile structure accurately."),
            ("human", "Please research the company at this URL: {url}")
        ])
        user_chain = user_profile_prompt | structured_llm
        user_profile = user_chain.invoke({"url": user_url})

        target_chain = user_profile_prompt | structured_llm
        target_profile = target_chain.invoke({"url": target_url})

        print("✅ Research complete. Profiles generated.")

        # --- PHASE 2: Perform Matching Analysis ---
        print("🤖 Performing business match analysis...")

        analysis_llm = llm.with_structured_output(AnalysisReport)

        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a world-class business analyst. Based on the two company profiles provided, perform a detailed comparative analysis. Your output must be a structured JSON object conforming to the AnalysisReport model."),
            ("human", """
            Please analyze the following two companies and generate a match report.

            **Company A Profile:**
            - Name: {user_name}
            - Description: {user_description}
            - Industry: {user_industry}
            - Size: {user_size}
            - Specialties: {user_specialties}

            **Company B Profile:**
            - Name: {target_name}
            - Description: {target_description}
            - Industry: {target_industry}
            - Size: {target_size}
            - Specialties: {target_specialties}
            """)
        ])

        analysis_chain = analysis_prompt | analysis_llm
        analysis_report = analysis_chain.invoke({
            "user_name": user_profile.company_name,
            "user_description": user_profile.company_description,
            "user_industry": user_profile.industry_type,
            "user_size": user_profile.company_size,
            "user_specialties": user_profile.specialties,
            "target_name": target_profile.company_name,
            "target_description": target_profile.company_description,
            "target_industry": target_profile.industry_type,
            "target_size": target_profile.company_size,
            "target_specialties": target_profile.specialties,
        })

        print("✅ Analysis complete.")

        # --- PHASE 3: Combine and Return All Data ---
        return jsonify({
            'status': 'success',
            'user_profile': user_profile.dict(),
            'target_profile': target_profile.dict(),
            'analysis_report': analysis_report.dict()
        })

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)