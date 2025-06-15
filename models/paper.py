from dataclasses import dataclass

@dataclass
class Paper:
    title: str
    authors: list
    year: int
    abstract: str
    citation_count: int

    
