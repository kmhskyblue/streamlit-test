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
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chatbot_history" not in st.session_state:
    st.session_state.chatbot_history = []

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
    # 빈 문자열, None 제거
    clean_chunks = [chunk for chunk in chunks if isinstance(chunk, str) and chunk.strip()]
    if not clean_chunks:
        raise ValueError("입력할 유효한 텍스트 청크가 없습니다.")
    response = client.embeddings.create(
        input=clean_chunks,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_similar_chunks(query: str, chunks: List[str], embeddings: List[List[float]], k=3):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query는 비어있거나 유효하지 않습니다.")
    
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
            if st.button("🧹 Clear", key="clear_button_chat"):
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
    if st.button("🧹 Clear PDF", key="clear_button_chatpdf"):
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

def load_rules():
    with open("library_rules.txt", "r", encoding="utf-8") as f:
        return f.read()

library_rules = load_rules()

# --------------------------
# Tab 4: Chatbot
# --------------------------
with tab4:
    st.header("📚 국립부경대학교 도서관 챗봇")

    if not st.session_state.api_key:
        st.warning("API Key를 먼저 입력하세요.")
    else:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🧹 Clear", key="clear_button_chatbot"):
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
                        {"role": "system", "content": f"다음 국립부경대학교 도서관 규정을 참고하여 질문에 답변하세요:\n{library_rules}"},
                        *st.session_state.chatbot_history
                    ]
                )
                answer = response.choices[0].message.content.strip()
                st.session_state.chatbot_history.append({"role": "assistant", "content": answer})

        for msg in st.session_state.chatbot_history:
            st.chat_message(msg["role"]).write(msg["content"])
