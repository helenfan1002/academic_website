import streamlit as st
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle

st.set_page_config(layout="wide")

elements = {
    "nodes": [
        {"data": {"id": 1, "label": "POST", "content": "智能巡检机器人在变电运维中的应用分析"}},
        {"data": {"id": 2, "label": "POST", "content": "变电运维工作中智能巡检机器人的应用"}},
        {"data": {"id": 3, "label": "POST", "content": "集成电路应用"}},
        {"data": {"id": 4, "label": "POST", "content": "智能巡检机器人在变电运维工作中的应用研究"}},
    ],
    "edges": [
        {"data": {"id": 5, "label": "QUOTES", "source": 1, "target": 2}},
        {"data": {"id": 6, "label": "QUOTES", "source": 1, "target": 3}},
        {"data": {"id": 7, "label": "QUOTES", "source": 1, "target": 4}},
    ],
}

node_styles = [
    NodeStyle("POST", "#2A629A", "content", "description"),
]

edge_styles = [
    EdgeStyle("QUOTES", caption='label', directed=True),
]

layout = {"name":"cose","animate":"end","nodeDimensionIncludeLabels":False}
st.markdown("##: Example")
st_link_analysis(elements, layout, node_styles, edge_styles)
