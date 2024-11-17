from typing import Dict, List, Optional
import json
import asyncio
from resume_analysis.utils.cache import Cache
from resume_analysis.utils.exceptions import LLMError
from ..config import Config
import requests
import re

class LLMAnalyzer:
    def __init__(self, config: Optional[Config] = None):
        """Initialize LLM Analyzer with optional configuration"""
        self.config = config or Config()
        self.cache = Cache(ttl=self.config.CACHE_TTL)
        self.api_url = "https://api-inference.huggingface.co/models/gpt2"
        self.headers = {"Authorization": f"Bearer {self.config.HUGGINGFACE_TOKEN}"}
        
    async def analyze_resume(self, resume_text: str) -> Dict:
        """Analyze resume using LLM"""
        try:
            # Mock data with better scoring
            return {
                'technical_analysis': {
                    'skill_depth_score': 7.5,
                    'key_technical_achievements': [
                        'Python Development',
                        'Machine Learning',
                        'TypeScript/JavaScript',
                        'Blockchain Development',
                        'Web Development'
                    ],
                    'project_score': 8.0,
                    'technical_complexity': 'High'
                },
                'soft_skills_analysis': {
                    'communication': 8.0,
                    'leadership': 7.0,
                    'teamwork': 8.5,
                    'key_attributes': [
                        'Strong project leadership',
                        'Effective communication',
                        'Cross-functional collaboration'
                    ]
                },
                'project_evaluation': {
                    'project_score': 8.2,
                    'technical_complexity': 'High',
                    'recommended_projects': [
                        'Full-stack Web Application',
                        'ML Model Deployment',
                        'Blockchain dApp'
                    ]
                },
                'growth_assessment': {
                    'score': 8.5,
                    'growth_indicators': [
                        'Diverse project portfolio',
                        'Quick learning ability',
                        'Technical versatility'
                    ],
                    'improvement_areas': [
                        'Cloud Technologies',
                        'System Design',
                        'DevOps Practices'
                    ]
                },
                'overall_score': 8.0
            }
        except Exception as e:
            raise LLMError(f"Resume analysis failed: {str(e)}")
        

    async def _get_llm_response(self, prompt: str) -> Dict:
        """Get response from Hugging Face Inference API"""
        max_retries = 3
        max_tokens = 800  # Maximum tokens for input to leave room for output
        
        # Truncate prompt if too long (using rough token estimation)
        estimated_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        if estimated_tokens > max_tokens:
            words = prompt.split()
            truncated_words = words[:int(max_tokens/1.3)]
            prompt = ' '.join(truncated_words)
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 100,
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "return_full_text": False,
                            "truncation": True,
                            "max_length": 1024
                        }
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return self._parse_llm_response(response)
                
                if response.status_code == 503:  # Model is loading
                    await asyncio.sleep(2)
                    continue
                    
                if attempt == max_retries - 1:
                    raise LLMError(f"Failed to get valid response: {response.text}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise LLMError(f"LLM processing failed: {str(e)}")
                await asyncio.sleep(1)
                
        return {}  # Fallback empty response

    def _extract_structured_data(self, text: str) -> Optional[Dict]:
        """Extract structured data from unstructured LLM response"""
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback extraction
            score_pattern = r'(?:score|rating):\s*(\d+)'
            scores = re.findall(score_pattern, text, re.I)
            
            list_pattern = r'(?:skills|achievements|areas):\s*\[(.*?)\]'
            lists = re.findall(list_pattern, text, re.I)
            
            return {
                'extracted_score': int(scores[0]) if scores else 5,
                'extracted_items': [
                    item.strip() 
                    for sublist in lists 
                    for item in sublist.split(',')
                ] if lists else []
            }
            
        except Exception:
            return None

    def _generate_analysis_prompts(self) -> Dict[str, str]:
        """Generate analysis prompt templates"""
        base_prompt = (
            "Analyze this section of a resume and provide a JSON response. "
            "Focus on specific details and quantifiable metrics.\n\n{text}"
        )
        
        return {
            'technical_depth': base_prompt,
            'soft_skills': base_prompt,
            'project_analysis': base_prompt,
            'growth_potential': base_prompt
        }

    def _structure_analysis(self, analyses: Dict) -> Dict:
        """Structure the analysis results"""
        try:
            return {
                'technical_analysis': analyses.get('technical_depth', {}),
                'soft_skills_analysis': analyses.get('soft_skills', {}),
                'project_evaluation': analyses.get('project_analysis', {}),
                'growth_assessment': analyses.get('growth_potential', {}),
                'overall_score': self._calculate_overall_score(analyses)
            }
        except Exception as e:
            raise LLMError(f"Failed to structure analysis: {str(e)}")

    def _calculate_overall_score(self, analyses: Dict) -> float:
        """Calculate overall score"""
        try:
            scores = []
            for category, data in analyses.items():
                if isinstance(data, dict) and 'score' in data:
                    scores.append(data['score'])
            
            if not scores:
                return 0
            
            return round(sum(scores) / len(scores), 2)
        except Exception as e:
            raise LLMError(f"Failed to calculate overall score: {str(e)}")

    async def analyze_text(self, text: str) -> Dict:
        """Analyze text using LLM"""
        try:
            # Check cache first
            cache_key = f"llm_analysis_{hash(text)}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
                
            # Prepare analysis prompts
            analyses = await asyncio.gather(
                self._analyze_technical_depth(text),
                self._analyze_soft_skills(text),
                self._analyze_projects(text),
                self._analyze_growth_potential(text)
            )
            
            # Structure results
            result = {
                'technical_depth': analyses[0],
                'soft_skills': analyses[1],
                'project_analysis': analyses[2],
                'growth_potential': analyses[3]
            }
            
            # Cache result
            self.cache.set(cache_key, result)
            return result
            
        except Exception as e:
            raise LLMError(f"LLM analysis failed: {str(e)}")
            
    async def _analyze_technical_depth(self, text: str) -> Dict:
        """Analyze technical skills and depth"""
        # Implementation would use actual LLM API call
        # This is a placeholder
        return {
            'skill_depth_score': 0.8,
            'key_technical_achievements': ['Python', 'Machine Learning']
        }
        
    async def _analyze_soft_skills(self, text: str) -> Dict:
        """Analyze soft skills"""
        return {
            'score': 0.7,
            'identified_skills': ['Communication', 'Leadership']
        }
        
    async def _analyze_projects(self, text: str) -> Dict:
        """Analyze project experience"""
        return {
            'project_score': 0.75,
            'technical_complexity': 'High'
        }
        
    async def _analyze_growth_potential(self, text: str) -> Dict:
        """Analyze growth potential"""
        return {
            'score': 0.85,
            'growth_indicators': ['Learning ability', 'Initiative']
        }

    def _chunk_text(self, text: str, max_length: int = 300) -> List[str]:
        """Split text into smaller chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Count actual tokens (rough approximation)
            word_tokens = len(word) // 4 + 1  # Rough estimate of tokens per word
            
            if current_length + word_tokens > max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def _combine_chunk_results(self, results: List[Dict]) -> Dict:
        """Combine results from multiple chunks"""
        combined = {
            'skill_depth_score': 0,
            'key_technical_achievements': [],
            'project_score': 0,
            'technical_complexity': 'Medium'
        }
        
        if not results:
            return combined
            
        # Average numerical scores
        scores = [r.get('skill_depth_score', 0) for r in results if isinstance(r.get('skill_depth_score'), (int, float))]
        if scores:
            combined['skill_depth_score'] = sum(scores) / len(scores)
        
        # Combine lists of achievements
        for result in results:
            if isinstance(result.get('key_technical_achievements'), list):
                combined['key_technical_achievements'].extend(result['key_technical_achievements'])
        
        # Remove duplicates while preserving order
        combined['key_technical_achievements'] = list(dict.fromkeys(combined['key_technical_achievements']))
        
        return combined

    def _parse_llm_response(self, response: requests.Response) -> Dict:
        """Parse and validate LLM response"""
        try:
            response_data = response.json()
            if isinstance(response_data, list) and response_data:
                response_text = response_data[0].get("generated_text", "")
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return self._extract_structured_data(response_text) or {}
            return {}
        except Exception:
            return {}