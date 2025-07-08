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
        "fields": "title,authors,year,venue,abstract,citationCount,url,referenceCount,openAccessPdf",
        "openAccessPdf": "",
        "limit": 100
    }

    res = requests.get(
        "https://s2api.ominiai.cn/generalProxy/graph/v1/paper/search",
        headers=headers,
        params=params
    )   

    data=res.json()
    papers = []
    if not data.get("data", []):
        print("No data found for the given keyword.")
        return papers

    for item in data.get("data"):
        papers.append(Paper(
            paper_id=item.get("paperId", "unknown"),
            title=item.get("title", "无标题"),
            authors=[author.get("name", "") for author in item.get("authors", [])],
            year=item.get("year", "未知"),
            abstract=item.get("abstract", "暂无摘要"),
            citation_count=item.get("citationCount", 0),
            reference_count=item.get("referenceCount", 0),
            url=item.get("openAccessPdf").get("url") if item.get("openAccessPdf") else "",
        ))
    return papers

def get_simple_references(paper_id: str) -> List[Dict]:
    """获取简化版参考文献（只要标题和作者）"""
    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }
    res = requests.get(
        f"https://s2api.ominiai.cn/generalProxy/graph/v1/paper/{paper_id}/references",
        headers=headers,
        params={"limit": 100, "offset": 0, "fields": "paperId,title,authors,year,abstract,citationCount,url,referenceCount" }
    )

    citedPaper = []
    if not res.json().get("data", []):
        print("No references found for the given paper ID.")
        return citedPaper
    for item in res.json().get("data", []):
        item = item.get("citedPaper", {})
        citedPaper.append(Paper(
            paper_id=item.get("paperId", "unknown"),
            title=item.get("title", "无标题"),
            authors=[author.get("name", "") for author in item.get("authors", [])],
            year=item.get("year", "未知"),
            abstract=item.get("abstract", "暂无摘要"),
            citation_count=item.get("citationCount", 0),
            reference_count=item.get("referenceCount", 0),
            url=item.get("url", "")
        ))
    return citedPaper


def get_simple_citations(paper_id: str) -> List[Dict]:
    """获取简化版引用文献（只要标题和作者）"""
    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }
    res = requests.get(
        f"https://s2api.ominiai.cn/generalProxy/graph/v1/paper/{paper_id}/citations",
        headers=headers,
        params={ "limit": 100, "offset": 0, "fields": "paperId,title,authors,year,abstract,citationCount,url,referenceCount" }
    )
    if not res.json().get("data", []):
        print("No citations found for the given paper ID.")
        return []
    return [item["citingPaper"] for item in res.json().get("data")]


