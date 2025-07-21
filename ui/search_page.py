import streamlit as st
from engine.fetcher import fetch_papers, get_simple_references, get_simple_citations
from engine.database import Database
from models.paper import Paper
from datetime import datetime
from typing import List

def show():
    if "page_state" not in st.session_state:
        st.session_state["page_state"] = "search_bar"
        st.rerun()
    
    st.header("🔍 学术文献搜索")
    
    current_state = st.session_state["page_state"]
    if current_state == "search_bar":
        search_bar()
    elif current_state == "search_results":
        search_results()
    elif current_state == "paper_details":
        paper_details()

def search_bar(value: str = ""):
    """简化的搜索栏，不带过滤条件"""
    with st.form("search_form"):
        keyword = st.text_input(
            "请输入关键词",
            value=value
        )
        
        if st.form_submit_button("搜索"):
            if not keyword.strip():
                st.warning("请输入搜索关键词")
                return
                
            with st.spinner("正在搜索文献..."):
                results = fetch_papers(keyword=keyword)
            
            if not results:
                st.warning("没有找到符合条件的文献")
            else:
                years = [p.year for p in results if p.year is not None]
                st.session_state.update({
                    "search_results": results,
                    "search_keyword": keyword,
                    "page_state": "search_results",
                    "filter_year_min": min(years) if years else 1900,
                    "filter_year_max": max(years) if years else datetime.now().year,
                    "selected_authors": []
                })
                st.rerun()

def search_results():
    """带过滤器的搜索结果页面"""
    search_bar(value=st.session_state.get("search_keyword", ""))
    
    all_results = st.session_state.get("search_results", [])
    if not all_results:
        st.warning("没有找到文献")
        return

    st.subheader("过滤选项")
    col1, col2 = st.columns(2)
    
    with col1:
        year_min = st.number_input(
            "起始年份", 
            min_value=1900,
            max_value=datetime.now().year,
            value=st.session_state.get("filter_year_min", 1900)
        )
        year_max = st.number_input(
            "结束年份",
            min_value=1900,
            max_value=datetime.now().year,
            value=st.session_state.get("filter_year_max", datetime.now().year)
        )
    
    with col2:
        all_authors = sorted(list({
            author 
            for paper in all_results 
            for author in paper.authors
        }))
        selected_authors = st.multiselect(
            "选择作者（可多选）",
            options=all_authors,
            default=st.session_state.get("selected_authors", [])
        )
    
    st.session_state.update({
        "filter_year_min": year_min,
        "filter_year_max": year_max,
        "selected_authors": selected_authors
    })
    
    filtered_results = [
        paper for paper in all_results
        if (year_min <= paper.year <= year_max) and
           (not selected_authors or any(author in selected_authors for author in paper.authors))
    ]
    
    if not filtered_results:
        st.warning("没有匹配过滤条件的文献")
        return
    
    st.markdown(f"**找到 {len(filtered_results)} 篇文献**")
    
    paginated_results = get_paginated_results(filtered_results)
    for idx, paper in enumerate(paginated_results):
        with st.container(border=True):
            display_paper_card(paper, idx)
    
    display_pagination_controls(len(filtered_results))

def display_paper_card(paper: Paper, index: int):
    """显示单篇论文卡片（添加收藏功能）"""
    from engine.database import Database
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {paper.title}")
        st.caption(f"作者：{', '.join(paper.authors)} | 年份：{paper.year} | 引用：{paper.citation_count}")
        
    
    with col2:
        with Database() as db:
            is_favorited = db.paper_exists(paper.paper_id)  
        
            if st.button("⭐ 已收藏" if is_favorited else "☆ 收藏", 
                        key=f"fav_{index}"):
                try:
                    if is_favorited:
                        db.remove_paper(paper.paper_id)
                        st.toast("已取消收藏")
                    else:
                        db.add_paper(paper)
                        st.toast("已收藏论文")
                    st.session_state.force_rerun = not getattr(st.session_state, 'force_rerun', False)
                    st.rerun()
                except Exception as e:
                    st.error(f"操作失败: {str(e)}")
        
            if st.button("详情", key=f"detail_{index}"):
                st.session_state.update({
                    "paper_details": paper,
                    "page_state": "paper_details"
                })
                st.rerun()
    with st.expander("摘要", expanded=True):
        abstract = paper.abstract or "暂无摘要"
        abstract = abstract[:min(200, len(abstract))] + ("..." if len(abstract) > 200 else "")
        st.write(abstract)


def get_paginated_results(data: List[Paper]) -> List[Paper]:
    """获取当前页的结果"""
    pagination = st.session_state.get("pagination", {"current_page": 1, "items_per_page": 5})
    start = (pagination["current_page"] - 1) * pagination["items_per_page"]
    end = start + pagination["items_per_page"]
    return data[start:end]

def display_pagination_controls(total_items: int):
    """显示分页控制UI"""
    pagination = st.session_state.setdefault("pagination", {
        "current_page": 1,
        "items_per_page": 5
    })
    total_pages = max(1, (total_items - 1) // pagination["items_per_page"] + 1)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ 上一页", disabled=pagination["current_page"] <= 1):
            pagination["current_page"] -= 1
            st.rerun()
    with col3:
        if st.button("下一页 ➡️", disabled=pagination["current_page"] >= total_pages):
            pagination["current_page"] += 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align: center'>第 {pagination['current_page']} 页 / 共 {total_pages} 页</div>",
            unsafe_allow_html=True
        )

def paper_details():
    """文献详情页"""
    paper = st.session_state.get("paper_details")
    if not paper:
        st.warning("文献信息加载失败")
        st.session_state["page_state"] = "search_results"
        st.rerun()
    
    st.markdown(f"# {paper.title}")
    st.markdown(f"**作者**: {', '.join(paper.authors)}")
    st.markdown(f"**发表年份**: {paper.year} | **被引用次数**: {paper.citation_count}")

    if getattr(paper, 'url', None):
        pdf_display = f'<embed src="https:aclanthology.org/2020.acl-main.447.pdf" width="800" height="1000" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.markdown(f"[📄 查看PDF全文]({paper.url})")
    else:
        st.info("本文献暂无可用PDF全文")

    tab1, tab2, tab3 = st.tabs(["摘要", "参考文献", "引用文献"])

    with tab1:
        st.markdown("### 摘要")
        st.write(paper.abstract or "暂无摘要")

    with tab2:
        references = get_simple_references(paper.paper_id)
        st.markdown(f"### 参考文献（{len(references)}）")
        if references:
            for ref in references[:min(50, len(references))]:
                st.write(f"- {ref.title} ({', '.join(ref.authors)})")
        else:
            st.info("暂无参考文献数据")

    with tab3:
        st.markdown(f"### 被引用（{paper.citation_count}）")
        if paper.citation_count > 0:
            citations = get_simple_citations(paper.paper_id)
            if citations:
                for cite in citations[:min(50, len(citations))]:
                    st.write(f"- {cite.get('title', '无标题')} ({', '.join(author.get('name', '') for author in cite.get('authors', {}))})")
            else:
                st.info("暂无引用文献数据")

    if st.button("返回搜索结果"):
        st.session_state["page_state"] = "search_results"
        st.rerun()

if __name__ == "__main__":
    show()
