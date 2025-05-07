import streamlit as st
import openai
import PyPDF2
import tempfile
import os

# ChatPDF용 전역 세션 상태
if "pdf_store_id" not in st.session_state:
    st.session_state.pdf_store_id = None
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇", "ChatPDF"])

# 페이지 추가: ChatPDF
if page == "ChatPDF":
    st.title("ChatPDF - PDF 문서 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일 업로드", type="pdf")

    if uploaded_file and st.session_state.api_key:
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

        # OpenAI에 업로드
        try:
            client = openai.OpenAI(api_key=st.session_state.api_key)

            # 벡터 저장소 생성
            vector_store = client.beta.vector_stores.create(name="ChatPDF Vector Store")

            # 파일 업로드 후 벡터 스토어에 추가
            file_obj = client.files.create(file=open(pdf_path, "rb"), purpose="assistants")
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[file_obj.id],
            )

            st.session_state.pdf_store_id = vector_store.id
            st.success("PDF 업로드 및 벡터 저장소 구성 완료!")

        except Exception as e:
            st.error(f"PDF 처리 중 오류 발생: {e}")

        # 임시 파일 삭제
        os.remove(pdf_path)

    # 대화 인터페이스
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
                # Assistant 임시 생성 및 파일 연결
                client = openai.OpenAI(api_key=st.session_state.api_key)
                assistant = client.beta.assistants.create(
                    name="PDF Assistant",
                    instructions="업로드된 PDF 내용을 기반으로 질문에 답하세요.",
                    tools=[{"type": "file_search"}],
                    model="gpt-4-0125-preview",
                    tool_resources={
                        "file_search": {"vector_store_ids": [st.session_state.pdf_store_id]}
                    }
                )

                # Thread 생성
                thread = client.beta.threads.create(
                    messages=[{"role": "user", "content": user_input}]
                )

                # 실행 및 응답
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
                    st.error("응답 처리 중 오류가 발생했습니다.")

            except Exception as e:
                st.error(f"오류 발생: {e}")

    # 벡터 스토어 및 대화 초기화
    if st.button("Clear"):
        if st.session_state.pdf_store_id:
            try:
                client = openai.OpenAI(api_key=st.session_state.api_key)
                client.beta.vector_stores.delete(st.session_state.pdf_store_id)
                st.session_state.pdf_store_id = None
                st.session_state.pdf_messages = []
                st.success("벡터 저장소 및 대화 초기화 완료.")
            except Exception as e:
                st.error(f"벡터 저장소 삭제 실패: {e}")

# 규정 불러오기 함수
def load_library_rules():
    with open("rules.txt", "r", encoding="utf-8") as f:
        return f.read()

PUKYONG_LIB_RULES = load_library_rules()

# 페이지 설정
st.set_page_config(page_title="GPT 챗봇 앱", layout="centered")

# API Key 입력 및 저장
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key_input:
    st.session_state.api_key = api_key_input
    openai.api_key = api_key_input

# 페이지 선택
page = st.sidebar.radio("페이지 선택", ["질문하기", "Chat", "도서관 챗봇"])

# 공통: 대화 초기화 함수
def reset_chat(state_key, system_prompt=None):
    st.session_state[state_key] = []
    if system_prompt:
        st.session_state[state_key].append({"role": "system", "content": system_prompt})

# 질문하기 페이지 (간단한 질문 인터페이스)
if page == "질문하기":
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
