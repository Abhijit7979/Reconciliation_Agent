from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemPermission
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI
from rich import print
import os 
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openrouter import ChatOpenRouter
from langchain_groq import ChatGroq

SYSTEM_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "SYSTEM_PROMPT.md").read_text()
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["RECON_OPENAI_BASE_URL"] = os.getenv("RECON_OPENAI_BASE_URL")
os.environ["RECON_OPENAI_MODEL"] = os.getenv("RECON_OPENAI_MODEL")
from langchain_claude_code import ClaudeCodeChatModel




def ClaudeAgent(llm:str="claude-haiku-4-5-20251001", file_path:str="/Users/abhi/Documents/MS_USA/main_agent_recon/user_files",):

    agent =ClaudeCodeChatModel(
        name="recon_agent",
    model= llm
    ,permission_mode="bypassPermissions",
    cwd=file_path,
    system_prompt=SYSTEM_PROMPT,
    max_budget_usd=2,
    oauth_token=os.getenv("CLAUDE_CODE_OAUTH_TOKEN"),
    skills=["/prompts/reconciliation/"],
    )

    return agent

def DeepAgent(llm:str,file_path:str="/Users/abhi/Documents/MS_USA/main_agent_recon/user_files/**"):
    # llm=ChatOpenAI(model=os.getenv("RECON_OPENAI_MODEL"), base_url=os.getenv("RECON_OPENAI_BASE_URL"))
    # llm=ChatGoogleGenerativeAI(model="gemini-3-flash-preview",api_key="AIzaSyBVphpkbVXitmiX-jUuCu4DmbIXeGn8aFU")
    # llm=ChatOpenRouter(model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", api_key=os.getenv("OPENROUTER_API_KEY"))
    llm=ChatGroq(model="openai/gpt-oss-120b",api_key=os.getenv("GROQ_API_KEY"))

    # you can use any of the llms above

    agent=create_deep_agent(
    model=llm,
    system_prompt=SYSTEM_PROMPT,
    permissions=[
        FilesystemPermission(
            paths=[file_path],
            operations=["read", "write"],
            mode="allow",
        )
    ],
    name="recon_agent",
    backend=FilesystemBackend(root_dir="/Users/abhi/Documents/MS_USA/main_agent_recon/user_files",virtual_mode=False)
    )

    return agent