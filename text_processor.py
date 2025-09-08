import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from reddit_fetcher import RedditFetcher

# Load environment variables
load_dotenv()


class TextProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Initialize tokenizer for GPT-4
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    def count_tokens(self, text):
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text, max_chunk_size=3000):
        """
        Split text into chunks that fit within token limits.
        Tries to split at paragraph boundaries when possible.
        
        Args:
            text (str): Text to chunk
            max_chunk_size (int): Maximum tokens per chunk
            
        Returns:
            list: List of text chunks
        """
        if self.count_tokens(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit, save current chunk
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            if self.count_tokens(test_chunk) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Single paragraph is too long, split by sentences
                    sentences = paragraph.split('. ')
                    temp_chunk = ""
                    for sentence in sentences:
                        test_sentence = temp_chunk + ". " + sentence if temp_chunk else sentence
                        if self.count_tokens(test_sentence) > max_chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = sentence
                            else:
                                # Single sentence too long, force split
                                chunks.append(sentence)
                        else:
                            temp_chunk = test_sentence
                    current_chunk = temp_chunk
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_text_for_narration(self, raw_text):
        """
        Process Reddit post text to make it suitable for narration.
        Cleans formatting, improves readability, but preserves all content.
        Handles long texts by chunking them if necessary.
        
        Args:
            raw_text (str): Raw Reddit post text
            
        Returns:
            str: Processed text ready for text-to-speech
        """
        if not raw_text:
            return ""
        
        try:
            # Check if text needs chunking
            input_tokens = self.count_tokens(raw_text)
            print(f"Input text tokens: {input_tokens}")
            
            # If text is too long, process in chunks
            if input_tokens > 3000:  # Leave room for prompt and response
                print("Text is long, processing in chunks...")
                return self._process_text_in_chunks(raw_text)
            
            # Process normally for shorter texts
            return self._process_single_chunk(raw_text)
            
        except Exception as e:
            print(f"Error processing text with OpenAI: {e}")
            # Return cleaned text as fallback
            return self._basic_text_cleanup(raw_text)
    
    def _process_single_chunk(self, raw_text):
        """Process a single chunk of text"""
        prompt = f"""Extract the story content from this Reddit post for audio narration. 

CRITICAL REQUIREMENTS:
- START with the post title as the very first line
- Then include the COMPLETE story exactly as written
- DO NOT summarize, condense, shorten, or paraphrase ANY content
- Remove ONLY: post metadata, URLs, hyperlinks, and Reddit formatting
- Keep EVERY sentence, paragraph, and detail of the actual story
- Preserve ALL dialogue, quotes, and conversations exactly
- Keep ALL emotional expressions, thoughts, and descriptions
- Maintain the exact chronological order and flow
- Convert markdown formatting to natural speech (remove **, *, etc.)
- Change "Update:" to "Update." for better narration flow
- Remove subreddit references and user info (except the title)
- If the story is long, keep it long - do NOT shorten it

FORMAT REQUIREMENTS:
- Line 1: The exact post title (clean, no formatting)
- Line 2: Empty line
- Line 3+: The complete story content

What to remove:
- Subreddit names, user info, timestamps
- URLs, hyperlinks, and link references
- Reddit-specific formatting (**, *, #, etc.)
- "Edit:" or "EDIT:" labels (convert to "Edit.")
- Comment sections, replies, or user discussions
- Any text that appears to be from commenters rather than the original poster
- Awards, voting info, or other Reddit metadata

What to keep EXACTLY:
- The post title as the first line
- Every sentence of the actual story content
- All dialogue and conversations
- All emotional descriptions and thoughts  
- All details, no matter how small
- All updates and follow-up content
- Natural paragraph breaks and flow

Original text:
{raw_text}

Return the title on the first line, then a blank line, then the complete extracted story content with clean formatting for narration. Do not add any commentary or explanations."""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a precise text extractor that removes only formatting and metadata while preserving 100% of the actual story content. You NEVER summarize, condense, or paraphrase. You extract the complete story exactly as written."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,  # Reduced from 8000 to stay within limits
            temperature=0.1
        )
        
        processed_text = response.choices[0].message.content.strip()
        
        print(f"Text processing completed:")
        print(f"Original length: {len(raw_text)} characters")
        print(f"Processed length: {len(processed_text)} characters")
        
        return processed_text
    
    def _process_text_in_chunks(self, raw_text):
        """Process long text by splitting it into chunks"""
        # First, extract the title from the full text
        title = self._extract_title(raw_text)
        
        chunks = self.chunk_text(raw_text, max_chunk_size=2500)
        processed_chunks = []
        
        print(f"Processing {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            try:
                if i == 0:
                    # First chunk gets the full treatment with title
                    processed_chunk = self._process_single_chunk(chunk)
                else:
                    # Subsequent chunks get story-only processing
                    processed_chunk = self._process_chunk_content_only(chunk)
                processed_chunks.append(processed_chunk)
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                # Use basic cleanup as fallback
                processed_chunks.append(self._basic_text_cleanup(chunk))
        
        # Combine all processed chunks
        final_text = "\n\n".join(processed_chunks)
        
        print(f"Chunked processing completed:")
        print(f"Original length: {len(raw_text)} characters")
        print(f"Processed length: {len(final_text)} characters")
        
        return final_text
    
    def _extract_title(self, raw_text):
        """Extract just the title from the raw text"""
        try:
            prompt = f"""Extract ONLY the title from this Reddit post.

Return just the title text, clean and without any formatting or extra text.

Original text:
{raw_text[:1000]}...

Return only the title:"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You extract titles from Reddit posts. Return only the clean title text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error extracting title: {e}")
            return "Reddit Story"
    
    def _process_chunk_content_only(self, chunk):
        """Process a chunk for content only (no title)"""
        prompt = f"""Clean this Reddit post content for audio narration.

REQUIREMENTS:
- Remove Reddit formatting and metadata
- Keep ALL story content exactly as written
- Do NOT add a title - this is a continuation
- Convert markdown to natural speech
- Change "Update:" to "Update."

Content:
{chunk}

Return only the cleaned content:"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You clean Reddit content while preserving all story details."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
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
    
    def generate_hashtags(self, post_title, post_content, subreddit):
        """
        Generate relevant hashtags for the video based on the Reddit post content.
        Always includes #reddit and #redditstories, then adds 3-5 content-relevant hashtags.
        
        Args:
            post_title (str): Reddit post title
            post_content (str): Reddit post content
            subreddit (str): Subreddit name
            
        Returns:
            str: Space-separated hashtags string
        """
        # Default hashtags
        hashtags = ["#reddit", "#redditstories"]
        
        try:
            prompt = f"""Based on this Reddit post, generate 3-5 relevant hashtags for social media.

POST DETAILS:
- Subreddit: r/{subreddit}
- Title: {post_title}
- Content preview: {post_content[:500]}...

REQUIREMENTS:
- Return exactly 3-5 hashtags (no more, no less)
- Make them relevant to the story content and themes
- Use lowercase
- Include the subreddit name as a hashtag if appropriate
- Focus on emotions, themes, and story elements
- Make them engaging for social media
- Do NOT include #reddit or #redditstories as those are already included

Return ONLY the hashtags separated by spaces, starting with #. No other text."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert social media hashtag generator. You create engaging, relevant hashtags based on content themes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            generated_hashtags = response.choices[0].message.content.strip()
            
            # Parse and clean generated hashtags
            generated_list = [tag.strip() for tag in generated_hashtags.split() if tag.startswith('#')]
            
            # Add generated hashtags to the default ones
            hashtags.extend(generated_list)
            
            print(f"Generated hashtags: {' '.join(hashtags)}")
            
            return ' '.join(hashtags)
            
        except Exception as e:
            print(f"Error generating hashtags with OpenAI: {e}")
            # Fallback hashtags based on subreddit
            fallback_hashtags = self._generate_fallback_hashtags(subreddit)
            hashtags.extend(fallback_hashtags)
            return ' '.join(hashtags)
    
    def _generate_fallback_hashtags(self, subreddit):
        """
        Generate basic hashtags when OpenAI is not available
        """
        subreddit_lower = subreddit.lower()
        
        # Common subreddit hashtag mappings
        subreddit_hashtags = {
            'amitheasshole': ['#aita', '#drama', '#judgment'],
            'relationship_advice': ['#relationships', '#advice', '#drama'],
            'tifu': ['#fail', '#mistake', '#funny'],
            'maliciouscompliance': ['#pettyrevenge', '#compliance', '#work'],
            'entitledparents': ['#entitled', '#parenting', '#drama'],
            'choosingbeggars': ['#choosing', '#beggar', '#funny'],
            'justnomil': ['#inlaws', '#family', '#drama'],
            'letsnotmeet': ['#creepy', '#scary', '#true']
        }
        
        if subreddit_lower in subreddit_hashtags:
            return subreddit_hashtags[subreddit_lower]
        else:
            # Generic hashtags
            return [f'#{subreddit_lower}', '#storytelling', '#viral']


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
    
    # Test hashtag generation
    print("\nTesting hashtag generation...")
    hashtags = processor.generate_hashtags(
        post_title=post_data['title'],
        post_content=processed_text,
        subreddit=post_data['subreddit']
    )
    print(f"Generated hashtags: {hashtags}")
    
    # Save hashtags to file
    hashtags_filename = f"test_hashtags_{post_data['subreddit']}.txt"
    try:
        with open(hashtags_filename, 'w', encoding='utf-8') as f:
            f.write(hashtags)
        print(f"✅ Hashtags saved to: {hashtags_filename}")
    except Exception as e:
        print(f"❌ Error saving hashtags: {e}")


if __name__ == "__main__":
    test_processor()