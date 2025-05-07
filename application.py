import streamlit as st
import openai

# 페이지 설정
st.set_page_config(page_title="GPT-4.1 Mini 웹 챗봇", layout="centered")

st.title("GPT-4.1 Mini 웹 챗봇")

# API Key 입력 및 저장
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.text_input("OpenAI API Key를 입력하세요", type="password", value=st.session_state.api_key)

if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 질문 입력
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

# 응답 출력
if st.button("질문하기") and user_input and st.session_state.api_key:
    try:
        with st.spinner("GPT가 생각 중입니다..."):
            answer = get_gpt_response(user_input, st.session_state.api_key)
            st.markdown("#### GPT의 응답:")
            st.write(answer)
    except Exception as e:
        st.error(f"에러 발생: {e}")
elif not st.session_state.api_key:
    st.warning("API Key를 먼저 입력해주세요.")

