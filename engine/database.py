import sqlite3
from typing import List, Optional
from models.paper import Paper
import json

class Database:
    def __init__(self, db_path='favorites.db'):
        self._db_path = db_path  # 使用下划线前缀表示内部属性
        self.conn = None  # 延迟初始化
        
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
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"创建表失败: {str(e)}")
        
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
                    # 如果作者数据格式错误，使用空列表
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
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.Error:
                pass  # 忽略关闭时的错误
            finally:
                self.conn = None