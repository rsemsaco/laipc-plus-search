from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
TITLE_FILL = PatternFill("solid", fgColor="17365D")
TITLE_FONT = Font(color="FFFFFF", bold=True, size=16)
SUBTITLE_FONT = Font(color="666666", italic=True)
HIGH_FILL = PatternFill("solid", fgColor="FCE4D6")
MEDIUM_FILL = PatternFill("solid", fgColor="FFF2CC")
EXPLORE_FILL = PatternFill("solid", fgColor="E2F0D9")
KNOWN_FILL = PatternFill("solid", fgColor="E2F0D9")
DATASET_FILL = PatternFill("solid", fgColor="DDEBF7")
REVIEW_FILL = PatternFill("solid", fgColor="FCE4D6")
LINK_FONT = Font(color="0563C1", underline="single")


CANDIDATE_FIELDS = [
    "record_uid",
    "candidate_rank",
    "corpus_status",
    "retrieval_priority",
    "retrieval_priority_score",
    "record_kind",
    "title",
    "year",
    "authors",
    "doi",
    "pmid",
    "pmcid",
    "journal",
    "publisher",
    "article_url",
    "dataset_url",
    "sources",
    "hit_count",
    "query_ids",
    "query_families",
    "has_data_signal",
    "has_supplement",
    "is_open_access",
    "has_pdf",
    "has_fulltext",
    "behavior_term_hits",
    "stress_model_hits",
    "priority_reasons",
    "related_dois",
    "abstract",
    "known_id",
    "known_scientific_fit",
    "known_data_reuse",
    "known_prior_priority",
    "triagem_gpt",
    "motivo_triagem",
    "pdf_necessario",
    "dataset_necessario",
    "s_provisorio",
    "d_provisorio",
    "work_status",
]


FIELD_LABELS = {
    "record_uid": "ID estável",
    "candidate_rank": "Ordem",
    "corpus_status": "Status corpus",
    "retrieval_priority": "Prioridade",
    "retrieval_priority_score": "Score",
    "record_kind": "Tipo",
    "title": "Título",
    "year": "Ano",
    "authors": "Autores",
    "doi": "DOI",
    "pmid": "PMID",
    "pmcid": "PMCID",
    "journal": "Periódico",
    "publisher": "Publicador",
    "article_url": "URL artigo",
    "dataset_url": "URL dataset",
    "sources": "Fontes",
    "hit_count": "Ocorrências",
    "query_ids": "Queries",
    "query_families": "Famílias de busca",
    "has_data_signal": "Sinal de dados",
    "has_supplement": "Suplemento",
    "is_open_access": "Open access",
    "has_pdf": "PDF",
    "has_fulltext": "Texto completo",
    "behavior_term_hits": "Ensaios detectados",
    "stress_model_hits": "Modelos detectados",
    "priority_reasons": "Motivos da prioridade",
    "related_dois": "DOIs relacionados",
    "abstract": "Abstract",
    "known_id": "ID conhecido",
    "known_scientific_fit": "S prévio",
    "known_data_reuse": "D prévio",
    "known_prior_priority": "P prévia",
    "triagem_gpt": "Triagem GPT",
    "motivo_triagem": "Motivo da triagem",
    "pdf_necessario": "PDF necessário?",
    "dataset_necessario": "Dataset necessário?",
    "s_provisorio": "S provisório",
    "d_provisorio": "D provisório",
    "work_status": "Status Work",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = ILLEGAL_CHARACTERS_RE.sub("", text)
    return text


def excel_safe(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False)
    elif isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            value = "; ".join(
                " | ".join(
                    filter(
                        None,
                        [
                            clean_text(item.get("doi") or item.get("identifier")),
                            clean_text(item.get("relation_type")),
                        ],
                    )
                )
                for item in value
            )
        else:
            value = "; ".join(clean_text(item) for item in value)
    text = clean_text(value)
    return text[:32000]


def stable_uid(record: dict[str, Any]) -> str:
    identity = str(
        record.get("dedup_key")
        or record.get("doi")
        or record.get("pmid")
        or record.get("pmcid")
        or record.get("title")
        or "unknown"
    )
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10].upper()
    return f"LAP-{digest}"


