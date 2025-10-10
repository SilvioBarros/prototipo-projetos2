# prototipo-projetos2

## ⚙️ Instalação e Execução

Para configurar e executar o projeto localmente, siga os passos correspondentes ao seu sistema operacional.

---
### Para Windows 💻

1.  **Clone o Repositório:**
    Abra o PowerShell ou o Command Prompt e clone o projeto do GitHub.
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_AQUI]
    cd [NOME_DA_PASTA_DO_PROJETO]
    ```

2.  **Crie o Ambiente Virtual (`venv`):**
    Este comando cria uma pasta `venv` que isolará as dependências do projeto.
    ```bash
    python -m venv venv
    ```

3.  **Ative o Ambiente Virtual:**
    Você precisa ativar o `venv` em cada novo terminal que abrir para trabalhar no projeto.
    ```bash
    .\venv\Scripts\activate
    ```
    O seu terminal deverá agora mostrar `(venv)` no início da linha.

4.  **(Opcional) Atualize o `pip`:**
    É uma boa prática garantir que o instalador de pacotes esteja na sua versão mais recente.
    ```bash
    python.exe -m pip install --upgrade pip
    ```

5.  **Instale as Bibliotecas Necessárias:**
    Você pode instalar todas de uma vez (método rápido) ou uma por uma (para maior controle).

    > **Método Recomendado (Rápido):**
    > Cole o seguinte comando para instalar todas as dependências de uma vez.
    > ```bash
    > pip install flask google-generativeai pandas python-docx PyPDF2 openpyxl python-dotenv xlrd
    > ```

    > **Método Alternativo (Passo a Passo):**
    > Se preferir instalar cada biblioteca individualmente para maior controle ou para identificar possíveis problemas de instalação, execute os seguintes comandos, um por um:
    > ```bash
    > pip install flask
    > pip install google-generativeai
    > pip install pandas
    > pip install python-docx
    > pip install PyPDF2
    > pip install openpyxl
    > pip install python-dotenv
    > pip install xlrd
    > ```

6.  **Configure sua Chave de API:**
    Crie um arquivo chamado `.env` na pasta principal do projeto. Dentro dele, adicione sua chave da API do Gemini, substituindo `SUA_CHAVE_AQUI`.
    ```
    GEMINI_API_KEY="SUA_CHAVE_AQUI"
    ```

7.  **Execute a Aplicação:**
    Com o `venv` ativo, inicie o servidor Flask.
    ```bash
    python app.py
    ```

8.  **Acesse no Navegador:**
    Abra seu navegador e acesse o endereço: [http://127.0.0.1:5001](http://127.0.0.1:5001)

---
### Para Linux e macOS 🐧🍏

1.  **Clone o Repositório:**
    Abra o seu terminal e clone o projeto do GitHub.
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_AQUI]
    cd [NOME_DA_PASTA_DO_PROJETO]
    ```

2.  **Crie o Ambiente Virtual (`venv`):**
    Use `python3` para garantir que está usando a versão correta do Python.
    ```bash
    python3 -m venv venv
    ```

3.  **Ative o Ambiente Virtual:**
    Ative o `venv` para a sua sessão atual do terminal.
    ```bash
    source venv/bin/activate
    ```
    O seu terminal deverá agora mostrar `(venv)` no início da linha.

4.  **(Opcional) Atualize o `pip`:**
    Mantenha o instalador de pacotes atualizado.
    ```bash
    python -m pip install --upgrade pip
    ```

5.  **Instale as Bibliotecas Necessárias:**
    Você pode escolher o método rápido ou o passo a passo.

    > **Método Recomendado (Rápido):**
    > Cole o seguinte comando para instalar todas as dependências de uma vez.
    > ```bash
    > pip install flask google-generativeai pandas python-docx PyPDF2 openpyxl python-dotenv xlrd
    > ```

    > **Método Alternativo (Passo a Passo):**
    > Se preferir instalar cada biblioteca individualmente para maior controle, execute os seguintes comandos, um por um:
    > ```bash
    > pip install flask
    > pip install google-generativeai
    > pip install pandas
    > pip install python-docx
    > pip install PyPDF2
    > pip install openpyxl
    > pip install python-dotenv
    > pip install xlrd
    > ```

6.  **Configure sua Chave de API:**
    Crie um arquivo chamado `.env` na pasta principal do projeto. Dentro dele, adicione sua chave da API do Gemini.
    ```
    GEMINI_API_KEY="SUA_CHAVE_AQUI"
    ```

7.  **Execute a Aplicação:**
    Com o `venv` ativo, inicie o servidor Flask.
    ```bash
    python app.py
    ```

8.  **Acesse no Navegador:**
    Abra seu navegador e acesse o endereço: [http://127.0.0.1:5001](http://127.0.0.1:5001)
