from typing import Dict, Optional
from resume_analysis.models.llm_analyzer import LLMAnalyzer
from resume_analysis.models.resume_scorer import ResumeScorer
from resume_analysis.config import Config
from resume_analysis.utils.exceptions import ResumeAnalysisError
from resume_analysis.parsers.profile_parser import ProfileParser
import re

class EnhancedResumeScorer:
    def __init__(self, config: Config):
        self.config = config
        self.llm_analyzer = LLMAnalyzer(config)
        self.traditional_scorer = ResumeScorer(config.GITHUB_TOKEN)
        self.profile_parser = ProfileParser({
            'github_token': config.GITHUB_TOKEN
        })
    
    async def analyze_profile(
        self,
        resume_pdf: bytes,
        github_username: Optional[str] = None,
        linkedin_pdf: Optional[bytes] = None
    ) -> Dict:
        try:
            # Parse all sources into concatenated text
            concatenated_text = await self.profile_parser.parse_all_sources(
                resume_pdf,
                github_username,
                linkedin_pdf
            )
            
            # Extract section-specific content
            sections = self._split_sections(concatenated_text)
            
            # Perform analyses
            traditional_analysis = await self.traditional_scorer.analyze_async(sections['resume'])
            llm_analysis = await self.llm_analyzer.analyze_resume(concatenated_text)
            
            return self._combine_analyses(
                traditional_analysis, 
                llm_analysis,
                sections
            )
            
        except Exception as e:
            raise ResumeAnalysisError(f"Analysis failed: {str(e)}")
    
    def _split_sections(self, concatenated_text: str) -> Dict[str, str]:
        """Split concatenated text into its component sections"""
        sections = {
            'resume': '',
            'github': '',
            'linkedin': ''
        }
        
        # Split text on section markers
        parts = re.split(r'\n===\n', concatenated_text)
        for part in parts:
            if 'RESUME SECTION:' in part:
                sections['resume'] = part.split('RESUME SECTION:')[1].strip()
            elif 'GITHUB SECTION:' in part:
                sections['github'] = part.split('GITHUB SECTION:')[1].strip()
            elif 'LINKEDIN SECTION:' in part:
                sections['linkedin'] = part.split('LINKEDIN SECTION:')[1].strip()
                
        return sections
    
    def _combine_analyses(self, traditional: Dict, llm: Dict, sections: Dict[str, str]) -> Dict:
        """Combine traditional and LLM analyses into enhanced scores"""
        if not traditional.get('domain_scores'):
            return {}
        
        try:
            enhanced_scores = {}
            
            # Calculate domain-specific enhanced scores
            for domain in traditional['domain_scores']:
                github_factor = 1.0 if sections.get('github') else 0.8
                linkedin_factor = 1.0 if sections.get('linkedin') else 0.9
                
                traditional_score = traditional['domain_scores'].get(domain, 0)
                llm_technical_score = llm.get('technical_analysis', {}).get('skill_depth_score', 0)
                llm_project_score = llm.get('project_evaluation', {}).get('project_score', 0)
                
                enhanced_scores[domain] = {
                    'score': round(
                        0.4 * traditional_score * github_factor * linkedin_factor +
                        0.3 * llm_technical_score +
                        0.3 * llm_project_score,
                        2
                    ),
                    'technical_depth': llm.get('technical_analysis', {}),
                    'project_insights': llm.get('project_evaluation', {}),
                    'growth_potential': llm.get('growth_assessment', {}),
                    'source_completeness': {
                        'resume': bool(sections.get('resume')),
                        'github': bool(sections.get('github')),
                        'linkedin': bool(sections.get('linkedin'))
                    }
                }
            
            # Return combined analysis with all components
            return {
                'enhanced_scores': enhanced_scores,
                'llm_analysis': llm,
                'traditional_analysis': traditional,
                'recommendations': self._generate_recommendations(enhanced_scores)
            }
            
        except Exception as e:
            raise ResumeAnalysisError(f"Failed to combine analyses: {str(e)}")
    
    def _generate_recommendations(self, enhanced_scores: Dict) -> Dict:
        """Generate recommendations based on enhanced scores"""
        if not enhanced_scores:
            return {
                'strongest_domains': [],
                'improvement_areas': [],
                'recommended_focus': [],
                'learning_path': []
            }
        
        recommendations = {
            'strongest_domains': [],
            'improvement_areas': [],
            'recommended_focus': [],
            'learning_path': []
        }
        
        try:
            # Analyze scores and generate specific recommendations
            for domain, details in enhanced_scores.items():
                score = details.get('score', 0)
                growth_potential = details.get('growth_potential', {}).get('score', 0)
                
                if score >= 8.0:
                    recommendations['strongest_domains'].append(domain)
                elif score < 6.0:
                    recommendations['improvement_areas'].append(domain)
                    
                # Add learning recommendations based on growth potential
                if growth_potential >= 7.0:
                    recommendations['learning_path'].append({
                        'domain': domain,
                        'focus_areas': details.get('technical_depth', {}).get('improvement_areas', []),
                        'suggested_projects': details.get('project_insights', {}).get('recommended_projects', [])
                    })
                    
            # Determine recommended focus areas
            if recommendations['improvement_areas']:
                recommendations['recommended_focus'] = recommendations['improvement_areas'][:2]
            elif recommendations['strongest_domains']:
                recommendations['recommended_focus'] = recommendations['strongest_domains'][:1]
                
            return recommendations
            
        except Exception as e:
            raise ResumeAnalysisError(f"Failed to generate recommendations: {str(e)}")