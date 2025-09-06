import os
from openai import OpenAI
from dotenv import load_dotenv
from reddit_fetcher import RedditFetcher

# Load environment variables
load_dotenv()


class TextProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def process_text_for_narration(self, raw_text):
        """
        Process Reddit post text to make it suitable for narration.
        Cleans formatting, improves readability, but preserves all content.
        
        Args:
            raw_text (str): Raw Reddit post text
            
        Returns:
            str: Processed text ready for text-to-speech
        """
        if not raw_text:
            return ""
        
        try:
            prompt = f"""Please process this Reddit post text to make it suitable for audio narration. 

IMPORTANT REQUIREMENTS:
- DO NOT summarize, shorten, or remove any content
- Keep ALL the story content intact
- Remove Reddit-specific formatting (markdown, links, asterisks, etc.)
- Fix any awkward punctuation or formatting artifacts
- Do not include the first section
- Make it flow naturally when read aloud
- Add appropriate pauses with commas and periods
- Convert "Update:" sections to "Update." for better narration
- Remove URLs and hyperlink text but keep the context
- Keep all dialogue and quoted text
- Preserve the chronological order of events

Original text:
{raw_text}

Return ONLY the processed text, no additional commentary."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert text processor that prepares written content for audio narration. You preserve all content while improving readability and flow."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            processed_text = response.choices[0].message.content.strip()
            
            print(f"Text processing completed:")
            print(f"Original length: {len(raw_text)} characters")
            print(f"Processed length: {len(processed_text)} characters")
            
            return processed_text
            
        except Exception as e:
            print(f"Error processing text with OpenAI: {e}")
            # Return cleaned text as fallback
            return self._basic_text_cleanup(raw_text)
    
    def _basic_text_cleanup(self, text):
        """
        Basic text cleanup without OpenAI as fallback
        """
        # Remove common Reddit formatting
        cleaned = text.replace('**', '')
        cleaned = cleaned.replace('*', '')
        cleaned = cleaned.replace('#', '')
        cleaned = cleaned.replace('&gt;', '')
        cleaned = cleaned.replace('&lt;', '')
        
        # Fix spacing
        cleaned = ' '.join(cleaned.split())
        
        return cleaned


def test_processor():
    """Test the text processor with real Reddit content"""
    processor = TextProcessor()
    fetcher = RedditFetcher()
    
    # Get Reddit URL from user
    reddit_url = input("Enter a Reddit post URL to process: ").strip()
    
    if not reddit_url:
        print("No URL provided. Exiting test.")
        return
    
    print("TESTING TEXT PROCESSOR WITH REDDIT CONTENT")
    print("="*50)
    
    # Fetch Reddit post data
    print("Fetching Reddit post...")
    post_data = fetcher.fetch_post(reddit_url)
    
    if not post_data:
        print("Failed to fetch Reddit post data.")
        return
    
    print(f"\nSuccessfully fetched post from r/{post_data['subreddit']}")
    print(f"Title: {post_data['title']}")
    print(f"Content length: {len(post_data['full_text'])} characters")
    
    # Process the text for narration
    print("\nProcessing text for narration...")
    processed_text = processor.process_text_for_narration(post_data['full_text'])
    
    print("\n" + "="*50)
    print("PROCESSED TEXT FOR NARRATION")
    print("="*50)
    print(processed_text)
    
    # Save processed text to file for review
    filename = f"processed_text_{post_data['subreddit']}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        print(f"\n✅ Processed text saved to: {filename}")
    except Exception as e:
        print(f"\n❌ Error saving processed text: {e}")


if __name__ == "__main__":
    test_processor()