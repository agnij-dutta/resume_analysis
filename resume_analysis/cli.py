import sys
import json
from resume_analysis.main import analyze_candidate, analyze_linkedin_profile
import asyncio

async def main():
    command = sys.argv[1]
    input_data = json.loads(sys.argv[2])
    
    if command == "analyze_candidate":
        result = await analyze_candidate(
            resume_pdf=input_data['resume_pdf'],
            github_username=input_data.get('github_username'),
            linkedin_url=input_data.get('linkedin_url'),
            hackathons=input_data.get('hackathons')
        )
        print(json.dumps(result))
        
    elif command == "analyze_linkedin":
        result = await analyze_linkedin_profile(input_data['pdf_content'])
        print(json.dumps(result))

if __name__ == "__main__":
    asyncio.run(main()) 