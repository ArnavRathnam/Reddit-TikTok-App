import requests
import re
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

def extract_dates(text):
    date_regex = r'(Original Post\s*:\s*[^\n]+|Update\s*:\s*[^\n]+)'
    date_matches = re.findall(date_regex, text, re.IGNORECASE)
    dates = []
    for match in date_matches:
        try:
            dt = date_parser.parse(match.split(':', 1)[1].strip(), fuzzy=True)
            dates.append((match, dt))
        except Exception:
            continue
    return dates

def calculate_relative_times(dates):
    if not dates:
        return []
    dates_sorted = sorted(dates, key=lambda x: x[1])
    original_date = dates_sorted[0][1]
    rel_times = []
    for i, (label, dt) in enumerate(dates_sorted):
        if i == 0:
            rel_times.append(("Original post", label))
        else:
            delta = relativedelta(dt, original_date)
            if delta.years:
                time_str = f"{delta.years} year{'s' if delta.years > 1 else ''} later"
            elif delta.months:
                time_str = f"{delta.months} month{'s' if delta.months > 1 else ''} later"
            else:
                days = (dt - original_date).days
                weeks = days // 7
                if weeks:
                    time_str = f"{weeks} week{'s' if weeks > 1 else ''} later"
                else:
                    time_str = f"{days} day{'s' if days != 1 else ''} later"
            rel_times.append((f"Update {i}: {time_str}", label))
    return rel_times

def split_into_lines(text, max_words=10):
    words = text.strip().split()
    lines = []
    for i in range(0, len(words), max_words):
        lines.append(" ".join(words[i:i+max_words]))
    return lines

def clean_content(content):
    # Remove repeated post headers or disclaimers
    lines = content.splitlines()
    cleaned_lines = []
    seen_intro = False
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        # Skip footer/editorial clutter
        if any(kw in line_stripped.lower() for kw in ["please do not harass", "refer to rules", "i am not the oop"]):
            continue
        # Skip repeated intros
        if line_stripped.startswith("[Original Post]") or line_stripped.startswith("[Update]"):
            continue
        if line_stripped.startswith("EDIT: Added comments"):
            break
        cleaned_lines.append(line_stripped)
    return "\n".join(cleaned_lines)

def generate_script(title, username, origin_subreddit, content, rel_times):
    print(title)
    print(f"Originally posted by u/{username} in r/{origin_subreddit}\n")

    segments = []
    update_map = {label: tag for tag, label in rel_times}
    body_lines = content.splitlines()

    for line in body_lines:
        line = line.strip()
        if not line:
            continue

        # Insert update markers
        for tag, label in rel_times:
            if label.lower() in line.lower():
                segments.append(f"{tag}")
                break
        else:
            segments.extend(split_into_lines(line))

    for segment in segments:
        print(segment)

def fetch_from_url():
    url = input("Enter Reddit post JSON URL: ").strip()
    if not url.endswith(".json"):
        print("URL must end with .json")
        return

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return

    data = response.json()
    post_data = data[0]['data']['children'][0]['data']
    title = post_data['title']
    content_raw = post_data['selftext']
    content = clean_content(content_raw)

    # Extract original poster and subreddit from text
    user_match = re.search(r'OOP is u/(\w+)', content)
    sub_match = re.search(r'in r/(\w+)', content)
    username = user_match.group(1) if user_match else 'unknown_user'
    origin_subreddit = sub_match.group(1) if sub_match else 'unknown_sub'

    dates = extract_dates(content)
    rel_times = calculate_relative_times(dates)

    generate_script(title, username, origin_subreddit, content, rel_times)

if __name__ == '__main__':
    fetch_from_url()