import streamlit as st
import openai
import PyPDF2
import tempfile
import os

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

if "pdf_store_id" not in st.session_state:
    st.session_state.pdf_store_id = None
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

if page == "ChatPDF":
    st.title("📄 ChatPDF - PDF 문서 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

    if uploaded_file:
        # 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        # 텍스트 추출
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()

        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)

            # 벡터 저장소 생성
            vector_store = client.beta.vector_stores.create(name="ChatPDF Vector Store")

            # 파일 업로드 및 연결
            file_obj = client.files.create(file=open(pdf_path, "rb"), purpose="assistants")
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[file_obj.id],
            )

            st.session_state.pdf_store_id = vector_store.id
            st.success("PDF 업로드 완료!")

        except Exception as e:
            st.error(f"PDF 처리 중 오류 발생: {e}")

        os.remove(pdf_path)

    # 채팅 인터페이스
    if st.session_state.pdf_store_id:
        for msg in st.session_state.pdf_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("PDF 내용에 대해 질문해 보세요")

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.pdf_messages.append({"role": "user", "content": user_input})

            try:
                client = openai.OpenAI(api_key=st.session_state.api_key)
                assistant = client.beta.assistants.create(
                    name="PDF Assistant",
                    instructions="업로드된 PDF 내용을 바탕으로 답하세요.",
                    tools=[{"type": "file_search"}],
                    model="gpt-4-0125-preview",
                    tool_resources={
                        "file_search": {"vector_store_ids": [st.session_state.pdf_store_id]}
                    }
                )

                thread = client.beta.threads.create(
                    messages=[{"role": "user", "content": user_input}]
                )

                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id=assistant.id
                )

                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    answer = messages.data[0].content[0].text.value

                    with st.chat_message("assistant"):
                        st.markdown(answer)
                    st.session_state.pdf_messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("응답 처리 실패")

            except Exception as e:
                st.error(f"응답 중 오류: {e}")

    if st.button("Clear"):
        if st.session_state.pdf_store_id:
            try:
                client = openai.OpenAI(api_key=st.session_state.api_key)
                client.beta.vector_stores.delete(st.session_state.pdf_store_id)
                st.session_state.pdf_store_id = None
                st.session_state.pdf_messages = []
                st.success("초기화 완료")
            except Exception as e:
                st.error(f"벡터 저장소 삭제 오류: {e}")

# ----------------------
# ✅ 나머지 페이지는 비워두기
# ----------------------

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

elif page == "도서관 챗봇":
    st.title("도서관 챗봇 (미구현)")
