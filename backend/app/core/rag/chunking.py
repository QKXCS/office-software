from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )


def get_markdown_splitter() -> MarkdownHeaderTextSplitter:
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    )


def chunk_text(text: str) -> list[str]:
    splitter = get_text_splitter()
    docs = splitter.create_documents([text])
    return [d.page_content for d in docs]


def chunk_markdown(md_text: str) -> list[str]:
    splitter = get_markdown_splitter()
    docs = splitter.split_text(md_text)
    result = []
    for doc in docs:
        header = doc.metadata.get("h1", "")
        content = doc.page_content
        result.append(f"# {header}\n{content}" if header else content)
    return result


def chunk_document(content: str, doc_type: str = "text") -> list[str]:
    if doc_type in ("md", "markdown"):
        return chunk_markdown(content)
    return chunk_text(content)
