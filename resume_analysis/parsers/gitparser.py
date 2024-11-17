from github import Github
from urllib3.util import parse_url
import urllib3
import re

def _clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?-]', '', text)
    
    # Normalize line endings
    text = text.replace('\r', '\n')
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    return text.strip()

def extract_gituname_from_url(url):
    url_parsed = parse_url(url)
    if url_parsed.path:
        path_parts = url_parsed.path.strip('/').split('/')
        if len(path_parts) >= 1 and path_parts[0]:
            return path_parts[0]
    return None

def _parse_github_profile(username: str) -> str:
    print('parsegit called')
    """Extract relevant information from GitHub profile"""
    try:
        g = Github('') # remove token before commiting to git
        user = g.get_user(username)
        repos = user.get_repos()
        
        text = f"GitHub Profile - {username}\n"
        text += f"Bio: {user.bio or ''}\n\n"
        

        # Collect languages and topics
        languages = set()
        topics = set()
        repo_texts = []
        
        for repo in repos:
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
        text += "\n---\n".join(repo_texts)  # Include top 5 repos
        for rawitem in [str(x) + " : " + str(y) + "\n" for (x, y) in user.raw_data.items()]:
            text += rawitem
        # print(text)
        text = _clean_text(text)
        return text
        
    except Exception as e:
        raise ValueError(f"Failed to parse GitHub profile: {str(e)}")
    
# usecase

# uname = extract_gituname_from_url("https://github.com/googleboy-byte")
# gittext = _parse_github_profile(uname)