def prepare_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    enriched: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        item["record_uid"] = stable_uid(item)
        item["candidate_rank"] = ""
        for field in (
            "triagem_gpt",
            "motivo_triagem",
            "pdf_necessario",
            "dataset_necessario",
            "s_provisorio",
            "d_provisorio",
            "work_status",
        ):
            item[field] = ""
        enriched.append(item)

    candidates = [
        item
        for item in enriched
        if item.get("corpus_status") in {"NEW", "RELATED_TO_KNOWN"}
    ]
    for index, item in enumerate(candidates, start=1):
        item["candidate_rank"] = index

    handoff = [
        item
        for item in candidates
        if item.get("retrieval_priority") == "Alta"
        or item.get("record_kind") == "dataset"
    ]
    return enriched, candidates, handoff


def _csv_value(value: Any) -> str | int | float:
    if isinstance(value, (int, float)):
        return value
    return excel_safe(value)


def write_flat_csv(path: Path, records: list[dict[str, Any]], fields: list[str] = CANDIDATE_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: _csv_value(record.get(field)) for field in fields})


def _apply_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30


def _priority_fill(priority: str):
    if priority == "Alta":
        return HIGH_FILL
    if priority == "Media":
        return MEDIUM_FILL
    return EXPLORE_FILL


def _write_table_sheet(
    wb: Workbook,
    name: str,
    records: list[dict[str, Any]],
    fields: list[str] = CANDIDATE_FIELDS,
) -> None:
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    headers = [FIELD_LABELS.get(field, field) for field in fields]
    ws.append(headers)
    _apply_header(ws)

    for record in records:
        row_values = [excel_safe(record.get(field)) for field in fields]
        ws.append(row_values)
        row_index = ws.max_row

        fill = _priority_fill(str(record.get("retrieval_priority") or ""))
        if record.get("corpus_status") == "KNOWN":
            fill = KNOWN_FILL
        elif record.get("record_kind") == "dataset":
            fill = DATASET_FILL

        for cell in ws[row_index]:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

        for field in ("retrieval_priority", "corpus_status", "record_kind"):
            if field in fields:
                col = fields.index(field) + 1
                ws.cell(row=row_index, column=col).fill = fill

        for field in (
            "triagem_gpt",
            "motivo_triagem",
            "pdf_necessario",
            "dataset_necessario",
            "s_provisorio",
            "d_provisorio",
            "work_status",
        ):
            if field in fields:
                col = fields.index(field) + 1
                ws.cell(row=row_index, column=col).fill = REVIEW_FILL

        for field in ("article_url", "dataset_url"):
            if field not in fields:
                continue
            col = fields.index(field) + 1
            cell = ws.cell(row=row_index, column=col)
            value = str(cell.value or "")
            if value.startswith(("http://", "https://")):
                cell.hyperlink = value
                cell.font = LINK_FONT

    if ws.max_row > 1:
        ws.auto_filter.ref = ws.dimensions

    width_overrides = {
        "A": 16,
        "B": 9,
        "C": 20,
        "D": 14,
        "E": 10,
        "F": 12,
        "G": 55,
        "H": 9,
        "I": 32,
        "J": 28,
        "K": 14,
        "L": 14,
        "M": 24,
        "N": 24,
        "O": 42,
        "P": 42,
    }
    for col_index in range(1, len(fields) + 1):
        letter = get_column_letter(col_index)
        ws.column_dimensions[letter].width = width_overrides.get(letter, 22)

    if "abstract" in fields:
        ws.column_dimensions[get_column_letter(fields.index("abstract") + 1)].width = 75
    if "priority_reasons" in fields:
        ws.column_dimensions[get_column_letter(fields.index("priority_reasons") + 1)].width = 42
    if "related_dois" in fields:
        ws.column_dimensions[get_column_letter(fields.index("related_dois") + 1)].width = 42


