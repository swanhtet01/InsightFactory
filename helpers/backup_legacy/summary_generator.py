"""
Executive summary generator using GPT-4o.
"""

import openai
import os

# Load API key directly from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                openai.api_key = line.split('=', 1)[1].strip()
                break

def generate_summary(kpis, trends=None):
    """
    Generate executive-level summaries from KPIs and trends using GPT-4o.
    Args:
        kpis (dict): Computed KPI metrics.
        trends (dict): Trend analysis data (optional).
    Returns:
        str: Executive summary text.
    """
    prompt = f"""
    You are a factory director. Write an executive summary of the following tyre production KPIs. Use clear, concise, director-level language. Highlight trends, anomalies, and actionable insights.
    KPIs: {kpis}
    Trends: {trends}
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an executive summary assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()
