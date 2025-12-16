# 🚀 ETL Pipeline com IA Generativa (Python)

Pipeline **ETL (Extract, Transform, Load)** desenvolvido em **Python**, integrando uma **API REST própria**, processamento de dados via CSV e **IA Generativa (Google Gemini)** para enriquecimento automático de dados.

O projeto foi construído como parte do desafio  
**“Explorando IA Generativa em um Pipeline de ETL com Python”**, do **Bootcamp Santander 2025 – Ciência de Dados com Python**, com foco em **arquitetura, integração de serviços e boas práticas**, indo além de um simples script demonstrativo.

---

## 🎯 Objetivo do Projeto

Demonstrar, de forma prática e profissional, como:

- Consumir dados estruturados a partir de arquivos CSV;
- Integrar sistemas via **API REST**;
- Enriquecer dados com **IA Generativa**, respeitando limites técnicos (custo, quota e governança);
- Persistir atualizações de volta em uma API;
- Apresentar resultados de forma **legível para usuários não técnicos**.

Este repositório representa **o pipeline ETL**.  
A **API de usuários** utilizada como fonte e destino dos dados está em um **repositório separado**, reforçando a separação de responsabilidades.

---

## 🧱 Arquitetura da Solução

```text
CSV (IDs de usuários)
        ↓
[ Extract ]
Leitura do CSV + validação
        ↓
[ Extract ]
GET /usuario/{id} (API REST)
        ↓
[ Transform ]
IA Generativa (Google Gemini)
Criação de mensagens personalizadas
        ↓
[ Load ]
PUT /usuario/{id} (API REST)
        ↓
Relatório CSV + saída amigável no terminal
