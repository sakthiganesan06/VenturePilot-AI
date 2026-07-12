"""
RAG Pipeline — LangChain + FAISS + Sentence Transformers + IBM COS
"""

import os
import json
import logging
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    try:
        from langchain_core.documents import Document
    except ImportError:
        from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain/FAISS not installed — RAG will use keyword-based fallback")

    # Stub so type annotations resolve at class-definition time
    class Document:  # type: ignore
        def __init__(self, page_content: str = "", metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}


KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge_base"
)

VECTOR_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".vector_db"
)


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.

    Workflow:
    1. Load knowledge base documents (from disk or IBM COS).
    2. Chunk, embed, and index documents into FAISS.
    3. On query: retrieve top-k chunks.
    4. Return context string for Granite prompt injection.
    """

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self._docs_loaded = False

        if LANGCHAIN_AVAILABLE:
            self._init_embeddings()
            self._load_or_build_index()

    # ── Init ───────────────────────────────────────────────────────────────────
    def _init_embeddings(self):
        try:
            model_name = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info(f"✅ Embeddings model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Embeddings init error: {e}")
            self.embeddings = None

    def _load_or_build_index(self):
        if not self.embeddings:
            return
        try:
            if os.path.exists(VECTOR_DB_PATH):
                self.vector_store = FAISS.load_local(
                    VECTOR_DB_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ FAISS index loaded from disk")
                self._docs_loaded = True
            else:
                self._build_index_from_knowledge_base()
        except Exception as e:
            logger.error(f"FAISS load error: {e}")
            self._build_index_from_knowledge_base()

    def _build_index_from_knowledge_base(self):
        docs = self._load_documents()
        if not docs:
            logger.warning("No knowledge base documents found — creating seed documents")
            docs = self._seed_documents()
        self._index_documents(docs)

    # ── Document Loading ───────────────────────────────────────────────────────
    def _load_documents(self) -> List[Document]:
        docs: List[Document] = []
        kb_path = Path(KNOWLEDGE_BASE_DIR)
        kb_path.mkdir(parents=True, exist_ok=True)

        for fp in kb_path.rglob("*.txt"):
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                docs.append(Document(page_content=text, metadata={"source": str(fp), "type": "txt"}))
            except Exception as e:
                logger.error(f"Error loading {fp}: {e}")

        for fp in kb_path.rglob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                text = json.dumps(data, indent=2) if isinstance(data, dict) else str(data)
                docs.append(Document(page_content=text, metadata={"source": str(fp), "type": "json"}))
            except Exception as e:
                logger.error(f"Error loading {fp}: {e}")

        logger.info(f"Loaded {len(docs)} documents from knowledge base")
        return docs

    def _seed_documents(self) -> List[Document]:
        """Seed the vector database with built-in startup knowledge."""
        seed_texts = [
            ("startup_india_scheme", "Startup India Scheme: DPIIT-recognized startups get 3-year income tax exemption, reduced patent filing fees (80% discount), fast-track IPR mechanism, ₹10,000 Cr fund of funds, and access to the Startup India Seed Fund (up to ₹20L for pre-revenue startups). Eligibility: Company incorporated in India <10 years, turnover <₹100Cr, working towards innovation/development of product/service. Required docs: Incorporation certificate, board resolution, PAN card, website/pitch deck."),
            ("msme_registration", "MSME Udyam Registration: Free online registration providing access to government subsidies, priority sector lending, collateral-free loans under CGTMSE scheme (up to ₹2Cr), preference in government procurement, protection against delayed payments, and various state-level subsidies. Micro: Investment <₹1Cr, Turnover <₹5Cr. Small: Investment <₹10Cr, Turnover <₹50Cr."),
            ("dpiit_recognition", "DPIIT Recognition for Startups: Unlocks angel tax exemption under Section 56(2)(viib), eligible for Startup India Seed Fund, fast-track IP filings, self-certification under 9 labour laws, no inspection for 3 years. Process: Apply at Startup India portal, submit company details, brief description of innovative nature, upload incorporation docs."),
            ("saas_metrics", "SaaS Startup Key Metrics: MRR (Monthly Recurring Revenue), ARR (Annual Recurring Revenue), Churn Rate (industry benchmark 5-10% monthly for SMB SaaS), CAC (Customer Acquisition Cost), LTV (Lifetime Value), LTV:CAC ratio (target >3:1), NRR (Net Revenue Retention, target >100%), Payback Period (target <12 months). A healthy SaaS startup should achieve ₹1Cr ARR within 18-24 months of launch."),
            ("funding_stages", "Startup Funding Stages in India: Pre-seed (₹5L-₹50L, F&F/angels/grants), Seed (₹50L-₹5Cr, angels/micro-VCs/incubators), Series A (₹5Cr-₹50Cr, VCs, requires ₹1Cr+ ARR), Series B (₹50Cr-₹200Cr, growth stage), Series C+ (₹200Cr+, expansion). Key Indian VCs: Accel, Sequoia India, Matrix Partners, Kalaari Capital, Blume Ventures, Prime Venture Partners. Key accelerators: Y Combinator (India friendly), 100x.vc, Antler India."),
            ("company_registration", "Company Registration India: Private Limited Company (most preferred for startups) — Ministry of Corporate Affairs registration, ₹7,000-₹15,000 cost, 7-15 days process, minimum 2 directors, minimum ₹1 paid-up capital. Requires: DIN for all directors, DSC, MoA, AoA, PAN, TAN. Alternatives: LLP (₹5,000-₹10,000, simpler compliance), OPC (single founder). Post-registration: GST (if turnover >₹20L), Professional Tax, ESIC/PF if team >10."),
            ("market_research_india", "Indian Startup Ecosystem 2024-25: 110,000+ DPIIT-recognized startups, 100+ unicorns, ₹10L+ Cr total startup ecosystem value. Key sectors: FinTech (₹1,900 Cr funding), HealthTech, EdTech, AgriTech, CleanTech, EV, AI/ML, SaaS. Tier-2 cities seeing 40% growth in startup registrations. Government spending ₹1,000 Cr annually on startup ecosystem. 60% of new startups are first-generation entrepreneurs."),
            ("valuation_methods", "Startup Valuation Methods: Pre-revenue — Scorecard Method (compare to avg seed deal ₹50L-₹3Cr), Berkus Method (up to ₹2.5Cr for 5 factors), Cost-to-Duplicate. Post-revenue — Revenue Multiple (SaaS: 8-15x ARR), Discounted Cash Flow (rarely used early-stage), Comparable Transactions (look at recent India startup deals). Typical seed valuation in India: ₹3Cr-₹15Cr pre-money."),
            ("gtm_strategy", "Go-to-Market Strategy for B2B SaaS in India: Product-Led Growth (PLG) works best — free tier drives adoption, convert 2-5% to paid. Content Marketing (SEO for startup-related keywords — 500K+ monthly searches). LinkedIn Outreach (best B2B channel in India). Partner with incubators/accelerators (channel partner program). WhatsApp communities for founder networks. Tier-2 city targeting (Jaipur, Pune, Ahmedabad, Kochi) — lower CAC, less competition."),
            ("ai_trends_2025", "AI Startup Trends 2025: IBM Granite models emerging as enterprise-preferred due to explainability and IP protection. RAG (Retrieval-Augmented Generation) becoming standard for enterprise AI apps. Agentic AI platforms (multi-step autonomous workflows) are the next frontier. India AI market projected at $6B by 2025. Government AI Mission India investing ₹10,300 Cr. Key opportunities: AI for Bharat (vernacular AI), AI for MSME automation, AI for agriculture, AI for healthcare diagnostics.")
        ]

        docs = []
        for name, text in seed_texts:
            kb_path = Path(KNOWLEDGE_BASE_DIR)
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / f"{name}.txt").write_text(text, encoding="utf-8")
            docs.append(Document(page_content=text, metadata={"source": name, "type": "seed"}))

        logger.info(f"Created {len(docs)} seed knowledge base documents")
        return docs

    # ── Indexing ───────────────────────────────────────────────────────────────
    def _index_documents(self, docs: List[Document]):
        if not self.embeddings or not docs:
            return
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=64,
                separators=["\n\n", "\n", ". ", " "]
            )
            chunks = splitter.split_documents(docs)
            logger.info(f"Split into {len(chunks)} chunks")
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            os.makedirs(VECTOR_DB_PATH, exist_ok=True)
            self.vector_store.save_local(VECTOR_DB_PATH)
            self._docs_loaded = True
            logger.info("✅ FAISS index built and saved")
        except Exception as e:
            logger.error(f"FAISS indexing error: {e}")

    def add_document(self, text: str, metadata: dict):
        """Add a new document to the existing index."""
        if not LANGCHAIN_AVAILABLE or not self.embeddings:
            return
        doc = Document(page_content=text, metadata=metadata)
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
        chunks = splitter.split_documents([doc])
        if self.vector_store:
            self.vector_store.add_documents(chunks)
            self.vector_store.save_local(VECTOR_DB_PATH)
        else:
            self._index_documents([doc])

    # ── Retrieval ──────────────────────────────────────────────────────────────
    def retrieve(self, query: str, k: int = 5) -> str:
        """Return a concatenated context string of top-k retrieved chunks."""
        if not self.vector_store:
            return self._keyword_fallback(query)
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            if not docs:
                return self._keyword_fallback(query)
            context_parts = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "knowledge_base")
                context_parts.append(f"[Context {i} — Source: {source}]\n{doc.page_content}")
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"FAISS retrieval error: {e}")
            return self._keyword_fallback(query)

    def retrieve_with_scores(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Return (chunk_text, similarity_score) pairs."""
        if not self.vector_store:
            return [(self._keyword_fallback(query), 1.0)]
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [(doc.page_content, float(score)) for doc, score in results]
        except Exception as e:
            logger.error(f"FAISS scored retrieval error: {e}")
            return [(self._keyword_fallback(query), 0.0)]

    @staticmethod
    def _keyword_fallback(query: str) -> str:
        """Basic keyword matching when FAISS is unavailable."""
        q = query.lower()
        context = []
        if any(w in q for w in ["government", "scheme", "startup india", "msme", "dpiit"]):
            context.append("Startup India DPIIT recognition provides tax exemptions, seed fund access (up to ₹20L), and 80% patent fee discount. MSME registration enables subsidies and priority lending.")
        if any(w in q for w in ["fund", "investor", "angel", "vc", "capital"]):
            context.append("Indian startup funding stages: Pre-seed (₹5L-₹50L), Seed (₹50L-₹5Cr), Series A (₹5Cr-₹50Cr). Key VCs: Accel, Sequoia India, Blume Ventures.")
        if any(w in q for w in ["legal", "register", "compliance", "gst", "trademark"]):
            context.append("Company registration: Private Limited Company via MCA, cost ₹7,000-₹15,000. GST mandatory if turnover >₹20L. Trademark registration: ₹4,500/class, 18-24 months.")
        if any(w in q for w in ["saas", "revenue", "model", "pricing", "subscription"]):
            context.append("SaaS best practices: Freemium to drive adoption, target LTV:CAC >3:1, aim for <5% monthly churn, NRR >100% for healthy growth.")
        if any(w in q for w in ["market", "tam", "sam", "som", "size", "growth"]):
            context.append("Indian startup ecosystem: 110K+ DPIIT startups, 100+ unicorns. AI/SaaS market growing at 34% CAGR. TAM for B2B SaaS tools in India: ₹4,200 Cr.")
        return "\n\n".join(context) if context else "No specific context found. Applying general startup knowledge and best practices."


# Singleton
rag_pipeline = RAGPipeline()
