from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_llm


def extract_all_insights(transcript: str) -> dict:
    """Extract action items, key decisions, and open questions in a single LLM call."""
    llm = get_llm(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting analyst. Analyze the following meeting transcript "
            "and extract three distinct sections using the EXACT headings below:\n\n"
            "=== ACTION ITEMS ===\n"
            "List all action items with:\n"
            "- Task description\n"
            "- Owner (who is responsible)\n"
            "- Deadline (if mentioned, else 'Not specified')\n"
            "If none found, write 'No action items found.'\n\n"
            "=== KEY DECISIONS ===\n"
            "List all agreed decisions and resolutions made. If none, write 'No key decisions found.'\n\n"
            "=== OPEN QUESTIONS ===\n"
            "List all unresolved topics or open questions requiring follow-up. If none, write 'No open questions found.'"
        ),
        ("human", "{text}"),
    ])

    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"text": transcript[:30000]})

    # Parse sections
    act_part, dec_part, q_part = "", "", ""
    if "=== ACTION ITEMS ===" in result:
        parts = result.split("=== KEY DECISIONS ===")
        act_part = parts[0].replace("=== ACTION ITEMS ===", "").strip()
        if len(parts) > 1:
            subparts = parts[1].split("=== OPEN QUESTIONS ===")
            dec_part = subparts[0].strip()
            if len(subparts) > 1:
                q_part = subparts[1].strip()
    else:
        act_part = result
        dec_part = "Included in summary."
        q_part = "None noted."

    return {
        "action_items": act_part or "No action items found.",
        "key_decisions": dec_part or "No key decisions found.",
        "open_questions": q_part or "No open questions found.",
    }


def extract_action_items(transcript: str) -> str:
    return extract_all_insights(transcript)["action_items"]


def extract_key_decisions(transcript: str) -> str:
    return extract_all_insights(transcript)["key_decisions"]


def extract_questions(transcript: str) -> str:
    return extract_all_insights(transcript)["open_questions"]
