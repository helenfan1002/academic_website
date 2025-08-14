import streamlit as st
from engine.database import Database
from engine.fetcher import get_paper_relations
from models.paper import Paper
from typing import List
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle, Event
import time

def show():
    st.header("⭐ 我的收藏")
    
    # 从URL参数获取当前页面状态
    page = st.query_params.get("page", "list")
    
    if page == "list":
        show_favorites_list()
    elif page == "details":
        paper_details()
    elif page == "pdf":
        pdf_preview()
    else:
        # 默认返回收藏列表页面
        st.query_params.update({"page": "list"})
        st.rerun()

def show_favorites_list():
    """显示收藏列表"""
    db = Database()
    papers = db.get_all_papers()
    db.close()
    
    # 从URL获取过滤参数
    year_min = st.query_params.get("year_min")
    year_max = st.query_params.get("year_max") 
    authors_param = st.query_params.get("authors", "")
    selected_authors = authors_param.split(",") if authors_param else []
    
    filtered_papers = _show_filters(papers, year_min, year_max, selected_authors)
    _show_papers_list(filtered_papers)

def _show_filters(papers: List[Paper], url_year_min: str = None, url_year_max: str = None, url_selected_authors: List[str] = None) -> List[Paper]:
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
    
    # 从URL参数获取初始值，如果没有则使用默认值
    current_year_min = int(url_year_min) if url_year_min else min_year
    current_year_max = int(url_year_max) if url_year_max else max_year
    
    with col1:
        year_range = st.slider(
            "选择年份范围",
            min_value=min_year,
            max_value=max_year,
            value=(max(current_year_min, min_year), min(current_year_max, max_year))
        )
    
    with col2:
        all_authors = sorted(list({
            author for paper in papers 
            for author in paper.authors
            if author
        }))
        
        # 过滤掉不存在的作者
        valid_selected_authors = [a for a in (url_selected_authors or []) if a in all_authors]
        
        selected_authors = st.multiselect(
            "选择作者（可多选）",
            options=all_authors,
            default=valid_selected_authors
        )
    
    # 检查过滤条件是否发生变化
    if (year_range != (current_year_min, current_year_max) or 
        set(selected_authors) != set(url_selected_authors or [])):
        # 更新URL参数
        new_params = {
            "page": "list",
            "year_min": str(year_range[0]),
            "year_max": str(year_range[1])
        }
        if selected_authors:
            new_params["authors"] = ",".join(selected_authors)
        else:
            # 移除authors参数
            current_params = dict(st.query_params)
            if "authors" in current_params:
                del current_params["authors"]
            new_params = {**current_params, **new_params}
        
        st.query_params.update(new_params)
        st.rerun()
    
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
                    st.toast("已移除收藏")
                    st.rerun()
                
                if st.button("查看详情", key=f"detail_{paper.paper_id}"):
                    # 跳转到详情页面，在URL中保存论文ID
                    st.query_params.update({
                        "page": "details",
                        "paper_id": paper.paper_id,
                        "back": "list"
                    })
                    st.rerun()
                db.close()

