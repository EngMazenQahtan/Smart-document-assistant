import streamlit as st
import os
import json
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from pydantic import SecretStr
except ImportError:
    from pydantic.v1 import SecretStr
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import re

# ----------------------------------------------------
# إدارة الإعدادات وحفظها في ملف محلي دائم (config.json)
# ----------------------------------------------------
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def delete_config():
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
        except Exception as e:
            print(f"Error deleting config: {e}")

# تحميل الإعدادات عند البدء
config = load_config()

# ----------------------------------------------------
# إعدادات أدوات ويندوز الخارجية (Tesseract & Poppler)
# ----------------------------------------------------
# 1. إعداد مسار Tesseract OCR
TESSERACT_DEFAULT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_DEFAULT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_DEFAULT_PATH

# 2. إعداد مسار Poppler
POPPLER_PATH = None
possible_poppler_paths = [
    r'C:\poppler\Library\bin',
    r'C:\poppler\bin',
]
for path in possible_poppler_paths:
    if os.path.exists(path):
        POPPLER_PATH = path
        break
# ----------------------------------------------------

# ----------------------------------------------------
# قاموس الترجمات (عربي / إنجليزي)
# ----------------------------------------------------
TRANSLATIONS = {
    "Arabic": {
        "title": "📄 مساعد المستندات الذكي Document-GPT & Gemini",
        "subtitle": "قم برفع ملفات الـ PDF وسيقوم التطبيق باستخراج النصوص والدردشة معها بالذكاء الاصطناعي!",
        "settings_header": "🛠️ إعدادات الذكاء الاصطناعي",
        "provider_select": "اختر مزود الخدمة (LLM Provider):",
        "gemini_key_label": "أدخل مفتاح Google Gemini API Key:",
        "openai_key_label": "أدخل مفتاح OpenAI API Key:",
        "model_select": "اختر النموذج:",
        "save_keys_checkbox": "💾 حفظ الإعدادات والمفاتيح بشكل دائم",
        "delete_keys_button": "🗑️ حذف الإعدادات والمفاتيح المحفوظة",
        "status_header": "⚙️ حالة الأدوات الخارجية:",
        "tesseract_ok": "✅ Tesseract OCR: متصل وجاهز",
        "tesseract_err": "❌ Tesseract OCR: غير موجود بالمسار الافتراضي",
        "poppler_ok": "✅ Poppler: متصل وجاهز",
        "poppler_err": "❌ Poppler: غير موجود في C:\\poppler",
        "upload_label": "قم باختيار ملف PDF:",
        "api_warning": "⚠️ يرجى إدخال وتفعيل مفتاح الـ API في الشريط الجانبي أولاً لتتمكن من قراءة المستندات.",
        "api_warning_sidebar": "⚠️ يرجى إدخال مفتاح الـ API للمتابعة.",
        "dots_warning_gemini": "⚠️ يرجى استبدال النقاط بمفتاح الـ API الحقيقي الخاص بجوجل.",
        "dots_warning_openai": "⚠️ يرجى استبدال النقاط بمفتاح الـ API الحقيقي الخاص بـ OpenAI.",
        "processing_file": "جاري قراءة وتحويل {file_name} واستخراج النصوص عبر OCR...",
        "ocr_empty_warning": "تحذير: لم نتمكن من استخراج أي نص من {file_name}.",
        "file_error": "خطأ أثناء قراءة الملف {file_name}: {e}",
        "analysing_doc": "جاري تحليل محتوى المستندات واستخلاص الملخص عبر الذكاء الاصطناعي...",
        "success_extract": " تم استخراج النصوص وتحليل الكيانات بنجاح!",
        "expander_title": "📊 عرض التحليل والملخص الأولي للمستند",
        "chat_placeholder": "اسأل أي سؤال حول محتوى الملفات المرفوعة؟",
        "thinking": "جاري التفكير وتوليد الإجابة...",
        "tokens_usage": "⚡ استهلاك الرموز المميزة: {tokens} Tokens",
        "no_context_warning": "⚠️ لا يتوفر سياق حالياً للإجابة على الأسئلة. يرجى رفع ملف PDF وتأكيد تحليله أولاً.",
        "lang_label": "🌍 لغة الواجهة / Interface Language:",
        "openai_init_err": "خطأ أثناء تهيئة OpenAI: {e}",
        "gemini_init_err": "خطأ أثناء تهيئة Gemini: {e}",
        "ai_call_err": "خطأ أثناء استدعاء الذكاء الاصطناعي لتحليل الملف: {e}",
        "response_err": "خطأ أثناء توليد الإجابة: {e}"
    },
    "English": {
        "title": "📄 Smart Document-GPT & Gemini",
        "subtitle": "Upload PDF files, and the app will extract text and chat with them using AI!",
        "settings_header": "🛠️ AI Settings",
        "provider_select": "Select LLM Provider:",
        "gemini_key_label": "Enter Google Gemini API Key:",
        "openai_key_label": "Enter OpenAI API Key:",
        "model_select": "Select Model:",
        "save_keys_checkbox": "💾 Save settings and keys permanently",
        "delete_keys_button": "🗑️ Delete saved settings and keys",
        "status_header": "⚙️ External Tools Status:",
        "tesseract_ok": "✅ Tesseract OCR: Connected & Ready",
        "tesseract_err": "❌ Tesseract OCR: Not found in default path",
        "poppler_ok": "✅ Poppler: Connected & Ready",
        "poppler_err": "❌ Poppler: Not found in C:\\poppler",
        "upload_label": "Choose a PDF file:",
        "api_warning": "⚠️ Please enter and activate your API key in the sidebar first to read documents.",
        "api_warning_sidebar": "⚠️ Please enter your API key to continue.",
        "dots_warning_gemini": "⚠️ Please replace dots with your real Google API key.",
        "dots_warning_openai": "⚠️ Please replace dots with your real OpenAI API key.",
        "processing_file": "Reading, converting {file_name} and extracting text via OCR...",
        "ocr_empty_warning": "Warning: Could not extract any text from {file_name}.",
        "file_error": "Error reading file {file_name}: {e}",
        "analysing_doc": "Analyzing document contents and extracting summary via AI...",
        "success_extract": " Texts successfully extracted and analyzed!",
        "expander_title": "📊 View Analysis and Initial Document Summary",
        "chat_placeholder": "Ask any question about the uploaded document?",
        "thinking": "Thinking and generating response...",
        "tokens_usage": "⚡ Token usage: {tokens} Tokens",
        "no_context_warning": "⚠️ No context available to answer. Please upload a PDF file first.",
        "lang_label": "🌍 لغة الواجهة / Interface Language:",
        "openai_init_err": "Error initializing OpenAI: {e}",
        "gemini_init_err": "Error initializing Gemini: {e}",
        "ai_call_err": "Error calling AI to analyze document: {e}",
        "response_err": "Error generating response: {e}"
    }
}
# ----------------------------------------------------

