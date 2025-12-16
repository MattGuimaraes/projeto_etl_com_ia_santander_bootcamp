import os
import re
import textwrap
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

from google import genai
from google.genai import errors

from colorama import Fore, Style, init as colorama_init


# =========================
# (cores no terminal)
# =========================

colorama_init(autoreset=True)


# =========================
# CONFIGURAÇÃO
# =========================

@dataclass(frozen=True)
class Settings:
    api_url: str
    csv_path: str
    gemini_api_key: Optional[str]
    gemini_model: str
    icon_url: str
    timeout_sec: int = 20
    report_path: str = "report_etl.csv"

    wrap_news_width: int = 75  

def load_settings() -> Settings:
    load_dotenv()

    api_url = os.getenv("API_URL", "https://usersapipython.up.railway.app").rstrip("/")
    csv_path = os.getenv("CSV_PATH", "data/users_ids.csv")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    icon_url = os.getenv(
        "ICON_URL",
        "https://digitalinnovationone.github.io/santander-dev-week-2023-api/icons/credit.svg",
    )

    report_path = os.getenv("REPORT_PATH", "report_etl.csv")
    wrap_news_width = int(os.getenv("WRAP_NEWS_WIDTH", "75"))

    return Settings(
        api_url=api_url,
        csv_path=csv_path,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        icon_url=icon_url,
        report_path=report_path,
        wrap_news_width=wrap_news_width,
    )


# =========================
# UI / LOGS
# =========================

LINE = "=" * 60


def info(msg: str) -> None:
    print(Fore.GREEN + f"[INFO] {msg}" + Style.RESET_ALL)


def ok(msg: str) -> None:
    print(Fore.CYAN + f"[OK] {msg}" + Style.RESET_ALL)


def warn(msg: str) -> None:
    print(Fore.YELLOW + f"[WARN] {msg}" + Style.RESET_ALL)


def error(msg: str) -> None:
    print(Fore.RED + f"[ERROR] {msg}" + Style.RESET_ALL)


def done(msg: str) -> None:
    print(Fore.GREEN + f"[DONE] {msg}" + Style.RESET_ALL)


def separator() -> None:
    print("\n" + LINE + "\n")


# =========================
# UTIL
# =========================

def clean_text(text: str) -> str:
    """
    Remove formatação/markdown simples que pode confundir leigos.
    """
    text = (text or "").strip()

    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    text = text.replace("*", "")

    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_brl(value: float) -> str:
    """
    Formata número como moeda pt-BR sem depender de locale do sistema.
    Ex: 20000.0 -> R$ 20.000,00
    """
    try:
        n = float(value)
    except Exception:
        n = 0.0

    s = f"{n:,.2f}"  
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def wrap_text(text: str, width: int) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


# =========================
# EXTRACT (CSV -> IDs)
# =========================

def read_user_ids(csv_path: str) -> List[int]:
    df = pd.read_csv(csv_path)

    col_candidates = ["user_id", "UserID"]
    col = next((c for c in col_candidates if c in df.columns), None)
    if col is None:
        raise ValueError(
            f"CSV precisa ter coluna 'user_id' ou 'UserID'. Colunas encontradas: {list(df.columns)}"
        )

    ids = df[col].dropna().astype(int).tolist()
    if not ids:
        raise ValueError("Nenhum ID encontrado no CSV.")
    return ids


# =========================
# EXTRACT (API -> Users)
# =========================

def get_user(api_url: str, user_id: int, timeout_sec: int) -> Optional[Dict[str, Any]]:
    url = f"{api_url}/usuario/{user_id}"
    resp = requests.get(url, timeout=timeout_sec)

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code == 404:
        warn(f"Usuário {user_id} não encontrado na API (404). Ignorando.")
        return None

    error(f"GET {url} -> {resp.status_code} | {resp.text[:200]}")
    return None


# =========================
# TABELA LEGÍVEL
# =========================

def print_users_table(users: List[Dict[str, Any]], wrap_width: int) -> None:
    """
    Mostra resumo em tabela, com:
    - Saldo/Limite em moeda BR
    - Última News com quebra automática de linha (sem perder texto)
    """
    rows = []
    for u in users:
        conta = u.get("conta", {}) or {}
        news_list = u.get("news", []) or []
        last_news = news_list[-1].get("descricao", "") if news_list else ""

        balanco = float(conta.get("balanco", 0.0) or 0.0)
        limite = float(conta.get("limite", 0.0) or 0.0)

        rows.append(
            {
                "ID": u.get("id"),
                "Nome": u.get("nome"),
                "Agência": conta.get("agencia", ""),
                "Conta": conta.get("numero", ""),
                "Saldo": format_brl(balanco),
                "Limite": format_brl(limite),
                "Qtd News": len(news_list),
                "Última News": wrap_text(clean_text(last_news), wrap_width),
            }
        )

    df = pd.DataFrame(rows).sort_values(by="ID")

    with pd.option_context("display.max_colwidth", None, "display.width", 160):
        print(df.to_string(index=False))


