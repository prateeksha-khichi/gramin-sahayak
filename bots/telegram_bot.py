"""
Telegram Bot - Gramin Sahayak
IMPROVED: Better async voice handling with proper cleanup and error handling
"""

import os
import sys
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.error import TimedOut, NetworkError, RetryAfter
from loguru import logger
import asyncio

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.loan_service import LoanService
from services.fraud_service import FraudService
from services.rag_service import RAGService
from database.db_manager import db
from bots.voice_handler import VoiceHandler

# Conversation states - NOW 10 STATES for all fields
(
    AWAITING_GENDER,
    AWAITING_MARRIED,
    AWAITING_DEPENDENTS,
    AWAITING_INCOME,
    AWAITING_EDUCATION,
    AWAITING_EMPLOYMENT,
    AWAITING_PROPERTY,
    AWAITING_CREDIT_SCORE,
    AWAITING_LOAN_AMOUNT,
    AWAITING_PURPOSE
) = range(10)


class GraminSahayakBot:

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN missing")

        self.loan_service = LoanService()
        self.fraud_service = FraudService()
        self.rag_service = RAGService()
        self.voice_handler = VoiceHandler()

        self.app = (
            Application.builder()
            .token(self.token)
            .connect_timeout(30)
            .read_timeout(30)
            .write_timeout(30)
            .pool_timeout(30)
            .build()
        )
        
        self._register_handlers()
        self._register_error_handler()
        logger.info("✅ Bot Ready - Collecting 11 features")

    def _register_error_handler(self):
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
            try:
                logger.error(f"Error: {context.error}")
                if isinstance(context.error, (TimedOut, NetworkError)):
                    logger.warning("⚠️  Network issue")
                elif isinstance(context.error, RetryAfter):
                    await asyncio.sleep(context.error.retry_after)
                else:
                    if update and isinstance(update, Update) and update.effective_message:
                        try:
                            await update.effective_message.reply_text(
                                "❌ समस्या हुई। /start से शुरू करें।",
                                reply_markup=ReplyKeyboardRemove()
                            )
                        except:
                            pass
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
        
        self.app.add_error_handler(error_handler)

    async def _safe_send_message(self, update: Update, text: str, **kwargs):
        for attempt in range(3):
            try:
                return await update.message.reply_text(text, **kwargs)
            except (TimedOut, NetworkError):
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("fraud", self.fraud))
        self.app.add_handler(CommandHandler("schemes", self.schemes))
        self.app.add_handler(CommandHandler("stats", self.stats))

        loan_conv = ConversationHandler(
            entry_points=[CommandHandler("loan", self.loan_start)],
            states={
                AWAITING_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_gender)],
                AWAITING_MARRIED: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_married)],
                AWAITING_DEPENDENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_dependents)],
                AWAITING_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_income)],
                AWAITING_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_education)],
                AWAITING_EMPLOYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_employment)],
                AWAITING_PROPERTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_property)],
                AWAITING_CREDIT_SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_credit_score)],
                AWAITING_LOAN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_loan_amount)],
                AWAITING_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_purpose)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(loan_conv)
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    def _safe_db_log(self, telegram_id: str, query_type: str, query_text: str, response: str):
        try:
            if hasattr(db, 'log_query'):
                db.log_query(telegram_id=telegram_id, query_type=query_type, 
                           query_text=query_text, response=response)
        except Exception as e:
            logger.error(f"DB log: {e}")

    # Commands
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        try:
            db.get_or_create_user(
                telegram_id=str(user.id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
        except:
            pass

        keyboard = [
            [KeyboardButton("🏦 लोन जांच"), KeyboardButton("🔍 योजना")],
            [KeyboardButton("⚠️ धोखाधड़ी"), KeyboardButton("❓ मदद")]
        ]

        await self._safe_send_message(
            update,
            f"🙏 नमस्ते {user.first_name}!\n\n"
            "मैं **ग्रामीण सहायक** हूँ 🏦\n\n"
            "/loan – लोन पात्रता\n"
            "/fraud – योजना जांच\n"
            "/schemes – सरकारी योजनाएं",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._safe_send_message(update, 
            "📚 **मदद**\n\n"
            "/start - शुरू करें\n"
            "/loan - लोन जांच\n"
            "/cancel - रद्द करें"
        )

    async def fraud(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._safe_send_message(update, "🔍 योजना का नाम भेजें")

    async def schemes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._safe_send_message(update,
            "🏛️ **सरकारी योजनाएं**\n\n"
            "1️⃣ मुद्रा योजना – ₹10L तक\n"
            "2️⃣ किसान क्रेडिट कार्ड\n"
            "3️⃣ स्टैंड अप इंडिया"
        )

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            stats = db.get_user_stats(str(update.effective_user.id))
            msg = f"📊 सवाल: {stats.get('total_queries', 0)}"
        except:
            msg = "📊 डेटा नहीं मिला"
        await self._safe_send_message(update, msg)

    # LOAN FLOW - ALL 10 STEPS
    async def loan_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        context.user_data["loan"] = {}
        logger.info(f"User {update.effective_user.id} started loan")

        keyboard = [["पुरुष / Male"], ["महिला / Female"]]
        await self._safe_send_message(
            update,
            "🏦 **लोन पात्रता जांच**\n\n"
            "**1️⃣ लिंग?** (Gender)\n"
            "/cancel रद्द करें",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return AWAITING_GENDER

    async def get_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gender = update.message.text.strip()
        context.user_data["loan"]["gender"] = gender
        logger.info(f"Gender: {gender}")

        keyboard = [["हाँ / Yes"], ["नहीं / No"]]
        await self._safe_send_message(
            update,
            f"✅ लिंग: {gender}\n\n**2️⃣ शादीशुदा?** (Married)",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return AWAITING_MARRIED

    async def get_married(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        married = update.message.text.strip()
        context.user_data["loan"]["marital_status"] = married
        logger.info(f"Married: {married}")

        keyboard = [["0"], ["1"], ["2"], ["3+"]]
        await self._safe_send_message(
            update,
            f"✅ विवाह: {married}\n\n**3️⃣ आश्रित?** (Dependents)\nकितने लोग आप पर निर्भर हैं?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return AWAITING_DEPENDENTS

    async def get_dependents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        dependents = update.message.text.strip()
        context.user_data["loan"]["dependents"] = dependents
        logger.info(f"Dependents: {dependents}")

        await self._safe_send_message(
            update,
            f"✅ आश्रित: {dependents}\n\n**4️⃣ मासिक आय?**\n(उदा: 25000)",
            reply_markup=ReplyKeyboardRemove()
        )
        return AWAITING_INCOME

    async def get_income(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()
        cleaned = self._extract_number(user_input)
        
        try:
            income = int(cleaned.replace(",", ""))
            if income < 1000 or income > 10000000:
                await self._safe_send_message(update, "❌ आय ₹1,000 - ₹1 करोड़ के बीच")
                return AWAITING_INCOME
            
            context.user_data["loan"]["income"] = income
            logger.info(f"Income: {income}")

            keyboard = [["स्नातक / Graduate"], ["अस्नातक / Not Graduate"]]
            await self._safe_send_message(
                update,
                f"✅ आय: ₹{income:,}\n\n**5️⃣ शिक्षा?**",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return AWAITING_EDUCATION
        except:
            await self._safe_send_message(update, "❌ संख्या लिखें (25000)")
            return AWAITING_INCOME

    async def get_education(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        education = update.message.text.strip()
        context.user_data["loan"]["education"] = education
        logger.info(f"Education: {education}")

        keyboard = [["हाँ / Yes"], ["नहीं / No"]]
        await self._safe_send_message(
            update,
            f"✅ शिक्षा: {education}\n\n**6️⃣ खुद का व्यवसाय?** (Self Employed)",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return AWAITING_EMPLOYMENT

    async def get_employment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        employment = update.message.text.strip()
        context.user_data["loan"]["employment_type"] = employment
        logger.info(f"Employment: {employment}")

        keyboard = [["ग्रामीण / Rural"], ["शहरी / Urban"], ["अर्ध-शहरी / Semiurban"]]
        await self._safe_send_message(
            update,
            f"✅ रोजगार: {employment}\n\n**7️⃣ संपत्ति क्षेत्र?** (Property Area)",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return AWAITING_PROPERTY

    async def get_property(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        property_area = update.message.text.strip()
        context.user_data["loan"]["property_area"] = property_area
        logger.info(f"Property: {property_area}")

        await self._safe_send_message(
            update,
            f"✅ क्षेत्र: {property_area}\n\n**8️⃣ क्रेडिट स्कोर?**\n(300-900, नहीं पता तो 650)",
            reply_markup=ReplyKeyboardRemove()
        )
        return AWAITING_CREDIT_SCORE

    async def get_credit_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()
        cleaned = self._extract_number(user_input)
        
        try:
            score = int(cleaned)
            if not (300 <= score <= 900):
                await self._safe_send_message(update, "❌ 300-900 के बीच")
                return AWAITING_CREDIT_SCORE
            
            context.user_data["loan"]["credit_score"] = score
            logger.info(f"Credit: {score}")

            await self._safe_send_message(
                update,
                f"✅ स्कोर: {score}\n\n**9️⃣ कितना लोन?**\n(उदा: 500000)"
            )
            return AWAITING_LOAN_AMOUNT
        except:
            await self._safe_send_message(update, "❌ 300-900 संख्या")
            return AWAITING_CREDIT_SCORE

    async def get_loan_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()
        cleaned = self._extract_number(user_input)
        
        try:
            amt = int(cleaned.replace(",", ""))
            if amt < 10000 or amt > 50000000:
                await self._safe_send_message(update, "❌ ₹10K - ₹5 करोड़")
                return AWAITING_LOAN_AMOUNT
            
            context.user_data["loan"]["loan_amount_requested"] = amt
            logger.info(f"Amount: {amt}")

            keyboard = [["घर"], ["खेती"], ["व्यवसाय"], ["शिक्षा"]]
            await self._safe_send_message(
                update,
                f"✅ राशि: ₹{amt:,}\n\n**🔟 किसलिए?**",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return AWAITING_PURPOSE
        except:
            await self._safe_send_message(update, "❌ सही राशि")
            return AWAITING_LOAN_AMOUNT

    async def get_purpose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        purpose = update.message.text.strip()
        context.user_data["loan"]["loan_purpose"] = purpose
        logger.info(f"Purpose: {purpose}")
        
        await self._safe_send_message(
            update,
            "⏳ जांच हो रही है...",
            reply_markup=ReplyKeyboardRemove()
        )

        logger.info(f"Full loan data: {context.user_data['loan']}")
        
        # Run prediction in executor if it's blocking
        result = await asyncio.get_event_loop().run_in_executor(
            None, self.loan_service.predict_eligibility, context.user_data["loan"]
        )
        
        self._safe_db_log(
            telegram_id=str(update.effective_user.id),
            query_type="loan_check",
            query_text=str(context.user_data["loan"]),
            response=result["message_hindi"]
        )
        
        await self._safe_send_message(update, result["message_hindi"])
        context.user_data.clear()
        return ConversationHandler.END

    def _extract_number(self, text: str) -> str:
        import re
        text = text.strip().lower()
        if text.replace(",", "").isdigit():
            return text.replace(",", "")
        
        hindi_map = {'हजार': 1000, 'लाख': 100000, 'बीस': 20, 'तीस': 30}
        for word, val in hindi_map.items():
            if word in text:
                digits = re.findall(r'\d+', text)
                if digits and word in ['हजार', 'लाख']:
                    return str(int(digits[0]) * val)
                return str(val)
        
        digits = re.findall(r'\d+', text)
        return digits[0] if digits else text

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await self._safe_send_message(
            update,
            "❌ रद्द। /loan से फिर शुरू करें",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def _process_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """
        Process voice message and return transcribed text
        IMPROVED: Better async handling, cleanup, and error messages
        """
        path = None
        processing_msg = None
        
        try:
            # Show processing indicator
            processing_msg = await update.message.reply_text("🎤 सुन रहा हूँ…")
            
            # Download voice file with unique name
            file = await update.message.voice.get_file()
            path = os.path.abspath(f"voice_{update.effective_user.id}_{update.message.message_id}.ogg")
            
            logger.info(f"Downloading voice to: {path}")
            await file.download_to_drive(path)
            logger.info("Voice file downloaded successfully")
            
            # Convert speech to text - run in executor to avoid blocking
            text = await asyncio.get_event_loop().run_in_executor(
                None, self.voice_handler.speech_to_text, path
            )
            
            logger.info(f"🔍 Voice handler returned: '{text}' (type: {type(text).__name__})")
            
            # Delete processing message
            if processing_msg:
                try:
                    await processing_msg.delete()
                except:
                    pass
            
            # Validate transcription
            if text and isinstance(text, str) and len(text.strip()) > 0:
                logger.success(f"✅ Voice recognized: {text}")
                await update.message.reply_text(f"✅ समझा: \"{text}\"")
                return text.strip()
            else:
                logger.warning(f"⚠️ Voice recognition failed. Text: {repr(text)}")
                await update.message.reply_text(
                    "❌ आवाज़ साफ़ नहीं आई। कृपया:\n"
                    "• साफ और धीरे बोलें\n"
                    "• शोर से दूर रहें\n"
                    "• फिर से कोशिश करें या टाइप करें"
                )
                return None
                
        except Exception as e:
            logger.error(f"❌ Voice processing error: {e}")
            logger.exception("Full traceback:")
            
            # Clean up processing message
            if processing_msg:
                try:
                    await processing_msg.delete()
                except:
                    pass
            
            await update.message.reply_text(
                "❌ आवाज़ को समझने में समस्या हुई। कृपया टाइप करें।"
            )
            return None
            
        finally:
            # Always clean up voice file
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Cleaned up: {path}")
                except Exception as e:
                    logger.warning(f"Could not delete {path}: {e}")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages
        IMPROVED: Uses _process_voice helper with better async patterns
        """
        try:
            # Process voice to get text
            text = await self._process_voice(update, context)
            
            # If transcription successful, get answer from RAG
            if text:
                # Run RAG query in executor to avoid blocking (if it's CPU-intensive)
                reply = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.rag_service.answer_question(text)["answer"]
                )
                
                # Log the interaction
                self._safe_db_log(
                    telegram_id=str(update.effective_user.id),
                    query_type="voice_query",
                    query_text=text,
                    response=reply
                )
                
                await self._safe_send_message(update, reply)
            
        except Exception as e:
            logger.error(f"Voice handler error: {e}")
            logger.exception("Full traceback:")
            await self._safe_send_message(update, "❌ समस्या हुई। /start से शुरू करें।")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text
        if query == "🏦 लोन जांच":
            await self.loan_start(update, context)
        elif query == "⚠️ धोखाधड़ी":
            await self.fraud(update, context)
        elif query == "🔍 योजना":
            await self.schemes(update, context)
        elif query == "❓ मदद":
            await self.help(update, context)
        else:
            # Run RAG query in executor
            reply = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.rag_service.answer_question(query)["answer"]
            )
            await self._safe_send_message(update, reply)

    def run(self):
        logger.info("🚀 Bot running - 11 features with improved async")
        self.app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    GraminSahayakBot().run()