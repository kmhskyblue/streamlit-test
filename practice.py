import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="GPT-4.1 Mini Chat", layout="centered")

# 제목
st.title("GPT-4.1 Mini 질문 응답기")

# API 키 입력
api_key = st.text_input("OpenAI API Key를 입력하세요:", type="password")

# 질문 입력
question = st.text_area("질문을 입력하세요:")

# 버튼 누르면 실행
if st.button("GPT에게 물어보기"):
    if not api_key:
        st.warning("API 키를 입력해주세요.")
    elif not question.strip():
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # OpenAI 클라이언트 생성
            client = OpenAI(api_key=api_key)

            with st.spinner("GPT가 응답을 생성 중입니다..."):
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",  # 또는 gpt-4.1-mini로 변경
                    messages=[{"role": "user", "content": question}],
                    temperature=0.7,
                )

                answer = response.choices[0].message.content
                st.success("응답 완료")
                st.markdown("GPT 응답:")
                st.write(answer)

        except Exception as e:
            st.error(f"오류 발생: {e}")

