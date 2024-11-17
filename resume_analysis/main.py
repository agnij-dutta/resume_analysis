import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from dotenv import load_dotenv
from resume_analysis.models.enhanced_resume_scorer import EnhancedResumeScorer
from resume_analysis.models.hackathon_matcher import HackathonMatcher
from typing import List, Dict, Optional
import json
from resume_analysis.utils.rate_limiter import RateLimiter
from resume_analysis.config import Config
from resume_analysis.parsers.profile_parser import ProfileParser
import asyncio

# Load environment variables
load_dotenv()

def initialize_llm():
    """Initialize LLM with environment variables and validate tokens"""
    try:
        huggingface_token = os.getenv('HUGGINGFACE_TOKEN')
        if not huggingface_token:
            raise ValueError("HUGGINGFACE_TOKEN not found in environment variables")
        
        # Test connection with a smaller, more reliable model
        response = requests.post(
            "https://api-inference.huggingface.co/models/gpt2",
            headers={"Authorization": f"Bearer {huggingface_token}"},
            json={"inputs": "Test"},
            timeout=10
        )
        
        if response.status_code in [200, 503]:  # 503 is acceptable as it means model is loading
            print("Successfully initialized Hugging Face client")
            return True
            
        raise ValueError(f"API test failed with status code: {response.status_code}")
        
    except requests.Timeout:
        print("Connection timeout. Please try again.")
        return False
    except requests.RequestException as e:
        print(f"Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error initializing LLM: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Set the HUGGINGFACE_TOKEN environment variable")
        print("2. Created an API token at https://huggingface.co/settings/tokens")
        return False

def analyze_skills(skills: List[str]) -> Dict:
    return {"skill_count": len(skills), "skills": skills}

def analyze_experience(experience: List[Dict]) -> str:
    years = sum(exp.get('duration_years', 0) for exp in experience)
    if years < 2: return "Entry"
    elif years < 5: return "Mid"
    else: return "Senior"

def analyze_education(education: List[Dict]) -> str:
    degrees = [edu.get('degree', '').lower() for edu in education]
    if any('phd' in d for d in degrees): return "PhD"
    elif any('master' in d for d in degrees): return "Masters"
    elif any('bachelor' in d for d in degrees): return "Bachelors"
    return "Other"

async def analyze_candidate(
    resume_pdf: bytes,
    github_username: Optional[str] = None,
    hackathons: Optional[List[Dict]] = None
) -> Dict:
    """
    Analyze a candidate's profile and match with hackathons
    """
    try:
        if not initialize_llm():
            raise RuntimeError("Failed to initialize LLM")
            
        config = Config()
        scorer = EnhancedResumeScorer(config)
        
        # Initialize analysis dict
        analysis = {}
        
        # Analyze resume
        resume_analysis = await scorer.analyze_profile(
            resume_pdf,
            github_username
        )
        analysis['resume_analysis'] = resume_analysis
        
        # Add GitHub analysis if username provided
        if github_username:
            github_analysis = await analyze_github_profile(github_username)
            analysis['github_analysis'] = github_analysis
        
        # Match with hackathons if provided
        if hackathons:
            matcher = HackathonMatcher()
            matches = matcher.match_hackathons(resume_analysis, hackathons)
            analysis['hackathon_matches'] = matches
            
        return analysis
        
    except Exception as e:
        print(f"Error in analyze_candidate: {str(e)}")
        raise

async def analyze_github_profile(username: str) -> Dict:
    try:
        parser = ProfileParser()
        github_data = await parser.parse_github_profile(username)
        
        # GitHub-specific analysis
        analysis_results = {
            'profile_data': github_data,
            'analysis': {
                'repository_count': len(github_data.get('repositories', [])),
                'total_stars': sum(repo.get('stars', 0) for repo in github_data.get('repositories', [])),
                'languages': github_data.get('languages', {}),
                'contribution_level': github_data.get('contributions_last_year', 0),
                'top_projects': sorted(
                    github_data.get('repositories', []),
                    key=lambda x: x.get('stars', 0),
                    reverse=True
                )[:5]
            }
        }
        
        return analysis_results
    except Exception as e:
        raise ValueError(f"Failed to analyze GitHub profile: {str(e)}")

def print_analysis_results(results: Dict):
    """Pretty print analysis results"""
    print("\n" + "="*50)
    print("🎯 RESUME ANALYSIS REPORT")
    print("="*50)
    
    # Overall Score
    overall_score = results['resume_analysis']['llm_analysis']['overall_score']
    print(f"\n📊 OVERALL SCORE: {overall_score}/10")
    print("-"*50)
    
    # Domain Scores
    print("\n💡 DOMAIN EXPERTISE")
    print("-"*30)
    for domain, details in results['resume_analysis']['enhanced_scores'].items():
        score = details['score']
        print(f"{domain.upper():15} : {score:4.1f}/10")
    
    # Technical Skills
    print("\n🔧 TECHNICAL ACHIEVEMENTS")
    print("-"*30)
    tech_achievements = results['resume_analysis']['llm_analysis']['technical_analysis']['key_technical_achievements']
    for achievement in tech_achievements:
        print(f"• {achievement}")
    
    # GitHub Analysis
    if 'github_analysis' in results:
        print("\n📚 GITHUB PORTFOLIO")
        print("-"*30)
        github = results['github_analysis']['analysis']
        print(f"Repositories : {github['repository_count']}")
        print(f"Total Stars  : {github['total_stars']}")
        print("\nTop Projects:")
        for project in github['top_projects'][:3]:
            print(f"• {project['name']} ({project['stars']}⭐)")
    
    # Recommendations
    print("\n📈 RECOMMENDATIONS")
    print("-"*30)
    recs = results['resume_analysis']['recommendations']
    if recs['strongest_domains']:
        print("\nStrengths:")
        for domain in recs['strongest_domains']:
            print(f"• {domain}")
    
    print("\nAreas for Growth:")
    for area in recs['improvement_areas'][:3]:
        print(f"• {area}")
    
    # Hackathon Matches
    if results.get('hackathon_matches'):
        print("\n🏆 HACKATHON MATCHES")
        print("-"*30)
        for match in results['hackathon_matches']:
            print(f"\n• {match['hackathon']['name']}")
            print(f"  Compatibility: {match['compatibility_score']*100:.1f}%")

if __name__ == "__main__":
    try:
        # Test resume file
        with open("Resume Suparno Saha.pdf", "rb") as f:
            resume_pdf = f.read()
            
        # Example hackathon data
        sample_hackathons = [{
            "id": "1",
            "name": "Example Hackathon",
            "primary_track": "ai_ml",
            "difficulty": "Intermediate"
        }]
        
        # Run the analysis
        results = asyncio.run(analyze_candidate(
            resume_pdf=resume_pdf,
            github_username="agnij-dutta",
            hackathons=sample_hackathons
        ))
        
        # Print formatted results
        print_analysis_results(results)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}") 