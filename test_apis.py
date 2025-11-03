import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_NEWSDATA = os.getenv("API_NEWSDATA", "")
API_FMP = os.getenv("API_FMP", "")
API_BENZINGA = os.getenv("API_BENZINGA", "")

def test_newsdata():
    print("Testing NewsData.io API...")
    if not API_NEWSDATA:
        print("API_NEWSDATA not set.")
        return
    url = f"https://newsdata.io/api/1/news?apikey={API_NEWSDATA}&q=crypto&language=en"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        results = j.get("results", [])
        print(f"Success: Fetched {len(results)} articles.")
        if results:
            print(f"Sample: {results[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")

def test_fmp():
    print("Testing Financial Modeling Prep API...")
    if not API_FMP:
        print("API_FMP not set.")
        return
    # Updated endpoint for crypto news
    url = f"https://financialmodelingprep.com/api/v3/fmp/articles?page=0&size=20&apikey={API_FMP}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        content = j.get("content", [])
        print(f"Success: Fetched {len(content)} articles.")
        if content:
            print(f"Sample: {content[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")

def test_benzinga():
    print("Testing Benzinga API...")
    if not API_BENZINGA:
        print("API_BENZINGA not set.")
        return
    url = f"https://api.benzinga.com/api/v1/news?token={API_BENZINGA}&category=crypto&limit=20"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        j = r.json()
        data = j.get("data", [])
        print(f"Success: Fetched {len(data)} articles.")
        if data:
            print(f"Sample: {data[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_newsdata()
    test_fmp()
    test_benzinga()
