"""
RAG Service - High-level service combining RAG + LLM
"""

from typing import Dict
from loguru import logger

from rag.rag_pipeline import RAGPipeline
from utils.llm_client import LLMClient


class RAGService:
    """
    Service for RAG-based question answering
    """

    def __init__(self):
        self.rag_pipeline = RAGPipeline()
        self.llm_client = LLMClient()
        self._initialized = False  # ✅ prevents double indexing

        logger.info("🧠 RAGService created (lazy initialization enabled)")

    def _ensure_initialized(self):
        """Build index only once, safely"""
        if not self._initialized:
            logger.info("🔄 Building RAG index...")
            self.rag_pipeline.build_index()
            self._initialized = True
            logger.info("✅ RAG index ready")

    def answer_question(
        self,
        question: str,
        language: str = "hindi",
        include_sources: bool = True
    ) -> Dict[str, any]:
        """
        Answer a question using RAG + LLM
        """
        try:
            # ✅ Ensure index exists
            self._ensure_initialized()

            rag_result = self.rag_pipeline.query(question, language=language)

            if not rag_result.get('context'):
                return {
                    'answer': "क्षमा करें, मुझे इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं है।",
                    'sources': [],
                    'context_used': '',
                    'confidence': 0.0
                }

            answer = self.llm_client.generate(
                rag_result['prompt'],
                max_tokens=400,
                temperature=0.3
            )

            avg_score = sum(
                c['score'] for c in rag_result['retrieved_chunks']
            ) / len(rag_result['retrieved_chunks'])

            if include_sources and rag_result.get('sources'):
                answer += f"\n\n📚 स्रोत: {', '.join(rag_result['sources'])}"

            return {
                'answer': answer,
                'sources': rag_result['sources'],
                'context_used': rag_result['context'][:500],
                'confidence': round(float(avg_score), 2)
            }

        except Exception as e:
            logger.error(f"❌ RAG service error: {e}")
            return {
                'answer': "क्षमा करें, अभी उत्तर उपलब्ध नहीं है।",
                'sources': [],
                'context_used': '',
                'confidence': 0.0
            }

    def explain_scheme(self, scheme_name: str) -> str:
        try:
            self._ensure_initialized()
            prompt = self.rag_pipeline.explain_scheme(scheme_name)
            return self.llm_client.generate(prompt, max_tokens=600)
        except Exception as e:
            logger.error(f"Error explaining scheme: {e}")
            return "क्षमा करें, योजना की जानकारी नहीं मिली।"

    def explain_term(self, term: str) -> str:
        try:
            self._ensure_initialized()
            prompt = self.rag_pipeline.explain_term(term)
            return self.llm_client.generate(prompt, max_tokens=300)
        except Exception as e:
            logger.error(f"Error explaining term: {e}")
            return "क्षमा करें, शब्द का अर्थ नहीं मिला।"

    def get_service_status(self) -> Dict[str, any]:
        rag_stats = self.rag_pipeline.get_stats()
        llm_available = self.llm_client.client is not None

        return {
            'rag_status': rag_stats.get('status', 'unknown'),
            'llm_available': llm_available,
            'total_documents': rag_stats.get('total_chunks', 0),
            'service_healthy': rag_stats.get('status') == 'indexed'
        }
