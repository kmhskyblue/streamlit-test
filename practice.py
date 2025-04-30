import streamlit as st
import openai

# 페이지 설정
st.set_page_config(page_title="GPT-4.1 Mini Chat", layout="centered")

# 제목
st.title("GPT-4.1 Mini 질문 응답기")

# OpenAI API 키 입력 받기
api_key = st.text_input("OpenAI API Key를 입력하세요:", type="password")

# 사용자 질문 입력
question = st.text_area("질문을 입력하세요:")

# 버튼 클릭 시 GPT에게 질문
if st.button("GPT에게 물어보기"):
    if not api_key:
        st.warning("API 키를 입력해주세요.")
    elif not question.strip():
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # OpenAI API 키 설정
            openai.api_key = api_key

            # GPT-4.1 Mini 모델 호출
            with st.spinner("GPT가 응답을 생성 중입니다..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",  # 실제 사용 가능 모델명 확인 필요
                    messages=[
                        {"role": "user", "content": question}
                    ],
                    temperature=0.7,
                )

                # 결과 출력
                answer = response.choices[0].message["content"]
                st.success("응답 완료")
                st.markdown("GPT 응답:")
                st.write(answer)

        except Exception as e:
            st.error(f"오류 발생: {e}")
