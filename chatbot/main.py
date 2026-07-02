import streamlit as st
from pathlib import Path
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_teddynote.prompts import load_prompt
from dotenv import load_dotenv
from langsmith import Client

# API KEY 정보로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")

st.title("나만의 ChatGPT 💬")

client = Client()

# 처음 1번만 실행하기 위한 코드
if "messages" not in st.session_state:
    # 대화 기록을 저장 하기 위한 용도로 생성.
    st.session_state["messages"] = []

# 사이드바 생성
with st.sidebar:
    clear_btn = st.button("대화기록 초기화")

    selected_prompt = st.selectbox(
        "프롬프트를 선택해 주세요",
        ("기본모드", "만두 레시피", "요약"), index=0
    )


if clear_btn:
        st.session_state["messages"] = []

# 이전 대화를 출력
def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)
        
# 새로운 메시지를 추가
def add_message(role, message):
    st.session_state["messages"].append(ChatMessage(role=role, content=message))



# 체인 생성
def create_chain(prompt_type):
    # prompt | llm | output_parser

    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 친절한 ai 어시스턴트이다. 다음의 질문에 간결하게 답변해주세요"),
            ("user", "#Question:\n{question}"),
        ]
    )


    if prompt_type == "만두 레시피":
        # Windows 사용자 only: 인코딩을 cp949로 설정
        prompt = load_prompt("prompts/recipe.yaml", encoding="utf-8")
    elif prompt_type == "요약":
        # 요약 프롬프트
        prompt = client.pull_prompt("teddynote/chain-of-density-map-korean")

            
    # Google Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    # 출력 파서
    output_parser = StrOutputParser()

    # 체인 생성
    chain = prompt | llm | output_parser

    return chain

print_messages()

# 사용자의 입력
user_input = st.chat_input("질문 해주세요!")


if user_input:
    # 사용자의 입력
    st.chat_message("user").write(user_input)
    # chain 을 생성
    chain = create_chain(selected_prompt)

    # 스트리밍 처리
    response = chain.stream({"question": user_input})
    with st.chat_message("assistant"):
        # 빈 공간(컨테이너)를 만들어서, 여기에 토큰을 스트리밍 출력한다. 
        container = st.empty()
        
        ai_answer = ""
        for token in response:
            ai_answer += token
            container.markdown(ai_answer)  # 토큰 스트리밍 출력


    # 대화기록을 저장한다. 
    st.session_state["messages"].append(ChatMessage(role= "user", content=user_input))
    st.session_state["messages"].append(ChatMessage(role= "assistant", content=ai_answer))
