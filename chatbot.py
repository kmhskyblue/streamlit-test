import streamlit as st
import openai

# 도서관 규정 내용
PUKYONG_LIB_RULES = """
국립부경대학교 도서관 규정 요약:

1. 이용 대상: 국립부경대학교 구성원 및 허가 받은 외부인.
2. 운영 시간: 학기 중 평일 09:00~21:00, 방학 중 평일 09:00~18:00.
3. 대출 규정:
   - 학부생: 5권 14일
   - 대학원생 및 교직원: 10권 30일
4. 연체 시 연체일수만큼 대출 정지.
5. 자료 분실 시 동일 자료로 변상하거나 도서관 지정 기준에 따른 배상금 납부.
6. 열람실에서는 정숙을 유지해야 하며 음식물 반입 금지.

자세한 사항은 부경대 도서관 홈페이지 참조.
"""

st.set_page_config(page_title="국립부경대학교 도서관 챗봇", layout="centered")

# API 키 입력
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 페이지 선택
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇"])

# 단일 질문 페이지
if page == "질문하기":
    st.title("GPT-4.1 Mini 질문하기")

    user_input = st.text_input("질문을 입력하세요")

    @st.cache_data(show_spinner="답변 생성 중...")
    def get_gpt_response(prompt, api_key):
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    if st.button("질문하기") and user_input and st.session_state.api_key:
        try:
            with st.spinner("응답 생성 중입니다..."):
                answer = get_gpt_response(user_input, st.session_state.api_key)
                st.subheader("GPT의 응답:")
                st.write(answer)
        except Exception as e:
            st.error(f"에러 발생: {e}")
    elif not st.session_state.api_key:
        st.warning("API Key를 입력해주세요.")

# 일반 챗봇 페이지
elif page == "Chat":
    st.title("GPT-4.1 Mini Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    user_message = st.chat_input("메시지를 입력하세요")

    for msg in st.session_state.messages[1:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    if user_message:
        st.session_state.messages.append({"role": "user", "content": user_message})

        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=st.session_state.messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": reply})

            with st.chat_message("assistant"):
                st.markdown(reply)
        except Exception as e:
            st.error(f"에러 발생: {e}")

    if st.button("대화 초기화"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        st.success("대화가 초기화되었습니다.")

# 부경대 도서관 챗봇 페이지
elif page == "도서관 챗봇":
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
