pip install openai PyPDF2

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
