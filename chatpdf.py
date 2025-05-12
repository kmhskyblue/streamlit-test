import streamlit as st
from openai import OpenAI
import PyPDF2
import numpy as np
from typing import List

st.set_page_config(page_title="GPT 웹앱", layout="wide")

# --------------------------
# API Key 입력
# --------------------------
st.sidebar.title("🔐 API Key 설정")
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")
if api_key_input:
    st.session_state.api_key = api_key_input

# --------------------------
# 세션 상태 초기화
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "당신은 친절한 AI 챗봇입니다."}]
if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []
if "pdf_embeddings" not in st.session_state:
    st.session_state.pdf_embeddings = []

# --------------------------
# 유틸 함수들
# --------------------------
def get_client():
    return OpenAI(api_key=st.session_state.api_key)

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def chunk_text(text: str, max_tokens=500) -> List[str]:
    sentences = text.split(". ")
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk + sentence) < max_tokens:
            chunk += sentence + ". "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + ". "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def embed_chunks(chunks: List[str]):
    client = get_client()
    response = client.embeddings.create(
        input=chunks,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_similar_chunks(query: str, chunks: List[str], embeddings: List[List[float]], k=3):
    client = get_client()
    query_embedding = client.embeddings.create(
        input=[query],
        model="text-embedding-3-small"
    ).data[0].embedding
    similarities = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(similarities)[::-1][:k]
    return "\n\n".join([chunks[i] for i in top_indices])

def ask_pdf_bot(query: str, context: str):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "다음 문서를 참고하여 질문에 답하세요:\n" + context},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content.strip()

def get_single_response(prompt: str):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "당신은 친절한 AI 비서입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# --------------------------
# 탭 UI 구성
# --------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🧠 Ask GPT", "💬 Chat", "📄 ChatPDF", "📚 Chatbot"])

# --------------------------
# Tab 1: Ask GPT
# --------------------------
with tab1:
    st.header("🧠 GPT에 단일 질문")
    if not st.session_state.api_key:
        st.warning("API Key를 먼저 입력하세요.")
    else:
        user_prompt = st.text_input("질문을 입력하세요:")
        if user_prompt:
            with st.spinner("GPT 응답 생성 중..."):
                response = get_single_response(user_prompt)
                st.markdown("### ✅ GPT 응답")
                st.write(response)

# --------------------------
# Tab 2: Chat
# --------------------------
with tab2:
    st.header("💬 GPT와 대화하기")
    if not st.session_state.api_key:
        st.warning("API Key를 먼저 입력하세요.")
    else:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🧹 Clear"):
                st.session_state.chat_history = [{"role": "system", "content": "당신은 친절한 AI 챗봇입니다."}]
                st.rerun()

        user_msg = st.chat_input("메시지를 입력하세요")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.spinner("응답 중..."):
                client = get_client()
                res = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=st.session_state.chat_history
                )
                reply = res.choices[0].message.content.strip()
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

        for msg in st.session_state.chat_history[1:]:
            st.chat_message(msg["role"]).write(msg["content"])

# --------------------------
# Tab 3: ChatPDF
# --------------------------
with tab3:
    st.header("📄 PDF 업로드 후 질문하기")

    uploaded_file = st.file_uploader("PDF 파일 업로드", type="pdf")
    if st.button("🧹 Clear PDF"):
        st.session_state.pdf_chunks = []
        st.session_state.pdf_embeddings = []
        st.success("PDF 데이터가 초기화되었습니다.")

    if uploaded_file and st.session_state.api_key:
        with st.spinner("PDF 분석 중..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            chunks = chunk_text(raw_text)
            embeddings = embed_chunks(chunks)

            st.session_state.pdf_chunks = chunks
            st.session_state.pdf_embeddings = embeddings
            st.success(f"{len(chunks)}개의 청크로 분할 및 임베딩 완료!")

    if st.session_state.pdf_chunks:
        query = st.text_input("PDF 내용 기반 질문을 입력하세요:")
        if query:
            with st.spinner("응답 생성 중..."):
                context = search_similar_chunks(query, st.session_state.pdf_chunks, st.session_state.pdf_embeddings)
                answer = ask_pdf_bot(query, context)
                st.markdown("### 📄 GPT 응답")
                st.write(answer)

# 기존 세션 상태 유지
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chatbot_history" not in st.session_state:
    st.session_state.chatbot_history = []

# 규정 내용
pknu_library_rules = """
제1조(목적) 이 규정은 국립부경대학교 도서관(이하 "도서관"이라 한다)의 발전계획 수립 및 시행, 직원 배치, 학술정보자료의 확보 및 이용·관리 등에 필요한 사항을 규정함을 목적으로 한다.

제2조(임무) 도서관은 국내외의 학술정보자료를 수집·정리·보존하여 이를 교수, 학생 및 지역 주민의 연구·학습에 제공하는 것을 임무로 한다.

제3조(조직) 도서관에는 도서관장과 사서직원 및 그 밖의 직원이 두어지며, 도서관장은 도서관의 업무를 총괄하고 도서관 운영위원회를 둔다.

제4조(발전계획) 도서관장은 5년마다 발전계획을 수립하고 매년 시행계획을 수립한다.

제5조(이용자격) 본교 교직원, 학생 및 특별한 허가를 받은 외부인이 이용할 수 있다.

제6조(자료대출)
① 학부생은 5책 14일간 대출할 수 있다.
② 대학원생은 10책 30일간, 교직원은 20책 60일간 대출 가능하다.

제7조(휴관일) 도서관의 휴관일은 일요일, 국정공휴일, 임시휴관일(관장이 지정)이다.
"""

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🧠 Ask GPT", "💬 Chat", "📄 ChatPDF", "📚 Chatbot"])

# Chatbot 탭
with tab4:
    st.header("📚 국립부경대학교 도서관 챗봇")

    if not st.session_state.api_key:
        st.warning("API Key를 입력하세요.")
    else:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🧹 Clear"):
                st.session_state.chatbot_history = []
                st.rerun()

        user_q = st.chat_input("도서관에 대해 궁금한 점을 입력하세요")
        if user_q:
            client = OpenAI(api_key=st.session_state.api_key)

            st.session_state.chatbot_history.append({"role": "user", "content": user_q})

            with st.spinner("답변 생성 중..."):
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": f"다음 국립부경대학교 도서관 규정을 참고하여 질문에 답변하세요:\n{pknu_library_rules}"},
                        *st.session_state.chatbot_history
                    ]
                )
                answer = response.choices[0].message.content.strip()
                st.session_state.chatbot_history.append({"role": "assistant", "content": answer})

        for msg in st.session_state.chatbot_history:
            st.chat_message(msg["role"]).write(msg["content"])
