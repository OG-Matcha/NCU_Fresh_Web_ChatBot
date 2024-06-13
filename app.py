import streamlit as st
from llm import ConversationBot

def submit():
    st.session_state.user_input = st.session_state.widget
    st.session_state.widget = ''
    process_input()

def process_input():
    st.session_state.chat_log.append(("你", st.session_state.user_input))

    response = st.session_state.generator.start_process(st.session_state.user_input)

    st.session_state.chat_log.append(("AI", response))

    st.session_state.clear_input = True

if "generator" not in st.session_state:
    st.session_state.generator = ConversationBot()

if "chat_log" not in st.session_state:
    st.session_state.chat_log = [("AI", "🧡 哈囉哈囉~ 我是中央大學的吉祥物 - 松鼠🐿️！有什麼問題需要我的幫助嗎？啾啾~ 😊")]

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

st.text_input('請輸入回答', key='widget', on_change=submit)

with st.container(height=500, border=True):
    for speaker, message in st.session_state.chat_log:
        st.write(f"{speaker}: {message}")
