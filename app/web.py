"""
Простой веб-интерфейс для ИИ-ассистента.
Запуск: python -m app.web

Требует: pip install streamlit
Открывается в браузере: http://localhost:8501
"""
from __future__ import annotations

import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ИИ-ассистент техподдержки", page_icon="🤖")

st.title("🤖 ИИ-ассистент технической поддержки")
st.markdown("Задайте ваш вопрос и получите ответ на основе базы знаний.")

# Инициализация чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Ввод сообщения
if prompt := st.chat_input("Ваш вопрос..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Запрос к ИИ
    with st.chat_message("assistant"):
        with st.spinner("Ищу ответ..."):
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
            )
            
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "Ты ИИ-ассистент техподдержки. Отвечай кратко и по делу."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            reply = response.choices[0].message.content
            st.markdown(reply)
    
    st.session_state.messages.append({"role": "assistant", "content": reply})
