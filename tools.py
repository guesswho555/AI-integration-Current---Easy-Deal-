import datetime
from langchain.tools import tool

@tool
def save_report_to_file(report_data: str, filename: str = "business_match_report.txt") -> str:
    """
    Saves the detailed business match report data to a text file.
    Use this tool to save the final analysis.
    The input should be the full, detailed report as a single string.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_text = f"--- Business Match Analysis Report ---\n"
        formatted_text += f"Generated On: {timestamp}\n\n"
        formatted_text += report_data
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_text)
            
        return f"Report successfully saved to {filename}"
    except Exception as e:
        return f"Error saving file: {e}"