# =========================
# TRANSFORM (Gemini -> News)
# =========================

def next_news_id(user: Dict[str, Any]) -> int:
    news_list = user.get("news", []) or []
    if not news_list:
        return 1
    return max(int(n.get("id", 0)) for n in news_list) + 1


def generate_ai_news_gemini(client: genai.Client, model: str, user: Dict[str, Any]) -> str:
    nome = user.get("nome", "Cliente")

    prompt = (
        "Você é um especialista em marketing bancário.\n"
        f"Crie uma mensagem para {nome} sobre a importância dos investimentos "
        "(máximo de 100 caracteres)."
    )

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = clean_text(getattr(response, "text", "") or "")

        if not text:
            text = f"{nome}, investir com consistência fortalece seu futuro financeiro."

        return text[:100]

    except errors.APIError as e:
        error(f"Gemini APIError {getattr(e, 'code', 'N/A')}: {getattr(e, 'message', str(e))}")
        return clean_text(f"{nome}, investir com consistência fortalece seu futuro financeiro.")[:100]
    except Exception as e:
        error(f"Gemini erro inesperado: {e}")
        return clean_text(f"{nome}, investir com consistência fortalece seu futuro financeiro.")[:100]


def transform_add_news_gemini(settings: Settings, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY não encontrada. Configure no .env ou variável de ambiente.")

    client = genai.Client(api_key=settings.gemini_api_key)

    for u in users:
        msg = generate_ai_news_gemini(client, settings.gemini_model, u)
        length = len(msg)

        u.setdefault("news", [])
        u["news"].append(
            {
                "id": next_news_id(u),
                "icone": settings.icon_url,
                "descricao": msg,
            }
        )

        ok(f"News (Gemini) gerada para {u.get('nome')} -> {msg} ({length} caracteres)")

    try:
        client.close()
    except Exception:
        pass

    return users


# =========================
# LOAD (PUT -> API)
# =========================

def update_user(api_url: str, user: Dict[str, Any], timeout_sec: int) -> bool:
    user_id = user.get("id")
    url = f"{api_url}/usuario/{user_id}"

    resp = requests.put(url, json=user, timeout=timeout_sec)
    if resp.status_code == 200:
        return True

    error(f"PUT {url} -> {resp.status_code} | {resp.text[:200]}")
    return False


# =========================
# REPORT (Excel)
# =========================

def save_report_csv(users: List[Dict[str, Any]], path: str) -> None:
    rows = []
    for u in users:
        conta = u.get("conta", {}) or {}
        news_list = u.get("news", []) or []
        last_news = news_list[-1].get("descricao", "") if news_list else ""

        rows.append(
            {
                "user_id": u.get("id"),
                "nome": u.get("nome"),
                "agencia": conta.get("agencia", ""),
                "conta": conta.get("numero", ""),
                "balanco": conta.get("balanco", 0.0),
                "limite": conta.get("limite", 0.0),
                "qtd_news_total": len(news_list),
                "ultima_news": clean_text(last_news),
            }
        )

    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    info(f"Relatório gerado para Excel: {path}")


# =========================
# MAIN
# =========================

def main():
    settings = load_settings()

    info(f"API_URL={settings.api_url}")
    info(f"CSV_PATH={settings.csv_path}")
    info(f"GEMINI_MODEL={settings.gemini_model}")

    user_ids = read_user_ids(settings.csv_path)
    info(f"IDs do CSV: {user_ids}")

    separator()

    users: List[Dict[str, Any]] = []
    for uid in user_ids:
        u = get_user(settings.api_url, uid, settings.timeout_sec)
        if u:
            users.append(u)

    if not users:
        raise RuntimeError("Nenhum usuário válido foi carregado da API.")

    info("Usuários carregados da API (resumo):\n")
    print_users_table(users, wrap_width=settings.wrap_news_width)

    separator()

    users = transform_add_news_gemini(settings, users)

    separator()

    save_report_csv(users, settings.report_path)

    ok_count = 0
    for u in users:
        if update_user(settings.api_url, u, settings.timeout_sec):
            ok_count += 1

    done(f"Atualizações concluídas: {ok_count}/{len(users)}")
    done(f"Abra o relatório no Excel: {settings.report_path}")


if __name__ == "__main__":
    main()
