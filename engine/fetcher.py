import requests
from models.paper import Paper
from typing import List, Dict

def fetch_papers(keyword: str) -> List[Paper]:

    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }

    params={
        "query": keyword,
        "fields": "title,authors,year,venue,abstract,citationCount,url",
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
            citation_count=item.get("citationCount", 0),
            url=item.get("url")
        ))
    return papers

def get_simple_references(paper_id: str) -> List[Dict]:
    """获取简化版参考文献（只要标题和作者）"""
    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }
    res = requests.get(
        f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references",
        params={"fields": "paper_id,contexts", "limit": 100}
    )

    citedPaper = []
    for item in res.json().get("data", []):
        citedPaper.append(Paper(
            paper_id=item.get("id", "unknown"),
            contexts=item.get("contexts","暂无参考文献")
        ))
    return citedPaper


def get_simple_citations(paper_id: str) -> List[Dict]:
    """获取简化版引用文献（只要标题和作者）"""
    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }
    res = requests.get(
        f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations",
        params={"fields": "title,authors", "limit": 100}
    )
    return [item["citingPaper"] for item in res.json().get("data", [])]


