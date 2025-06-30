import requests
from models.paper import Paper
from typing import List, Optional

def fetch_papers(keyword:str, 
    year_start:Optional[int]= None, 
    year_end:Optional[int]= None, 
    author_name:Optional[str]= None):

    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }

    params={
        "query": keyword,
        "fields": "title,authors,year,venue,abstract,citationCount",
        "limit": 100
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
            paper_id=item.get("id", "unknown"),
            title=item.get("title", "无标题"),
            authors=[author.get("name", "") for author in item.get("authors", [])],
            year=item.get("year", "未知"),
            abstract=item.get("abstract", "暂无摘要"),
            citation_count=item.get("citationCount", 0)
        ))
    return papers


