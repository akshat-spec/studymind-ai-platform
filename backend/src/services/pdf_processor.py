import os
import fitz # PyMuPDF
import logging
from src.db.session import async_session_maker
from src.db.models import Document
from src.services.vector_store import vector_store
from sqlalchemy import select, update

# Configure logging for missing images
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_CHUNK_SIZE = 512 # tokens approximation -> roughly words for naive split, better with proper tokenizer
OVERLAP = 50

# A simple tokenizer using space split to approximate tokens
def count_tokens(text: str) -> int:
    return len(text.split())

def chunk_text(text: str, page_num: int) -> tuple[list[str], list[dict]]:
    """
    Respect paragraph boundaries — never split mid-paragraph.
    Prepend page number to each chunk: "[Page N] chunk text..."
    """
    paragraphs = text.split('\n\n')
    chunks = []
    metadatas = []
    
    current_chunk = ""
    current_chunk_tokens = 0
    chunk_index = 0

    prefix = f"[Page {page_num}] "
    prefix_tokens = count_tokens(prefix)

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        para_tokens = count_tokens(paragraph)
        
        if current_chunk_tokens + para_tokens > MAX_CHUNK_SIZE:
            # Push current chunk
            if current_chunk:
                final_text = prefix + current_chunk.strip()
                chunks.append(final_text)
                metadatas.append({"page": page_num, "chunk_index": chunk_index})
                chunk_index += 1
            
            # Start new chunk with overlap - simple approach takes last few paragraphs
            # but instructions say never split mid-paragraph, so we just take the new paragraph
            current_chunk = paragraph + "\n\n"
            current_chunk_tokens = para_tokens
        else:
            current_chunk += paragraph + "\n\n"
            current_chunk_tokens += para_tokens
            
    # Push the remaining text
    if current_chunk:
        final_text = prefix + current_chunk.strip()
        chunks.append(final_text)
        metadatas.append({"page": page_num, "chunk_index": chunk_index})

    return chunks, metadatas

async def process_pdf(doc_id: str, file_path: str):
    """
    Background task to process a PDF file, extract text, chunk it, and save to Chroma.
    """
    logger.info(f"Starting processing for Document ID: {doc_id}")
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        
        title = doc.metadata.get("title")
        if not title:
            title = os.path.basename(file_path)
            
        all_chunks = []
        all_metas = []
        total_words = 0
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text") # Gracefully handles multi-column in PyMuPDF with right blocks
            
            # Detect image-only page
            if not text.strip() and len(page.get_images()) > 0:
                logger.warning(f"Document {doc_id} Page {page_num + 1} is image-only. Skipping text extraction.")
                continue
                
            total_words += count_tokens(text)
            
            chunks, metas = chunk_text(text, page_num + 1)
            all_chunks.extend(chunks)
            all_metas.extend(metas)
            
        doc.close()
        
        # We need a collection identifier
        collection_id = f"doc_{doc_id}"
        
        # Add to vector store
        await vector_store.create_collection(doc_id)
        if all_chunks:
            await vector_store.add_chunks(doc_id, all_chunks, all_metas)
            
        # Update DB State
        async with async_session_maker() as db:
            document = await db.execute(select(Document).where(Document.id == doc_id))
            document = document.scalar_one_or_none()
            if document:
                document.status = "ready"
                document.page_count = page_count
                document.title = title
                document.chroma_collection_id = collection_id
                await db.commit()
                logger.info(f"Finished processing Document ID: {doc_id}")

    except Exception as e:
        logger.error(f"Failed to process Document {doc_id}: {str(e)}")
        async with async_session_maker() as db:
            await db.execute(
                update(Document).where(Document.id == doc_id).values(status="failed")
            )
            await db.commit()
