# app.py (versão corrigida para gerar resumos e dados de dashboard)

# python -m venv venv <-- usado para criar um ambiente virtual
# venv\Scripts\activate <-- Windows
# source venv/bin/activate <-- macOS/Linux
# python.exe -m pip install --upgrade pip <-- atualizar pip

import os
import traceback
import re
import json
from typing import Dict, Union
from datetime import datetime

import docx
import google.generativeai as genai
import pandas as pd
import PyPDF2
from flask import Flask, Response, jsonify, render_template, request
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv

# --- CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE ---
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# --- FUNÇÕES DE EXTRAÇÃO DE TEXTO (COM A VERSÃO CORRETA PARA EXCEL) ---

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
                return "ERRO: O arquivo PDF está protegido por senha."
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"ERRO ao ler PDF: {e}"
    return text

def extrair_texto_excel(caminho_arquivo: str) -> str:
    """Extrai texto de todas as abas de um arquivo Excel (.xlsx ou .xls)."""
    try:
        if caminho_arquivo.lower().endswith('.xlsx'):
            engine = 'openpyxl'
        elif caminho_arquivo.lower().endswith('.xls'):
            engine = 'xlrd'
        else:
            return "ERRO: Extensão de arquivo não reconhecida como Excel."

        df_dict = pd.read_excel(caminho_arquivo, engine=engine, sheet_name=None)
        if not df_dict:
            return "AVISO: O arquivo Excel foi lido, mas está vazio."

        texto_completo = []
        for nome_aba, df_aba in df_dict.items():
            texto_completo.append(f"--- Conteúdo da Aba: '{nome_aba}' ---")
            if not df_aba.empty:
                texto_completo.append(df_aba.to_string(index=False))
            else:
                texto_completo.append("(Aba vazia)")
        return "\n\n".join(texto_completo)
    except Exception as e:
        return f"ERRO ao ler Excel: {e}. O arquivo pode estar corrompido ou protegido."

# --- CONFIGURAÇÃO DO APP FLASK ---

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- LÓGICA PRINCIPAL (COM O NOVO PROMPT) ---

