#!/usr/bin/env python3
"""
TV Show Calendar Generator
Fetches ALL episodes from TVmaze API and generates an iCalendar (.ics) file
"""

import json
import urllib.request
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

# Shows to track: (TVmaze ID, Show Name)
SHOWS = [
    (65876, "Hell's Paradise: Jigokuraku"),
    (61739, "Hijack"),
    (48450, "Jujutsu Kaisen"),  # Includes ALL seasons (S1, S2, S3 The Culling Game)
]

def fetch_episodes(show_id):
    """Fetch all episodes for a show from TVmaze API"""
    url = f"https://api.tvmaze.com/shows/{show_id}/episodes"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching show {show_id}: {e}")
        return []

def fetch_show_info(show_id):
    """Fetch show info from TVmaze API"""
    url = f"https://api.tvmaze.com/shows/{show_id}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching show info {show_id}: {e}")
        return {}

def generate_calendar():
    """Generate iCalendar with ALL episodes (past, present, and future)"""
    cal = Calendar()
    cal.add('prodid', '-//TV Show Calendar//github.com/kz-ai-dev//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'TV Show Calendar')
    cal.add('x-wr-timezone', 'America/New_York')
    
    events_added = 0
    
    for show_id, show_name in SHOWS:
        print(f"Fetching {show_name}...")
        
        # Get show info for network/platform
        show_info = fetch_show_info(show_id)
        network = "Unknown"
        if show_info.get('network'):
            network = show_info['network']['name']
        elif show_info.get('webChannel'):
            network = show_info['webChannel']['name']
        
        # Get episodes
        episodes = fetch_episodes(show_id)
        
        for ep in episodes:
            if not ep.get('airdate'):
                continue
            
            air_date = datetime.strptime(ep['airdate'], '%Y-%m-%d').date()
            
            # Include ALL episodes with air dates (past, present, future)
            
            # Create event
            event = Event()
            
            # Title: Show Name - SXXEYY: Episode Title
            season = ep.get('season', 0)
            number = ep.get('number', 0)
            ep_title = ep.get('name', 'TBA')
            event.add('summary', f"{show_name} - S{season:02d}E{number:02d}: {ep_title}")
            
            # Description with details
            description = f"Show: {show_name}\n"
            description += f"Episode: {ep_title}\n"
            description += f"Season {season}, Episode {number}\n"
            description += f"Network/Platform: {network}\n"
            if ep.get('runtime'):
                description += f"Runtime: {ep['runtime']} min\n"
            if ep.get('summary'):
                # Strip HTML tags from summary
                summary = ep['summary'].replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', '')
                description += f"\n{summary}"
            
            event.add('description', description)
            
            # Date/Time (use airdate with noon EST as default time)
            airtime = ep.get('airtime', '12:00')
            if not airtime:
                airtime = '12:00'
            
            try:
                hour, minute = map(int, airtime.split(':'))
            except:
                hour, minute = 12, 0
            
            # Create datetime in EST (shows usually air in evening)
            est = pytz.timezone('America/New_York')
            start_dt = datetime(air_date.year, air_date.month, air_date.day, hour, minute)
            start_dt = est.localize(start_dt)
            
            # Default 30 min duration for anime, 45-60 for live action
            runtime = ep.get('runtime', 30)
            if not runtime:
                runtime = 30
            end_dt = start_dt + timedelta(minutes=runtime)
            
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            
            # Unique ID for the event
            event.add('uid', f"tvshow-{show_id}-s{season}e{number}@kz-ai-dev.github.io")
            
            # URL to episode page
            if ep.get('url'):
                event.add('url', ep['url'])
            
            # Categories
            event.add('categories', ['TV Show', network])
            
            # Created/Modified timestamps
            now = datetime.now(pytz.UTC)
            event.add('dtstamp', now)
            event.add('created', now)
            
            cal.add_component(event)
            events_added += 1
            print(f"  Added: S{season:02d}E{number:02d} - {ep_title} ({air_date})")
    
    print(f"\nTotal events added: {events_added}")
    return cal

if __name__ == '__main__':
    print("Generating TV Show Calendar...")
    print("=" * 50)
    
    calendar = generate_calendar()
    
    # Write to file
    output_file = 'tv-calendar.ics'
    with open(output_file, 'wb') as f:
        f.write(calendar.to_ical())
    
    print("=" * 50)
    print(f"Calendar saved to: {output_file}")
    print(f"Subscribe URL will be: https://kz-ai-dev.github.io/tv-show-calendar/{output_file}")
