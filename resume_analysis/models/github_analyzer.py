from github import Github
from typing import Dict, List, Optional
from collections import defaultdict
import pandas as pd

class GitHubAnalyzer:
    def __init__(self, access_token: str):
        self.github = Github(access_token)
        
    def analyze_profile(self, username: str) -> Dict:
        user = self.github.get_user(username)
        repos = user.get_repos()
        
        analysis = {
            'total_repos': 0,
            'languages': defaultdict(int),
            'topics': defaultdict(int),
            'stars': 0,
            'contributions': 0,
            'domain_scores': defaultdict(float)
        }
        
        for repo in repos:
            analysis['total_repos'] += 1
            analysis['stars'] += repo.stargazers_count
            
            # Analyze languages
            if repo.language:
                analysis['languages'][repo.language] += 1
            
            # Analyze topics
            for topic in repo.get_topics():
                analysis['topics'][topic] += 1
        
        # Calculate domain scores based on repos and topics
        analysis['domain_scores'] = self._calculate_domain_scores(analysis)
        
        return analysis
    
    def _calculate_domain_scores(self, analysis: Dict) -> Dict[str, float]:
        domain_keywords = {
            'ai_ml': ['machine-learning', 'deep-learning', 'data-science', 'tensorflow', 'pytorch'],
            'web_dev': ['web', 'frontend', 'backend', 'fullstack', 'javascript'],
            'blockchain': ['blockchain', 'web3', 'ethereum', 'smart-contracts'],
            'cloud': ['aws', 'azure', 'kubernetes', 'docker', 'devops'],
            'cybersecurity': ['security', 'cryptography', 'penetration-testing']
        }
        
        scores = defaultdict(float)
        for domain, keywords in domain_keywords.items():
            domain_repos = sum(1 for topic in analysis['topics'] if any(k in topic for k in keywords))
            scores[domain] = (domain_repos / max(analysis['total_repos'], 1)) * 10
            
        return dict(scores) 