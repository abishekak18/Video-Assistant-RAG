import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.llm import get_llm


def split_transcript(transcript: str, chunk_size: int = 15000) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=500
    )
    return splitter.split_text(transcript)


def summarize(transcript: str) -> str:
    llm = get_llm(temperature=0.3)

    # Fast single-pass summary for standard transcripts (avoids 429 rate limit errors)
    if len(transcript) < 35000:
        single_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert meeting analyst. Produce a concise, high-value executive summary "
                "of the meeting transcript. Format as:\n"
                "### 📌 High-Level Overview\n(2-3 sentences)\n\n"
                "### 📋 Key Discussion Points\n(Bulleted list with bold subheadings)\n\n"
                "### 💡 Primary Takeaways & Outcomes\n(Bullet points)"
            ),
            ("human", "{text}"),
        ])
        chain = single_prompt | llm | StrOutputParser()
        return chain.invoke({"text": transcript})

    # Multi-chunk map-reduce for very long transcripts (>35,000 chars)
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize this portion of a meeting transcript concisely in bullet points."),
        ("human", "{text}"),
    ])
    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(1.0)  # Rate limit safety delay
        chunk_summaries.append(map_chain.invoke({"text": chunk}))

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting summarizer. Combine these partial summaries "
            "into one final professional executive meeting summary in structured bullet points.",
        ),
        ("human", "{text}"),
    ])

    combined_chain = combined_prompt | llm | StrOutputParser()
    return combined_chain.invoke({"text": combined})


def generate_title(transcript: str) -> str:
    llm = get_llm(temperature=0.3)

    title_chain = (
        ChatPromptTemplate.from_messages([
            (
                "system",
                "Based on the meeting transcript, generate a short professional meeting title "
                "(max 8 words). Only return the title, nothing else.",
            ),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    return title_chain.invoke({"text": transcript[:3000]}).strip(' "\'\n')




