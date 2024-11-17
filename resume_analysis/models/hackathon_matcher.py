from typing import Dict, List
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from  .resume_scorer import ResumeScorer

class HackathonMatcher:
    def __init__(self, historical_data_path: str = None):
        self.resume_scorer = ResumeScorer()
        self.model = RandomForestClassifier()
        if historical_data_path:
            self._train_model(historical_data_path)
        self.tracks = {
            'ai_ml': {
                'name': 'AI/ML',
                'min_score': 0.6,
                'recommended_skills': ['Python', 'TensorFlow', 'PyTorch', 'Data Science']
            },
            'web_dev': {
                'name': 'Web Development',
                'min_score': 0.5,
                'recommended_skills': ['JavaScript', 'React', 'Node.js', 'HTML/CSS']
            },
            'blockchain': {
                'name': 'Blockchain',
                'min_score': 0.65,
                'recommended_skills': ['Solidity', 'Web3.js', 'Smart Contracts']
            },
            'cloud': {
                'name': 'Cloud Computing',
                'min_score': 0.55,
                'recommended_skills': ['AWS', 'Azure', 'Docker', 'Kubernetes']
            },
            'cybersecurity': {
                'name': 'Cybersecurity',
                'min_score': 0.7,
                'recommended_skills': ['Network Security', 'Cryptography', 'Penetration Testing']
            }
        }
    
    def _train_model(self, data_path: str):
        # Load and prepare historical data
        data = pd.read_csv(data_path)
        X = data[['domain_score', 'experience', 'github_score']]
        y = data['accepted']
        self.model.fit(X, y)
    
    def match_hackathons(self, enhanced_analysis: Dict, hackathons: List[Dict]) -> List[Dict]:
        """Match candidate with hackathons based on enhanced analysis"""
        matches = []
        
        for hackathon in hackathons:
            primary_track = hackathon.get('primary_track', '')
            if not primary_track or primary_track not in self.tracks:
                continue
                
            # Get domain-specific scores
            domain_score = enhanced_analysis.get('enhanced_scores', {}).get(
                primary_track, 
                {}
            ).get('score', 0)
            
            # Get LLM insights
            llm_analysis = enhanced_analysis.get('llm_analysis', {})
            technical_depth = llm_analysis.get('technical_analysis', {})
            project_evaluation = llm_analysis.get('project_evaluation', {})
            
            # Calculate compatibility
            compatibility = self._calculate_compatibility(
                domain_score,
                technical_depth,
                project_evaluation,
                hackathon,
                primary_track
            )
            
            if compatibility >= self.tracks[primary_track]['min_score']:
                matches.append({
                    'hackathon': hackathon,
                    'compatibility_score': round(compatibility, 2),
                    'technical_match': {
                        'score': technical_depth.get('skill_depth_score', 0),
                        'strengths': technical_depth.get('key_technical_achievements', [])
                    },
                    'project_match': {
                        'score': project_evaluation.get('project_score', 0),
                        'complexity_match': project_evaluation.get('technical_complexity', 'Medium')
                    },
                    'recommendations': self._generate_track_recommendations(
                        enhanced_analysis,
                        hackathon,
                        primary_track
                    )
                })
        
        return sorted(matches, key=lambda x: x['compatibility_score'], reverse=True)
    
    def _calculate_compatibility(self, domain_score: float, technical_depth: Dict, 
                               project_evaluation: Dict, hackathon: Dict, track: str) -> float:
        """Calculate compatibility score between candidate and hackathon"""
        weights = {
            'domain_score': 0.4,
            'technical_depth': 0.3,
            'project_complexity': 0.3
        }
        
        # Normalize scores to 0-1 range
        technical_score = technical_depth.get('skill_depth_score', 0) / 10
        project_score = project_evaluation.get('project_score', 0) / 10
        domain_score = domain_score / 10
        
        # Apply difficulty adjustment
        difficulty_factor = {
            'Beginner': 1.2,
            'Intermediate': 1.0,
            'Advanced': 0.8
        }.get(hackathon.get('difficulty'), 1.0)
        
        raw_score = (
            weights['domain_score'] * domain_score +
            weights['technical_depth'] * technical_score +
            weights['project_complexity'] * project_score
        ) * difficulty_factor
        
        return min(max(raw_score, 0), 1)  # Ensure score is between 0 and 1
    
    def _generate_track_recommendations(self, enhanced_analysis: Dict, 
                                     hackathon: Dict, track: str) -> Dict:
        """Generate track-specific recommendations"""
        track_info = self.tracks[track]
        missing_skills = [
            skill for skill in track_info['recommended_skills']
            if skill not in enhanced_analysis.get('llm_analysis', {})
                .get('technical_analysis', {})
                .get('key_technical_achievements', [])
        ]
        
        return {
            'track_name': track_info['name'],
            'recommended_skills': missing_skills,
            'min_score_required': track_info['min_score'],
            'preparation_tips': [
                f"Focus on learning {skill}" for skill in missing_skills[:3]
            ] if missing_skills else ["You have the core skills for this track!"]
        } 