"""
IBM Cloud Object Storage Service
"""

import os
import json
import logging
import io
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

try:
    import ibm_boto3
    from ibm_botocore.client import Config
    IBM_COS_AVAILABLE = True
except ImportError:
    IBM_COS_AVAILABLE = False
    logger.warning("ibm-cos-sdk not installed — COS operations will use local filesystem fallback")


class COSService:
    """IBM Cloud Object Storage wrapper with local filesystem fallback."""

    def __init__(self):
        self.api_key           = os.environ.get("IBM_COS_API_KEY", "")
        self.instance_crn      = os.environ.get("IBM_COS_INSTANCE_CRN", "")
        self.endpoint_url      = os.environ.get("IBM_COS_ENDPOINT", "https://s3.us-south.cloud-object-storage.appdomain.cloud")
        self.auth_endpoint     = os.environ.get("IBM_COS_AUTH_ENDPOINT", "https://iam.cloud.ibm.com/identity/token")
        self.bucket_kb         = os.environ.get("IBM_COS_BUCKET_KB", "startup-knowledge-base")
        self.bucket_reports    = os.environ.get("IBM_COS_BUCKET_REPORTS", "startup-reports")
        self.bucket_resources  = os.environ.get("IBM_COS_BUCKET_RESOURCES", "startup-resources")
        self._client = None
        self._local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")
        os.makedirs(self._local_dir, exist_ok=True)

        if IBM_COS_AVAILABLE and self.api_key:
            self._init_client()

    @property
    def client(self):
        """Lazy loader for the ibm_boto3 client."""
        if self._client is None and IBM_COS_AVAILABLE:
            self._init_client()
        return self._client

    def _init_client(self):
        # Reload configuration in case environment variables were loaded late
        self.api_key           = os.environ.get("IBM_COS_API_KEY", "")
        self.instance_crn      = os.environ.get("IBM_COS_INSTANCE_CRN", "")
        self.endpoint_url      = os.environ.get("IBM_COS_ENDPOINT", "https://s3.us-south.cloud-object-storage.appdomain.cloud")
        self.auth_endpoint     = os.environ.get("IBM_COS_AUTH_ENDPOINT", "https://iam.cloud.ibm.com/identity/token")
        self.bucket_kb         = os.environ.get("IBM_COS_BUCKET_KB", "startup-knowledge-base")
        self.bucket_reports    = os.environ.get("IBM_COS_BUCKET_REPORTS", "startup-reports")
        self.bucket_resources  = os.environ.get("IBM_COS_BUCKET_RESOURCES", "startup-resources")

        if not self.api_key:
            logger.warning("IBM_COS_API_KEY not found in environment. COSService will remain in local fallback mode.")
            return

        try:
            self._client = ibm_boto3.client(
                "s3",
                ibm_api_key_id=self.api_key,
                ibm_service_instance_id=self.instance_crn,
                ibm_auth_endpoint=self.auth_endpoint,
                config=Config(signature_version="oauth"),
                endpoint_url=self.endpoint_url,
            )
            logger.info("✅ IBM COS client initialised")
        except Exception as e:
            logger.error(f"COS init error: {e}")
            self._client = None

    # ── Upload ─────────────────────────────────────────────────────────────────
    def upload_file(self, bucket: str, key: str, content: bytes, content_type: str = "application/octet-stream") -> bool:
        if self.client:
            try:
                self.client.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
                logger.info(f"Uploaded to COS: {bucket}/{key}")
                return True
            except Exception as e:
                logger.error(f"COS upload error: {e}")
        # Fallback: local file
        local_path = os.path.join(self._local_dir, key.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved locally (COS unavailable): {local_path}")
        return True

    def upload_json(self, bucket: str, key: str, data: dict) -> bool:
        return self.upload_file(bucket, key, json.dumps(data, indent=2).encode(), "application/json")

    def upload_text(self, bucket: str, key: str, text: str) -> bool:
        return self.upload_file(bucket, key, text.encode(), "text/plain")

    # ── Download ───────────────────────────────────────────────────────────────
    def download_file(self, bucket: str, key: str) -> Optional[bytes]:
        if self.client:
            try:
                response = self.client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except Exception as e:
                logger.error(f"COS download error: {e}")
        local_path = os.path.join(self._local_dir, key.replace("/", "_"))
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()
        return None

    def download_json(self, bucket: str, key: str) -> Optional[dict]:
        data = self.download_file(bucket, key)
        if data:
            try:
                return json.loads(data)
            except Exception:
                pass
        return None

    # ── List ───────────────────────────────────────────────────────────────────
    def list_objects(self, bucket: str, prefix: str = "") -> List[dict]:
        if self.client:
            try:
                response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                return [
                    {"key": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"].isoformat()}
                    for obj in response.get("Contents", [])
                ]
            except Exception as e:
                logger.error(f"COS list error: {e}")
        # List local fallback
        items = []
        for fname in os.listdir(self._local_dir):
            fpath = os.path.join(self._local_dir, fname)
            if os.path.isfile(fpath):
                items.append({"key": fname, "size": os.path.getsize(fpath), "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()})
        return items

    # ── Presigned URL ──────────────────────────────────────────────────────────
    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> Optional[str]:
        if self.client:
            try:
                url = self.client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires)
                return url
            except Exception as e:
                logger.error(f"COS presigned URL error: {e}")
        return f"/api/export/download/{key}"

    # ── Knowledge Base ─────────────────────────────────────────────────────────
    def save_blueprint(self, session_id: str, blueprint: dict) -> str:
        key = f"blueprints/{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        self.upload_json(self.bucket_reports, key, blueprint)
        return key

    def get_resource_list(self) -> List[dict]:
        """Return list of downloadable resources from COS resources bucket."""
        files = self.list_objects(self.bucket_resources)
        # Augment with metadata
        resources = []
        for f in files:
            name = f["key"].split("/")[-1]
            ext  = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
            resources.append({
                "name": name.replace("_", " ").replace("-", " ").rsplit(".", 1)[0].title(),
                "key": f["key"],
                "type": ext,
                "size_kb": round(f["size"] / 1024, 1),
                "modified": f["modified"][:10],
                "url": self.get_presigned_url(self.bucket_resources, f["key"])
            })
        if not resources:
            resources = self._mock_resources()
        return resources

    @staticmethod
    def _mock_resources() -> List[dict]:
        return [
            {"name": "Startup Business Plan Template", "key": "startup_plan.docx", "type": "DOCX", "size_kb": 245, "modified": "2025-01-10", "url": "#"},
            {"name": "Investor Pitch Deck Template", "key": "pitch_deck.pptx", "type": "PPTX", "size_kb": 1820, "modified": "2025-01-08", "url": "#"},
            {"name": "Business Model Canvas PDF", "key": "bmc.pdf", "type": "PDF", "size_kb": 380, "modified": "2025-01-05", "url": "#"},
            {"name": "Startup India Complete Guide", "key": "startup_india_guide.pdf", "type": "PDF", "size_kb": 960, "modified": "2025-01-03", "url": "#"},
            {"name": "MSME Registration Guide", "key": "msme_guide.pdf", "type": "PDF", "size_kb": 540, "modified": "2024-12-28", "url": "#"},
            {"name": "Founders Agreement Template", "key": "founders_agreement.docx", "type": "DOCX", "size_kb": 120, "modified": "2024-12-20", "url": "#"},
            {"name": "SaaS Financial Model", "key": "saas_financial_model.xlsx", "type": "XLSX", "size_kb": 680, "modified": "2024-12-15", "url": "#"},
            {"name": "Term Sheet Template", "key": "term_sheet.docx", "type": "DOCX", "size_kb": 95, "modified": "2024-12-10", "url": "#"},
            {"name": "DPIIT Recognition Guide", "key": "dpiit_guide.pdf", "type": "PDF", "size_kb": 420, "modified": "2024-12-05", "url": "#"},
            {"name": "Startup Valuation Calculator", "key": "valuation_calc.xlsx", "type": "XLSX", "size_kb": 290, "modified": "2024-11-30", "url": "#"},
        ]


# Singleton
cos_service = COSService()
