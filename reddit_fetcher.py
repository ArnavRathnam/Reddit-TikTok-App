import requests
import time
from urllib.parse import urlparse


class RedditFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'reddit-tiktok-app/1.0 (by /u/user)'
        }
    
    def fetch_post(self, reddit_url):
        """
        Fetch Reddit post data by adding .json to the URL
        
        Args:
            reddit_url (str): Reddit post URL
            
        Returns:
            dict: Post data containing title, selftext, and metadata
        """
        # Add .json to the URL if not already present
        if not reddit_url.endswith('.json'):
            json_url = reddit_url + '.json'
        else:
            json_url = reddit_url
        
        try:
            print(f"Fetching data from: {json_url}")
            response = requests.get(json_url, headers=self.headers, timeout=10)
            
            if response.status_code == 429:
                print("Rate limited. Waiting 5 seconds...")
                time.sleep(5)
                response = requests.get(json_url, headers=self.headers, timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            # Extract post data from Reddit JSON structure
            post_data = self._extract_post_data(data)
            return post_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Reddit data: {e}")
            return None
    
    def _extract_post_data(self, json_data):
        """
        Extract relevant post data from Reddit JSON response
        
        Args:
            json_data (list): Reddit JSON response
            
        Returns:
            dict: Extracted post data
        """
        try:
            # Reddit JSON returns a list, first item contains post data
            post_listing = json_data[0]['data']['children'][0]['data']
            
            post_data = {
                'title': post_listing.get('title', ''),
                'selftext': post_listing.get('selftext', ''),
                'author': post_listing.get('author', ''),
                'subreddit': post_listing.get('subreddit', ''),
                'score': post_listing.get('score', 0),
                'num_comments': post_listing.get('num_comments', 0),
                'created_utc': post_listing.get('created_utc', 0),
                'url': post_listing.get('url', ''),
                'permalink': post_listing.get('permalink', '')
            }
            
            # Combine title and selftext for full content
            full_text = post_data['title']
            if post_data['selftext']:
                full_text += "\n\n" + post_data['selftext']
            
            post_data['full_text'] = full_text
            
            print(f"Successfully extracted post from r/{post_data['subreddit']}")
            print(f"Title: {post_data['title'][:100]}...")
            print(f"Content length: {len(post_data['full_text'])} characters")
            
            return post_data
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing Reddit JSON: {e}")
            return None


def test_fetcher():
    """Test the Reddit fetcher with a sample URL"""
    fetcher = RedditFetcher()
    
    # Test with a sample Reddit URL (you can replace with actual BORUpdates URL)
    test_url = input("Enter a Reddit post URL to test: ").strip()
    
    if not test_url:
        print("No URL provided. Exiting test.")
        return
    
    post_data = fetcher.fetch_post(test_url)
    
    if post_data:
        print("\n" + "="*50)
        print("POST DATA EXTRACTED SUCCESSFULLY")
        print("="*50)
        print(f"Subreddit: r/{post_data['subreddit']}")
        print(f"Author: u/{post_data['author']}")
        print(f"Score: {post_data['score']}")
        print(f"Comments: {post_data['num_comments']}")
        print(f"Content length: {len(post_data['full_text'])} characters")
        print("\nFirst 500 characters of full text:")
        print(post_data['full_text'][:500] + "..." if len(post_data['full_text']) > 500 else post_data['full_text'])
    else:
        print("Failed to fetch post data.")


if __name__ == "__main__":
    test_fetcher()