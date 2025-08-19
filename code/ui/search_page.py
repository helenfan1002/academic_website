import streamlit as st
from engine.fetcher import fetch_papers, get_paper_relations
from engine.database import Database
from models.paper import Paper
from datetime import datetime
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle, Event
import time

def show():
    st.header("🔍 学术文献搜索")
    
    # 从URL参数获取当前页面状态
    page = st.query_params.get("page", "search")
    
    if page == "search":
        search_page()
    elif page == "results":
        search_results_page()
    elif page == "details":
        paper_details_page()
    elif page == "pdf":
        pdf_preview_page()
    else:
        # 默认返回搜索页面
        st.query_params.update({"page": "search"})
        st.rerun()

def search_page():
    """搜索页面"""
    # 从URL获取搜索关键词（用于返回时恢复搜索框内容）
    keyword = st.query_params.get("q", "")
    
    with st.form("search_form"):
        search_input = st.text_input("请输入关键词", value=keyword)

        if st.form_submit_button("搜索"):
            if not search_input.strip():
                st.warning("请输入搜索关键词")
                return

            with st.spinner("正在搜索文献..."):
                results = fetch_papers(keyword=search_input)

            if not results:
                st.warning("没有找到符合条件的文献")
            else:
                # 将搜索结果存储到session_state（临时存储）
                years = [p.year for p in results if p.year is not None]
                st.session_state.update({
                    "search_results": results,
                    "filter_year_min": min(years) if years else 1900,
                    "filter_year_max": max(years) if years else datetime.now().year,
                    "selected_authors": []
                })
                
                # 跳转到结果页面，并在URL中保存搜索关键词
                st.query_params.update({
                    "page": "results", 
                    "q": search_input
                })
                st.rerun()

