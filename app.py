import streamlit as st
from ui import search_page, graph_page, analysis_page, favorites_page

def main():
    st.sidebar.title("📚 学术文献管理与分析系统")
    page = st.sidebar.radio("功能选择", ["🔍 搜索文献", "🌐 引用图谱", "📊 数据分析", "⭐ 我的收藏"])

    if page == "🔍 搜索文献":
        search_page.show()
    elif page == "🌐 引用图谱":
        graph_page.show()
    elif page == "📊 数据分析":
        analysis_page.show()
    elif page == "⭐ 我的收藏":
        favorites_page.show()

if __name__ == '__main__':
    main()
