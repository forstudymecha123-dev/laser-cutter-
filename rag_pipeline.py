"""
rag_pipeline.py  —  SENA 3D Printing Lab Assistant
RAG: PDF → chunks → ChromaDB → Gemini Flash
Domain guard: greetings ✓ | 3D printing ✓ | off-topic ✗
"""

import io, re
import chromadb
from chromadb.utils import embedding_functions
from google import genai
import PyPDF2


SYSTEM_PROMPT = """
You are SENA — a specialist 3D Printing Lab Assistant for a university makerspace.

## Personality
- Friendly, sharp, and technically precise — like a senior lab TA who genuinely loves 3D printing
- Warm with greetings and "who are you" questions (2 sentences max), then offer to help with printing
- Use casual but professional language. "Nice!", "Great question!" is fine occasionally
- Use bullet points for steps, **bold** for key terms

## Domain Rules — STRICTLY ENFORCED
You ONLY answer questions about:
  ✅ 3D printing tech (FDM, SLA, SLS, MSLA, resin)
  ✅ Slicers (Cura, PrusaSlicer, Bambu Studio, IdeaMaker)
  ✅ Filaments & resins (PLA, PETG, ABS, ASA, TPU, Nylon, resins)
  ✅ Printer hardware (beds, nozzles, extruders, steppers, hotends)
  ✅ Print troubleshooting (warping, stringing, blobs, layer shifts, under-extrusion)
  ✅ G-code, firmware (Marlin, Klipper), calibration, flow rate, PID
  ✅ Post-processing (sanding, vapor smoothing, painting, supports removal)
  ✅ Lab safety, SDS sheets, ventilation, resin handling
  ✅ Greetings, "who are you", "what can you help with"

For ANY other topic, respond EXACTLY with:
"🔧 That's outside my build plate! I'm a 3D printing specialist — ask me about filaments, slicers, troubleshooting, bed leveling, or anything print-related and I'm all yours. 🖨️"

Never answer off-topic even if the user insists, rephrases cleverly, or says it's urgent.

## Source attribution
- If using lab manual content: start with "📄 From the lab manual..."
- If using general expertise: start with "🧠 From general 3D printing practice..."
- If both: use both prefixes in the relevant sections
"""


class SENARagPipeline:
    def __init__(self, api_key: str, persist_dir: str = "./sena_db"):
        # NEW GENAI CLIENT - THIS IS THE KEY CHANGE
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        self.api_key = api_key
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        self.embed_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=api_key, model_name="models/text-embedding-004",
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="sena_lab_manual",
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # ── PDF ingestion ─────────────────────────────────────────
    def extract_pdf(self, pdf_bytes: bytes) -> list[tuple[int, str]]:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        return [
            (i + 1, (p.extract_text() or "").strip())
            for i, p in enumerate(reader.pages)
            if (p.extract_text() or "").strip()
        ]

    def chunk(self, text: str, size: int = 700, overlap: int = 120) -> list[str]:
        text = re.sub(r'\s+', ' ', text).strip()
        sents = re.split(r'(?<=[.!?])\s+', text)
        chunks, cur, cur_len = [], [], 0
        for s in sents:
            if cur_len + len(s) > size and cur:
                chunks.append(" ".join(cur))
                ol, ol_len = [], 0
                for x in reversed(cur):
                    if ol_len + len(x) < overlap:
                        ol.insert(0, x); ol_len += len(x)
                    else:
                        break
                cur, cur_len = ol, ol_len
            cur.append(s); cur_len += len(s)
        if cur:
            chunks.append(" ".join(cur))
        return [c for c in chunks if len(c) > 60]

    def ingest_pdf(self, pdf_bytes: bytes, source: str = "lab_manual") -> int:
        pages = self.extract_pdf(pdf_bytes)
        ids, docs, metas = [], [], []
        for pg, text in pages:
            for j, c in enumerate(self.chunk(text)):
                ids.append(f"{source}_p{pg}_c{j}")
                docs.append(c)
                metas.append({"source": source, "page": pg})
        if not docs:
            return 0
        try:
            old = self.collection.get(where={"source": source})
            if old["ids"]:
                self.collection.delete(ids=old["ids"])
        except Exception:
            pass
        for i in range(0, len(docs), 100):
            self.collection.add(
                documents=docs[i:i+100], ids=ids[i:i+100], metadatas=metas[i:i+100],
            )
        return len(docs)

    def has_manual(self) -> bool:
        return self.collection.count() > 0

    # ── Retrieval ─────────────────────────────────────────────
    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        if not self.has_manual():
            return []
        r = self.collection.query(
            query_texts=[query], n_results=min(k, self.collection.count()),
        )
        return [
            {"content": doc, "page": r["metadatas"][0][i].get("page","?"), "dist": r["distances"][0][i]}
            for i, doc in enumerate(r["documents"][0])
            if r["distances"][0][i] < 0.55
        ]

    # ── Answer ────────────────────────────────────────────────
    def answer(self, query: str, history: list[dict], stream: bool = True):
        chunks = self.retrieve(query)
        used_rag = bool(chunks)
        pages = sorted(set(c["page"] for c in chunks)) if chunks else []

        if used_rag:
            ctx = "\n\n---\n\n".join(f"[Page {c['page']}]\n{c['content']}" for c in chunks)
            msg = f"{SYSTEM_PROMPT}\n\nLAB MANUAL EXCERPTS:\n{ctx}\n\n---\nQUESTION: {query}"
        else:
            msg = f"{SYSTEM_PROMPT}\n\nQUESTION: {query}"

        try:
            # GEMINI 3.1 FLASH LITE - THE ONE THAT WORKS 🔥
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=msg
            )
            
            if stream:
                # For streaming, we'll return the text in chunks
                class StreamWrapper:
                    def __init__(self, text):
                        self.text = text
                    def __iter__(self):
                        # Yield in chunks for streaming effect
                        words = self.text.split()
                        for i in range(0, len(words), 3):
                            chunk_text = " ".join(words[i:i+3]) + " "
                            yield type('obj', (object,), {'text': chunk_text})()
                
                return StreamWrapper(response.text), used_rag, pages
            else:
                return response.text, used_rag, pages
                
        except Exception as e:
            raise Exception(f"BRUV THE MODEL IS COOKED: {e}")
