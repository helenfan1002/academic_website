from dataclasses import dataclass

@dataclass
class Paper:
    paper_id: str
    title: str
    authors: list
    year: int
    abstract: str
    citation_count: int

