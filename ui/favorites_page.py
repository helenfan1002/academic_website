import streamlit as st
from engine.database import Database
from engine.fetcher import get_simple_references, get_simple_citations
from models.paper import Paper
from datetime import datetime
from typing import List

def show():
    if "page_state" not in st.session_state:
        st.session_state["page_state"] = "favorites_list"
        
    current_state = st.session_state["page_state"]
    
    if current_state == "favorites_list":
        show_favorites_list()
    elif current_state == "paper_details":
        paper_details()
    elif current_state == "pdf_preview":
        pdf_preview()

def show_favorites_list():
    """显示收藏列表"""
    st.header("⭐ 我的收藏")
    
    db = Database()
    papers = db.get_all_papers()
    db.close()
    
    filtered_papers = _show_filters(papers)
    _show_papers_list(filtered_papers)

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

def _show_papers_list(papers: List[Paper]):
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
            
            with col2:
                db = Database()
                if st.button("移除收藏", key=f"remove_{paper.paper_id}"):
                    db.remove_paper(paper.paper_id)
                    db.close()
                    st.rerun()
                
                if st.button("查看详情", key=f"detail_{paper.paper_id}"):
                    st.session_state["paper_details"] = paper
                    st.session_state["page_state"] = "paper_details"
                    st.session_state["previous_page"] = "favorites_list"
                    db.close()
                    st.rerun()
                db.close()

def paper_details():
    """文献详情页"""
    paper = st.session_state.get("paper_details")
    if not paper:
        st.warning("文献信息加载失败")
        st.session_state["page_state"] = st.session_state.get("previous_page", "favorites_list")
        st.rerun()

    st.markdown(f"# {paper.title}")
    st.markdown(f"**作者**: {', '.join(paper.authors)}")
    st.markdown(f"**发表年份**: {paper.year} | **被引用次数**: {paper.citation_count}")

    if st.button("📄 查看PDF全文"):
        st.session_state["page_state"] = "pdf_preview"
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["摘要", "参考文献", "引用文献"])

    with tab1:
        st.markdown("### 摘要")
        st.write(paper.abstract or "暂无摘要")

    with tab2:
        references = get_simple_references(paper.paper_id)
        st.markdown(f"### 参考文献（{len(references)})")
        if references:
            for ref in references[:min(50, len(references))]:
                st.write(f"- {ref.title} ({', '.join(ref.authors)})")
        else:
            st.info("暂无参考文献数据")

    with tab3:
        st.markdown(f"### 被引用（{paper.citation_count})")
        if paper.citation_count > 0:
            citations = get_simple_citations(paper.paper_id)
            if citations:
                for cite in citations[:min(50, len(citations))]:
                    st.write(f"- {cite.get('title', '无标题')} ({', '.join(author.get('name', '') for author in cite.get('authors', {}))})")
            else:
                st.info("暂无引用文献数据")

    if st.button("返回收藏列表"):
        st.session_state["page_state"] = "favorites_list"
        st.rerun()

def pdf_preview():
    """PDF预览页面"""
    paper = st.session_state.get("paper_details")
    if not paper:
        st.warning("文献信息加载失败")
        st.session_state["page_state"] = st.session_state.get("previous_page", "favorites_list")
        st.rerun()

    st.markdown(f"# {paper.title}")
    
    if getattr(paper, 'url', None):
        pdf_display = f'<embed src="{paper.url}" width="800" height="1000" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("本文献暂无可用PDF全文")

    if st.button("返回详情页"):
        st.session_state["page_state"] = "paper_details"
        st.rerun()

if __name__ == "__main__":
    show()
