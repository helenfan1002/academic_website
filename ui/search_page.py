import streamlit as st
from engine.fetcher import fetch_papers
from models.paper import Paper
from datetime import datetime
from typing import List

def show():
    st.header("🔍 学术文献搜索")
    keyword = st.text_input("请输入关键词")

    current_year = datetime.now().year
    DEFAULT_YEAR_RANGE = (2010, current_year)

    col1, col2 = st.columns(2)
            
    with col1:
        st.markdown("**按发布年度过滤**")
        year_range = st.slider(
            "选择年份范围",
            min_value=1900,
            max_value=datetime.now().year,
            value=DEFAULT_YEAR_RANGE,
            key="year_filter"
        )
                
    with col2:
        st.markdown("**按作者姓名过滤**")
        author_name = st.text_input(
            "输入作者姓名",
            placeholder="输入作者全名或姓氏",
            key="author_filter"
        )

    if st.button("搜索"):
        results = fetch_papers(keyword=keyword,                
                year_start=year_range[0],
                year_end=year_range[1],
                author_name=author_name if author_name.strip() else None,
            )
        if not results:
            st.warning("没有找到符合条件的文献")
        else:  
            for paper in results:
                detail_url = f"/detail_page?paper_id={paper.paper_id}"
                st.markdown(
                f"[**{paper.title}**]({detail_url})",
                )

                st.markdown(f"**{paper.title}**  ")
                st.markdown(f"作者：{', '.join(paper.authors)}")
                st.markdown(f"年份：{paper.year} | 被引用：{paper.citation_count}")
                abstract_display = paper.abstract[:200] + '...' if paper.abstract and len(paper.abstract) > 200 else (paper.abstract or "暂无摘要")
                st.markdown(f"**摘要**: {abstract_display}")
                st.markdown("---")
    

   
