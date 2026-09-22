"""
CaseGuard - GraphRAG Policy & Typology Grounding Engine
Grounds investigation agents with bank compliance policies, regulatory rules, and fraud typologies.
Uses semantic context retrieval rather than raw document dumps.
"""
from typing import List, Dict, Any


BANK_POLICY_DOCS = [
    {
        "id": "POL-SAR-001",
        "category": "SAR_FILING",
        "title": "BSA/AML Mandatory SAR Thresholds",
        "text": "Any aggregate transaction volume exceeding $5,000 involving potential money laundering, pass-through mule behavior, or rapid layering requires the filing of a Suspicious Activity Report (SAR) within 30 days under 31 CFR 1020.320.",
        "keywords": ["sar", "mule", "laundering", "5000", "regulatory"]
    },
    {
        "id": "POL-BLK-002",
        "category": "ACCOUNT_CONTROL",
        "title": "Account & Transaction Blocking Permissions",
        "text": "Autonomous agents may NOT unilaterally execute permanent account freezing or transaction cancellation without Human-in-the-Loop review. L1 analysts approve transaction holds; L2 senior analysts approve account locks.",
        "keywords": ["block", "freeze", "analyst", "permission", "approval"]
    },
    {
        "id": "POL-AUTH-003",
        "category": "STEP_UP_EVIDENCE",
        "title": "Controlled Evidence Gathering via Step-Up Auth",
        "text": "When confidence is below 75% but risk score exceeds 0.50, agents are authorized to automatically initiate non-disruptive evidence collection, including out-of-band Step-Up 2FA and customer transaction validation.",
        "keywords": ["step-up", "evidence", "confidence", "validation", "2fa"]
    },
    {
        "id": "TYP-DEV-101",
        "category": "TYPOLOGY",
        "title": "Device Multi-Accounting / Syndicate Ring",
        "text": "Fraud rings frequently rotate stolen card credentials across an emulator or shared hardware ID. Detection relies on graph degree: 3 or more distinct customer profiles or card numbers mapped to one device fingerprint within 72 hours.",
        "keywords": ["device", "sharing", "ring", "emulator", "syndicate"]
    },
    {
        "id": "TYP-VEL-102",
        "category": "TYPOLOGY",
        "title": "Rapid Fire Card Velocity Burst",
        "text": "Card testing bots trigger micro-authorizations or rapid sequential transactions within minutes. Characterized by sudden spike in transaction count (>4 in 24 hours) with elevated bank model risk scores.",
        "keywords": ["velocity", "burst", "card testing", "rapid", "spike"]
    }
]


class PolicyGroundingEngine:
    def __init__(self):
        self.docs = BANK_POLICY_DOCS

    def search_policy(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieve most relevant policy clauses based on keyword overlap / semantic alignment."""
        q_lower = query.lower()
        scored = []
        for doc in self.docs:
            score = 0
            for kw in doc["keywords"]:
                if kw in q_lower:
                    score += 2
            if doc["category"].lower() in q_lower:
                score += 3
            if score > 0:
                scored.append((score, doc))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            # Return top general policy if no direct match
            return [self.docs[0], self.docs[2]]
        return [item[1] for item in scored[:top_k]]

    def get_grounding_context(self, pattern_ids: List[str], confidence: float, risk_level: str) -> str:
        """Format synthesized policy context to pass to the agent."""
        query = " ".join(pattern_ids) + f" confidence {risk_level} block sar"
        relevant = self.search_policy(query)
        
        snippets = []
        for doc in relevant:
            snippets.append(f"[{doc['id']}] {doc['title']}: {doc['text']}")
            
        return "\n\n".join(snippets)