def paper_details():
    """文献详情页"""
    paper_id = st.query_params.get("paper_id")
    back_page = st.query_params.get("back", "list")
    
    if not paper_id:
        st.warning("未指定文献ID")
        st.query_params.update({"page": "list"})
        st.rerun()
        return

    # 从数据库获取论文详情
    db = Database()
    paper = db.get_cache_paper(paper_id)
    db.close()
    
    if not paper:
        st.warning("文献信息加载失败")
        st.query_params.update({"page": back_page})
        st.rerun()
        return

    # 检查是否需要重置tab状态
    if st.query_params.get("tab_reset"):
        # 清理所有可能的tab相关状态
        keys_to_remove = [key for key in st.session_state.keys() if 'tabs' in key.lower()]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # 清理URL中的tab_reset参数
        params = dict(st.query_params)
        if "tab_reset" in params:
            del params["tab_reset"]
            st.query_params.clear()
            st.query_params.update(params)

    st.markdown(f"# {paper.title}")
    st.markdown(f"**作者**: {', '.join(paper.authors)}")
    st.markdown(f"**发表年份**: {paper.year} | **被引用次数**: {paper.citation_count}")

    if st.button("📄 查看PDF全文"):
        st.query_params.update({
            "page": "pdf",
            "paper_id": paper_id,
            "back": "details"
        })
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["摘要", "参考文献", "引用文献", "引用图谱"])

    references, citations = get_paper_relations(paper.paper_id)
    
    with tab1:
        st.markdown("### 摘要")
        st.write(paper.abstract or "暂无摘要")

    with tab2:
        st.markdown(f"### 参考文献（{len(references)})")
        if references:
            for ref in references[:min(50, len(references))]:
                title = ref.title if hasattr(ref, 'title') and ref.title else '无标题'
                authors = ', '.join(ref.authors) if hasattr(ref, 'authors') and ref.authors else ''
                st.write(f"- {title} ({authors})")
        else:
            st.info("暂无参考文献数据")

    with tab3:
        st.markdown(f"### 被引用（{paper.citation_count})")
        if citations:
            for cite in citations[:min(50, len(citations))]:
                st.write(f"- {cite.title} ({', '.join(cite.authors)})")
        else:
            st.info("暂无引用文献数据")
    
    with tab4:
        st.markdown("## 引用关系图谱")

        def truncate_title(title: str, max_length: int = 30) -> str:
            """截断标题，保留核心信息"""
            if len(title) <= max_length:
                return title
            # 尝试在单词边界处截断
            words = title.split()
            result = ""
            for word in words:
                if len(result + " " + word) <= max_length - 3:
                    result = result + " " + word if result else word
                else:
                    break
            return result + "..." if len(title) > max_length else result

        elements = {
            "nodes": [{
                "data": {
                    "id": paper.paper_id,
                    "title": paper.title,
                    "short_title": truncate_title(paper.title),
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
                    "short_title": truncate_title(ref.title),
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
                    "short_title": truncate_title(cite.title),
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
                caption='short_title',
                icon='description'
            ),
            NodeStyle(
                label="reference",
                color="#4ECDC4", 
                caption="short_title",
                icon="description"
            ),
            NodeStyle(
                label="citation",
                color="#FFD166",
                caption="short_title",
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

        # 使用paper_id作为组件key的一部分，确保每个论文的图谱都有独立的状态
        graph_key = f"favorites_link_analysis_{paper_id}"
        
        def handle_dblclick():
            if graph_key in st.session_state:
                event_data = st.session_state[graph_key]
                if not event_data:
                    return
                if event_data.get("action") == "node_dblclick":
                    node_id = event_data["data"]["target_id"]
                    clicked_node = next(
                        (n for n in elements["nodes"] 
                         if n["data"]["id"] == node_id), None
                    )
                    if clicked_node and "paper_id" in clicked_node["data"]:
                        target_paper_id = clicked_node["data"]["paper_id"]
                        # 如果点击的是当前论文节点，不执行跳转
                        if target_paper_id != paper_id:
                            # 清理当前图谱的状态，避免状态污染
                            if graph_key in st.session_state:
                                del st.session_state[graph_key]
                            
                            # 跳转到点击的论文详情页，添加时间戳确保tab重置
                            st.query_params.update({
                                "page": "details",
                                "paper_id": target_paper_id,
                                "back": "details",
                                "from_paper": paper_id,  # 记录来源论文ID
                                "tab_reset": str(int(time.time()))  # 添加时间戳确保tab重置
                            })
                            st.rerun()
        
        handle_dblclick()

        st_link_analysis(
            elements,
            layout={
                "name": "concentric",
                "animate": "end",
                "nodeDimensionIncludeLabels": False,
                "avoidOverlap": True,
                "padding": 20,
                "spacingFactor": 1.2
            },
            node_styles=node_styles,
            edge_styles=edge_styles,
            events=events,
            key=graph_key,
        )

    # 返回按钮
    if st.button("返回"):
        from_paper = st.query_params.get("from_paper")
        
        if from_paper and back_page == "details":
            # 如果是从另一个详情页跳转来的，返回到源详情页
            st.query_params.update({
                "page": "details",
                "paper_id": from_paper,
                "back": "list"  # 源详情页的返回目标
            })
        else:
            # 返回收藏列表页
            st.query_params.update({"page": "list"})
        st.rerun()

def pdf_preview():
    """PDF预览页面"""
    paper_id = st.query_params.get("paper_id")
    
    if not paper_id:
        st.warning("未指定文献ID")
        st.query_params.update({"page": "list"})
        st.rerun()
        return

    db = Database()
    paper = db.get_cache_paper(paper_id)
    db.close()
    
    if not paper:
        st.warning("文献信息加载失败")
        st.query_params.update({"page": "list"})
        st.rerun()
        return

    st.markdown(f"# {paper.title}")
    
    if getattr(paper, 'url', None):
        pdf_display = f'<embed src="{paper.url}" width="800" height="1000" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("本文献暂无可用PDF全文")

    if st.button("返回详情页"):
        st.query_params.update({
            "page": "details",
            "paper_id": paper_id,
            "back": "list"
        })
        st.rerun()

if __name__ == "__main__":
    show()