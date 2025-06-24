import os
import re
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage


from config import Config
from database import get_unprocessed_files, update_file_processed_status, get_chat_history as db_get_chat_history, insert_chat_log as db_insert_chat_log

llm = None
embedding_function = None
vectorstore = None
retriever = None
contextualize_q_chain = None
answer_generation_chain = None
qa_template_simple = None

MAX_HISTORY_MESSAGES_FOR_CONTEXTUALIZATION = 4
MAX_STANDALONE_QUESTION_WORDS = 30
MIN_VALID_ANSWER_LENGTH = 15
MIN_CONTEXT_LENGTH_FOR_ANSWER = 5
MIN_KEYWORD_OVERLAP_FOR_RELEVANCE = 1

def docs2str(docs):
    """Menggabungkan konten halaman dari beberapa dokumen menjadi satu string."""
    return "\n\n".join(doc.page_content for doc in docs)

def approximate_token_count(text):
    if not text:
        return 0
    return len(text) // 4

def get_keywords_from_query(query_text):
    """Ekstrak kata kunci sederhana dari query."""
    if not query_text:
        return set()
    words = re.sub(r'[^\w\s]', '', query_text.lower()).split()
    keywords = {word for word in words if len(word) > 2}
    return keywords

def initialize_rag_components():
    """
    Menginisialisasi komponen RAG: LLM, Embedding, Vectorstore, Retriever,
    Contextualization Chain, dan Answer Generation Chain.
    """
    global llm, embedding_function, vectorstore, retriever, contextualize_q_chain, answer_generation_chain, qa_template_simple

    print("Menginisialisasi komponen RAG...")

    try:
        from huggingface_hub import hf_hub_download
        print("HuggingFace Hub import berhasil.")
    except ImportError:
        print("Error: huggingface_hub tidak terinstall. Install dengan: pip install huggingface_hub")
        llm = None
        return

    if not Config.LLM_MODEL_PATH:
        print("Error: LLM_MODEL_PATH tidak diatur di konfigurasi.")
        llm = None
    else:
        model_dir = os.path.dirname(Config.MODEL_CACHE_DIR)
        if model_dir and not os.path.exists(model_dir):
            print(f"Membuat direktori model: {model_dir}")
            os.makedirs(model_dir, exist_ok=True)

        model_cache_dir = os.environ.get('MODEL_CACHE_DIR', model_dir)
        model_filename = os.environ.get('MODEL_FILENAME', 'Nusantara-2.7b-Indo-Chat-v0.2.i1-Q6_K.gguf')
        model_repo_id = os.environ.get('MODEL_REPO_ID', 'mradermacher/Nusantara-2.7b-Indo-Chat-v0.2-i1-GGUF')

        if not os.path.exists(model_cache_dir):
            print(f"Membuat direktori cache model: {model_cache_dir}")
            os.makedirs(model_cache_dir, exist_ok=True)

        manual_model_path = os.path.join(model_cache_dir, model_filename)

        actual_model_path = None
        
        if os.path.exists(Config.LLM_MODEL_PATH):
            actual_model_path = Config.LLM_MODEL_PATH
            print(f"Model ditemukan di path config: {actual_model_path}")
        elif os.path.exists(manual_model_path):
            actual_model_path = manual_model_path
            print(f"Model ditemukan di cache dir: {actual_model_path}")
        else:
            print(f"Model {model_filename} tidak ditemukan di {manual_model_path}. Mencoba mengunduh...")
            
            try:
                token = Config.HUGGINGFACEHUB_API_TOKEN if Config.HUGGINGFACEHUB_API_TOKEN not in ["ISI_TOKEN_HUGGINGFACE_ANDA_DI_SINI_JIKA_ADA", "", None] else None
                
                downloaded_model_path = hf_hub_download(
                    repo_id=model_repo_id,
                    filename=model_filename,
                    cache_dir=model_cache_dir,
                    local_dir=model_cache_dir,
                    local_dir_use_symlinks=False,
                    token=token
                )
                
                if os.path.isdir(downloaded_model_path):
                    potential_path = os.path.join(downloaded_model_path, model_filename)
                    if os.path.exists(potential_path):
                        actual_model_path = potential_path
                    else:
                        actual_model_path = manual_model_path
                else:
                    actual_model_path = downloaded_model_path

                if not os.path.exists(actual_model_path):
                    print(f"Gagal mengunduh atau menemukan model di {actual_model_path} atau {manual_model_path}. Pastikan model ada atau dapat diunduh.")
                    llm = None
                    return
                else:
                    print(f"Model berhasil didownload ke: {actual_model_path}")
                    
            except Exception as e:
                print(f"Error saat mengunduh model: {e}. Pastikan Anda memiliki koneksi internet dan token HF jika diperlukan.")
                llm = None
                return

        if actual_model_path and os.path.exists(actual_model_path):
            print(f"Memuat LLM dari: {actual_model_path}")
            try:
                llm = LlamaCpp(
                    model_path=actual_model_path,
                    n_gpu_layers=20,
                    temperature=0.5,
                    top_p=0.95,
                    repeat_penalty=1.2,
                    stop=["Question:", "\n\n", "Human:", "Pertanyaan:"],
                    max_tokens=256,
                    n_ctx=2048,
                    n_batch=256,
                    verbose=False
                )
                print("LLM berhasil dimuat.")
                
                if actual_model_path != Config.LLM_MODEL_PATH and os.path.dirname(Config.LLM_MODEL_PATH):
                    try:
                        import shutil
                        os.makedirs(os.path.dirname(Config.LLM_MODEL_PATH), exist_ok=True)
                        if not os.path.exists(Config.LLM_MODEL_PATH):
                            shutil.copy2(actual_model_path, Config.LLM_MODEL_PATH)
                            print(f"Model juga disalin ke config path: {Config.LLM_MODEL_PATH}")
                    except Exception as copy_error:
                        print(f"Warning: Gagal menyalin model ke config path: {copy_error}")
                        
            except Exception as e:
                print(f"Error saat memuat LLM LlamaCpp: {e}")
                llm = None
        else:
            print(f"Error: File model LLM tidak ditemukan. Path yang dicoba: {Config.LLM_MODEL_PATH}, {manual_model_path}")
            llm = None

    if Config.HUGGINGFACEHUB_API_TOKEN and Config.HUGGINGFACEHUB_API_TOKEN not in ["ISI_TOKEN_HUGGINGFACE_ANDA_DI_SINI_JIKA_ADA", ""]:
        os.environ['HUGGINGFACEHUB_API_TOKEN'] = Config.HUGGINGFACEHUB_API_TOKEN
        print("Hugging Face Hub API Token telah diatur.")
    else:
        print("Hugging Face Hub API Token tidak diatur atau kosong di konfigurasi.")
    try:
        embedding_function = SentenceTransformerEmbeddings(model_name=Config.EMBEDDING_MODEL_NAME)
        print(f"Embedding function '{Config.EMBEDDING_MODEL_NAME}' berhasil dimuat.")
    except Exception as e:
        print(f"Error saat memuat embedding function '{Config.EMBEDDING_MODEL_NAME}': {e}")
        embedding_function = None

    if not os.path.exists(Config.CHROMA_PERSIST_DIRECTORY):
        os.makedirs(Config.CHROMA_PERSIST_DIRECTORY)
    if embedding_function: 
        try:
            vectorstore = Chroma(
                collection_name=Config.COLLECTION_NAME,
                persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
                embedding_function=embedding_function
            )
            retriever = vectorstore.as_retriever(
                search_type="mmr", 
                search_kwargs={'k': 5, 'fetch_k': 10, 'lambda_mult': 0.7} 
            )
            print(f"Vector store dan retriever berhasil diinisialisasi dari {Config.CHROMA_PERSIST_DIRECTORY}.")
            process_pending_documents()
        except Exception as e:
            print(f"Error saat menginisialisasi ChromaDB/Retriever: {e}")
            vectorstore = None
            retriever = None
    else:
        print("Vector store/Retriever tidak dapat diinisialisasi karena embedding function gagal dimuat.")
        vectorstore = None
        retriever = None

    if llm and retriever:
        contextualize_q_system_prompt = (
            "Diberikan riwayat percakapan dan pertanyaan pengguna terbaru "
            "yang mungkin merujuk pada konteks dalam riwayat percakapan, "
            "formulasikan pertanyaan mandiri yang dapat dipahami "
            "tanpa riwayat percakapan. JANGAN menjawab pertanyaan, "
            "cukup formulasikan ulang jika diperlukan dan kembalikan apa adanya."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
        print("Contextualization chain berhasil dibuat.")

        qa_template_simple = """Kamu adalah asisten ahli di bidang gizi dan kesehatan masyarakat.
PENTING: KELUARKAN KEMAMPUAN MAKSIMALMU untuk menjawab pertanyaan dengan natural dan terstruktur SESUAI KONTEKS yang diberikan.
Jika jawabannya tidak ada didalam KONTEKS, HARUS balas dengan: Maaf, saya tidak memiliki informasi yang cukup untuk menjawab pertanyaan ini.

Konteks:
{context}

Pertanyaan:
{question}

Jawaban:"""
        simple_qa_prompt = ChatPromptTemplate.from_template(qa_template_simple)

        answer_generation_chain = (
            RunnablePassthrough.assign(context=(lambda x: x["question"]) | retriever | RunnableLambda(docs2str))
            | simple_qa_prompt
            | llm
            | StrOutputParser()
        )

        print("Answer generation chain (RAG sederhana) berhasil dibuat.")
    else:
        print("Chains tidak dapat dibuat karena LLM atau Retriever tidak terinisialisasi.")
        contextualize_q_chain = None
        answer_generation_chain = None
        qa_template_simple = None

    print("Inisialisasi komponen RAG selesai.")


def process_document_to_vectorstore(filepath, file_id):
    global vectorstore, embedding_function
    if not vectorstore or not embedding_function:
        print("Error: Vectorstore atau embedding function belum terinisialisasi.")
        return False
    try:
        print(f"Memproses file: {filepath} (ID: {file_id})")
        loader = PyPDFLoader(filepath) if filepath.endswith(".pdf") else Docx2txtLoader(filepath)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300, length_function=len)
        splits = text_splitter.split_documents(documents)
        if not splits:
            print(f"Tidak ada teks yang dapat diekstrak dari {filepath}")
            update_file_processed_status(file_id) 
            return False
        for split in splits:
            split.metadata["source"] = os.path.basename(filepath)
            split.metadata["file_id"] = str(file_id) 
        vectorstore.add_documents(splits)
        print(f"Berhasil memproses dan menambahkan {len(splits)} chunk dari {filepath} ke vector store.")
        update_file_processed_status(file_id) 
        return True
    except Exception as e:
        print(f"Error saat memproses dokumen {filepath}: {e}")
        return False

