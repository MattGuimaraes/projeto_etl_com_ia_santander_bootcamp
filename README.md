# 📌 ETL Pipeline com IA Generativa (Python)

Pipeline ETL desenvolvido em Python que integra **CSV**, **API REST** e **IA Generativa** para enriquecer dados de usuários e persistir atualizações automaticamente.

O projeto foi construído a partir do desafio  
**“Explorando IA Generativa em um Pipeline de ETL com Python”**, do **Bootcamp Santander 2025 — Ciência de Dados com Python**.

---

## 🚀 Visão Geral

- Leitura de IDs a partir de um arquivo CSV;
- Extração de dados via API REST (FastAPI);
- Enriquecimento das informações com IA Generativa (Google Gemini);
- Persistência das atualizações na API;
- Geração de relatório final em CSV e visualização amigável no terminal.

---

## 🏛️ Arquitetura

![Arquitetura do Pipeline ETL](diagrams/arquitetura.png)

### Fluxo de Execução
![Fluxo de Execução](diagrams/fluxo_de_execução.png)
---

## 🛠️ Tecnologias Utilizadas

- Python  
- Pandas  
- Requests  
- FastAPI (API externa consumida)  
- Google Gemini (IA Generativa)  
- CSV / HTTP / JSON  

---

## 💻 Execução Local

```
pip install -r requirements.txt
python etl.py
```

## 🔀 Projeto Relacionado
- Users API (FASTApi + Railway)
  API REST utilizada como fonte e destino dos dados:
  **[https://usersapipython.up.railway.app/docs].**

# 🙋🏻 Autor
**Matheus Guimarães**
Estudante de Análise e Desenvolvimento de Sistemas | Dados | IA
