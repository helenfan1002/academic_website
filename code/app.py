import streamlit as st

def main():
    st.set_page_config(layout="wide")
    last_page = st.session_state.get("page", "")
    page1 = st.Page("ui/search_page.py", title="🔍 搜索文献")
    page2 = st.Page("ui/favorites_page.py", title="⭐ 我的收藏")
    
    pg = st.navigation([page1, page2])

    current_page = pg.url_path
    if current_page != last_page:
        st.session_state.clear()
        st.session_state["page"] = current_page

    pg.run()

if __name__ == '__main__':
    main()
