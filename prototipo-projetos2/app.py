# app.py (versão final para múltiplos arquivos e foco combinado)

# python -m venv venv <-- usado para criar um ambiente virtual
# venv\Scripts\activate <-- Windows
# source venv/bin/activate <-- macOS/Linux
# python.exe -m pip install --upgrade pip <-- atualizar pip

# IMPORTE NO TERMINAL TODAS AS BIBLIOTECAS NECESSÁRIAS ABAIXO:

# import os
# import traceback
# import re
# import json
# from typing import Dict, Union
# from datetime import datetime
# import docx
# import google.generativeai as genai
# import pandas as pd
# import PyPDF2
# from flask import Flask, Response, jsonify, render_template, request
# from werkzeug.datastructures import FileStorage
# from dotenv import load_dotenv



import os
import traceback
import re
import json
from typing import Dict, Union, List
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

# --- FUNÇÕES DE EXTRAÇÃO DE TEXTO (sem alterações) ---

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

# --- LÓGICA PRINCIPAL (COM O NOVO PROMPT MULTI-DOCUMENTO) ---

# MUDANÇA: A função agora recebe um único bloco de texto concatenado
def processar_documento_combinado(texto_concatenado: str, foco_usuario: str) -> Dict[str, str]:
    """Processa um bloco de texto concatenado de múltiplos documentos."""
    if not gemini_api_key:
        return {"erro": "A API Key do Gemini não está configurada. Verifique seu arquivo .env."}

    # ============================ INÍCIO DO NOVO PROMPT ================================
    
    instrucao_foco = ""
    if foco_usuario:
        instrucao_foco = f"""
        INSTRUÇÃO PRIORITÁRIA DO USUÁRIO: O usuário forneceu um foco específico para a análise combinada: "{foco_usuario}".
        Sua tarefa é ler TODOS os textos dos documentos fornecidos e sintetizar uma resposta única e coesa que atenda a esta solicitação. Encontre as informações relevantes em cada documento e combine-as.
        """
    else:
        instrucao_foco = "INSTRUÇÃO: Como o usuário não especificou um foco, crie um resumo geral combinando os pontos principais de todos os documentos fornecidos."
    
