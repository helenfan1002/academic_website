import streamlit as st
from engine.database import Database
from models.paper import Paper
from datetime import datetime
from typing import List

def show():
    st.header("⭐ 我的收藏")
    
    db = Database()
    
    papers = db.get_all_papers()
    
    filtered_papers = _show_filters(papers)
    
    _show_papers_list(filtered_papers, db)
    
    db.close()

def _show_filters(papers: List[Paper]) -> List[Paper]:
    """显示收藏论文的筛选器"""
    if not papers:
        return []
    
    years = [p.year for p in papers if p.year is not None]
    if not years:
        return papers
        
    min_year = min(years)
    max_year = max(years)
    
    if min_year == max_year:
        st.warning("所有收藏论文都来自同一年份")
        return papers
    
    st.subheader("筛选选项")
    col1, col2 = st.columns(2)
    
    with col1:
        year_range = st.slider(
            "选择年份范围",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    
    with col2:
        all_authors = sorted(list({
            author for paper in papers 
            for author in paper.authors
            if author
        }))
        selected_authors = st.multiselect(
            "选择作者（可多选）",
            options=all_authors,
            default=[]
        )
    
    filtered = [
        p for p in papers
        if (year_range[0] <= (p.year or min_year) <= year_range[1]) and
           (not selected_authors or any(a in selected_authors for a in p.authors))
    ]
    
    return filtered
def _show_papers_list(papers: List[Paper], db: Database):
    """显示论文列表"""
    if not papers:
        st.info("暂无收藏文献")
        return
    
    for paper in papers:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {paper.title}")
                st.caption(f"作者：{', '.join(paper.authors)} | 年份：{paper.year} | 引用：{paper.citation_count}")
                
                with st.expander("摘要"):
                    st.write(paper.abstract or "暂无摘要")
                
                if paper.url:
                    st.markdown(f"[📄 查看全文]({paper.url})")
            
            with col2:
                if st.button("移除收藏", key=f"remove_{paper.paper_id}"):
                    db.remove_paper(paper.paper_id)
                    st.rerun()
                
                if st.button("查看详情", key=f"detail_{paper.paper_id}"):
                    st.session_state["paper_details"] = paper
                    st.session_state["page_state"] = "paper_details"
                    st.rerun()

if __name__ == "__main__":
    show()
