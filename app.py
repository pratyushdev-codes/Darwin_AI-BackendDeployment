
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load your existing code
from main import EmpathethicCodeReviewer

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Empathetic Code Reviewer API",
    description="API for transforming critical code review comments into empathetic feedback and code analysis",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeReviewRequest(BaseModel):
    code_snippet: str
    review_comments: List[str]

class CodeAnalysisRequest(BaseModel):
    code_snippet: str
    query: str

class CodeReviewResponse(BaseModel):
    markdown_report: str
    success: bool
    message: str = ""

class CodeAnalysisResponse(BaseModel):
    analysis: str
    success: bool
    message: str = ""

@app.on_event("startup")
async def startup_event():
    """Initialize the code reviewer on startup"""
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
    
    # Initialize the reviewer and store it in app state
    app.state.reviewer = EmpathethicCodeReviewer(API_KEY)

@app.post("/review", response_model=CodeReviewResponse)
async def generate_empathetic_review(request: CodeReviewRequest):
    """
    Generate empathetic code review feedback from critical comments.
    
    Parameters:
    - code_snippet: The code being reviewed (string)
    - review_comments: List of critical review comments to transform
    
    Returns:
    - markdown_report: Formatted empathetic review in Markdown
    """
    try:
        # Prepare input data
        input_data = {
            "code_snippet": request.code_snippet,
            "review_comments": request.review_comments
        }
        
        # Process the review
        markdown_report = app.state.reviewer.process_review(input_data)
        
        return CodeReviewResponse(
            markdown_report=markdown_report,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating review: {str(e)}"
        )

@app.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze code based on user query and provide helpful feedback.
    
    Parameters:
    - code_snippet: The code to analyze (string)
    - query: User's question or request about the code
    
    Returns:
    - analysis: Formatted analysis and suggestions
    """
    try:
        # Create a review comment from the user's query
        review_comments = [request.query]
        
        # Prepare input data for the reviewer
        input_data = {
            "code_snippet": request.code_snippet,
            "review_comments": review_comments
        }
        
        # Process the analysis using the empathetic reviewer
        analysis_report = app.state.reviewer.process_review(input_data)
        
        return CodeAnalysisResponse(
            analysis=analysis_report,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing code: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)