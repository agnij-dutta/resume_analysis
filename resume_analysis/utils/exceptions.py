class ResumeAnalysisError(Exception):
    """Base exception for resume analysis errors"""
    pass

class TokenError(ResumeAnalysisError):
    """Raised for authentication token issues"""
    pass

class APITokenError(ResumeAnalysisError):
    """Raised for API token issues (GitHub, LinkedIn, etc)"""
    pass

class LLMError(ResumeAnalysisError):
    """Raised when LLM processing fails"""
    pass

class RateLimitError(ResumeAnalysisError):
    """Raised when rate limit is exceeded"""
    pass 