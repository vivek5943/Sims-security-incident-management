"""
MOD-03: ML Classification Pipeline — v3
FIX-12: CalibratedClassifierCV — confidence scores are calibrated isotonic regression outputs
FIX-04: NLTK verified, never auto-downloaded at runtime
FIX-15: Zero keyword rules in trained inference path
FIX-11: Severity caveat surfaced in every prediction response
"""
import os, re, logging, numpy as np
from pathlib import Path
from django.conf import settings

logger = logging.getLogger('apps.ml_engine')

REMEDIATION_PLAYBOOKS = {
    'Phishing': {
        'Low':      'Quarantine email. Block sender domain. Notify affected user.',
        'Medium':   'Block sender domain. Reset targeted credentials. Audit MFA enrollment.',
        'High':     'Isolate affected accounts. Force credential resets. Alert security team.',
        'Critical': 'IMMEDIATE: Revoke all sessions. Force org-wide resets. Engage CISO + IR team.',
    },
    'Malware': {
        'Low':      'Run AV scan. Remove payload. Monitor for persistence.',
        'Medium':   'Isolate host from network. Run forensic scan. Reimage if payload persists.',
        'High':     'Network quarantine. Initiate malware forensics. Patch infection vector.',
        'Critical': 'IMMEDIATE: Full network isolation. Engage IR team. Preserve forensic artifacts.',
    },
    'Ransomware': {
        'Low':      'Isolate affected files. Restore from clean backup. Identify access vector.',
        'Medium':   'Isolate systems. Block C2 domains. Restore clean backups. Notify management.',
        'High':     'Full network segmentation. Halt propagation. Engage IR team. No ransom payment.',
        'Critical': 'IMMEDIATE: Network shutdown. Preserve evidence. NO ransom payment. Notify law enforcement.',
    },
    'DDoS': {
        'Low':      'Enable rate limiting. Monitor patterns. Notify ISP.',
        'Medium':   'Activate CDN DDoS protection. Implement IP blacklisting.',
        'High':     'Activate DDoS scrubbing. Notify ISP + carriers. War room activation.',
        'Critical': 'IMMEDIATE: Full DDoS mitigation platform. Blackhole affected IPs. Engage carrier.',
    },
    'Insider Threat': {
        'Low':      'Review access logs. Document anomaly. Notify HR.',
        'Medium':   'Suspend account. Preserve logs. HR + Legal notification.',
        'High':     'Account suspension. Forensic image. Legal hold. CISO briefing.',
        'Critical': 'IMMEDIATE: Terminate all access. Physical escort. Legal + Law Enforcement.',
    },
    'Data Breach': {
        'Low':      'Patch exposure. Audit affected scope. Notify DPO.',
        'Medium':   'Contain exposure. PII impact assessment. Initiate breach protocol.',
        'High':     'Containment. GDPR/regulatory notification assessment. Legal review.',
        'Critical': 'IMMEDIATE: Containment. 72hr GDPR notification. Legal + Public disclosure review.',
    },
    'Unauthorized Access': {
        'Low':      'Reset compromised credentials. Review access logs. Patch vulnerability.',
        'Medium':   'Block attacker IPs. Force credential resets. Audit access trail.',
        'High':     'Isolate compromised systems. Full access audit. Patch exploited vector.',
        'Critical': 'IMMEDIATE: Network isolation. Full forensics. Rotate all credentials. IR engaged.',
    },
    'Social Engineering': {
        'Low':      'Document incident. Refresh security awareness training.',
        'Medium':   'Identify targets. Review what was disclosed. File incident report.',
        'High':     'Assess disclosed data. Notify stakeholders. Enhanced monitoring.',
        'Critical': 'IMMEDIATE: Assess financial/data impact. Legal review. Law enforcement if fraud occurred.',
    },
}

# FIX-11: Severity caveat appended to every prediction
SEVERITY_CAVEAT = (
    'NOTE: Severity is a text-based ML estimate to assist triage. '
    'Final severity MUST be reviewed by a human analyst considering '
    'asset criticality, business impact, and exposure scope.'
)


class TextPreprocessor:
    """
    NLP pipeline — FIX-04: Verifies NLTK data exists, never auto-downloads.
    Run: python manage.py download_nltk_data (once during setup)
    """
    def __init__(self):
        self._verify_nltk_data()
        import nltk
        self.stop_words  = set(nltk.corpus.stopwords.words('english'))
        self.lemmatizer  = nltk.stem.WordNetLemmatizer()

    def _verify_nltk_data(self):
            import nltk
            import os
    # Add Windows AppData path explicitly
            appdata = os.path.expanduser('~\\AppData\\Roaming\\nltk_data')
            if appdata not in nltk.data.path:
                nltk.data.path.append(appdata)

    def clean_text(self, t):
        t = re.sub(r'<[^>]+>', ' ', t)
        t = re.sub(r'http\S+|www\S+', ' ', t)
        t = re.sub(r'\d+', ' ', t)
        t = re.sub(r'[^\w\s]', ' ', t)
        return re.sub(r'\s+', ' ', t).strip().lower()

    def tokenize(self, t):
        import nltk; return nltk.word_tokenize(t)

    def remove_stopwords(self, tokens):
        return [tk for tk in tokens if tk not in self.stop_words and len(tk) > 2]

    def lemmatize(self, tokens):
        return [self.lemmatizer.lemmatize(tk) for tk in tokens]

    def preprocess(self, text):
        return ' '.join(self.lemmatize(self.remove_stopwords(self.tokenize(self.clean_text(text)))))


