import streamlit as st
import openai

# 규정 로딩 함수
def load_library_rules():
    with open("rules.txt", "r", encoding="utf-8") as f:
        return f.read()

# 규정 내용 불러오기
PUKYONG_LIB_RULES = load_library_rules()

# 기본 설정
st.set_page_config(page_title="국립부경대학교 도서관 챗봇", layout="centered")

# API Key 입력
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 페이지 선택
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇"])

# 도서관 챗봇 페이지
if page == "도서관 챗봇":
    st.title("국립부경대학교 도서관 챗봇")

    if "lib_messages" not in st.session_state:
        st.session_state.lib_messages = [
            {"role": "system", "content": "너는 국립부경대학교 도서관 규정을 안내하는 도우미야. 사용자 질문에 도서관 규정에 따라 성실히 답변해줘."},
            {"role": "system", "content": f"도서관 규정 내용:\n{PUKYONG_LIB_RULES}"}
        ]

    user_input = st.chat_input("도서관 관련 질문을 입력하세요")

    for msg in st.session_state.lib_messages[2:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    if user_input:
        st.session_state.lib_messages.append({"role": "user", "content": user_input})

        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=st.session_state.lib_messages,
                temperature=0.5
            )
            reply = response.choices[0].message.content.strip()
            st.session_state.lib_messages.append({"role": "assistant", "content": reply})

            with st.chat_message("assistant"):
                st.markdown(reply)

        except Exception as e:
            st.error(f"에러 발생: {e}")

    if st.button("대화 초기화"):
        st.session_state.lib_messages = [
            {"role": "system", "content": "너는 국립부경대학교 도서관 규정을 안내하는 도우미야. 사용자 질문에 도서관 규정에 따라 성실히 답변해줘."},
            {"role": "system", "content": f"도서관 규정 내용:\n{PUKYONG_LIB_RULES}"}
        ]
        st.success("대화가 초기화되었습니다.")
