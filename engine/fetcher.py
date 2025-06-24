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

    if year_start is not None and year_end is not None:
        params["year"] = f"{year_start}-{year_end}"
    elif year_start is not None:
        params["year"] = f"{year_start}-"
    elif year_end is not None:
        params["year"] = f"-{year_end}"

    if author_name:
        params["query"] = f'{keyword} author:"{author_name}"'

    res = requests.get(
        "https://s2api.ominiai.cn/generalProxy/graph/v1/paper/search",
        headers=headers,
        params=params
    )   

    data=res.json()
    papers = []
    for item in data.get("data", []):
        papers.append(Paper(
            paper_id=item.get("paperId", "unknown"),
            title=item.get("title", "无标题"),
            authors=[author.get("name", "") for author in item.get("authors", [])],
            year=item.get("year", "未知"),
            abstract=item.get("abstract", "暂无摘要"),
            citation_count=item.get("citationCount", 0)
        ))
    return papers

def fetch_paper_details(paper_id: str) -> Optional[Paper]:
    """根据 paper_id 获取单篇论文详情"""
    
    headers = {
        'OMINI-API-Model': 'semantic',
        'Authorization': 'Bearer sk-hO0A98XxnoSpiAH159765cAbC2C24eC48e8aA92925D7Ee77',
    }
    
    params={
        "id": paper_id,
        "fields": "title,authors,year,venue,abstract,citationCount,doi,pdf_url,venue"
    }

    res = requests.get(
        "https://s2api.ominiai.cn/generalProxy/graph/v1/paper/get",
        params=params,
        headers=headers,
    )
    
    res.raise_for_status()
    item = res.json().get("data")
        
    if not item:
        return None
            
    return Paper(
        paper_id=item.get("id", "unknown"),
        title=item.get("title", "无标题"),
        authors=[author.get("name", "") for author in item.get("authors", [])],
        year=int(item.get("year", 0)) if str(item.get("year", "")).isdigit() else None,
        abstract=item.get("abstract", "暂无摘要"),
        citation_count=item.get("citationCount", 0),
        doi=item.get("doi", ""),
        pdf_url=item.get("pdfUrl", ""),
        venue=item.get("venue", {}).get("name", "")
    )

