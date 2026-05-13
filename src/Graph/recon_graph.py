from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from src.agent.recon_agent import ClaudeAgent
from rich import print
from langchain_core.prompts import ChatPromptTemplate


class ReconGraph(BaseModel):
    user_prompt: str = Field(description="The user prompt for the reconciliation")
    output: str = Field(description="The output of the reconciliation file path")
    reference_excel: str = Field(description="The path of the reference excel file")
    file_path: str = Field(description="The path of the files to be reconciled")
    bill:str = Field(description="The path of the bill file.")
    invoice:str = Field(description="The path of the invoice file")
    bank_statement:str = Field(description="The path of the bank statement file")
    # llm_cost:str = Field(description="The cost of the llm")
    agent_response: str = Field(description="The response of the agent")



def node_recon(state: ReconGraph):

    prompt = ChatPromptTemplate.from_template(
        """You are a helpful assistant that can help with reconciliation. {user_prompt}
        
        file paths :
        1. {bill} folder path 
        2. {invoice} folder path 
        3. {bank_statement} pdf file path 
        4. {reference_excel} excel file path 
        5. {output} output file saving path

        Use skill reconciliation
        """
    )



    agent = ClaudeAgent(llm="claude-sonnet-4-6", file_path=state.file_path)

    agent_response = agent.stream(prompt.format(user_prompt=state.user_prompt, bill=state.bill, invoice=state.invoice, bank_statement=state.bank_statement, reference_excel=state.reference_excel, output=state.output))

    collected = []
    for chunk in agent_response:
        text = chunk
        print(chunk)
        if not isinstance(text, str):
            text = str(text)
        collected.append(text)
        # print(text)
    print()

    return {"agent_response": "".join(collected[-1])}


    
