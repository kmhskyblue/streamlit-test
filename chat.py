import streamlit as st
import openai

st.set_page_config(page_title="GPT-4.1 Mini 웹 챗봇", layout="centered")

# 기본 API 키 설정
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("🔑 OpenAI API Key 입력", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 사이드바 페이지 선택
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat"])

### ----------------------------------------
### 1️⃣ 질문하기 페이지
### ----------------------------------------
if page == "질문하기":
    st.title("GPT-4.1 Mini - 단일 질문")

    user_input = st.text_input("질문을 입력하세요")

    @st.cache_data(show_spinner="답변을 생성 중입니다...")
    def get_gpt_response(prompt, api_key):
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",  # 또는 최신 gpt-4o
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    if st.button("질문하기") and user_input and st.session_state.api_key:
        try:
            with st.spinner("GPT가 생각 중입니다..."):
                answer = get_gpt_response(user_input, st.session_state.api_key)
                st.markdown("####GPT의 응답:")
                st.write(answer)
        except Exception as e:
            st.error(f"에러 발생: {e}")
    elif not st.session_state.api_key:
        st.warning("API Key를 먼저 입력해주세요.")

### ----------------------------------------
### 2️⃣ Chat 페이지
### ----------------------------------------
elif page == "Chat":
    st.title("GPT-4.1 Mini ChatBot")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    # 사용자 메시지 입력
    user_message = st.chat_input("메시지를 입력하세요")
    
    # 이전 메시지 출력
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            with st.chat_message("사용자"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("GPT"):
                st.markdown(msg["content"])

    # 새 메시지 전송
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

            with st.chat_message("GPT"):
                st.markdown(reply)

        except Exception as e:
            st.error(f"에러 발생: {e}")

    # Clear 버튼
    if st.button("대화 초기화"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        st.experimental_rerun()
