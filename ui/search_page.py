import streamlit as st
from engine.fetcher import fetch_papers
from models.paper import Paper
from datetime import datetime
from typing import List


# def show():
#     st.header("🔍 学术文献搜索")
#     keyword = st.text_input("请输入关键词")

#     current_year = datetime.now().year
#     DEFAULT_YEAR_RANGE = (2010, current_year)

#     col1, col2 = st.columns(2)
            
#     with col1:
#         st.markdown("**按发布年度过滤**")
#         year_range = st.slider(
#             "选择年份范围",
#             min_value=1900,
#             max_value=datetime.now().year,
#             value=DEFAULT_YEAR_RANGE,
#             key="year_filter"
#         )
                
#     with col2:
#         st.markdown("**按作者姓名过滤**")
#         author_name = st.text_input(
#             "输入作者姓名",
#             placeholder="输入作者全名或姓氏",
#             key="author_filter"
#         )

#     if st.button("搜索"):
#         results = fetch_papers(keyword=keyword,                
#                 year_start=year_range[0],
#                 year_end=year_range[1],
#                 author_name=author_name if author_name.strip() else None,
#             )
#         if not results:
#             st.warning("没有找到符合条件的文献")
#         else:  
#             for paper in results:

#                 st.markdown(f"**{paper.title}**  ")
#                 st.markdown(f"作者：{', '.join(paper.authors)}")
#                 st.markdown(f"年份：{paper.year} | 被引用：{paper.citation_count}")
#                 abstract_display = paper.abstract[:200] + '...' if paper.abstract and len(paper.abstract) > 200 else (paper.abstract or "暂无摘要")
#                 st.markdown(f"**摘要**: {abstract_display}")
#                 detail_url = f"/ui/details_page?paper_id={paper.paper_id}"
#                 if st.button("前往详情页"):
#                     st.switch_page("pages/detail_page.py")
#                 st.markdown("---")



# 考虑搜索页面共有3个主要界面：搜索主界面、搜索结果界面、详情页
# 用st.session_state来管理页面状态：
# st.session_state用来存储一些全局状态信息，在Streamlit应用中可以跨页面共享数据。
# 这里我们用它来存储当前页面状态（page_state）和搜索结果（search_results）。
# search_bar、search_results、paper_details
def show():
    # 入口检查page_state
    # 如果没有page_state，说明是第一次访问，设置为search_bar并重新运行
    page_state = st.session_state.get("page_state", "")
    if not page_state:
        st.session_state["page_state"] = "search_bar"
        st.rerun()
    st.header("🔍 学术文献搜索")
    # 根据page_state调用不同的函数
    # 这里使用match-case语句来处理不同的页面状态
    match page_state:
        case "search_bar":
            search_bar()
        case "search_results":
            search_results()
        case "paper_details":
            paper_details()

def search_bar(value: str = "", year_range: None = None, author_name: str = ""):
    keyword = st.text_input("请输入关键词", value=value)
    if st.button("搜索"):
        results = fetch_papers(keyword=keyword)
        if not results:
            st.warning("没有找到符合条件的文献")
        else:  
            # 存储搜索结果到session_state, 包括 search_keyword, search_results
            # 设置 page_state 为 search_results, 再次rerun就会调用 search_results 函数
            st.session_state["search_results"] = results
            st.session_state["page_state"] = "search_results"
            st.session_state["search_keyword"] = keyword
            st.rerun()

def search_results():
    search_bar(value=st.session_state.get("search_keyword", ""))

    # 获取搜索结果, 从 session_state 中获取
    results: List[Paper] = st.session_state.get("search_results", [])
    if not results:
        st.warning("没有搜索结果，请尝试更换关键词搜索")
        return

    # 分页显示搜索结果
    results = paginate(results, items_per_page=5, key="search_results_pagination")
    for paper in results:
        st.markdown(f"**{paper.title}**  ")
        st.markdown(f"作者：{', '.join(paper.authors)}")
        st.markdown(f"年份：{paper.year} | 被引用：{paper.citation_count}")
        abstract_display = paper.abstract[:50] + '...' if paper.abstract and len(paper.abstract) > 50 else (paper.abstract or "暂无摘要")
        st.markdown(f"**摘要**: {abstract_display}")
        
        if st.button("前往详情页", key=paper.paper_id):
            # 将选中的文献详情存入 session_state
            # 并设置 page_state 为 paper_details, 再次rerun就会调用paper_details 函数
            st.session_state["paper_details"] = paper
            st.session_state["page_state"] = "paper_details"
            st.rerun()
        
        st.markdown("---")

def paper_details():
    paper: Paper = st.session_state.get("paper_details", None)
    if not paper:
        st.warning("没有选择文献详情，请先在搜索结果中选择一篇文献")
        return

    st.markdown(f"**{paper.title}**  ")
    st.markdown(f"作者：{', '.join(paper.authors)}")
    st.markdown(f"年份：{paper.year} | 被引用：{paper.citation_count}")
    st.markdown(f"**摘要**: {paper.abstract or '暂无摘要'}")
    
    if st.button("返回搜索结果"):
        # 返回搜索结果页面，清除 paper_details
        # 并设置 page_state 为 search_results, 再次rerun就会调用search_results 函数
        st.session_state["page_state"] = "search_results"
        st.session_state.pop("paper_details")
        st.rerun()

def paginate(data, items_per_page=5, key="pagination"):
    total_items = len(data)
    total_pages = (total_items - 1) // items_per_page + 1
    current_page = st.session_state.get(key, 1)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 上一页", disabled=current_page <= 1):
            st.session_state[key] = current_page - 1
            st.rerun()
    with col3:
        if st.button("下一页 ➡️", disabled=current_page >= total_pages):
            st.session_state[key] = current_page + 1
            st.rerun()
    with col2:
        st.markdown(f"<center>第 {current_page} 页 / 共 {total_pages} 页</center>", unsafe_allow_html=True)

    start = (current_page - 1) * items_per_page
    end = start + items_per_page
    return data[start:end]

if __name__ == "__main__":
    show()
