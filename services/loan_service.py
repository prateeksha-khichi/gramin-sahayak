"""
Loan Service - Loads trained loan eligibility model
Predicts eligibility and calculates EMI
FIXED: Now provides all 11 features the model expects
"""

from pathlib import Path
from typing import Dict

import joblib
import numpy as np
from loguru import logger
import sys

def clean_text(text):
    if text is None or (isinstance(text, float) and text != text):
        return ""
    text = str(text).lower()
    text = ' '.join(text.split())
    return text.strip()

sys.modules['__main__'].clean_text = clean_text


class LoanService:
    """
    Loan eligibility prediction service
    FIXED: Provides all 11 features
    """

    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.model_dir = BASE_DIR / "models" / "loan_eligibility"

        self.model = None
        self.edu_encoder = None
        self.self_emp_encoder = None
        self.status_encoder = None
        self.text_preprocessor = None
        
        # Additional encoders for missing features
        self.gender_encoder = None
        self.dependents_encoder = None
        self.property_encoder = None
        
        # Label mappings
        self.education_map = {}
        self.employment_map = {}
        self.status_map = {}
        self.gender_map = {}
        self.dependents_map = {}
        self.property_map = {}

        self._load_model()
        self._build_label_maps()
        
        # Log expected feature count
        if self.model:
            logger.info(f"Model expects {self.model.n_features_in_} features")

    # ------------------------------------------------------------------

    def _load_model(self):
        """Load model and all encoders"""
        try:
            # Core files
            self.model = joblib.load(self.model_dir / "loan_eligibility_model.pkl")
            self.edu_encoder = joblib.load(self.model_dir / "edu_encoder.pkl")
            self.self_emp_encoder = joblib.load(self.model_dir / "self_emp_encoder.pkl")
            self.status_encoder = joblib.load(self.model_dir / "status_encoder.pkl")
            
            # Try to load additional encoders if they exist
            try:
                self.gender_encoder = joblib.load(self.model_dir / "gender_encoder.pkl")
                logger.info("✅ Gender encoder loaded")
            except FileNotFoundError:
                logger.warning("⚠️  Gender encoder not found - will create dummy")
                self.gender_encoder = self._create_dummy_encoder([' Male', ' Female'])
            
            try:
                self.dependents_encoder = joblib.load(self.model_dir / "dependents_encoder.pkl")
                logger.info("✅ Dependents encoder loaded")
            except FileNotFoundError:
                logger.warning("⚠️  Dependents encoder not found - will create dummy")
                self.dependents_encoder = self._create_dummy_encoder(['0', '1', '2', '3+'])
            
            try:
                self.property_encoder = joblib.load(self.model_dir / "property_encoder.pkl")
                logger.info("✅ Property encoder loaded")
            except FileNotFoundError:
                logger.warning("⚠️  Property encoder not found - will create dummy")
                self.property_encoder = self._create_dummy_encoder([' Rural', ' Semiurban', ' Urban'])
            
            try:
                self.text_preprocessor = joblib.load(self.model_dir / "text_preprocessor.pkl")
            except:
                pass

            logger.success("✅ Loan eligibility model loaded")
            logger.info(f"Education classes: {list(self.edu_encoder.classes_)}")
            logger.info(f"Employment classes: {list(self.self_emp_encoder.classes_)}")
            logger.info(f"Status classes: {list(self.status_encoder.classes_)}")
            if self.gender_encoder:
                logger.info(f"Gender classes: {list(self.gender_encoder.classes_)}")
            if self.dependents_encoder:
                logger.info(f"Dependents classes: {list(self.dependents_encoder.classes_)}")
            if self.property_encoder:
                logger.info(f"Property classes: {list(self.property_encoder.classes_)}")

        except Exception:
            logger.exception("❌ Failed to load loan eligibility models")
            self.model = None

    def _create_dummy_encoder(self, classes):
        """Create a dummy label encoder for missing encoders"""
        from sklearn.preprocessing import LabelEncoder
        encoder = LabelEncoder()
        encoder.classes_ = np.array(classes)
        return encoder

    # ------------------------------------------------------------------

    def _build_label_maps(self):
        """Build comprehensive label mappings"""
        if not self.edu_encoder:
            return
        
        # Get actual classes
        edu_classes = [str(c) for c in self.edu_encoder.classes_]
        emp_classes = [str(c) for c in self.self_emp_encoder.classes_]
        status_classes = [str(c) for c in self.status_encoder.classes_]
        
        # EDUCATION
        edu_variations = {
            'graduate': ['graduate', 'graduated', 'graduation', 'grad', 'स्नातक'],
            'not graduate': ['not graduate', 'not graduated', 'no graduation', 'undergraduate', 
                           'undergrad', 'no degree', 'अस्नातक'],
        }
        
        for model_label in edu_classes:
            clean_label = model_label.strip().lower()
            self.education_map[model_label] = model_label
            self.education_map[clean_label] = model_label
            
            for base_term, variations in edu_variations.items():
                if base_term in clean_label:
                    for var in variations:
                        self.education_map[var.lower()] = model_label
        
        # EMPLOYMENT
        emp_variations = {
            'yes': ['yes', 'self employed', 'business', 'व्यवसाय'],
            'no': ['no', 'not self employed', 'salaried', 'job', 'नौकरी'],
            'farmer': ['farmer', 'farming', 'agriculture', 'किसान'],
        }
        
        for model_label in emp_classes:
            clean_label = model_label.strip().lower()
            self.employment_map[model_label] = model_label
            self.employment_map[clean_label] = model_label
            
            for base_term, variations in emp_variations.items():
                if base_term in clean_label:
                    for var in variations:
                        self.employment_map[var.lower()] = model_label
        
        # STATUS (Married)
        status_variations = {
            'yes': ['yes', 'married', 'शादीशुदा'],
            'no': ['no', 'single', 'unmarried', 'अविवाहित'],
        }
        
        for model_label in status_classes:
            clean_label = model_label.strip().lower()
            self.status_map[model_label] = model_label
            self.status_map[clean_label] = model_label
            
            for base_term, variations in status_variations.items():
                if base_term in clean_label:
                    for var in variations:
                        self.status_map[var.lower()] = model_label
        
        # GENDER
        if self.gender_encoder:
            gender_classes = [str(c) for c in self.gender_encoder.classes_]
            gender_variations = {
                'male': ['male', 'man', 'boy', 'पुरुष', 'm'],
                'female': ['female', 'woman', 'girl', 'महिला', 'f'],
            }
            
            for model_label in gender_classes:
                clean_label = model_label.strip().lower()
                self.gender_map[model_label] = model_label
                self.gender_map[clean_label] = model_label
                
                for base_term, variations in gender_variations.items():
                    if base_term in clean_label:
                        for var in variations:
                            self.gender_map[var.lower()] = model_label
        
        # DEPENDENTS
        if self.dependents_encoder:
            dep_classes = [str(c) for c in self.dependents_encoder.classes_]
            for model_label in dep_classes:
                clean_label = model_label.strip()
                self.dependents_map[model_label] = model_label
                self.dependents_map[clean_label] = model_label
                # Map numbers
                if clean_label.isdigit():
                    self.dependents_map[clean_label] = model_label
                if '+' in clean_label:
                    self.dependents_map['3+'] = model_label
                    self.dependents_map['3'] = model_label
        
        # PROPERTY AREA
        if self.property_encoder:
            prop_classes = [str(c) for c in self.property_encoder.classes_]
            prop_variations = {
                'urban': ['urban', 'city', 'शहरी'],
                'rural': ['rural', 'village', 'ग्रामीण'],
                'semiurban': ['semiurban', 'semi urban', 'town', 'कस्बा'],
            }
            
            for model_label in prop_classes:
                clean_label = model_label.strip().lower()
                self.property_map[model_label] = model_label
                self.property_map[clean_label] = model_label
                
                for base_term, variations in prop_variations.items():
                    if base_term in clean_label:
                        for var in variations:
                            self.property_map[var.lower()] = model_label
        
        logger.info(f"✅ Built {len(self.education_map)} education, {len(self.employment_map)} employment, "
                   f"{len(self.status_map)} status, {len(self.gender_map)} gender, "
                   f"{len(self.dependents_map)} dependents, {len(self.property_map)} property mappings")

    # ------------------------------------------------------------------

    def _map_label(self, user_input: str, label_map: dict, encoder_name: str, default_idx: int = 0) -> str:
        """Smart label mapping"""
        if not user_input:
            return list(label_map.values())[default_idx] if label_map else ""
        
        user_input_clean = str(user_input).strip().lower()
        
        if user_input in label_map:
            return label_map[user_input]
        
        if user_input_clean in label_map:
            return label_map[user_input_clean]
        
        for key, value in label_map.items():
            if user_input_clean in key.lower() or key.lower() in user_input_clean:
                logger.info(f"Fuzzy matched '{user_input}' -> '{value}' in {encoder_name}")
                return value
        
        default = list(label_map.values())[default_idx] if label_map else ""
        logger.warning(f"No match for '{user_input}' in {encoder_name}, using: '{default}'")
        return default

    # ------------------------------------------------------------------

    def predict_eligibility(self, user_data: Dict) -> Dict[str, any]:
        """Predict loan eligibility"""

        if self.model is None:
            return self._error_response("मॉडल लोड नहीं हो पाया")

        try:
            features = self._prepare_features(user_data)
            
            # Verify feature count
            expected = self.model.n_features_in_
            actual = features.shape[1]
            logger.info(f"Features: expected={expected}, actual={actual}")
            
            if actual != expected:
                logger.error(f"Feature mismatch! Expected {expected}, got {actual}")
                return self._error_response(f"Feature count mismatch: {actual} vs {expected}")
            
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0]

            eligible = bool(prediction == 1)
            confidence = float(max(probability))

            loan_details = self._calculate_loan_details(user_data, eligible)
            messages = self._generate_messages(eligible, loan_details)

            return {
                "eligible": eligible,
                "confidence": round(confidence, 2),
                "recommended_amount": loan_details["recommended_amount"],
                "emi": loan_details["emi"],
                "interest_rate": loan_details["interest_rate"],
                "tenure_months": loan_details["tenure_months"],
                "message_hindi": messages["hindi"],
                "message_english": messages["english"],
            }

        except Exception:
            logger.exception("❌ Loan prediction error")
            return self._error_response("आंतरिक त्रुटि")

    # ------------------------------------------------------------------

    def _prepare_features(self, user_data: Dict) -> np.ndarray:
        """
        Prepare ALL 11 features the model expects
        
        Standard loan model features:
        1. ApplicantIncome
        2. CoapplicantIncome
        3. LoanAmount
        4. Loan_Amount_Term
        5. Credit_History
        6. Gender (encoded)
        7. Married (encoded)
        8. Dependents (encoded)
        9. Education (encoded)
        10. Self_Employed (encoded)
        11. Property_Area (encoded)
        """
        
        # Numeric features
        applicant_income = user_data.get("income", 0)
        coapplicant_income = user_data.get("coapplicant_income", 0)  # NEW
        loan_amount = user_data.get("loan_amount_requested", 0) / 1000  # Convert to thousands
        loan_term = user_data.get("loan_term", 360)  # NEW: Default 360 months (30 years)
        credit_history = 1.0 if user_data.get("credit_score", 300) >= 650 else 0.0  # NEW: Binary
        
        # Categorical features - raw
        gender_raw = user_data.get("gender", "Male")  # NEW
        married_raw = user_data.get("marital_status", "No")
        dependents_raw = str(user_data.get("dependents", "0"))  # NEW
        education_raw = user_data.get("education", "Graduate")
        self_employed_raw = user_data.get("employment_type", "No")
        property_area_raw = user_data.get("property_area", "Semiurban")  # NEW
        
        # Map to model labels
        gender = self._map_label(gender_raw, self.gender_map, "gender", 0)
        married = self._map_label(married_raw, self.status_map, "married", 0)
        dependents = self._map_label(dependents_raw, self.dependents_map, "dependents", 0)
        education = self._map_label(education_raw, self.education_map, "education", 0)
        self_employed = self._map_label(self_employed_raw, self.employment_map, "employment", 0)
        property_area = self._map_label(property_area_raw, self.property_map, "property", 1)
        
        logger.info(f"Mapping - Gender: '{gender_raw}' -> '{gender}'")
        logger.info(f"Mapping - Married: '{married_raw}' -> '{married}'")
        logger.info(f"Mapping - Dependents: '{dependents_raw}' -> '{dependents}'")
        logger.info(f"Mapping - Education: '{education_raw}' -> '{education}'")
        logger.info(f"Mapping - Self_Employed: '{self_employed_raw}' -> '{self_employed}'")
        logger.info(f"Mapping - Property: '{property_area_raw}' -> '{property_area}'")
        
        # Encode categorical features
        try:
            gender_enc = self.gender_encoder.transform([gender])[0]
            married_enc = self.status_encoder.transform([married])[0]
            dependents_enc = self.dependents_encoder.transform([dependents])[0]
            education_enc = self.edu_encoder.transform([education])[0]
            self_employed_enc = self.self_emp_encoder.transform([self_employed])[0]
            property_enc = self.property_encoder.transform([property_area])[0]
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            raise
        
        # Build feature array in correct order
        features = np.array([[
            applicant_income,      # 1
            coapplicant_income,    # 2
            loan_amount,           # 3
            loan_term,             # 4
            credit_history,        # 5
            gender_enc,            # 6
            married_enc,           # 7
            dependents_enc,        # 8
            education_enc,         # 9
            self_employed_enc,     # 10
            property_enc           # 11
        ]])
        
        logger.info(f"Feature array shape: {features.shape}")
        logger.info(f"Features: {features[0]}")
        
        return features

    # ------------------------------------------------------------------

    def _calculate_loan_details(self, user_data: Dict, eligible: bool) -> Dict:
        """Calculate loan details"""
        requested = user_data.get("loan_amount_requested", 0)
        income = user_data.get("income", 0)

        interest_rate = self._get_interest_rate(user_data)
        max_eligible = income * 60

        recommended = min(requested, max_eligible) if eligible else 0
        tenure_months = 36

        if recommended > 0:
            r = interest_rate / (12 * 100)
            emi = recommended * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        else:
            emi = 0

        return {
            "recommended_amount": round(recommended, 2),
            "emi": round(emi, 2),
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
        }

    def _get_interest_rate(self, user_data: Dict) -> float:
        """Interest rate based on profile"""
        credit = user_data.get("credit_score", 300)
        employment = user_data.get("employment_type", "salaried").strip().lower()

        if 'farmer' in employment or 'farm' in employment:
            base = 4.0
        elif 'salaried' in employment or 'job' in employment or 'no' in employment:
            base = 8.5
        else:
            base = 10.0

        if credit >= 750:
            return base
        elif credit >= 650:
            return base + 1.5
        return base + 3.0

    # ------------------------------------------------------------------

    def _generate_messages(self, eligible: bool, loan: Dict) -> Dict:
        if eligible:
            return {
                "hindi": (
                    f"✅ बधाई हो! आप लोन के लिए पात्र हैं।\n\n"
                    f"💰 राशि: ₹{loan['recommended_amount']:,.0f}\n"
                    f"📅 EMI: ₹{loan['emi']:,.0f}\n"
                    f"📊 ब्याज: {loan['interest_rate']}%\n"
                    f"⏱️ अवधि: {loan['tenure_months']} महीने"
                ),
                "english": (
                    f"✅ Congratulations! You are eligible.\n\n"
                    f"💰 Amount: ₹{loan['recommended_amount']:,.0f}\n"
                    f"📅 EMI: ₹{loan['emi']:,.0f}\n"
                    f"📊 Interest: {loan['interest_rate']}%\n"
                    f"⏱️ Tenure: {loan['tenure_months']} months"
                ),
            }
        return {
            "hindi": "❌ आप वर्तमान में लोन के लिए पात्र नहीं हैं।\n\nसुझाव:\n• क्रेडिट स्कोर बढ़ाएं\n• आय बढ़ाएं",
            "english": "❌ Not eligible.\n\nSuggestions:\n• Improve credit score\n• Increase income",
        }

    # ------------------------------------------------------------------

    def _error_response(self, message: str) -> Dict:
        """Error response"""
        return {
            "eligible": False,
            "confidence": 0.0,
            "recommended_amount": 0.0,
            "emi": 0.0,
            "interest_rate": 0.0,
            "tenure_months": 0,
            "message_hindi": f"त्रुटि: {message}",
            "message_english": f"Error: {message}",
        }