# app.py (versão modernizada para Pylance)

# python -m venv venv <-- usado para criar um ambiente virtual
# venv\Scripts\activate <-- Windows
# source venv/bin/activate <-- macOS/Linux
# python.exe -m pip install --upgrade pip <-- atualizar pip

# Instalar as bibliotecas necessárias:
# pip install flask
# pip install pandas
# pip install python-docx
# pip install PyPDF2
# pip install openpyxl
# pip install -q -U google-genai
# pip install dotenv

import os
import traceback
from typing import Dict, Union

import docx
# import google.generativeai as genai
from google import genai
import pandas as pd
import PyPDF2
from flask import Flask, Response, jsonify, render_template, request
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv

# --- Funções de Extração de Texto ---

def extrair_texto_docx(caminho_arquivo: str) -> str:
    """Extrai texto de um arquivo .docx."""
    try:
        doc = docx.Document(caminho_arquivo)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        return f"ERRO ao ler DOCX: {e}"

def extrair_texto_pdf(caminho_arquivo: str) -> str:
    """Extrai texto de um arquivo .pdf."""
    text = ""
    try:
        with open(caminho_arquivo, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.is_encrypted:
                return "ERRO: O arquivo PDF está protegido por senha e não pode ser lido."
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"ERRO ao ler PDF: {e}"
    return text

def extrair_texto_excel(caminho_arquivo: str) -> str:
    """Extrai texto de um arquivo Excel (.xlsx, .xls)."""
    try:
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        return df.to_string()
    except Exception as e:
        return f"ERRO ao ler Excel: {e}"

# --- Configuração do App Flask ---

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Carregamento da API Key (Método Recomendado: Variável de Ambiente) ---

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("AVISO CRÍTICO: A variável de ambiente 'GEMINI_API_KEY' não foi encontrada.")

# --- Lógica Principal ---

def processar_documento(caminho_arquivo: str, extensao: str) -> Dict[str, str]:
    """Processa o documento extraindo texto e chamando a API do Gemini."""
    # if not gemini_api_key or "SUA_CHAVE_AQUI" in gemini_api_key:
    #     return {"erro": "A API Key do Gemini não está configurada corretamente."}

    print(f"Processando o arquivo: {caminho_arquivo}")
    texto_extraido = ""
    
    if extensao == '.docx':
        texto_extraido = extrair_texto_docx(caminho_arquivo)
    elif extensao == '.pdf':
        texto_extraido = extrair_texto_pdf(caminho_arquivo)
    elif extensao in ['.xlsx', '.xls']:
        texto_extraido = extrair_texto_excel(caminho_arquivo)
    else:
        return {"erro": f"Formato de arquivo '{extensao}' não é suportado."}

    if "ERRO:" in texto_extraido or not texto_extraido.strip():
        return {"erro": texto_extraido or "Não foi possível extrair conteúdo do documento."}

    print(f"Texto extraído com sucesso. Caracteres: {len(texto_extraido)}")

    try:
        print("Chamando a API do Gemini...")


        client = genai.Client()

        prompt = f"""
        Você é um assistente de comunicação interna para a empresa MC Sonae.
        Sua tarefa é analisar o seguinte texto extraído de um documento e criar um comunicado interno em formato HTML.

        Texto do documento:
        ---
        {texto_extraido}
        ---

        (Seu prompt detalhado continua aqui, sem alterações)
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        # print("Resposta recebida da API do Gemini.")

        print(response.text)


        # model = genai.GenerativeModel(
        #     model_name='gemini-2.5-flash',
        #     api_key=gemini_api_key
        # )

        # prompt = f"""
        # Você é um assistente de comunicação interna para a empresa MC Sonae.
        # Sua tarefa é analisar o seguinte texto extraído de um documento e criar um comunicado interno em formato HTML.

        # Texto do documento:
        # ---
        # {texto_extraido}
        # ---

        # (Seu prompt detalhado continua aqui, sem alterações)
        # """
        # response = model.generate_content(prompt)
        # print("Resposta recebida da API do Gemini.")
        
        # Limpeza da resposta para remover marcadores de bloco de código
        cleaned_response = response.text.replace('```html', '').replace('```', '').strip()  # type: ignore
        return {"resultado": cleaned_response}

    except Exception as e:
        print(f"ERRO CRÍTICO ao chamar a API do Gemini: {e}")
        return {"erro": f"Ocorreu um erro ao comunicar com a IA. Detalhes: {e}"}

# --- Rotas do Site ---

@app.route('/')
def index() -> str:
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file() -> Union[Response, tuple[Response, int]]:
    try:
        if 'file' not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado."}), 400
        
        file: FileStorage = request.files['file']
        
        # Garante que o nome do arquivo existe e não está vazio
        if not file or not file.filename:
            return jsonify({"erro": "Nenhum arquivo selecionado."}), 400

        filename = file.filename
        _, extensao = os.path.splitext(filename)
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print("--- Nova Requisição ---")
        print(f"Recebendo arquivo: {filename}")
        file.save(caminho_arquivo)
        print(f"Arquivo salvo em: {caminho_arquivo}")

        resultado = processar_documento(caminho_arquivo, extensao.lower())
        
        print("Limpando arquivo temporário...")
        os.remove(caminho_arquivo)
        print("--- Requisição Finalizada ---")
        
        return jsonify(resultado)

    except Exception as e:
        print("===== OCORREU UM ERRO INESPERADO =====")
        print(traceback.format_exc())
        print("========================================")
        return jsonify({"erro": "Um erro inesperado ocorreu no servidor."}), 500

if __name__ == '__main__':
    # Para desenvolvimento, use debug=True. Para produção, use um servidor WSGI como Gunicorn.
    app.run(debug=True, host='0.0.0.0', port=5001)