def process_pending_documents():
    print("Mengecek dokumen yang belum diproses...")
    unprocessed_files = get_unprocessed_files()
    if not unprocessed_files:
        print("Tidak ada dokumen baru untuk diproses.")
        return
    for db_file_entry in unprocessed_files:
        filepath, file_id = db_file_entry['filepath'], db_file_entry['id']
        if os.path.exists(filepath):
            print(f"Memulai pemrosesan untuk file: {db_file_entry['filename']} (ID: {file_id})")
            process_document_to_vectorstore(filepath, file_id)
        else:
            print(f"File {filepath} (ID: {file_id}) tidak ditemukan.")
            update_file_processed_status(file_id) 
    print("Selesai memproses dokumen yang tertunda.")

def get_rag_response(session_uuid: str, user_input: str):
    global contextualize_q_chain, answer_generation_chain, llm, retriever, qa_template_simple

    if not llm: 
        error_msg = "Model LLM tidak tersedia..."
        db_insert_chat_log(session_uuid, user_input, error_msg, "N/A - LLM Error")
        return error_msg
    if not contextualize_q_chain or not answer_generation_chain: 
        error_msg = "Sistem RAG belum siap..."
        db_insert_chat_log(session_uuid, user_input, error_msg, "N/A - RAG Chain Error")
        return error_msg
    if not qa_template_simple: 
        error_msg = "Template QA belum siap..."
        print(f"ERROR: {error_msg}")
        db_insert_chat_log(session_uuid, user_input, error_msg, "N/A - RAG Template Error")
        return error_msg

    raw_chat_history = db_get_chat_history(session_uuid)
    
    chat_history_for_contextualization = []
    if raw_chat_history:
        start_index = max(0, len(raw_chat_history) - MAX_HISTORY_MESSAGES_FOR_CONTEXTUALIZATION)
        limited_history = raw_chat_history[start_index:]
        for msg in limited_history:
            if msg["role"] == "human":
                chat_history_for_contextualization.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai" or msg["role"] == "bot":
                chat_history_for_contextualization.append(AIMessage(content=msg["content"]))
    
    generated_standalone_question = user_input 
    if chat_history_for_contextualization: 
        try:
            print(f"DEBUG: Input ke contextualize_q_chain - History: {len(chat_history_for_contextualization)} pesan, Input: '{user_input}'")
            raw_reformulated_question = contextualize_q_chain.invoke({
                "chat_history": chat_history_for_contextualization,
                "input": user_input
            })
            print(f"DEBUG: Output mentah dari contextualize_q_chain: '{raw_reformulated_question}'")

            cleaned_question = raw_reformulated_question.strip()
            prefixes_to_remove = ["ai:", "jawaban:", "output anda:", "output saya:"] 
            for prefix in prefixes_to_remove:
                if cleaned_question.lower().startswith(prefix):
                    cleaned_question = cleaned_question[len(prefix):].strip()
            
            word_count = len(cleaned_question.split())
            is_likely_answer = (
                word_count > MAX_STANDALONE_QUESTION_WORDS or
                not cleaned_question.endswith("?") and user_input != cleaned_question 
            )

            if is_likely_answer and cleaned_question != user_input: 
                print(f"DEBUG: Output kontekstualisasi ('{cleaned_question}') tampak seperti jawaban/terlalu panjang. Menggunakan input asli.")
                generated_standalone_question = user_input
            else:
                generated_standalone_question = cleaned_question

            print(f"DEBUG: Pertanyaan asli: '{user_input}', Pertanyaan standalone (setelah pembersihan): '{generated_standalone_question}' (Perkiraan Token: {approximate_token_count(generated_standalone_question)})")

        except Exception as e:
            print(f"Error saat kontekstualisasi pertanyaan: {e}. Menggunakan input asli.")
            generated_standalone_question = user_input 
    else:
        print(f"DEBUG: Tidak ada histori, pertanyaan digunakan langsung: '{generated_standalone_question}' (Perkiraan Token: {approximate_token_count(generated_standalone_question)})")

    standalone_question_for_rag = generated_standalone_question

    retrieved_docs_str = ""
    is_context_relevant_for_question = False
    if retriever:
        try:
            docs = retriever.invoke(standalone_question_for_rag) 
            retrieved_docs_str = docs2str(docs).strip() 
            print(f"DEBUG: Konteks yang diambil (Panjang: {len(retrieved_docs_str)}, Perkiraan Token: {approximate_token_count(retrieved_docs_str)}):\n---\n{retrieved_docs_str[:200]}...\n---")

            if retrieved_docs_str and len(retrieved_docs_str) >= MIN_CONTEXT_LENGTH_FOR_ANSWER:
                question_keywords = get_keywords_from_query(standalone_question_for_rag)
                context_sample_for_keywords = retrieved_docs_str[:1000].lower()
                
                common_keyword_count = 0
                if question_keywords:
                    for q_keyword in question_keywords:
                        if q_keyword in context_sample_for_keywords:
                            common_keyword_count += 1
                
                if common_keyword_count >= MIN_KEYWORD_OVERLAP_FOR_RELEVANCE:
                    is_context_relevant_for_question = True
            print(f"DEBUG: Apakah konteks relevan untuk pertanyaan ('{standalone_question_for_rag}')? {is_context_relevant_for_question}. Overlap kata kunci: {common_keyword_count}")

        except Exception as e:
            print(f"DEBUG: Error saat mengambil dokumen: {e}")
            retrieved_docs_str = "" 
    else:
        print("DEBUG: Retriever tidak terinisialisasi.")
        retrieved_docs_str = "" 

    if qa_template_simple:
        prompt_template_text = qa_template_simple.format(context="[KONTEKS_PLACEHOLDER]", question="[PERTANYAAN_PLACEHOLDER]")
        approx_prompt_tokens = approximate_token_count(prompt_template_text)
    else: 
        approx_prompt_tokens = 200 
        print("WARNING: qa_template_simple tidak terdefinisi saat menghitung perkiraan token.")

    approx_standalone_q_tokens = approximate_token_count(standalone_question_for_rag)
    approx_context_tokens = approximate_token_count(retrieved_docs_str)
    total_approx_tokens_for_qa = approx_prompt_tokens + approx_standalone_q_tokens + approx_context_tokens
    print(f"DEBUG: Perkiraan total token untuk answer_generation_chain: {total_approx_tokens_for_qa} (Prompt: {approx_prompt_tokens}, Q: {approx_standalone_q_tokens}, Context: {approx_context_tokens})")

    fallback_message = "Maaf, saya tidak memiliki informasi yang cukup untuk menjawab pertanyaan ini."

    try:
        bot_answer_raw = answer_generation_chain.invoke({
            "question": standalone_question_for_rag,
            }) 
        print(f"DEBUG: Output mentah dari answer_generation_chain: '{bot_answer_raw}'")

        bot_answer_stripped = bot_answer_raw.strip()
        
        if not bot_answer_stripped or len(bot_answer_stripped) < MIN_VALID_ANSWER_LENGTH:
            if fallback_message.lower() not in bot_answer_stripped.lower():
                 print(f"DEBUG Post-Proc: Output LLM ('{bot_answer_stripped}') kosong/pendek. Fallback.")
                 bot_answer = fallback_message
            else:
                print(f"DEBUG Post-Proc: Output LLM ('{bot_answer_stripped}') sudah mirip fallback.")
                bot_answer = bot_answer_stripped 
        elif not is_context_relevant_for_question and fallback_message.lower() not in bot_answer_stripped.lower():
            print(f"DEBUG Post-Proc: Konteks TIDAK relevan, tapi LLM jawab ('{bot_answer_stripped}') bukan fallback. Memaksa fallback.")
            bot_answer = fallback_message
        else:
            bot_answer = bot_answer_stripped
        
        model_name = os.path.basename(Config.LLM_MODEL_PATH) if Config.LLM_MODEL_PATH else "LlamaCpp_Unknown"
        db_insert_chat_log(session_uuid, user_input, bot_answer, model_name) 
        
        return bot_answer
        
    except Exception as e:
        print(f"Error saat menjalankan answer generation chain: {e}")
        error_response = fallback_message 
        model_name = os.path.basename(Config.LLM_MODEL_PATH) if Config.LLM_MODEL_PATH else "LlamaCpp_Unknown"
        db_insert_chat_log(session_uuid, user_input, f"Error: {str(e)} | Fallback: {error_response}", model_name)
        return error_response

if __name__ == '__main__':
    print("Menjalankan pengujian mandiri untuk rag_system.py...")
    initialize_rag_components()