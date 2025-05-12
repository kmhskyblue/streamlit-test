import streamlit as st
import openai import OpenAI
import PyPDF2
import numpy as np

from typing import List

st.set_page_config(page_title="GPT 웹앱 with PDF Chat", layout="wide")

# -------------------------------
# API Key 입력
# -------------------------------
st.sidebar.title("🔐 API Key 설정")
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")
if api_key_input:
    st.session_state.api_key = api_key_input

# -------------------------------
# 세션 상태 초기화
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "당신은 친절한 AI 챗봇입니다."}
    ]
if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []
if "pdf_embeddings" not in st.session_state:
    st.session_state.pdf_embeddings = []

# -------------------------------
# 공통 함수
# -------------------------------
def extract_text_from_pdf(file) -> str:
    pdf = PyPDF2.PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in pdf.pages)

def chunk_text(text: str, max_tokens=500) -> List[str]:
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk + sentence) < max_tokens:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def embed_chunks(chunks: List[str], api_key: str):
    openai.api_key = api_key
    response = openai.Embedding.create(
        input=chunks,
        model="text-embedding-3-small"
    )
    return [res["embedding"] for res in response["data"]]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_similar_chunks(query, chunks, embeddings, api_key, k=3):
    openai.api_key = api_key
    query_embedding = openai.Embedding.create(
        input=[query],
        model="text-embedding-3-small"
    )["data"][0]["embedding"]
    sims = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(sims)[::-1][:k]
    return "\n\n".join([chunks[i] for i in top_indices])

def ask_pdf_bot(query, context, api_key):
    messages = [
        {"role": "system", "content": "다음 문서를 참고하여 질문에 답하세요:\n" + context},
        {"role": "user", "content": query}
    ]
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# -------------------------------
# 탭 구성
# -------------------------------
tab1, tab2, tab3 = st.tabs(["🧠 Ask GPT", "💬 Chat GPT", "📄 ChatPDF"])

# 1. Ask GPT
with tab1:
    st.header("🧠 GPT에 질문하기")

    @st.cache_data(show_spinner=False)
    def get_single_response(prompt, api_key):
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "당신은 친절한 AI 비서입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    if not st.session_state.api_key:
        st.warning("API Key를 입력하세요.")
    else:
        question = st.text_input("질문을 입력하세요")
        if question:
            with st.spinner("GPT 응답 생성 중..."):
                answer = get_single_response(question, st.session_state.api_key)
                st.markdown("### ✅ GPT 응답")
                st.write(answer)

# 2. Chat GPT
with tab2:
    st.header("💬 GPT와 대화하기")
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = [
                {"role": "system", "content": "당신은 친절한 AI 챗봇입니다."}
            ]
            st.rerun()

    if not st.session_state.api_key:
        st.warning("API Key를 입력하세요.")
    else:
        user_input = st.chat_input("메시지를 입력하세요")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("GPT 응답 중..."):
                openai.api_key = st.session_state.api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=st.session_state.chat_history
                )
                reply = response.choices[0].message.content.strip()
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

        for msg in st.session_state.chat_history[1:]:
            st.chat_message(msg["role"]).write(msg["content"])

# 3. ChatPDF
with tab3:
    st.header("📄 ChatPDF: PDF 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])
    if st.button("🧹 Clear PDF Data"):
        st.session_state.pdf_chunks = []
        st.session_state.pdf_embeddings = []
        st.success("PDF 데이터 초기화 완료!")

    if uploaded_file and st.session_state.api_key:
        with st.spinner("PDF 분석 중..."):
            text = extract_text_from_pdf(uploaded_file)
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks, st.session_state.api_key)

            st.session_state.pdf_chunks = chunks
            st.session_state.pdf_embeddings = embeddings
            st.success(f"{len(chunks)}개 문단 분석 완료!")

    if st.session_state.pdf_chunks:
        query = st.text_input("PDF에 대해 질문하세요")
        if query:
            with st.spinner("응답 생성 중..."):
                context = search_similar_chunks(
                    query,
                    st.session_state.pdf_chunks,
                    st.session_state.pdf_embeddings,
                    st.session_state.api_key
                )
                answer = ask_pdf_bot(query, context, st.session_state.api_key)
                st.markdown("### 📄 GPT 응답")
                st.write(answer)
