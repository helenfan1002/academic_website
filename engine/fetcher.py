import requests
from models.paper import Paper

def fetch_papers(keyword):

    headers = {
    'OMINI-API-Model': 'semantic',
    'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }

    params={
        "query": "machine learning",
        "fields": "title,authors,year,venue,abstract",
        "limit": 5,
    }

    res = requests.get(
    "https://s2api.ominiai.cn/generalProxy/graph/v1/paper/search",
    headers=headers,
    params=params
    )   

    data=res.json()
    papers = []
    for item in data.get("data", []):
        papers.append(Paper(
            title=item.get("title", "无标题"),
            authors=[author.get("name", "") for author in item.get("authors", [])],
            year=item.get("year", "未知"),
            abstract=item.get("abstract", "暂无摘要"),
            citation_count=item.get("citationCount", 0)
        ))
    return papers
