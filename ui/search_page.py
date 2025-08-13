import streamlit as st
from engine.fetcher import fetch_papers, get_simple_references, get_simple_citations, get_paper_relations
from engine.database import Database
from models.paper import Paper
from datetime import datetime
from typing import List
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle, Event

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
    elif current_state == "pdf_preview":
        pdf_preview()

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
        years = [p.year for p in all_results if p.year is not None]
        if years: 
            year_min = min(years)
            year_max = max(years)
        else:
            year_min = 1900
            year_max = datetime.now().year

        year_range = st.slider(
            "选择年份范围",
            min_value=1900,
            max_value=datetime.now().year,
            value=(year_min, year_max)
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
        if (paper.year is None or
            (year_range[0] <= paper.year <= year_range[1])) and
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
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {paper.title}")
        st.caption(f"作者：{', '.join(paper.authors)} | 年份：{paper.year} | 引用：{paper.citation_count}")

    with col2:
        db = Database()
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
        db.close()
    with st.expander("摘要", expanded=True):
        st.write(paper.abstract[:100] + "..." if paper.abstract else "暂无摘要")


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
    paper: Paper = st.session_state.get("paper_details")
    if not paper:
        st.warning("文献信息加载失败")
        st.session_state["page_state"] = "search_results"
        st.rerun()

    st.markdown(f"# {paper.title}")
    st.markdown(f"**作者**: {', '.join(paper.authors)}")
    st.markdown(f"**发表年份**: {paper.year} | **被引用次数**: {paper.citation_count}")

    if st.button("📄 查看PDF全文"):
        st.session_state["page_state"] = "pdf_preview"
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["摘要", "参考文献", "引用文献","引用图谱"])

    references, citations = get_paper_relations(paper.paper_id)
    with tab1:
        st.markdown("### 摘要")
        st.write(paper.abstract or "暂无摘要")

    with tab2:
        # references = get_simple_references(paper.paper_id)
        st.markdown(f"### 参考文献（{paper.reference_count}）")
        if references:
            for ref in references: #[:min(50, len(references))]:
                title = ref.title if hasattr(ref, 'title') and ref.title else '无标题'
                authors = ', '.join(ref.authors) if hasattr(ref, 'authors') and ref.authors else ''
                st.write(f"- {title} ({authors})")
        else:
            st.info("暂无参考文献数据")

    with tab3:
        st.markdown(f"### 被引用（{paper.citation_count})")
        # citations = get_simple_citations(paper.paper_id)
        if citations:
            for cite in citations: #[:min(50, len(citations))]:
                st.write(f"- {cite.title} ({', '.join(cite.authors)})")
        else:
            st.info("暂无引用文献数据")
    
    with tab4:
        st.markdown("## 引用关系图谱")

        elements = {
            "nodes": [{
                "data": {
                    "id": paper.paper_id,
                    "title": paper.title,
                    "authors": ", ".join(paper.authors),
                    "online_url": paper.url,
                    "paper_id": paper.paper_id, 
                    "label": "current"
                }
            }],
            "edges": []
        }

        for ref in references[:10]:
            elements["nodes"].append({
                "data": {
                    "id": ref.paper_id,
                    "title": ref.title,
                    "authors": ", ".join(ref.authors),
                    "online_url": ref.url,
                    "paper_id": ref.paper_id, 
                    "label": "reference"
                }
            })
            elements["edges"].append({
                "data": {
                    "id": f"edge_{paper.paper_id}_to_{ref.paper_id}",
                    "source": paper.paper_id,
                    "target": ref.paper_id,
                    "relation": "cites"
                }
            })

        for cite in citations[:10]:
            elements["nodes"].append({
                "data": {
                    "id": cite.paper_id,
                    "title": cite.title,
                    "authors": ", ".join(cite.authors),
                    "online_url": cite.url,
                    "paper_id": cite.paper_id, 
                    "label": "citation"
                }
            })
            elements["edges"].append({
                "data": {
                    "id": f"edge_{cite.paper_id}_to_{paper.paper_id}",
                    "source": cite.paper_id,
                    "target": paper.paper_id,
                    "relation": "cited_by"
                }
            })

        node_styles = [
            NodeStyle(
                label='current', 
                color='#FF6B6B',
                caption='title',
                icon='description'
            ),
            NodeStyle(
                label="reference",
                color="#4ECDC4", 
                caption="title",
                icon="description"
            ),
            NodeStyle(
                label="citation",
                color="#FFD166",
                caption="title",
                icon="description"
            )
        ]

        edge_styles = [
            EdgeStyle("CITES", caption='label', directed=True),
            EdgeStyle("CITED_BY", caption='label', directed=True)
        ]

        events = [
            Event(
                name="node_dblclick", 
                event_type="dblclick", 
                selector="node"
            )
        ]

        def get_paper_by_id(paper_id: str) -> Paper:
            db = Database()
            return db.get_cache_paper(paper_id)

        def handle_dblclick():
            if "link_analysis" in st.session_state:
                event_data = st.session_state["link_analysis"]
                # print(event_data)
                if not event_data:
                    return
                if event_data.get("action") == "node_dblclick":
                    node_id = event_data["data"]["target_id"]
                    clicked_node = next(
                        n for n in elements["nodes"] 
                        if n["data"]["id"] == node_id
                    )
                    print(clicked_node["data"])
                    if "paper_id" in clicked_node["data"]:
                        st.session_state["paper_details"] = get_paper_by_id(clicked_node["data"]["paper_id"])
                        st.rerun()
        
        handle_dblclick()

        st_link_analysis(
            elements,
            layout={"name":"concentric","animate":"end","nodeDimensionIncludeLabels":False},
            node_styles=node_styles,
            edge_styles=edge_styles,
            events=events,
            key="link_analysis",
            # height="700px"
        )

    if st.button("返回搜索结果"):
        st.session_state["page_state"] = "search_results"
        st.rerun()

def pdf_preview():
    """PDF预览页面"""
    paper = st.session_state.get("paper_details")
    if not paper:
        st.warning("文献信息加载失败")
        st.session_state["page_state"] = "search_results"
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
