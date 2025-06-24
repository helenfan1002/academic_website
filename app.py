import streamlit as st
from ui import search_page, graph_page, analysis_page, favorites_page

def main():
    last_page = st.session_state.get("page", "")
    page1 = st.Page("ui/search_page.py", title="🔍 搜索文献")
    page2 = st.Page("ui/analysis_page.py", title="📊 数据分析")
    page3 = st.Page("ui/graph_page.py", title="🌐 引用图谱") 
    page4 = st.Page("ui/favorites_page.py", title="⭐ 我的收藏")
            
    pg = st.navigation([page1, page2, page3, page4])

    current_page = pg.url_path
    if current_page != last_page:
        st.session_state.clear()
        st.session_state["page"] = current_page

    pg.run()

if __name__ == '__main__':
    main()
