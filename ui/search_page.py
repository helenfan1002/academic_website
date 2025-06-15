import streamlit as st
from engine.fetcher import fetch_papers
from models.paper import Paper

def show():
    st.header("🔍 学术文献搜索")
    keyword = st.text_input("请输入关键词")
    if st.button("搜索"):
        results = fetch_papers(keyword)
        for paper in results:
            st.markdown(f"**{paper.title}**  ")
            st.markdown(f"作者：{', '.join(paper.authors)}")
            st.markdown(f"年份：{paper.year} | 被引用：{paper.citation_count}")
            abstract_display = paper.abstract[:200] + '...' if paper.abstract and len(paper.abstract) > 200 else (paper.abstract or "暂无摘要")
            st.markdown(f"**摘要**: {abstract_display}")
            st.markdown("---")

