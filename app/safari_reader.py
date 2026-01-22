import plistlib
import os
from typing import List, Dict
from datetime import datetime


def extract_reading_list(bookmarks_path: str) -> List[Dict]:
    """
    Extract reading list items from Safari's Bookmarks.plist file.

    Args:
        bookmarks_path: Path to Safari's Bookmarks.plist file

    Returns:
        List of dictionaries containing reading list items
    """
    if not os.path.exists(bookmarks_path):
        raise FileNotFoundError(f"Bookmarks file not found at {bookmarks_path}")

    with open(bookmarks_path, 'rb') as f:
        plist_data = plistlib.load(f)

    reading_list_items = []

    def traverse_bookmarks(children):
        """Recursively traverse bookmark structure to find reading list"""
        for item in children:
            if item.get('Title') == 'com.apple.ReadingList':
                # Found the reading list folder
                if 'Children' in item:
                    for reading_item in item['Children']:
                        url_string = reading_item.get('URLString', '')
                        reading_list_dict = reading_item.get('ReadingList', {})

                        reading_list_items.append({
                            'url': url_string,
                            'title': reading_item.get('URIDictionary', {}).get('title', ''),
                            'preview_text': reading_list_dict.get('PreviewText', ''),
                            'added_date': reading_list_dict.get('DateAdded'),
                        })
            elif 'Children' in item:
                # Continue traversing
                traverse_bookmarks(item['Children'])

    if 'Children' in plist_data:
        traverse_bookmarks(plist_data['Children'])

    return reading_list_items


def get_default_bookmarks_path() -> str:
    """Get the default Safari bookmarks path for macOS"""
    return os.path.expanduser('~/Library/Safari/Bookmarks.plist')