def _write_summary_sheet(
    wb: Workbook,
    profile: dict[str, Any],
    audit: dict[str, Any],
    run: dict[str, Any],
    candidate_count: int,
    handoff_count: int,
    executed_at: str,
) -> None:
    ws = wb.active
    ws.title = "Resumo"
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:D1")
    ws["A1"] = "LAIPC+ Search — Entrega prática"
    ws["A1"].fill = TITLE_FILL
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:D2")
    ws["A2"] = clean_text(profile.get("research_question"))
    ws["A2"].font = SUBTITLE_FONT
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 45

    status = audit.get("status_counts") or {}
    priority = audit.get("priority_counts") or {}
    rows = [
        ("Executado em (UTC)", executed_at),
        ("Perfil", profile.get("profile_id")),
        ("Providers", ", ".join(run.get("providers") or [])),
        ("Queries", audit.get("query_count") or run.get("query_count")),
        ("Registros brutos", audit.get("raw_record_count")),
        ("Registros únicos", audit.get("unique_record_count")),
        ("Duplicatas removidas", audit.get("duplicates_removed")),
        ("Artigos únicos", audit.get("article_count")),
        ("Datasets únicos", audit.get("dataset_count")),
        ("Corpus conhecido", audit.get("known_corpus_count")),
        ("KNOWN encontrados", status.get("KNOWN", 0)),
        ("RELATED_TO_KNOWN", status.get("RELATED_TO_KNOWN", 0)),
        ("NEW", status.get("NEW", 0)),
        ("Prioridade Alta", priority.get("Alta", 0)),
        ("Prioridade Média", priority.get("Media", 0)),
        ("Exploratória", priority.get("Exploratoria", 0)),
        ("Candidatos para triagem", candidate_count),
        ("Registros no Work handoff", handoff_count),
    ]

    start = 4
    for offset, (label, value) in enumerate(rows):
        row = start + offset
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=excel_safe(value))
        ws.cell(row=row, column=1).font = Font(bold=True, color="666666")
        ws.cell(row=row, column=2).font = Font(color="008000")

    note_row = start + len(rows) + 2
    ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=4)
    ws.cell(row=note_row, column=1, value="Limite metodológico")
    ws.cell(row=note_row, column=1).fill = HEADER_FILL
    ws.cell(row=note_row, column=1).font = HEADER_FONT

    notes = [
        "A prioridade Alta/Média/Exploratória é apenas uma heurística de recuperação.",
        "Registros NEW não recebem S0–S3 ou D0–D4 automaticamente.",
        "S/D existentes aparecem somente quando o registro corresponde ao corpus C01–C45 já auditado.",
        "O arquivo Work_Handoff contém candidatos de prioridade Alta e todos os datasets localizados para triagem humana/GPT.",
    ]
    for i, note in enumerate(notes, start=note_row + 1):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=4)
        ws.cell(row=i, column=1, value=note)
        ws.cell(row=i, column=1).alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18


def _write_query_sheet(wb: Workbook, plan: list[Any]) -> None:
    ws = wb.create_sheet("Plano_Busca")
    ws.sheet_view.showGridLines = False
    ws.append(["ID", "Família", "Consulta", "Racional"])
    _apply_header(ws)

    for item in plan:
        data = item.to_dict() if hasattr(item, "to_dict") else dict(item)
        ws.append(
            [
                data.get("query_id"),
                data.get("family"),
                data.get("query"),
                data.get("rationale"),
            ]
        )

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    widths = [10, 24, 70, 70]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def _write_method_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Metodologia")
    ws.sheet_view.showGridLines = False
    ws.append(["Código", "Definição operacional"])
    _apply_header(ws)

    definitions = [
        ("S3", "Estresse crônico + ≥3 testes + múltiplos domínios comportamentais significativos + mesmos animais confirmados."),
        ("S2", "Adequação científica forte, porém parcial ou com incerteza relevante."),
        ("S1", "Adequação limitada ou adjacente à pergunta central."),
        ("S0", "Inadequado para a pergunta central."),
        ("D4", "Dados individuais abertos + ID persistente + múltiplas medidas vinculáveis + metadados suficientes."),
        ("D3", "Dados individuais abertos/reutilizáveis, mas exigem reconstrução ou verificação para integração segura."),
        ("D2", "Source Data/suplemento parcial ou vínculo entre medidas incerto."),
        ("D1", "Dados apenas mediante solicitação ou acesso restrito."),
        ("D0", "Nenhum dado individual reutilizável identificado."),
        ("VINCULÁVEL", "Há chave/ID persistente ou documentação suficiente para ligar medidas do mesmo indivíduo."),
        ("PROVAVELMENTE VINCULÁVEL", "Há evidência forte de vínculo, mas ainda falta confirmação documental."),
        ("NÃO VINCULÁVEL", "Os arquivos não permitem reconstruir de forma segura a correspondência entre medidas individuais."),
        ("INCERTO", "Evidência insuficiente para concluir vínculo."),
    ]

    for code, definition in definitions:
        ws.append([code, definition])

    warning_row = ws.max_row + 2
    ws.cell(row=warning_row, column=1, value="Regras críticas")
    ws.cell(row=warning_row, column=1).fill = HEADER_FILL
    ws.cell(row=warning_row, column=1).font = HEADER_FONT
    rules = [
        "≥3 testes é sinal de busca, não critério suficiente por si só.",
        "Source Data não equivale automaticamente a dataset bruto multivariado.",
        "Mesmo N entre figuras não prova que são os mesmos animais.",
        "Ordem de linhas não é um identificador válido sem documentação.",
        "Classificação final S/D exige leitura do desenho experimental, Methods e, quando disponível, auditoria dos dados.",
    ]
    for rule in rules:
        ws.append(["", rule])

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 110
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_workbook(
    path: Path,
    profile: dict[str, Any],
    plan: list[Any],
    run: dict[str, Any],
    audit: dict[str, Any],
    all_records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    handoff: list[dict[str, Any]],
    executed_at: str,
) -> None:
    wb = Workbook()
    _write_summary_sheet(
        wb,
        profile=profile,
        audit=audit,
        run=run,
        candidate_count=len(candidates),
        handoff_count=len(handoff),
        executed_at=executed_at,
    )

    _write_table_sheet(wb, "Candidatos_NEW", candidates)
    _write_table_sheet(
        wb,
        "Alta_Prioridade",
        [r for r in candidates if r.get("retrieval_priority") == "Alta"],
    )
    _write_table_sheet(
        wb,
        "Datasets",
        [r for r in all_records if r.get("record_kind") == "dataset"],
    )
    _write_table_sheet(
        wb,
        "KNOWN",
        [r for r in all_records if r.get("corpus_status") == "KNOWN"],
    )
    _write_table_sheet(wb, "Work_Handoff", handoff)
    _write_query_sheet(wb, plan)
    _write_method_sheet(wb)

    wb.save(path)

    check = load_workbook(path, read_only=True, data_only=False)
    expected = {
        "Resumo",
        "Candidatos_NEW",
        "Alta_Prioridade",
        "Datasets",
        "KNOWN",
        "Work_Handoff",
        "Plano_Busca",
        "Metodologia",
    }
    missing = expected.difference(check.sheetnames)
    check.close()
    if missing:
        raise RuntimeError(f"Workbook validation failed. Missing sheets: {sorted(missing)}")


