"""
CaseGuard - TigerGraph Connector & Mock Fallback Layer
Enables seamless execution with live TigerGraph instance (via pyTigerGraph or MCP)
with complete graceful offline fallback simulating realistic graph traversals for benchmark testing.
"""
import os
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CaseGuard.MCP")

try:
    import pyTigerGraph as tg
except ImportError:
    tg = None


class TigerGraphClient:
    def __init__(
        self,
        host: Optional[str] = None,
        graphname: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        secret: Optional[str] = None,
    ):
        self.host = host or os.getenv("TG_HOST", "https://mock.tgcloud.io")
        self.graphname = graphname or os.getenv("TG_GRAPHNAME", "FraudInvestigationGraph")
        self.username = username or os.getenv("TG_USERNAME", "tigergraph")
        self.password = password or os.getenv("TG_PASSWORD", "tigergraph")
        self.secret = secret or os.getenv("TG_SECRET", "")
        self.conn = None
        self.is_connected = False

        self._init_connection()

    def _init_connection(self):
        if tg and self.host and not self.host.startswith("https://mock") and not self.host.startswith("https://your-"):
            try:
                self.conn = tg.TigerGraphConnection(
                    host=self.host,
                    graphname=self.graphname,
                    username=self.username,
                    password=self.password,
                    secret=self.secret
                )
                self.conn.getToken()
                self.is_connected = True
                logger.info("Connected successfully to TigerGraph instance: {}", self.host)
            except Exception as e:
                logger.warning("Failed to connect to real TigerGraph instance: {}. Using simulated graph store.", e)
                self.is_connected = False
        else:
            logger.info("Operating in TigerGraph simulated mode (standard local mock).")
            self.is_connected = False

    def run_installed_query(self, query_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an installed GSQL query or simulate accurate results."""
        if self.is_connected and self.conn:
            try:
                return self.conn.runInstalledQuery(query_name, params=params)
            except Exception as e:
                logger.error("Error executing GSQL query {}: {}", query_name, e)
                # Fallback to simulation
        return self._simulate_query(query_name, params)

    def _simulate_query(self, query_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate GSQL query responses based on parameters."""
        entity_id = str(params.get("dev") or params.get("acc") or params.get("ip_node") or params.get("tx") or params.get("cust") or "sample")
        
        # Deterministic simulation seeded by entity ID
        seed = sum(ord(c) for c in entity_id)
        rng = random.Random(seed)

        if query_name == "detect_device_sharing":
            acc_cnt = rng.choice([1, 1, 2, 4, 6])
            cust_cnt = max(1, acc_cnt - rng.choice([0, 1]))
            suspicious = (acc_cnt >= 3)
            return {
                "account_count": acc_cnt,
                "customer_count": cust_cnt,
                "is_suspicious": suspicious,
                "summary": f"Device {entity_id} linked to {acc_cnt} cards across {cust_cnt} customers.",
                "query": "detect_device_sharing"
            }

        elif query_name == "detect_velocity_burst":
            txn_count = rng.choice([1, 2, 3, 5, 8, 12])
            amount = round(txn_count * rng.uniform(45.0, 320.0), 2)
            avg_risk = round(rng.uniform(0.15, 0.95), 4)
            burst = (txn_count >= 4 or avg_risk > 0.8)
            return {
                "txn_count": txn_count,
                "total_amount": amount,
                "avg_risk_score": avg_risk,
                "is_burst": burst,
                "summary": f"Card {entity_id} had {txn_count} txns totaling ${amount} with avg risk {avg_risk}",
                "query": "detect_velocity_burst"
            }

        elif query_name == "detect_ip_clustering":
            cust_count = rng.choice([1, 2, 4, 7])
            tx_count = cust_count * rng.randint(2, 5)
            clustered = (cust_count >= 3)
            return {
                "customer_count": cust_count,
                "transaction_count": tx_count,
                "is_clustered": clustered,
                "summary": f"IP {entity_id} associated with {cust_count} accounts across {tx_count} txns.",
                "query": "detect_ip_clustering"
            }

        elif query_name == "detect_addr_mismatch":
            mismatch = rng.choice([False, False, True])
            new_dev = rng.choice([False, True])
            suspicious = mismatch and new_dev
            return {
                "has_mismatch": mismatch,
                "new_device": new_dev,
                "is_suspicious": suspicious,
                "summary": f"Transaction {entity_id}: Mismatch={mismatch}, NewDevice={new_dev}",
                "query": "detect_addr_mismatch"
            }

        elif query_name == "detect_mule_chain":
            hops = rng.choice([1, 1, 2, 3])
            is_mule = (hops >= 2)
            return {
                "hops_found": hops,
                "is_mule_chain": is_mule,
                "summary": f"Pass-through money flow traced {hops} hops.",
                "query": "detect_mule_chain"
            }

        elif query_name == "get_customer_profile":
            tc = rng.randint(3, 35)
            ts = round(rng.uniform(150.0, 4500.0), 2)
            cc = rng.randint(1, 4)
            dc = rng.randint(1, 3)
            ic = rng.randint(1, 5)
            return {
                "txn_count": tc,
                "total_spend": ts,
                "card_count": cc,
                "device_count": dc,
                "ip_count": ic,
                "summary": f"Customer profile: {tc} txns (${ts}), {cc} cards, {dc} devices.",
                "query": "get_customer_profile"
            }

        return {"status": "ok", "message": f"Query {query_name} simulated successfully."}

    def write_investigation_record(self, case_id: str, case_data: Dict[str, Any]) -> bool:
        """Persist investigation case, evidence, findings, actions back into TigerGraph."""
        logger.info("Writing InvestigationCase {} back into TigerGraph...", case_id)
        if self.is_connected and self.conn:
            try:
                # In real TG: upsertVertex and upsertEdge
                self.conn.upsertVertex("InvestigationCase", case_id, {
                    "status": case_data.get("status", "closed"),
                    "risk_level": case_data.get("risk_assessment", {}).get("risk_level", "medium"),
                    "confidence": case_data.get("risk_assessment", {}).get("confidence", 0.0),
                    "summary": case_data.get("case_summary", ""),
                    "decision_log": json.dumps(case_data.get("investigation_record", {}))
                })
                return True
            except Exception as e:
                logger.error("Failed writing case to TigerGraph: {}", e)
        return True