# (Dentro da função processar_documento_combinado)

    # ... (o código para criar a instrucao_foco continua o mesmo) ...

    current_date = datetime.now().strftime("%d de %B de %Y")
    prompt = f"""
    Você é um avançado e rigoroso assistente de análise de dados para a empresa MC Sonae. A data de hoje é {current_date}.

    --- REGRAS FUNDAMENTAIS ---
    1.  Sua resposta deve se basear **ESTRITA E EXCLUSIVAMENTE** no conteúdo dos textos fornecidos no bloco "texto bruto dos documentos".
    2.  É **PROIBIDO** buscar ou inferir qualquer informação externa da internet ou de seu conhecimento prévio.
    3.  Se um documento não contiver informações suficientes para preencher uma seção (como a tabela) ou para atender ao foco do usuário, preencha a seção correspondente com a frase **"Informação Não Processada"**. Não invente ou deduza dados.
    4.  A geração de uma tabela de dados para cada documento é **OBRIGATÓRIA**.

    {instrucao_foco}

    Sua tarefa principal é analisar o texto dos documentos fornecidos e gerar uma resposta consolidada, seguindo as regras acima. Os documentos estão separados por delimitadores "--- INÍCIO/FIM DO DOCUMENTO ---".

    O texto bruto dos documentos é:
    ---
    {texto_concatenado}
    ---

    Estruture sua resposta EXATAMENTE da seguinte forma:

    ### BLOC-HTML-CONJUNTO ###
    <details class="resumo-documento" open>
        <summary>
            <i class="fa-solid fa-file-pdf"></i> <strong>Análise do Documento:</strong> [aqui vai o nome do primeiro arquivo]
        </summary>
        <div class="conteudo-documento">
            <p><strong>Resumo Executivo deste Documento:</strong> [Aqui vai um parágrafo de resumo focado APENAS neste documento e baseado estritamente nas informações contidas nele].</p>
            
            <h4>Marcos Atingidos / Pontos-Chave:</h4>
            <ul>
                <li>[Insight 1 extraído especificamente deste arquivo]</li>
            </ul>

            <h4>Tabela de Dados Extraídos:</h4>
            [Crie OBRIGATORIAMENTE uma tabela HTML (`<table>`) aqui, resumindo os principais dados quantitativos ou pontos-chave do texto em formato de tabela. Extraia pelo menos 2-3 pontos-chave para a tabela. Se não encontrar dados suficientes, a tabela deve conter apenas a frase "Informação Não Processada".]
        </div>
    </details>
    
    ### FIM-BLOCO-HTML-CONJUNTO ###

    ### BLOC-DASHBOARD-JSON ###
    [
      {{
        "tipo_visualizacao_sugerida": "tabela",
        "titulo": "[Título para a tabela combinada, baseado no foco e nos dados reais dos documentos]",
        "dados": {{
          "colunas": ["Fonte do Documento", "Informação Chave Extraída"],
          "linhas": [
            ["[nome_do_arquivo.pdf]", "[Principal insight quantitativo ou qualitativo encontrado]"],
            ["[nome_do_outro_arquivo.docx]", "[Principal insight quantitativo ou qualitativo encontrado]"]
          ]
        }}
      }}
    ]
    ### FIM-BLOCO-DASHBOARD-JSON ###
    """

    
    # ============================= FIM DO NOVO PROMPT ==================================
    
    try:
        print("Chamando a API do Gemini com texto combinado...")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        response = model.generate_content(prompt)
        response_text = response.text
        print("Resposta combinada recebida da API do Gemini.")

        # Linhas novas
        html_match = re.search(r"### BLOC-HTML-CONJUNTO ###(.*)### FIM-BLOCO-HTML-CONJUNTO ###", response_text, re.DOTALL)
        html_content = html_match.group(1).strip() if html_match else ""

        json_match = re.search(r"### BLOC-DASHBOARD-JSON ###(.*)### FIM-BLOCO-DASHBOARD-JSON ###", response_text, re.DOTALL)
        json_content = json_match.group(1).strip() if json_match else "[]"

        try:
            json.loads(json_content)
        except json.JSONDecodeError:
            print("Aviso: A IA retornou um JSON inválido.")
            json_content = "[]"
        
        return { "resultado_html": html_content, "dashboard_sugestoes": json_content }

    except Exception as e:
        print(f"ERRO CRÍTICO ao chamar a API do Gemini: {e}")
        return {"erro": f"Ocorreu um erro ao comunicar com a IA. Detalhes: {e}"}

# --- ROTAS DO SITE (COM GRANDES MUDANÇAS NA ROTA /upload) ---

@app.route('/')
def index() -> str:
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file() -> Union[Response, tuple[Response, int]]:
    try:
        # MUDANÇA: Usar getlist para receber múltiplos arquivos
        uploaded_files: List[FileStorage] = request.files.getlist('files')
        foco_usuario = request.form.get('foco', '')

        if not uploaded_files or not uploaded_files[0].filename:
            return jsonify({"erro": "Nenhum arquivo enviado."}), 400
        
        textos_concatenados = []
        arquivos_processados_paths = []

        # MUDANÇA: Loop para processar cada arquivo enviado
        for file in uploaded_files:
            if file and file.filename:
                filename = file.filename
                _, extensao = os.path.splitext(filename)
                caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                file.save(caminho_arquivo)
                arquivos_processados_paths.append(caminho_arquivo)

                extractors = {'.docx': extrair_texto_docx, '.pdf': extrair_texto_pdf, '.xlsx': extrair_texto_excel, '.xls': extrair_texto_excel}
                extractor_func = extractors.get(extensao.lower())

                if extractor_func:
                    texto_extraido = extractor_func(caminho_arquivo)
                    # Adiciona o texto extraído com delimitadores claros
                    textos_concatenados.append(f"--- INÍCIO DO DOCUMENTO: {filename} ---\n\n{texto_extraido}\n\n--- FIM DO DOCUMENTO: {filename} ---")
                
        # Limpa os arquivos salvos no disco após a extração
        for path in arquivos_processados_paths:
            os.remove(path)

        if not textos_concatenados:
             return jsonify({"erro": "Não foi possível extrair texto de nenhum dos arquivos."}), 500

        # MUDANÇA: Junta todos os textos em um bloco só, separados por duas quebras de linha
        texto_final_concatenado = "\n\n".join(textos_concatenados)
        
        # MUDANÇA: Chama a função de processamento com o texto combinado
        resultado = processar_documento_combinado(texto_final_concatenado, foco_usuario)
        
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