def processar_documento(caminho_arquivo: str, extensao: str) -> Dict[str, str]:
    """Processa o documento extraindo texto e chamando a API do Gemini com o prompt otimizado."""
    if not gemini_api_key:
        return {"erro": "A API Key do Gemini não está configurada. Verifique seu arquivo .env."}

    extractors = {'.docx': extrair_texto_docx, '.pdf': extrair_texto_pdf, '.xlsx': extrair_texto_excel, '.xls': extrair_texto_excel}
    extractor_func = extractors.get(extensao)

    if not extractor_func:
        return {"erro": f"Formato de arquivo '{extensao}' não é suportado."}

    texto_extraido = extractor_func(caminho_arquivo)

    if "ERRO:" in texto_extraido or not texto_extraido.strip():
        return {"erro": texto_extraido or "Não foi possível extrair conteúdo do documento."}

    print(f"Texto extraído com sucesso. Caracteres: {len(texto_extraido)}")

    # ===================================================================================
    # ============================ INÍCIO DO NOVO PROMPT ================================
    # ===================================================================================
    
    current_date = datetime.now().strftime("%d de %B de %Y")
    prompt = f"""
    Você é um avançado assistente de análise de dados e comunicação para a empresa MC Sonae. A data de hoje é {current_date}.
    Sua tarefa é analisar o texto de um relatório de projeto e gerar dois blocos de informação distintos: um comunicado em HTML e os dados estruturados para um dashboard em formato JSON.

    O texto bruto do relatório é:
    ---
    {texto_extraido}
    ---

    Por favor, estruture sua resposta EXATAMENTE da seguinte forma, usando os delimitadores ### para separar os blocos, sem adicionar textos ou explicações fora deles.

    ### BLOC-HTML ###
    <div class="comunicado">
        <h2>[Aqui vai o Título do Projeto ou Relatório]</h2>
        <p><strong>Resumo Executivo:</strong> [Aqui vai um parágrafo curto com os pontos mais importantes e o status atual do projeto].</p>
        <h3>Marcos Atingidos</h3>
        <ul>
            <li>[Descreva o Marco 1 que foi atingido]</li>
            <li>[Descreva o Marco 2 que foi atingido]</li>
        </ul>
        <h3>Tabela de Dados Relevantes</h3>
        [Se dados tabulares importantes forem encontrados, crie uma tabela HTML simples (<table><tr><th>...</th></tr><tr><td>...</td></tr></table>) aqui. Se não, escreva "<p>Não foram encontrados dados tabulares para exibição.</p>"]
        <h3>Próximos Passos</h3>
        <ul>
            <li>[Descreva o próximo passo 1]</li>
            <li>[Descreva o próximo passo 2]</li>
        </ul>
    </div>
    ### FIM-BLOCO-HTML ###

    ### BLOC-DASHBOARD-JSON ###
    [
      {{
        "tipo_visualizacao_sugerida": "grafico_barras",
        "titulo": "[Título descritivo para o gráfico, ex: 'Progresso das Tarefas por Área']",
        "dados": {{
          "labels": ["[Categoria 1, ex: 'Desenvolvimento']", "[Categoria 2, ex: 'Testes']"],
          "valores": ["[Valor 1, ex: 80]", "[Valor 2, ex: 60]"]
        }}
      }},
      {{
        "tipo_visualizacao_sugerida": "tabela",
        "titulo": "[Título descritivo para a tabela, ex: 'Status Detalhado das Entregas']",
        "dados": {{
          "colunas": ["ID da Tarefa", "Status", "Responsável"],
          "linhas": [
            ["PROJ-001", "Concluído", "Ana"],
            ["PROJ-002", "Em Andamento", "Bruno"]
          ]
        }}
      }},
      {{
        "tipo_visualizacao_sugerida": "kpi",
        "titulo": "[Título para o KPI, ex: 'Orçamento Executado']",
        "valor": "[Valor principal, ex: '75%']",
        "descricao": "[Breve descrição de contexto, ex: 'de um total de R$ 50.000']"
      }}
    ]
    ### FIM-BLOCO-DASHBOARD-JSON ###
    """
    
    # ===================================================================================
    # ============================= FIM DO NOVO PROMPT ==================================
    # ===================================================================================

    try:
        print("Chamando a API do Gemini...")
        
        # --- MÉTODO CORRETO DE CHAMADA DA API ---
        genai.configure(api_key=gemini_api_key)
        # Usamos um modelo conhecido e estável
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        response = model.generate_content(prompt)
        response_text = response.text
        print("Resposta recebida da API do Gemini.")

        # Extrai o conteúdo HTML de forma segura
        html_match = re.search(r"### BLOC-HTML ###(.*)### FIM-BLOCO-HTML ###", response_text, re.DOTALL)
        html_content = html_match.group(1).strip() if html_match else ""

        # Extrai o conteúdo JSON de forma segura
        json_match = re.search(r"### BLOC-DASHBOARD-JSON ###(.*)### FIM-BLOCO-DASHBOARD-JSON ###", response_text, re.DOTALL)
        json_content = json_match.group(1).strip() if json_match else "[]"

        # Garante que o JSON é válido antes de retornar
        try:
            json.loads(json_content)
        except json.JSONDecodeError:
            print("Aviso: A IA retornou um JSON inválido. Retornando uma lista vazia.")
            json_content = "[]"
        
        return {
            "resultado_html": html_content,
            "dashboard_sugestoes": json_content
        }

    except Exception as e:
        print(f"ERRO CRÍTICO ao chamar a API do Gemini: {e}")
        return {"erro": f"Ocorreu um erro ao comunicar com a IA. Detalhes: {e}"}

# --- ROTAS DO SITE (COM AJUSTE NO RETORNO) ---

@app.route('/')
def index() -> str:
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file() -> Union[Response, tuple[Response, int]]:
    try:
        if 'file' not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado."}), 400
        
        file: FileStorage | None = request.files.get('file')
        
        if not file or not file.filename:
            return jsonify({"erro": "Nenhum arquivo selecionado."}), 400

        filename = file.filename
        _, extensao = os.path.splitext(filename)
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(caminho_arquivo)
        resultado = processar_documento(caminho_arquivo, extensao.lower())
        os.remove(caminho_arquivo)
        
        # Ajuste para retornar o novo formato de dados para o frontend
        if "erro" in resultado:
            return jsonify(resultado), 500
        else:
            return jsonify({
                "html": resultado.get("resultado_html", ""),
                "dashboard": resultado.get("dashboard_sugestoes", "[]")
            })

    except Exception as e:
        print("===== OCORREU UM ERRO INESPERADO NA ROTA UPLOAD =====")
        print(traceback.format_exc())
        return jsonify({"erro": "Um erro inesperado ocorreu no servidor."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)