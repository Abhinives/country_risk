import streamlit as st
import json
import pandas as pd
import asyncio
from gpt_researcher import GPTResearcher
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import re
import os
import feedparser
from dotenv import load_dotenv

load_dotenv()


# def fetch_geopolitical_news(country):
#     feed_url = f"https://news.google.com/rss/search?q={country}+geopolitical+incidents&hl=en-US&gl=US&ceid=US:en"
#     feed = feedparser.parse(feed_url)
    
#     news_items = []
#     for entry in feed.entries[:5]:  # Fetch top 5 news articles
#         news_items.append({
#             "title": entry.title,
#             "link": entry.link,
#             "published": entry.published
#         })
#     return news_items

async def extract_geopolitical_data(report_text, country):
    """Extracts structured geopolitical incident data from the research report using GPT-4."""

    # llm = AzureChatOpenAI(
    #                 deployment_name="gpt-4o-mini",
    #                 openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", None),
    #                 azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None),  
    #                 openai_api_version=os.getenv("OPENAI_API_VERSION", None),
    #                 temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", 0))
    #             )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
    NO PREAMBLE. Extract structured geopolitical incident data from the following research report.
    Return the data in JSON format as specified:

    **JSON Format:**
    {{
        "country": "{country}",
        "incidents": [
            {{
                "title": "Incident title",
                "summary": "Brief summary of the incident",
                "date": "Date of incident (if mentioned (dd-MM-YYYY), else leave empty)",
                "source": "Source name (if available)",
                "referenceurl": "URL to the source (if available)"
            }}
        ]
    }}

    **Research Report:**  
    {report_text}

    - Extract the data **accurately**.
    - If no geopolitical incidents are found, return: {{ "country": "{country}", "incidents": [] }}.
    - Do not infer or create missing data.
    """

    messages = [
        SystemMessage(content="You are an expert at extracting structured geopolitical data from research reports."),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    response = clean_response_from_db(response.content)


    try:
        return eval(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON"}

def clean_response_from_db(response):
    """Removes triple backticks and 'json' from the database response."""
    cleaned_content = re.sub(r"^```json\s*", "", response, flags=re.MULTILINE)  # Remove ```html at the start
    cleaned_content = re.sub(r"```[\s]*$", "", cleaned_content, flags=re.MULTILINE)  # Remove ending ```
    return cleaned_content.strip()
def extract_multiple_metrics_from_report(report_text, metrics):
    """Extracts all economic metrics from a single report in one call."""
    
    # llm = AzureChatOpenAI(
    #                 deployment_name="gpt-4o-mini",
    #                 openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", None),
    #                 azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", None),  
    #                 openai_api_version=os.getenv("OPENAI_API_VERSION", None),
    #                 temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", 0))
    #             )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    metrics_list = ", ".join(metrics)

    prompt = f"""
    NO PREAMBLE. Extract economic data for the following metrics from the research report.
    Return the data in JSON format.

    **Metrics to extract**: {metrics_list}

    **JSON Format:**
    {{
        "country": "Country Name",
        "metrics": [
            {{
                "name": "Metric Name",
                "details": [
                    {{
                        "reporting company": "Company reporting the metric",
                        "metric value": "Value of the metric",
                        "referenceurl": "URL source"
                    }}
                ]
            }}
        ]
    }}

    - Extract values **accurately** along with their sources.
    - If a metric is missing, include an empty list for `"details"`.
    - Do not infer missing data.

    **Report Text:**  
    {report_text}
    """

    messages = [
        SystemMessage(content="You are an expert at extracting structured financial data from reports."),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    response = (clean_response_from_db(response.content))

    try:
        return eval(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON"}

# Async function to fetch data for a country
async def fetch_data(country):
    """Fetches multiple economic metrics in a single GPTResearcher call for efficiency."""
    
    metrics = [
        "GDP", "GDP per Capita", "GDP Growth", "Inflation", "Government Type", "Admin Divisions",
        "Services Sector", "Industry Sector", "Agriculture Sector", "Exports", "Imports", "Trading Partners",
        "Public Debt", "Foreign Reserves", "Credit Rating", "Population", "Unemployment"
    ]
    # metrics = [
    #     "GDP"
    # ]
    query = f"Economic metrics of {country}: " + ", ".join(metrics)
    
    researcher = GPTResearcher(query, report_type="brief")
    await researcher.conduct_research()
    report = await researcher.write_report()

    # Extract all metrics in a single LLM call
    json_data = extract_multiple_metrics_from_report(report, metrics)

    return json_data

async def fetch_geopolitical_incidents(country):
    """Uses GPT Researcher to fetch recent geopolitical incidents for a given country."""
    
    query = f"Recent geopolitical incidents in {country}"
    researcher = GPTResearcher(query, report_type="detailed")
    
    await researcher.conduct_research()
    report = await researcher.write_report()
    report = await extract_geopolitical_data(report, country)

    return report

# Streamlit UI
st.title("Country Risk Agent")

# Input field for country name
country_name = st.text_input("Enter Country Name:")

if st.button("Fetch Data") and country_name:
    with st.spinner("Fetching data, please wait..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data= asyncio.run(fetch_data(country_name))
        geopolitical_news = asyncio.run(fetch_geopolitical_incidents(country_name))
        # print(data)
        print(geopolitical_news)
        # Convert to DataFrame
        table_data = []
        if isinstance(data, dict) and "metrics" in data:
            for item in data["metrics"]:
                metric_name = item.get("name", "N/A")
                details = item.get("details", [])
                
                for detail in details:
                    reference_url = detail.get("referenceurl", "N/A")
                    clickable_url = f'<a href="{reference_url}" target="_blank">{reference_url}</a>' if reference_url.startswith("http") else "N/A"
                    table_data.append([
                        metric_name,
                        detail.get("reporting company", "N/A"),
                        detail.get("metric value", "N/A"),
                        clickable_url
                    ])

            df = pd.DataFrame(table_data, columns=["Metric Name", "Reporting Company", "Metric Value", "Reference URL"])
            
            st.write("### Extracted Economic Metrics")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.warning("No economic metrics found.")

        st.subheader("Recent Geopolitical Incidents")
        if not geopolitical_news.get("incidents"):
            st.write("No recent geopolitical incidents found.")
        else:
            for incident in geopolitical_news["incidents"]:
                st.markdown(f"**{incident.get('title', 'Untitled')}**")
                st.write(f"Date: {incident.get('date', 'Unknown')}")
                st.write(incident.get("summary", "No summary provided."))
                if incident.get("referenceurl"):
                    urls = incident["referenceurl"].split(", ")
                    for url in urls:
                        st.markdown(f"[{url}]({url})", unsafe_allow_html=True)
