from fastapi import APIRouter, HTTPException, Depends
from src.modules.technical_writer.api.schemas import GenerateDocRequest, GenerateDocResponse
from src.modules.technical_writer.domain.models import DocumentationType
from src.modules.technical_writer.services.api_doc_generator import APIDocGenerator
from src.modules.technical_writer.services.user_guide_generator import UserGuideGenerator
from src.modules.technical_writer.services.code_doc_generator import CodeDocGenerator
from src.modules.technical_writer.services.release_notes_generator import ReleaseNotesGenerator

router = APIRouter(prefix="/technical_writer", tags=["Technical Writer"])


# Dependency Injection
def get_api_doc_generator():
    return APIDocGenerator()


def get_user_guide_generator():
    return UserGuideGenerator()


def get_code_doc_generator():
    return CodeDocGenerator()


def get_release_notes_generator():
    return ReleaseNotesGenerator()


@router.post("/generate", response_model=GenerateDocResponse)
async def generate_documentation(
    request: GenerateDocRequest,
    api_gen: APIDocGenerator = Depends(get_api_doc_generator),
    guide_gen: UserGuideGenerator = Depends(get_user_guide_generator),
    code_gen: CodeDocGenerator = Depends(get_code_doc_generator),
    release_gen: ReleaseNotesGenerator = Depends(get_release_notes_generator),
):
    """Generates documentation based on the request."""
    try:
        if request.doc_type == DocumentationType.API:
            if not request.source_code:
                raise HTTPException(status_code=400, detail="source_code is required for API documentation")
            result = await api_gen.generate_api_docs(code=request.source_code)
            return GenerateDocResponse(content=result.markdown_docs, metadata={"endpoints": result.endpoints_count})

        elif request.doc_type == DocumentationType.USER_GUIDE:
            if not request.feature_name:
                raise HTTPException(status_code=400, detail="feature_name is required for User Guide")

            # Use AST generator if source code is provided
            if request.source_code:
                from src.modules.technical_writer.services.ast_doc_generator import ASTUserGuideGenerator

                ast_gen = ASTUserGuideGenerator()
                result = ast_gen.generate(
                    code=request.source_code, feature_name=request.feature_name, audience=request.target_audience
                )
                return GenerateDocResponse(
                    content=result.guide_markdown, metadata={"sections": len(result.sections), "generator": "AST"}
                )
            else:
                # Fallback to template generator
                result = await guide_gen.generate_user_guide(
                    feature=request.feature_name, target_audience=request.target_audience
                )
                return GenerateDocResponse(
                    content=result.guide_markdown, metadata={"sections": len(result.sections), "generator": "Template"}
                )

        elif request.doc_type == DocumentationType.CODE:
            if not request.source_code:
                raise HTTPException(status_code=400, detail="source_code is required for Code documentation")
            result = await code_gen.document_function(function_code=request.source_code)
            return GenerateDocResponse(content=result.documented_code)

        elif request.doc_type == DocumentationType.RELEASE_NOTES:
            if not request.version:
                raise HTTPException(status_code=400, detail="version is required for Release Notes")

            # Construct fake commits from features/fixes to satisfy the service interface
            fake_commits = []
            if request.features:
                for f in request.features:
                    fake_commits.append({"message": f"feat: {f}"})
            if request.fixes:
                for f in request.fixes:
                    fake_commits.append({"message": f"fix: {f}"})

            result = await release_gen.generate_release_notes(git_commits=fake_commits, version=request.version)
            return GenerateDocResponse(content=result.markdown)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported documentation type: {request.doc_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_supported_types():
    """Returns supported documentation types."""
    return [t.value for t in DocumentationType]
