import traceback
import chromadb
import ollama
import streamlit as st

class AI:
    def __init__(self):
        try:
            db = chromadb.PersistentClient(
                host=os.getenv("CHROMADB_HOST"),
                port=os.getenv("CHROMADB_PORT"),
                user=os.getenv("CHROMADB_USER"),
                password=os.getenv("CHROMADB_PASS")
            )
            self.collection = db.get_or_create_collection("listing_rules")
        except Exception as e:
            st.error("Failed to initialize ChromaDB client.")
            st.error(traceback.format_exc())

    def query(self, q, top=10):
        res_db = self.collection.query(query_texts=[q])["documents"][0][0:top]
        context = ' '.join(res_db).replace("\n", " ")
        return context

    def respond(self, lst_messages, model="phi3", use_knowledge=False):
        q = lst_messages[-1]["content"]
        context = self.query(q)

        if use_knowledge:
            prompt = f"Give the most accurate answer using your knowledge and the following additional information:\n{context}"
        else:
            prompt = f"Give the most accurate answer using only the following information:\n{context}"

        res_ai = ollama.chat(model=model, 
                             messages=[{"role": "assistant", "content": prompt}] + lst_messages,
                             stream=False)  # Ensure to use stream=False to get full response

        # Extract and return the full response content
        full_response = res_ai["message"]["content"]
        return full_response

# Initialize AI instance
ai = AI()

# Streamlit UI
st.title('💬 PSE GPT: Retrieval-Augmented Generation')
st.sidebar.title("Chat History")
app = st.session_state

if "messages" not in app:
    app["messages"] = [{"role":"assistant", "content":"How can I help you today?"}]

if 'history' not in app:
    app['history'] = []

# Display chat history
for msg in app["messages"]:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="😎").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar="👾").write(msg["content"])

# Chat input and AI response
if txt := st.chat_input():
    app["messages"].append({"role":"user", "content":txt})
    st.chat_message("user", avatar="😎").write(txt)

    try:
        app["full_response"] = ai.respond(app["messages"])
        st.chat_message("assistant", avatar="👾").write(app["full_response"])
        app["messages"].append({"role":"system", "content":app["full_response"]})
    except Exception as e:
        st.error("Failed to get a response from AI.")
        st.error(traceback.format_exc())

    # Display chat history in sidebar
    app['history'].append("😎: "+txt)
    app['history'].append("👾: "+app["full_response"])
    st.sidebar.markdown("<br />".join(app['history'])+"<br /><br />", unsafe_allow_html=True)
