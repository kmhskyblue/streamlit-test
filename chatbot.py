import streamlit as st
import openai

# 규정 불러오기 함수
def load_library_rules():
    with open("rules.txt", "r", encoding="utf-8") as f:
        return f.read()

PUKYONG_LIB_RULES = load_library_rules()

# 페이지 설정
st.set_page_config(page_title="GPT 챗봇 앱", layout="centered")

# API Key 입력 및 저장
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 페이지 선택
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇"])

# 공통: 대화 초기화 함수
def reset_chat(state_key, system_prompt=None):
    st.session_state[state_key] = []
    if system_prompt:
        st.session_state[state_key].append({"role": "system", "content": system_prompt})

# 질문하기 페이지 (간단한 질문 인터페이스)
if page == "질문하기":
    st.title("질문하기")
    question = st.text_input("무엇이든 질문하세요:")

    if question and st.session_state.api_key:
        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[{"role": "user", "content": question}]
            )
            st.markdown(f"**답변:** {response.choices[0].message.content.strip()}")
        except Exception as e:
            st.error(f"에러 발생: {e}")

# Chat 페이지 (자유로운 채팅)
elif page == "Chat":
    st.title("Chat GPT")

    if "chat_messages" not in st.session_state:
        reset_chat("chat_messages")

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("메시지를 입력하세요")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=st.session_state.chat_messages
            )
            reply = response.choices[0].message.content.strip()

            with st.chat_message("assistant"):
                st.markdown(reply)

            st.session_state.chat_messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"에러 발생: {e}")

    if st.button("대화 초기화"):
        reset_chat("chat_messages")
        st.success("대화가 초기화되었습니다.")

# 도서관 챗봇 페이지
elif page == "도서관 챗봇":
    st.title("국립부경대학교 도서관 챗봇")

    if "lib_messages" not in st.session_state:
        reset_chat("lib_messages")
        st.session_state.lib_messages.append(
            {"role": "system", "content": "너는 국립부경대학교 도서관 규정을 안내하는 도우미야. 사용자 질문에 도서관 규정에 따라 성실히 답변해줘."}
        )
        st.session_state.lib_messages.append(
            {"role": "system", "content": f"도서관 규정 내용:\n{PUKYONG_LIB_RULES}"}
        )

    for msg in st.session_state.lib_messages[2:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    user_input = st.chat_input("도서관 관련 질문을 입력하세요")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.lib_messages.append({"role": "user", "content": user_input})

        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=st.session_state.lib_messages,
                temperature=0.5
            )
            reply = response.choices[0].message.content.strip()

            with st.chat_message("assistant"):
                st.markdown(reply)

            st.session_state.lib_messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"에러 발생: {e}")

    if st.button("대화 초기화"):
        reset_chat("lib_messages")
        st.session_state.lib_messages.append(
            {"role": "system", "content": "너는 국립부경대학교 도서관 규정을 안내하는 도우미야. 사용자 질문에 도서관 규정에 따라 성실히 답변해줘."}
        )
        st.session_state.lib_messages.append(
            {"role": "system", "content": f"도서관 규정 내용:\n{PUKYONG_LIB_RULES}"}
        )
        st.success("대화가 초기화되었습니다.")