# ----------------------------------------------------
# تهيئة إعدادات صفحة Streamlit والتنسيقات الفائقة (CSS)
# ----------------------------------------------------
st.set_page_config(page_title="Document-GPT & Gemini", page_icon="📄", layout="wide")

# حقن أكواد CSS المذهلة للتصميم العصري والجذاب
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&family=Outfit:wght@300;400;600;700&display=swap');

/* تنسيق الخلفية والنصوص العامة */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Cairo', 'Outfit', sans-serif;
    background-color: #0e1117;
    color: #ffffff;
}

/* تزيين العنوان الرئيسي بتدرج لوني براق */
.main-title {
    background: linear-gradient(135deg, #00C6FF, #0072FF, #00F2FE, #4FACFE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.7rem;
    margin-bottom: 0.1rem;
    text-shadow: 0px 4px 10px rgba(0, 114, 255, 0.15);
}

.subtitle {
    color: #a3b8cc;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* القائمة الجانبية بنمط Glassmorphism */
[data-testid="stSidebar"] {
    background-color: rgba(17, 22, 32, 0.96) !important;
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* عناوين القائمة الجانبية */
.sidebar-title {
    font-weight: 700;
    color: #00C6FF;
    font-size: 1.3rem;
    margin-bottom: 0.8rem;
    text-shadow: 0 0 15px rgba(0, 198, 255, 0.2);
}

/* حاويات مخصصة لعرض الحالة بشكل جذاب */
.status-container {
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 12px;
    margin-bottom: 12px;
    font-size: 0.95rem;
    transition: all 0.3s ease;
}
.status-container:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 198, 255, 0.3);
    background: rgba(255, 255, 255, 0.04);
    box-shadow: 0 4px 15px rgba(0, 198, 255, 0.1);
}

/* محاذاة اللغات واتجاهات الكتابة */
.rtl-dir {
    direction: rtl;
    text-align: right;
}
.ltr-dir {
    direction: ltr;
    text-align: left;
}

/* تجميل أزرار الاستدعاء وعناصر Streamlit */
div.stButton > button {
    background: linear-gradient(135deg, #0072FF, #00C6FF) !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    transition: all 0.3s ease !important;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 15px rgba(0, 198, 255, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)
# ----------------------------------------------------

# ----------------------------------------------------
# إعدادات الشريط الجانبي (المزود، اللغة، المفاتيح والمحاذاة)
# ----------------------------------------------------

# 1. اختيار لغة التطبيق
selected_lang = st.sidebar.selectbox(
    "🌍 لغة الواجهة / Interface Language:",
    ["العربية (Arabic)", "English"],
    index=0 if config.get("language", "Arabic") == "Arabic" else 1
)
language = "Arabic" if selected_lang == "العربية (Arabic)" else "English"
st.session_state.language = language

# تحديد اتجاه العرض حسب اللغة المختارة
text_align_class = "rtl-dir" if language == "Arabic" else "ltr-dir"

st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="sidebar-title">{TRANSLATIONS[language]["settings_header"]}</div>', unsafe_allow_html=True)

# 2. اختيار مزود الخدمة
provider = st.sidebar.selectbox(
    TRANSLATIONS[language]["provider_select"],
    ["Google Gemini", "OpenAI"],
    index=0 if config.get("provider", "Google Gemini") == "Google Gemini" else 1
)

# 3. إعداد الحقول والمفاتيح بناء على المزود
client = None
if provider == "Google Gemini":
    default_key = config.get("gemini_api_key", "")
    api_key_input = st.sidebar.text_input(
        TRANSLATIONS[language]["gemini_key_label"], 
        value=default_key, 
        type="password",
        key="api_key_input_gemini"
    )
    
    # قائمة الموديلات الحديثة لعام 2026
    default_model = config.get("gemini_model", "gemini-2.5-flash")
    gemini_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-flash", "gemini-3-pro", "gemini-3.1-flash", "gemini-3.1-pro"]
    model_index = gemini_models.index(default_model) if default_model in gemini_models else 0
    
    model_name = st.sidebar.selectbox(
        TRANSLATIONS[language]["model_select"], 
        gemini_models,
        index=model_index
    )
    
    if api_key_input:
        if api_key_input == "...":
            st.sidebar.error(TRANSLATIONS[language]["dots_warning_gemini"])
        else:
            try:
                client = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0,
                    google_api_key=SecretStr(api_key_input)
                )
            except Exception as e:
                st.sidebar.error(TRANSLATIONS[language]["gemini_init_err"].format(e=e))
    else:
        st.sidebar.warning(TRANSLATIONS[language]["api_warning_sidebar"])

else:  # OpenAI
    default_key = config.get("openai_api_key", "")
    api_key_input = st.sidebar.text_input(
        TRANSLATIONS[language]["openai_key_label"], 
        value=default_key, 
        type="password",
        key="api_key_input_openai"
    )
    
    default_model = config.get("openai_model", "gpt-4o-mini")
    openai_models = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"]
    model_index = openai_models.index(default_model) if default_model in openai_models else 1
    
    model_name = st.sidebar.selectbox(
        TRANSLATIONS[language]["model_select"], 
        openai_models,
        index=model_index
    )
    
    if api_key_input:
        if api_key_input == "...":
            st.sidebar.error(TRANSLATIONS[language]["dots_warning_openai"])
        else:
            try:
                client = ChatOpenAI(
                    model=model_name,
                    temperature=0,
                    api_key=SecretStr(api_key_input)
                )
            except Exception as e:
                st.sidebar.error(TRANSLATIONS[language]["openai_init_err"].format(e=e))
    else:
        st.sidebar.warning(TRANSLATIONS[language]["api_warning_sidebar"])

# 4. تفعيل أو إلغاء تفعيل الحفظ الدائم للمفاتيح
save_keys = st.sidebar.checkbox(
    TRANSLATIONS[language]["save_keys_checkbox"],
    value=config.get("save_keys", True)
)

# حفظ الإعدادات تلقائياً في ملف config.json عند أي تغيير
if save_keys:
    new_config = {
        "language": language,
        "provider": provider,
        "gemini_api_key": api_key_input if provider == "Google Gemini" else config.get("gemini_api_key", ""),
        "openai_api_key": api_key_input if provider == "OpenAI" else config.get("openai_api_key", ""),
        "gemini_model": model_name if provider == "Google Gemini" else config.get("gemini_model", "gemini-2.5-flash"),
        "openai_model": model_name if provider == "OpenAI" else config.get("openai_model", "gpt-4o-mini"),
        "save_keys": True
    }
    if new_config != config:
        save_config(new_config)
        config = new_config

# زر لحذف المفاتيح والإعدادات المسجلة
if st.sidebar.button(TRANSLATIONS[language]["delete_keys_button"]):
    delete_config()
    # مسح مفاتيح الجلسة بالكامل لتفريغ الحقول عند إعادة التشغيل
    if "api_key_input_gemini" in st.session_state:
        del st.session_state["api_key_input_gemini"]
    if "api_key_input_openai" in st.session_state:
        del st.session_state["api_key_input_openai"]
    st.sidebar.success("🗑️ Saved settings deleted!" if language == "English" else "🗑️ تم حذف الإعدادات والمفاتيح المحفوظة بنجاح!")
    st.rerun()

# 5. عرض حالة الأدوات الخارجية بنقوش رائعة وجديدة
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="sidebar-title">{TRANSLATIONS[language]["status_header"]}</div>', unsafe_allow_html=True)

if os.path.exists(TESSERACT_DEFAULT_PATH):
    st.sidebar.markdown(f'<div class="status-container">{TRANSLATIONS[language]["tesseract_ok"]}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="status-container">{TRANSLATIONS[language]["tesseract_err"]}</div>', unsafe_allow_html=True)

if POPPLER_PATH:
    st.sidebar.markdown(f'<div class="status-container">{TRANSLATIONS[language]["poppler_ok"]} ({os.path.basename(POPPLER_PATH)})</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="status-container">{TRANSLATIONS[language]["poppler_err"]}</div>', unsafe_allow_html=True)
# ----------------------------------------------------


# ----------------------------------------------------
# متن الصفحة الرئيسي وعرض العناوين والملف
# ----------------------------------------------------
st.markdown(f'<h1 class="main-title {text_align_class}">{TRANSLATIONS[language]["title"]}</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle {text_align_class}">{TRANSLATIONS[language]["subtitle"]}</p>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(TRANSLATIONS[language]["upload_label"], type=["pdf"], accept_multiple_files=True)

# إدارة وإعداد الـ session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context" not in st.session_state:
    st.session_state.context = ""

# عرض محادثات الدردشة القديمة بشكل منسق مع محاذاة RTL/LTR
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        alignment_class = "rtl-dir" if language == "Arabic" else "ltr-dir"
        st.markdown(f'<div class="{alignment_class}">{message["content"]}</div>', unsafe_allow_html=True)

# دالة تنظيف النص
def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"[^\w\s]", "", text)
    text = text.strip()
    return text

# معالجة الملف المرفوع تلقائياً عند رفعه
if uploaded_files:
    if client is None:
        st.error(TRANSLATIONS[language]["api_warning"])
    else:
        # قراءة واستخراج النصوص
        extracted_text_all = ""
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            
            with st.spinner(TRANSLATIONS[language]["processing_file"].format(file_name=file_name)):
                try:
                    pdf_bytes = uploaded_file.read()
                    if POPPLER_PATH:
                        images = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
                    else:
                        images = convert_from_bytes(pdf_bytes)
                    
                    extracted_text = ""
                    for i in range(len(images)):
                        text = pytesseract.image_to_string(images[i], lang="eng")
                        extracted_text += text
                    
                    cleaned_text = clean_text(extracted_text)
                    if cleaned_text:
                        extracted_text_all += cleaned_text + " "
                    else:
                        st.warning(TRANSLATIONS[language]["ocr_empty_warning"].format(file_name=file_name))
                except Exception as e:
                    st.error(TRANSLATIONS[language]["file_error"].format(file_name=file_name, e=e))
        
        if extracted_text_all.strip():
            # بناء طلب التحليل الأولي
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that identifies and extracts entities like names, dates, addresses, emails, phone numbers, etc. Extracting relationships between entities. Summarizing key information from the document.",
                },
                {
                    "role": "user",
                    "content": f"Here is the text extracted from the document:\n\n{extracted_text_all.strip()}\n\nPlease identify and extract key entities, relationships, and provide a short summary.",
                },
            ]
            
            with st.spinner(TRANSLATIONS[language]["analysing_doc"]):
                try:
                    ai_msg = client.invoke(messages)
                    st.session_state.context = ai_msg.content
                    st.success(TRANSLATIONS[language]["success_extract"])
                    
                    # عرض التحليل والملخص الأولي
                    with st.expander(TRANSLATIONS[language]["expander_title"], expanded=True):
                        st.markdown(st.session_state.context)
                except Exception as e:
                    st.error(TRANSLATIONS[language]["ai_call_err"].format(e=e))

