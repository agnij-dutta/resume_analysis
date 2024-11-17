from typing import Dict, List
import spacy
from collections import defaultdict
import re

class SkillExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.domain_skills = {
            'ai_ml': [
                'machine learning', 'deep learning', 'neural networks', 'tensorflow',
                'pytorch', 'scikit-learn', 'computer vision', 'nlp', 'data science'
            ],
            'web_dev': [
                'react', 'angular', 'vue', 'nodejs', 'javascript', 'typescript',
                'html', 'css', 'web development', 'frontend', 'backend'
            ],
            'blockchain': [
                'solidity', 'web3', 'ethereum', 'smart contracts', 'defi',
                'blockchain', 'cryptocurrency', 'consensus mechanisms'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops',
                'ci/cd', 'microservices', 'cloud architecture'
            ],
            'cybersecurity': [
                'penetration testing', 'security', 'cryptography', 'network security',
                'ethical hacking', 'vulnerability assessment', 'firewall'
            ]
        }

    def extract_skills(self, text: str) -> Dict:
        doc = self.nlp(text.lower())
        found_skills = defaultdict(list)
        
        # Extract skills using pattern matching
        for domain, skills in self.domain_skills.items():
            for skill in skills:
                if skill in text.lower():
                    found_skills[domain].append(skill)
        
        # Extract years of experience per domain
        for domain in self.domain_skills.keys():
            experience = self._extract_experience(text, domain)
            if experience:
                found_skills[f"{domain}_experience"] = experience
                
        return dict(found_skills)
        
    def _extract_experience(self, text: str, domain: str) -> int:
        """Extract years of experience for a specific domain"""
        patterns = [
            rf"(\d+)\s*(?:years?|yrs?).+?(?:experience|exp).+?{domain}",
            rf"{domain}.+?(\d+)\s*(?:years?|yrs?).+?(?:experience|exp)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return max(map(int, matches))
        return 0