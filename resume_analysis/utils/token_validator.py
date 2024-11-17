from huggingface_hub import HfApi
from typing import Tuple, Optional
import os

class TokenValidator:
    @staticmethod
    def validate_huggingface_token(token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Hugging Face token has correct permissions
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            api = HfApi(token=token)
            
            # Try to access model info (this will validate read permissions)
            api.model_info("meta-llama/Llama-2-7b-chat-hf")
            
            return True, None
            
        except Exception as e:
            if "401" in str(e):
                return False, "Invalid token or insufficient permissions. Please ensure you have READ access."
            elif "403" in str(e):
                return False, "Token lacks required permissions. Please ensure READ access is enabled."
            else:
                return False, f"Error validating token: {str(e)}" 