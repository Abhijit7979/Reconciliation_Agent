import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
from typing import List
import shutil
from langgraph.graph import StateGraph, START, END
from src.Graph.recon_graph import ReconGraph, node_recon

app = FastAPI()

USER_FILES_DIR = Path(__file__).resolve().parent.parent / "user_files"
REFERENCE_EXCEL = Path(__file__).resolve().parent / "prompts" / "sample_template.xlsx"




@app.post("/reconcile-from-folder")
async def reconcile_from_folder(
    folder_path: str = Form(...),
    user_prompt: str = Form(default="Please reconcile the provided financial documents."),
):
    session_dir = Path(folder_path).expanduser().resolve()
    if not session_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Folder not found: {session_dir}")

    bills_dir = session_dir / "bills"
    invoice_dir = session_dir / "invoice"
    if not bills_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Missing 'bills' folder in {session_dir}")
    if not invoice_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Missing 'invoice' folder in {session_dir}")

    pdf_files = [
        p for p in session_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".pdf"
    ]
    if not pdf_files:
        raise HTTPException(status_code=400, detail=f"No bank statement PDF found in {session_dir}")
    if len(pdf_files) > 1:
        raise HTTPException(
            status_code=400,
            detail=f"Multiple PDFs found in {session_dir}; expected exactly one bank statement PDF",
        )
    bank_statement_path = pdf_files[0]

    output_dir = session_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    graph = StateGraph(ReconGraph)
    graph.add_node("recon", node_recon)
    graph.add_edge(START, "recon")
    graph.add_edge("recon", END)
    compiled = graph.compile()

    initial_state = ReconGraph(
        user_prompt=user_prompt,
        output=str(output_dir),
        reference_excel=str(REFERENCE_EXCEL),
        file_path=str(session_dir),
        bill=str(bills_dir),
        invoice=str(invoice_dir),
        bank_statement=str(bank_statement_path),
        agent_response="",
    )

    result = await asyncio.to_thread(compiled.invoke, initial_state)

    return JSONResponse(
        {
            "session_dir": str(session_dir),
            "output_dir": str(output_dir),
            "bank_statement": str(bank_statement_path),
            "agent_response": result.get("agent_response", ""),
        }
    )