# منطقة الدردشة الحية والذكية مع المستند
user_query = st.chat_input(TRANSLATIONS[language]["chat_placeholder"])
if user_query:
    # عرض سؤال المستخدم وإضافته للسجل
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        alignment_class = "rtl-dir" if language == "Arabic" else "ltr-dir"
        st.markdown(f'<div class="{alignment_class}">{user_query}</div>', unsafe_allow_html=True)
    
    if client is None:
        st.error(TRANSLATIONS[language]["api_warning"])
    elif st.session_state.context:
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "Context:\n"
            "{context}"
        )
        messages = [
            {
                "role": "system",
                "content": system_prompt.format(context=st.session_state.context),
            },
            {
                "role": "user",
                "content": user_query,
            },
        ]
        
        with st.spinner(TRANSLATIONS[language]["thinking"]):
            try:
                response = client.invoke(messages)
                
                # إضافة وحفظ إجابة البوت
                st.session_state.messages.append({"role": "assistant", "content": response.content})
                with st.chat_message("assistant"):
                    alignment_class = "rtl-dir" if language == "Arabic" else "ltr-dir"
                    st.markdown(f'<div class="{alignment_class}">{response.content}</div>', unsafe_allow_html=True)
                    
                    # طباعة معلومات التوكنز في حال توفرها
                    if "token_usage" in response.response_metadata:
                        tokens = response.response_metadata["token_usage"].get("total_tokens")
                        if tokens:
                            st.caption(TRANSLATIONS[language]["tokens_usage"].format(tokens=tokens))
            except Exception as e:
                st.error(TRANSLATIONS[language]["response_err"].format(e=e))
    else:
        st.warning(TRANSLATIONS[language]["no_context_warning"])