def export_stage5(
    output_dir: Path,
    profile: dict[str, Any],
    plan: list[Any],
    run: dict[str, Any],
    audit: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc).isoformat()
    all_records, candidates, handoff = prepare_records(records)

    xlsx_path = output_dir / "LAIPC_Search.xlsx"
    candidates_csv = output_dir / "LAIPC_Search.csv"
    handoff_csv = output_dir / "work_handoff.csv"

    build_workbook(
        xlsx_path,
        profile=profile,
        plan=plan,
        run=run,
        audit=audit,
        all_records=all_records,
        candidates=candidates,
        handoff=handoff,
        executed_at=executed_at,
    )
    write_flat_csv(candidates_csv, candidates)
    write_flat_csv(handoff_csv, handoff)

    log = {
        "app": "LAIPC+ Search Engine",
        "stage": "5",
        "executed_at_utc": executed_at,
        "profile_id": profile.get("profile_id"),
        "research_question": profile.get("research_question"),
        "providers": run.get("providers"),
        "query_count": len(plan),
        "provider_query_calls": run.get("provider_query_calls"),
        "retrieval_errors": run.get("errors"),
        "stage4_audit": audit,
        "candidate_count": len(candidates),
        "work_handoff_count": len(handoff),
        "work_handoff_rule": "NEW/RELATED_TO_KNOWN with retrieval priority Alta, plus every dataset record.",
        "scientific_classification": "Not performed for NEW records. S0-S3 and D0-D4 require GPT/Work review.",
    }
    (output_dir / "search_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    status = audit.get("status_counts") or {}
    priority = audit.get("priority_counts") or {}
    summary = [
        "# LAIPC+ Search — Stage 5",
        "",
        f"- Profile: {profile.get('profile_id')}",
        f"- Unique records: {audit.get('unique_record_count')}",
        f"- KNOWN: {status.get('KNOWN', 0)}",
        f"- RELATED_TO_KNOWN: {status.get('RELATED_TO_KNOWN', 0)}",
        f"- NEW: {status.get('NEW', 0)}",
        f"- Priority Alta: {priority.get('Alta', 0)}",
        f"- Candidate records exported: {len(candidates)}",
        f"- Work handoff records: {len(handoff)}",
        "",
        "## Next step",
        "Send LAIPC_Search.xlsx and work_handoff.csv to ChatGPT.",
        "ChatGPT will perform scientific pre-triage and select the records whose PDFs/datasets should be audited in Work.",
        "S0-S3 and D0-D4 are not assigned automatically by the search engine.",
    ]
    (output_dir / "search_summary.md").write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    return {
        "executed_at_utc": executed_at,
        "candidate_count": len(candidates),
        "work_handoff_count": len(handoff),
        "xlsx": str(xlsx_path),
        "csv": str(candidates_csv),
        "handoff_csv": str(handoff_csv),
    }
