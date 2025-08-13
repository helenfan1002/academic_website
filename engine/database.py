import sqlite3
from typing import List, Optional, Tuple
from models.paper import Paper
import json

class Database:
    def __init__(self, db_path='Paper.db'):
        self._db_path = db_path
        self.conn = None
        
    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self._db_path)
            self._create_tables()
        return self
        
    def __enter__(self):
        """上下文管理器入口"""
        return self.connect()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        
    def _create_tables(self):
        """创建数据库表"""
        try:
            cursor = self.conn.cursor()
            # 收藏表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                abstract TEXT,
                citation_count INTEGER,
                reference_count INTEGER,
                url TEXT,
                added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            # 缓存表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_relations_cache (
                paper_id TEXT PRIMARY KEY,
                references_json TEXT,
                citations_json TEXT
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_cache (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                abstract TEXT,
                citation_count INTEGER,
                reference_count INTEGER,
                url TEXT,
                added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"创建表失败: {str(e)}")
        
    # ---------------- 收藏表相关 ----------------
    def get_all_papers(self) -> List[Paper]:
        """获取所有收藏的论文"""
        if self.conn is None:
            self.connect()
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM papers ORDER BY added_time DESC")
            papers = []
            for row in cursor.fetchall():
                try:
                    papers.append(Paper(
                        paper_id=row[0],
                        title=row[1],
                        authors=json.loads(row[2]),
                        year=row[3],
                        abstract=row[4],
                        citation_count=row[5],
                        reference_count=row[6],
                        url=row[7]
                    ))
                except json.JSONDecodeError:
                    papers.append(Paper(
                        paper_id=row[0],
                        title=row[1],
                        authors=[],
                        year=row[3],
                        abstract=row[4],
                        citation_count=row[5],
                        reference_count=row[6],
                        url=row[7]
                    ))
            return papers
        except sqlite3.Error as e:
            raise Exception(f"查询论文失败: {str(e)}")
    
    def paper_exists(self, paper_id: str) -> bool:
        """检查论文是否存在"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM papers WHERE id = ? LIMIT 1", (paper_id,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            raise Exception(f"检查论文存在失败: {str(e)}")
    
    def add_paper(self, paper: Paper):
        """添加论文到收藏"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO papers 
            (id, title, authors, year, abstract, citation_count, reference_count, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.paper_id,
                paper.title,
                json.dumps(paper.authors),
                paper.year,
                paper.abstract,
                paper.citation_count,
                paper.reference_count,
                paper.url
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"添加论文失败: {str(e)}")
    
    def remove_paper(self, paper_id: str):
        """从收藏移除论文"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"移除论文失败: {str(e)}")
    
    # ---------------- 缓存表相关 ----------------
    def update_relations(self, paper_id: str, references: List[dict], citations: List[dict]):
        """同时更新 references 和 citations"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO paper_relations_cache (paper_id, references_json, citations_json)
            VALUES (?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET
                references_json=excluded.references_json,
                citations_json=excluded.citations_json
            """, (
                paper_id,
                json.dumps(references),
                json.dumps(citations)
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"更新缓存失败: {str(e)}")

    def get_relations(self, paper_id: str) -> Optional[Tuple[List[dict], List[dict]]]:
        """获取 references 和 citations"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT references_json, citations_json
            FROM paper_relations_cache
            WHERE paper_id = ?
            """, (paper_id,))
            row = cursor.fetchone()
            if row:
                refs_json, cits_json = row
                return json.loads(refs_json), json.loads(cits_json)
            return (None, None)
        except sqlite3.Error as e:
            raise Exception(f"读取缓存失败: {str(e)}")
    
    def add_cache_paper(self, paper: Paper):
        """向缓存表添加或更新论文"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO paper_cache
            (id, title, authors, year, abstract, citation_count, reference_count, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.paper_id,
                paper.title,
                json.dumps(paper.authors),
                paper.year,
                paper.abstract,
                paper.citation_count,
                paper.reference_count,
                paper.url
            ))
            self.conn.commit()
            return paper
        except sqlite3.Error as e:
            raise Exception(f"添加缓存论文失败: {str(e)}")

    def get_cache_paper(self, paper_id: str) -> Optional[Paper]:
        """通过 ID 从缓存表获取论文"""
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM paper_cache WHERE id = ? LIMIT 1", (paper_id,))
            row = cursor.fetchone()
            if row:
                try:
                    return Paper(
                        paper_id=row[0],
                        title=row[1],
                        authors=json.loads(row[2]),
                        year=row[3],
                        abstract=row[4],
                        citation_count=row[5],
                        reference_count=row[6],
                        url=row[7]
                    )
                except json.JSONDecodeError:
                    return Paper(
                        paper_id=row[0],
                        title=row[1],
                        authors=[],
                        year=row[3],
                        abstract=row[4],
                        citation_count=row[5],
                        reference_count=row[6],
                        url=row[7]
                    )
            return None
        except sqlite3.Error as e:
            raise Exception(f"读取缓存论文失败: {str(e)}")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.Error:
                pass  # 忽略关闭时的错误
            finally:
                self.conn = None
