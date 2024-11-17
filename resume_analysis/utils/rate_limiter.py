from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = deque()

    def can_make_request(self) -> bool:
        now = datetime.now()
        
        # Remove old requests
        while self.requests and (now - self.requests[0]) > timedelta(seconds=self.time_window):
            self.requests.popleft()
        
        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
            
        return False 