def search_results_page():
    """搜索结果页面"""
    keyword = st.query_params.get("q", "")
    
    # 如果没有搜索结果数据，重新执行搜索
    if "search_results" not in st.session_state and keyword:
        with st.spinner("正在搜索文献..."):
            results = fetch_papers(keyword=keyword)
        if results:
            years = [p.year for p in results if p.year is not None]
            st.session_state.update({
                "search_results": results,
                "filter_year_min": min(years) if years else 1900,
                "filter_year_max": max(years) if years else datetime.now().year,
                "selected_authors": []
            })
    
    # 显示搜索框（可以修改搜索）
    with st.form("search_form"):
        search_input = st.text_input("请输入关键词", value=keyword)
        
        if st.form_submit_button("搜索"):
            if not search_input.strip():
                st.warning("请输入搜索关键词")
                return
                
            with st.spinner("正在搜索文献..."):
                results = fetch_papers(keyword=search_input)

            if not results:
                st.warning("没有找到符合条件的文献")
            else:
                years = [p.year for p in results if p.year is not None]
                st.session_state.update({
                    "search_results": results,
                    "filter_year_min": min(years) if years else 1900,
                    "filter_year_max": max(years) if years else datetime.now().year,
                    "selected_authors": []
                })
                
                # 更新URL参数
                st.query_params.update({
                    "page": "results", 
                    "q": search_input
                })
                st.rerun()

    all_results = st.session_state.get("search_results", [])
    if not all_results:
        st.warning("没有找到文献")
        return

    # 从URL获取过滤参数
    page_num = int(st.query_params.get("p", "1"))
    year_min = int(st.query_params.get("year_min", str(st.session_state.get("filter_year_min", 1900))))
    year_max = int(st.query_params.get("year_max", str(st.session_state.get("filter_year_max", datetime.now().year))))
    authors_param = st.query_params.get("authors", "")
    selected_authors = authors_param.split(",") if authors_param else []

    st.subheader("过滤选项")
    col1, col2 = st.columns(2)

    with col1:
        years = [p.year for p in all_results if p.year is not None]
        if years: 
            available_year_min = min(years)
            available_year_max = max(years)
        else:
            available_year_min = 1900
            available_year_max = datetime.now().year

        year_range = st.slider(
            "选择年份范围",
            min_value=1900,
            max_value=datetime.now().year,
            value=(max(year_min, available_year_min), min(year_max, available_year_max)),
            key="year_slider"
        )

    with col2:
        all_authors = sorted(list({
            author 
            for paper in all_results 
            for author in paper.authors
        }))
        
        # 过滤掉不存在的作者
        valid_selected_authors = [a for a in selected_authors if a in all_authors]
        
        selected_authors_new = st.multiselect(
            "选择作者（可多选）",
            options=all_authors,
            default=valid_selected_authors,
            key="author_multiselect"
        )

    # 检查过滤条件是否发生变化
    if (year_range != (year_min, year_max) or 
        set(selected_authors_new) != set(selected_authors)):
        # 更新URL参数
        new_params = {
            "page": "results",
            "q": keyword,
            "p": "1",  # 重置页码
            "year_min": str(year_range[0]),
            "year_max": str(year_range[1])
        }
        if selected_authors_new:
            new_params["authors"] = ",".join(selected_authors_new)
        else:
            # 移除authors参数
            current_params = dict(st.query_params)
            if "authors" in current_params:
                del current_params["authors"]
            new_params = {**current_params, **new_params}
        
        st.query_params.update(new_params)
        st.rerun()

    # 应用过滤器
    filtered_results = [
        paper for paper in all_results
        if (paper.year is None or
            (year_range[0] <= paper.year <= year_range[1])) and
           (not selected_authors_new or any(author in selected_authors_new for author in paper.authors))
    ]

    if not filtered_results:
        st.warning("没有匹配过滤条件的文献")
        return

    st.markdown(f"**找到 {len(filtered_results)} 篇文献**")

    # 分页处理
    items_per_page = 5
    total_pages = max(1, (len(filtered_results) - 1) // items_per_page + 1)
    current_page = min(page_num, total_pages)  # 确保页码不超出范围
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_results = filtered_results[start_idx:end_idx]

    # 显示论文卡片
    for idx, paper in enumerate(paginated_results):
        with st.container(border=True):
            display_paper_card(paper, start_idx + idx, keyword)

    # 分页控制
    display_pagination_controls(current_page, total_pages, keyword, year_range, selected_authors_new)

def display_paper_card(paper: Paper, index: int, keyword: str):
    """显示单篇论文卡片"""
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
                st.rerun()
            except Exception as e:
                st.error(f"操作失败: {str(e)}")

        if st.button("详情", key=f"detail_{index}"):
            # 跳转到详情页面，在URL中保存论文ID
            st.query_params.update({
                "page": "details",
                "paper_id": paper.paper_id,
                "back": "results",  # 记录返回页面
                "q": keyword  # 保持搜索关键词
            })
            st.rerun()
        db.close()
        
    with st.expander("摘要", expanded=True):
        st.write(paper.abstract[:100] + "..." if paper.abstract else "暂无摘要")

def display_pagination_controls(current_page: int, total_pages: int, keyword: str, year_range: tuple, selected_authors: list):
    """显示分页控制UI"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    # 构建基础URL参数
    base_params = {
        "page": "results",
        "q": keyword,
        "year_min": str(year_range[0]),
        "year_max": str(year_range[1])
    }
    if selected_authors:
        base_params["authors"] = ",".join(selected_authors)
    
    with col1:
        if st.button("⬅️ 上一页", disabled=current_page <= 1):
            st.query_params.update({**base_params, "p": str(current_page - 1)})
            st.rerun()
    
    with col3:
        if st.button("下一页 ➡️", disabled=current_page >= total_pages):
            st.query_params.update({**base_params, "p": str(current_page + 1)})
            st.rerun()
    
    with col2:
        st.markdown(
            f"<div style='text-align: center'>第 {current_page} 页 / 共 {total_pages} 页</div>",
            unsafe_allow_html=True
        )

def paper_details_page():
    """文献详情页"""
    paper_id = st.query_params.get("paper_id")
    back_page = st.query_params.get("back", "search")
    keyword = st.query_params.get("q", "")
    
    if not paper_id:
        st.warning("未指定文献ID")
        st.query_params.update({"page": "search"})
        st.rerun()
        return

    # 从数据库获取论文详情
    db = Database()
    paper = db.get_cache_paper(paper_id)
    db.close()
    
    if not paper:
        st.warning("文献信息加载失败")
        st.query_params.update({"page": back_page, "q": keyword})
        st.rerun()
        return

    st.markdown(f"# {paper.title}")
    st.markdown(f"**作者**: {', '.join(paper.authors)}")
    st.markdown(f"**发表年份**: {paper.year} | **被引用次数**: {paper.citation_count}")

    if st.button("📄 查看PDF全文"):
        st.query_params.update({
            "page": "pdf",
            "paper_id": paper_id,
            "back": "details",
            "q": keyword
        })
        st.rerun()

    # 检查是否需要清理tab相关的session_state来重置tab选择
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["摘要", "参考文献", "引用文献", "引用图谱"])

    references, citations = get_paper_relations(paper.paper_id)
    
    with tab1:
        st.markdown("### 摘要")
        st.write(paper.abstract or "暂无摘要")

    with tab2:
        st.markdown(f"### 参考文献（{paper.reference_count}）")
        if references:
            for ref in references:
                title = ref.title if hasattr(ref, 'title') and ref.title else '无标题'
                authors = ', '.join(ref.authors) if hasattr(ref, 'authors') and ref.authors else ''
                st.write(f"- {title} ({authors})")
        else:
            st.info("暂无参考文献数据")

    with tab3:
        st.markdown(f"### 被引用（{paper.citation_count})")
        if citations:
            for cite in citations:
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
                    "authors": ", ".join(paper.authors),
                    "ref_count": paper.reference_count,
                    "cite_count": paper.citation_count,
                    "online_url": paper.url,
                    "short_title": truncate_title(paper.title),
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
                    "ref_count": ref.reference_count,
                    "cite_count": ref.citation_count,
                    "online_url": ref.url,
                    "short_title": truncate_title(ref.title),
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
                    "ref_count": cite.reference_count,
                    "cite_count": cite.citation_count,
                    "short_title": truncate_title(cite.title),
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
                caption='short_title',  # 使用短标题
                icon='description'
            ),
            NodeStyle(
                label="reference",
                color="#4ECDC4", 
                caption="short_title",  # 使用短标题
                icon="description"
            ),
            NodeStyle(
                label="citation",
                color="#FFD166",
                caption="short_title",  # 使用短标题
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
        graph_key = f"link_analysis_{paper_id}"
        
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
                    if clicked_node and "id" in clicked_node["data"]:
                        target_paper_id = clicked_node["data"]["id"]
                        # 如果点击的是当前论文节点，不执行跳转
                        if target_paper_id != paper_id:
                            # 清理当前图谱的状态，避免状态污染
                            if graph_key in st.session_state:
                                del st.session_state[graph_key]
                            
                            # 跳转到点击的论文详情页，记录来源论文ID，添加时间戳确保tab重置
                            st.query_params.update({
                                "page": "details",
                                "paper_id": target_paper_id,
                                "back": "details",
                                "from_paper": paper_id,  # 记录来源论文ID
                                "q": keyword,
                                "tab_reset": str(int(time.time()))  # 添加时间戳确保tab重置
                            })
                            st.rerun()
        
        handle_dblclick()

        st_link_analysis(
            elements,
            layout={
                "name": "concentric",
                "animate": "end",
                "nodeDimensionIncludeLabels": False,  # 节点大小不包含标签
                "avoidOverlap": True,  # 避免重叠
                "padding": 20,  # 增加节点间距
                "spacingFactor": 1.2  # 间距因子
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
                "back": "results",  # 源详情页的返回目标
                "q": keyword
            })
        elif back_page == "results":
            # 返回搜索结果页
            st.query_params.update({"page": "results", "q": keyword})
        else:
            # 默认返回搜索页
            st.query_params.update({"page": "search"})
        st.rerun()

def pdf_preview_page():
    """PDF预览页面"""
    paper_id = st.query_params.get("paper_id")
    keyword = st.query_params.get("q", "")
    
    if not paper_id:
        st.warning("未指定文献ID")
        st.query_params.update({"page": "search"})
        st.rerun()
        return

    db = Database()
    paper = db.get_cache_paper(paper_id)
    db.close()
    
    if not paper:
        st.warning("文献信息加载失败")
        st.query_params.update({"page": "search"})
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
            "back": "results",
            "q": keyword
        })
        st.rerun()

if __name__ == "__main__":
    show()
