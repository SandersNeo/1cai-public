import uuid
from fastapi import APIRouter, HTTPException, Depends
from src.modules.security.api.schemas import ScanRequest, ScanResponse, ScanType
from src.modules.security.services.vulnerability_scanner import VulnerabilityScanner
from src.modules.security.services.sensitive_data_scanner import SensitiveDataScanner
from src.modules.security.services.compliance_checker import ComplianceChecker
from src.modules.security.services.dependency_auditor import DependencyAuditor

router = APIRouter(prefix="/security", tags=["Security Officer"])


# Dependency Injection
def get_vulnerability_scanner():
    return VulnerabilityScanner()


def get_sensitive_data_scanner():
    return SensitiveDataScanner()


def get_compliance_checker():
    return ComplianceChecker()


def get_dependency_auditor():
    return DependencyAuditor()


@router.post("/scan", response_model=ScanResponse)
async def perform_scan(
    request: ScanRequest,
    vuln_scanner: VulnerabilityScanner = Depends(get_vulnerability_scanner),
    secret_scanner: SensitiveDataScanner = Depends(get_sensitive_data_scanner),
    compliance_checker: ComplianceChecker = Depends(get_compliance_checker),
    dep_auditor: DependencyAuditor = Depends(get_dependency_auditor),
):
    """Performs a security scan based on the request."""
    scan_id = str(uuid.uuid4())
    try:
        if request.scan_type == ScanType.VULNERABILITY:
            # Read file content for scanning
            try:
                with open(request.target_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

            result = await vuln_scanner.scan_vulnerabilities(code=code)
            return ScanResponse(scan_id=scan_id, status="completed", result=result.model_dump())

        elif request.scan_type == ScanType.SECRETS:
            # Read file content for scanning (SensitiveDataScanner scans code string, not directory directly in this implementation)
            try:
                with open(request.target_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

            result = await secret_scanner.scan_code(code=code)
            return ScanResponse(scan_id=scan_id, status="completed", result=result.model_dump())

        elif request.scan_type == ScanType.COMPLIANCE:
            if not request.compliance_framework:
                raise HTTPException(status_code=400, detail="compliance_framework is required for Compliance scan")

            try:
                with open(request.target_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

            result = await compliance_checker.check_compliance(code=code, framework=request.compliance_framework)
            return ScanResponse(scan_id=scan_id, status="completed", result=result.model_dump())

        elif request.scan_type == ScanType.DEPENDENCY:
            # DependencyAuditor expects a list of dependencies, not a path.
            # For this API, we might need to parse requirements.txt or similar.
            # For simplicity, we'll implement a basic requirements.txt parser here.
            dependencies = []
            try:
                with open(request.target_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("==")
                            if len(parts) == 2:
                                dependencies.append({"name": parts[0], "version": parts[1]})
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read requirements file: {e}")

            result = await dep_auditor.audit_dependencies(dependencies)
            return ScanResponse(scan_id=scan_id, status="completed", result=result.model_dump())

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported scan type: {request.scan_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_supported_types():
    """Returns supported scan types."""
    return [t.value for t in ScanType]
