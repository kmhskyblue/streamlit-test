import streamlit as st
import openai
import PyPDF2
import faiss
import numpy as np
import tempfile
import os
from sklearn.feature_extraction.text import TfidfVectorizer

# ----------------------
# 🔐 OpenAI API Key 설정
# ----------------------
st.sidebar.title("설정")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if api_key:
    st.session_state.api_key = api_key
    openai.api_key = api_key
else:
    st.warning("API Key를 입력하세요.")
    st.stop()

# 규정 불러오기 함수
def load_library_rules():
    with open("rules.txt", "r", encoding="utf-8") as f:
        return f.read()

PUKYONG_LIB_RULES = load_library_rules()

# 공통: 대화 초기화 함수
def reset_chat(state_key, system_prompt=None):
    st.session_state[state_key] = []
    if system_prompt:
        st.session_state[state_key].append({"role": "system", "content": system_prompt})

# ----------------------
# 🗂 페이지 선택
# ----------------------
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇", "ChatPDF"])

# ----------------------
# 📄 ChatPDF 페이지 구현
# ----------------------

if page == "ChatPDF":
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

if page == "ChatPDF":
    st.title("📄 ChatPDF - PDF 문서 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

    if uploaded_file:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        # PDF에서 텍스트 추출
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()

        # 텍스트 벡터화
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text])

        # FAISS를 이용해 벡터 저장소 구성
        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        faiss_index = np.array(vectors.toarray(), dtype=np.float32)
        index.add(faiss_index)

        st.success("PDF 업로드 및 벡터 저장소 구성 완료!")

        # 사용자의 질문 받기
        user_input = st.text_input("PDF 내용에 대해 질문해 보세요")

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.pdf_messages.append({"role": "user", "content": user_input})

            # 사용자의 질문 벡터화
            question_vector = vectorizer.transform([user_input]).toarray().astype(np.float32)

            # FAISS를 통해 유사도 높은 벡터 검색
            D, I = index.search(question_vector, k=1)
            best_match = text  # 가장 가까운 문서

            # OpenAI 모델을 사용하여 질문에 답변
            response = openai.Completion.create(
                model="text-davinci-003",  # 또는 GPT-4 사용
                prompt=f"Q: {user_input}\nA: {best_match}",
                max_tokens=150
            )

            answer = response.choices[0].text.strip()

            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.pdf_messages.append({"role": "assistant", "content": answer})

        # 임시 파일 삭제
        os.remove(pdf_path)

    # 벡터 스토어 초기화 (Clear 버튼)
    if st.button("Clear"):
        st.session_state.pdf_messages = []
        st.success("대화 및 벡터 저장소 초기화 완료")

# 질문하기 페이지 (간단한 질문 인터페이스)
elif page == "질문하기":
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
