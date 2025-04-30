import streamlit as st
from openai import Openai

st.set_page_config(page_title="GPT-4.1 Mini Chat", layout="centered")

st.title("GPT-4.1 Mini 질문 응답기")

# API Key 입력 받기 (비밀번호 타입으로)
api_key = st.text_input("OpenAI API Key를 입력하세요:", type="password")

# 질문 입력
question = st.text_area("질문을 입력하세요:")

# 버튼 클릭 시 실행
if st.button("GPT에게 물어보기"):
    if not api_key:
        st.warning("API 키를 입력해주세요.")
    elif not question.strip():
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # OpenAI API 설정
            openai.api_key = api_key

            # GPT-4.1 Mini 모델로 요청
            with st.spinner("GPT가 응답을 생성 중입니다..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",  # gpt-4.1-mini가 정식 모델명일 경우 변경
                    messages=[
                        {"role": "user", "content": question}
                    ],
                    temperature=0.7,
                )

                answer = response.choices[0].message["content"]
                st.success("응답 완료")
                st.markdown(f"GPT 응답:\n\n{answer}")

        except Exception as e:
            st.error(f"오류 발생: {e}")
