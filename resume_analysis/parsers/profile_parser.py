from typing import Dict, Optional, List
import PyPDF2
import io
from github import Github
import re
import aiohttp
from datetime import datetime, timedelta

class ProfileParser:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.github_token = self.config.get('github_token')
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else ''
        }

    async def parse_all_sources(self, 
                              resume_pdf: bytes,
                              github_username: Optional[str] = None,
                              linkedin_pdf: Optional[bytes] = None) -> str:
        """Parse and concatenate all available profile sources"""
        
        sections = []
        
        # Parse Resume PDF
        if resume_pdf:
            resume_text = await self._parse_resume_pdf(resume_pdf)
            sections.append(f"RESUME SECTION:\n{resume_text}")
        
        # Parse GitHub Profile
        if github_username and self.github_token:
            github_text = await self._parse_github_profile(github_username)
            sections.append(f"GITHUB SECTION:\n{github_text}")
            
        # Parse LinkedIn PDF
        if linkedin_pdf:
            linkedin_text = await self._parse_linkedin_pdf(linkedin_pdf)
            sections.append(f"LINKEDIN SECTION:\n{linkedin_text}")
            
        return "\n\n" + "\n\n===\n\n".join(sections) + "\n"

    async def _parse_linkedin_pdf(self, pdf_content: bytes) -> str:
        """Parse LinkedIn profile PDF export"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            # Extract structured information
            structured_data = {
                'basic_info': self._extract_basic_info(text),
                'experience': self._extract_experience(text),
                'education': self._extract_education(text),
                'skills': self._extract_skills(text)
            }

            # Format the extracted information
            formatted_text = self._format_linkedin_data(structured_data)
            return formatted_text

        except Exception as e:
            raise ValueError(f"Failed to parse LinkedIn PDF: {str(e)}")

    def _format_linkedin_data(self, data: Dict) -> str:
        """Format structured LinkedIn data into text"""
        text = "LinkedIn Profile\n\n"
        
        # Basic Info
        if data['basic_info']:
            text += f"Name: {data['basic_info'].get('name', '')}\n"
            text += f"Headline: {data['basic_info'].get('headline', '')}\n"
            text += f"Location: {data['basic_info'].get('location', '')}\n\n"
        
        # Experience
        text += "Experience:\n"
        for exp in data['experience']:
            text += f"- {exp.get('title', '')} at {exp.get('company', '')}\n"
            text += f"  {exp.get('date_range', '')}\n"
            if exp.get('description'):
                text += f"  {exp['description']}\n"
            text += "\n"
        
        # Education
        text += "Education:\n"
        for edu in data['education']:
            text += f"- {edu.get('degree', '')} from {edu.get('school', '')}\n"
            if edu.get('date_range'):
                text += f"  {edu['date_range']}\n"
            text += "\n"
        
        # Skills
        text += "Skills:\n"
        for skill in data['skills']:
            text += f"- {skill}\n"
            
        return text

            
    async def _parse_resume_pdf(self, pdf_bytes: bytes) -> str:
        """Extract and clean text from PDF resume"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Clean extracted text
            text = self._clean_text(text)
            return text
            
        except Exception as e:
            raise ValueError(f"Failed to parse PDF resume: {str(e)}")
    
    async def _parse_github_profile(self, username: str) -> str:
        """Extract relevant information from GitHub profile"""
        try:
            g = Github(self.github_token)
            user = g.get_user(username)
            repos = user.get_repos()
            
            text = f"GitHub Profile - {username}\n"
            text += f"Bio: {user.bio or ''}\n\n"
            
            # Collect languages and topics
            languages = set()
            topics = set()
            repo_texts = []
            
            for repo in repos:
                if not repo.fork:  # Skip forked repositories
                    if repo.language:
                        languages.add(repo.language)
                    topics.update(repo.get_topics())
                    
                    # Get detailed repo info
                    repo_text = f"Repository: {repo.name}\n"
                    repo_text += f"Description: {repo.description or 'No description'}\n"
                    repo_text += f"Language: {repo.language or 'Not specified'}\n"
                    repo_text += f"Stars: {repo.stargazers_count}\n"
                    repo_text += f"Topics: {', '.join(repo.get_topics())}\n"
                    repo_texts.append(repo_text)
            
            # Add summary sections
            text += f"Programming Languages: {', '.join(languages)}\n"
            text += f"Topics & Skills: {', '.join(topics)}\n\n"
            text += "Notable Repositories:\n"
            text += "\n---\n".join(repo_texts)  
            
            return text
            
        except Exception as e:
            raise ValueError(f"Failed to parse GitHub profile: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        # Normalize line endings
        text = text.replace('\r', '\n')
        text = re.sub(r'\n\s*\n+', '\n\n', text) 
        
        return text.strip()
    
    def _extract_basic_info(self, text: str) -> Dict:
        """Extract basic profile information"""
        basic_info = {}
        
        # Name is usually at the start of the PDF
        name_match = re.search(r'^([^\n]+)', text)
        if name_match:
            basic_info['name'] = name_match.group(1).strip()

        # Extract headline (usually follows the name)
        headline_match = re.search(r'^[^\n]+\n([^\n]+)', text)
        if headline_match:
            basic_info['headline'] = headline_match.group(1).strip()

        # Extract location
        location_match = re.search(r'Location\s*([^\n]+)', text, re.IGNORECASE)
        if location_match:
            basic_info['location'] = location_match.group(1).strip()

        return basic_info

    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience entries"""
        experience = []
        
        # Find the Experience section
        exp_section = re.search(r'Experience\s*(.+?)(?=Education|Skills|$)', text, re.DOTALL | re.IGNORECASE)
        if exp_section:
            exp_text = exp_section.group(1)
            
            # Split into individual roles
            # LinkedIn PDF usually formats each role with company name followed by role details
            roles = re.split(r'\n(?=[A-Za-z]+ · )', exp_text)
            
            for role in roles:
                if not role.strip():
                    continue
                    
                role_dict = {}
                
                # Extract company and title
                company_match = re.search(r'(.+?) · (.+?)\n', role)
                if company_match:
                    role_dict['company'] = company_match.group(1).strip()
                    role_dict['title'] = company_match.group(2).strip()

                # Extract dates
                dates_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', role)
                if dates_match:
                    role_dict['date_range'] = dates_match.group(0).strip()

                # Extract description
                desc_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}.+?\n(.+?)(?=\n\n|$)', role, re.DOTALL)
                if desc_match:
                    role_dict['description'] = desc_match.group(1).strip()

                experience.append(role_dict)

        return experience

    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education entries"""
        education = []
        
        # Find the Education section
        edu_section = re.search(r'Education\s*(.+?)(?=Experience|Skills|$)', text, re.DOTALL | re.IGNORECASE)
        if edu_section:
            edu_text = edu_section.group(1)
            
            # Split into individual education entries
            entries = re.split(r'\n(?=[A-Za-z])', edu_text)
            
            for entry in entries:
                if not entry.strip():
                    continue
                    
                edu_dict = {}
                
                # Extract school name
                school_match = re.search(r'(.+?)\n', entry)
                if school_match:
                    edu_dict['school'] = school_match.group(1).strip()

                # Extract degree
                degree_match = re.search(r'(?:Bachelor|Master|PhD|BSc|MSc|MBA|MD|JD).+?(?:\n|$)', entry)
                if degree_match:
                    edu_dict['degree'] = degree_match.group(0).strip()

                # Extract dates
                dates_match = re.search(r'\d{4}\s*-\s*(?:\d{4}|Present)', entry)
                if dates_match:
                    edu_dict['date_range'] = dates_match.group(0).strip()

                education.append(edu_dict)

        return education

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills list"""
        skills = []
        
        # Find the Skills section
        skills_section = re.search(r'Skills\s*(.+?)(?=Languages|Interests|$)', text, re.DOTALL | re.IGNORECASE)
        if skills_section:
            skills_text = skills_section.group(1)
            
            # Split into individual skills
            # Skills are usually bullet-pointed or separated by newlines
            skills = [skill.strip() for skill in re.split(r'[•\n]', skills_text) if skill.strip()]

        return skills 

    async def parse_github_profile(self, username: str) -> Dict:
        """Parse GitHub profile data"""
        try:
            # Get user data
            user_url = f'https://api.github.com/users/{username}'
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(user_url) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch GitHub profile: {response.status}")
                    user_data = await response.json()
                
                # Get repositories
                repos_url = f'https://api.github.com/users/{username}/repos'
                async with session.get(repos_url) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch repositories: {response.status}")
                    repos_data = await response.json()
                
                # Get languages
                languages = {}
                for repo in repos_data:
                    lang = repo.get('language')
                    if lang:
                        languages[lang] = languages.get(lang, 0) + 1
                
                return {
                    'username': user_data.get('login'),
                    'name': user_data.get('name'),
                    'bio': user_data.get('bio'),
                    'repositories': [{
                        'name': repo['name'],
                        'description': repo.get('description'),
                        'stars': repo.get('stargazers_count', 0),
                        'language': repo.get('language'),
                        'url': repo['html_url']
                    } for repo in repos_data],
                    'languages': languages,
                    'contributions_last_year': await self._get_contributions(username, session)
                }
                
        except Exception as e:
            raise ValueError(f"GitHub profile parsing failed: {str(e)}")
            
    async def _get_contributions(self, username: str, session: aiohttp.ClientSession) -> int:
        """Get contribution count for the last year"""
        try:
            url = f'https://api.github.com/users/{username}/events'
            async with session.get(url) as response:
                if response.status != 200:
                    return 0
                events = await response.json()
                
            # Count push events in the last year
            one_year_ago = datetime.now() - timedelta(days=365)
            return sum(1 for event in events 
                      if event['type'] == 'PushEvent' 
                      and datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') > one_year_ago)
                      
        except Exception:
            return 0 