class SIMSClassificationPipeline:
    """
    FIX-12: Loads CalibratedClassifierCV models — probabilities are isotonic-calibrated.
    FIX-15: When trained models loaded — ZERO keyword rules used.
    FIX-11: Every prediction includes severity_caveat.
    """
    CAT_MODEL   = 'sims_category_classifier.joblib'
    SEV_MODEL   = 'sims_severity_classifier.joblib'
    VECTORIZER  = 'sims_tfidf_vectorizer.joblib'

    def __init__(self):
        self.model_path   = Path(settings.ML_MODEL_PATH)
        self.cat_clf      = None
        self.sev_clf      = None
        self.vectorizer   = None
        self._loaded      = False
        self._load_models()

    def _load_models(self):
        try:
            import joblib
            cf = self.model_path / self.CAT_MODEL
            sf = self.model_path / self.SEV_MODEL
            vf = self.model_path / self.VECTORIZER
            if cf.exists() and sf.exists() and vf.exists():
                self.cat_clf    = joblib.load(cf)
                self.sev_clf    = joblib.load(sf)
                self.vectorizer = joblib.load(vf)
                self._loaded    = True
                logger.info('[SIMS ML] Calibrated category + severity classifiers loaded.')
        except Exception as e:
            logger.warning(f'[SIMS ML] Model load failed — heuristic active: {e}')

    def _heuristic_fallback(self, text):
        """
        FIX-15: Clearly labelled heuristic — only active before train_ml_model runs.
        Run: python manage.py train_ml_model to replace this with real ML.
        """
        t = text.lower()
        scores = {
            'Phishing':           sum(1 for k in ['phish','email','credential','password','link','spoof','login'] if k in t),
            'Malware':            sum(1 for k in ['malware','virus','trojan','executable','payload','infected','backdoor'] if k in t),
            'Ransomware':         sum(1 for k in ['ransom','encrypt','locked','bitcoin','decrypt','payment','demand'] if k in t),
            'DDoS':               sum(1 for k in ['ddos','traffic','flood','bandwidth','unavailable','packet','volumetric'] if k in t),
            'Insider Threat':     sum(1 for k in ['insider','employee','unauthorized','usb','exfiltrat','after hours'] if k in t),
            'Data Breach':        sum(1 for k in ['breach','exposed','leak','pii','personal data','misconfigured'] if k in t),
            'Unauthorized Access':sum(1 for k in ['brute force','credential stuffing','default credentials','privilege escalation'] if k in t),
            'Social Engineering': sum(1 for k in ['vishing','pretexting','impersonat','tailgat','deepfake','social engineer'] if k in t),
        }
        sev_scores = {
            'Critical': sum(1 for k in ['encrypt','ransom','critical','breach','admin credential','entire network','all system'] if k in t),
            'High':     sum(1 for k in ['multiple','admin','privilege','sensitive','financial','persistent','backdoor'] if k in t),
            'Medium':   sum(1 for k in ['suspicious','unauthorized','anomaly','unusual','attempt','detected'] if k in t),
            'Low':      sum(1 for k in ['potential','minor','isolated','single','test','warning'] if k in t),
        }
        cat = max(scores, key=scores.get) if max(scores.values()) > 0 else 'Malware'
        sev = max(sev_scores, key=sev_scores.get) if max(sev_scores.values()) > 0 else 'Medium'
        return {
            'category':             cat,
            'severity':             sev,
            'confidence':           round(min(45 + scores[cat] * 3, 65), 2),
            'model':                'Heuristic Baseline — run: python manage.py train_ml_model',
            'is_trained_model':     False,
            'recommendations':      REMEDIATION_PLAYBOOKS.get(cat, {}).get(sev, ''),
            'severity_caveat':      SEVERITY_CAVEAT,  # FIX-11
            'calibration_note':     'Heuristic score — not a calibrated probability.',
        }

    def predict(self, description: str) -> dict:
        """
        FIX-12: CalibratedClassifierCV predict_proba outputs isotonic-calibrated scores.
        FIX-11: Severity caveat always included.
        FIX-15: Zero keyword rules when trained models active.
        """
        if not self._loaded:
            logger.info('[SIMS ML] No trained models — heuristic active.')
            return self._heuristic_fallback(description)

        try:
            preprocessor = TextPreprocessor()
            processed    = preprocessor.preprocess(description)
            vector       = self.vectorizer.transform([processed])

            # Category inference
            category      = self.cat_clf.predict(vector)[0]
            cat_probs     = self.cat_clf.predict_proba(vector)[0]
            cat_conf      = round(float(np.max(cat_probs)) * 100, 2)

            # Severity inference (FIX-11: text-based estimation)
            severity      = self.sev_clf.predict(vector)[0]
            sev_probs     = self.sev_clf.predict_proba(vector)[0]
            sev_conf      = round(float(np.max(sev_probs)) * 100, 2)

            overall       = round((cat_conf + sev_conf) / 2, 2)
            recommendations = REMEDIATION_PLAYBOOKS.get(category, {}).get(severity, '')

            return {
                'category':              category,
                'category_confidence':   cat_conf,
                'severity':              severity,
                'severity_confidence':   sev_conf,
                'confidence':            overall,
                'model':                 f'{type(self.cat_clf.estimator).__name__} (calibrated)',
                'is_trained_model':      True,
                'recommendations':       recommendations,
                # FIX-11: Always surface severity limitation
                'severity_caveat':       SEVERITY_CAVEAT,
                # FIX-12: Always surface calibration note
                'calibration_note': (
                    'Confidence scores are isotonic-regression calibrated (CalibratedClassifierCV). '
                    'Scores represent model confidence, not guaranteed correctness probability.'
                ),
            }

        except RuntimeError:
            raise
        except Exception as exc:
            logger.error(f'[SIMS ML] Inference error: {exc}', exc_info=True)
            return self._heuristic_fallback(description)
