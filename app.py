import os
import concurrent.futures
import requests
from litellm import completion
from dotenv import load_dotenv

# Carrega as chaves salvas no arquivo .env ou nos Secrets do Codespaces
load_dotenv()

# Configuração das 10 APIs baseadas na lista escolhida
# Nota: Muitas usam formatos idênticos (OpenAI compatible) mapeados pelo LiteLLM ou URLs diretas
CONFIG_APIS = {
    "1. Groq (Llama 3.3)": {
        "model": "groq/llama-3.3-70b-versatile",
        "api_key": os.getenv("GROQ_API_KEY")
    },
    "2. Google Gemini (Flash)": {
        "model": "gemini/gemini-2.5-flash",
        "api_key": os.getenv("GEMINI_API_KEY")
    },
    "3. Cerebras (Llama 3.1)": {
        "model": "cerebras/llama3.1-8b",
        "api_key": os.getenv("CEREBRAS_API_KEY")
    },
    "4. OpenRouter (Mistral Free)": {
        "model": "openrouter/mistralai/mistral-7b-instruct:free",
        "api_key": os.getenv("OPENROUTER_API_KEY")
    },
    "5. SiliconFlow (Qwen 2.5)": {
        "model": "openai/qwen/qwen2.5-72b-instruct", # Formato Custom OpenAI
        "api_key": os.getenv("SILICONFLOW_API_KEY"),
        "api_base": "https://siliconflow.cn"
    },
    "6. NVIDIA NIM (Phi-3)": {
        "model": "openai/microsoft/phi-3-medium-128k-instruct",
        "api_key": os.getenv("NVIDIA_API_KEY"),
        "api_base": "https://nvidia.com"
    },
    "7. Mistral AI (Codestral)": {
        "model": "mistral/codestral-latest",
        "api_key": os.getenv("MISTRAL_API_KEY")
    },
    "8. Cloudflare Workers AI": {
        "model": "cloudflare/@cf/meta/llama-3-8b-instruct",
        "api_key": os.getenv("CLOUDFLARE_API_KEY"),
        "cf_account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID")
    },
    "10. Kilo Code / LLM7": {
        "model": "openai/qwen-2.5-72b",
        "api_key": os.getenv("LLM7_API_KEY", "free-key"),
        "api_base": "https://llm7.net"
    }
}

def chamar_api_litellm(nome, config, prompt):
    """Chama os provedores gerenciados pelo LiteLLM"""
    if not config["api_key"] and "LLM7" not in nome:
        return f"❌ Chave ausente (Configure {nome.split(' ')[1].upper()}_API_KEY)"
    
    try:
        # Define os parâmetros de ambiente temporariamente para o LiteLLM ler
        kwargs = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "api_key": config["api_key"],
            "timeout": 15
        }
        if "api_base" in config:
            kwargs["api_base"] = config["api_base"]
            
        resposta = completion(**kwargs)
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def chamar_pollinations_anonimo(prompt):
    """Chama a API 9 (Pollinations) via requisição HTTP direta (Sem chave)"""
    url = f"https://pollinations.ai{prompt}"
    try:
        resposta = requests.get(url, timeout=15)
        if resposta.status_code == 200:
            return resposta.text.strip()
        return f"❌ Erro HTTP {resposta.status_code}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def consultar_todas_as_llms(prompt):
    print(f"🤖 Enviando o prompt para as 10 LLMs em paralelo...\nPrompt: '{prompt}'\n" + "="*50 + "\n")
    
    resultados = {}
    
    # Executa todas de forma assíncrona/paralela para economizar tempo
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futuros = {
            executor.submit(chamar_api_litellm, nome, dados, prompt): nome 
            for nome, dados in CONFIG_APIS.items()
        }
        # Adiciona a anônima do Pollinations separadamente
        futuros[executor.submit(chamar_pollinations_anonimo, prompt)] = "9. Pollinations (Anônimo/Sem Chave)"
        
        for futuro in concurrent.futures.as_completed(futuros):
            nome_provedor = futuros[futuro]
            try:
                resultados[nome_provedor] = futuro.result()
            except Exception as e:
                resultados[nome_provedor] = f"❌ Falha crítica: {e}"

    # Exibe os resultados organizados por ordem alfabética/numérica
    for nome in sorted(resultados.keys()):
        print(f"=== {nome} ===")
        print(resultados[nome])
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    # DIGITE A SUA PERGUNTA AQUI
    pergunta = "Explique em uma frase curta o que é computação quântica."
    consultar_todas_as_llms(pergunta)
