#!/usr/bin/env python3
import argparse
import os
import sys
import logging
import markdown
import requests
import base64
import urllib3
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import re

import json
from datetime import datetime

# Disable SSL Warnings for LocalWP
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def convert_md_to_html(md_content):
    """Convert Markdown to HTML with extensions."""
    # Enable tables extension for better comparison charts
    return markdown.markdown(md_content, extensions=['extra', 'codehilite', 'tables'])

def generate_image_url(prompt):
    """
    Generate an image URL using Pollinations.ai (Free, No API Key).
    """
    # URL Encode the prompt
    encoded_prompt = requests.utils.quote(prompt)
    # 1280x720 is standard feature image size
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={datetime.now().timestamp()}"

def upload_media(image_url, title, wp_url, user, password):
    """
    Download image from URL and upload to WordPress Media Library.
    Returns the Media ID.
    """
    try:
        # A. Download Image
        logger.info(f"Downloading image from: {image_url}")
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        image_data = img_response.content
        
        # B. Upload to WordPress
        filename = f"{re.sub(r'[^a-zA-Z0-9]', '', title).lower()[:20]}_feature.jpg"
        api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media"
        
        credentials = f"{user}:{password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename={filename}'
        }
        
        logger.info(f"Uploading {filename} to WordPress...")
        response = requests.post(api_url, headers=headers, data=image_data, verify=False)
        response.raise_for_status()
        
        media_id = response.json().get('id')
        logger.info(f"Image uploaded successfully! Media ID: {media_id}")
        return media_id

    except Exception as e:
        logger.error(f"Failed to generate/upload image: {e}")
        return None

def generate_schema(title, content_md):
    """
    Generate JSON-LD Schema for SEO (Rich Snippets).
    Attempts to extract aggregate rating from Markdown tables.
    """
    # 1. Extract Ratings (looking for pattern: | 9.5/10 | or similar)
    ratings = re.findall(r'\|\s*(\d+(?:\.\d+)?)\s*/\s*10\s*\|', content_md)
    
    schema_type = "Article"
    aggregate_rating = None
    
    if ratings:
        # Calculate Average Rating for an "AggregateRating" schema
        scores = [float(r) for r in ratings]
        if scores:
            avg_score = sum(scores) / len(scores)
            count = len(scores)
            aggregate_rating = {
                "@type": "AggregateRating",
                "ratingValue": f"{avg_score:.1f}",
                "reviewCount": str(count),
                "bestRating": "10",
                "worstRating": "1"
            }
            # If we have ratings, treat it as a Product Guide/Review
            schema_type = "Product" 
    
    # Construct Schema
    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": title.replace('"', ''),
        "datePublished": datetime.now().isoformat(),
        "author": {
            "@type": "Person",
            "name": "Expert Reviewer" 
        }
    }

    if aggregate_rating:
         schema["name"] = title.replace('"', '')
         schema["aggregateRating"] = aggregate_rating
         # For Product schema, we need a name. Using title is a reasonable proxy for "The Products in X".
    
    return f'<script type="application/ld+json">{json.dumps(schema)}</script>'

def enhance_affiliate_content(html_content, schema_json=""):
    """
    Post-process HTML to add affiliate optimizations.
    """
    # 1. Inject Schema (Hidden)
    enhanced_html = schema_json + html_content

    # 2. Inject FTC Disclosure
    disclosure = (
        '<div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #0073aa; margin-bottom: 25px; font-style: italic; font-size: 0.9em;">'
        '<strong>Disclosure:</strong> As an Amazon Associate, we earn from qualifying purchases. '
        'This means if you click a link and buy something, we may receive a small commission at no extra cost to you. '
        'Our content is independent and reader-supported.'
        '</div>'
    )
    enhanced_html = disclosure + enhanced_html

    # 2. Convert CTA Placeholders to Buttons
    # Regex to find [Check Price], [View Deal], [Check Latest Price]
    # Replace with WordPress Block Button HTML
    cta_pattern = r'\[(Check Price|View Deal|Check Latest Price)\]'
    
    def replace_cta(match):
        text = match.group(1)
        # Using standard WP block button classes for compatibility
        return (
            f'<div class="wp-block-buttons">'
            f'<div class="wp-block-button">'
            f'<a class="wp-block-button__link has-background has-vivid-green-cyan-background-color has-text-color has-white-color" '
            f'style="border-radius:5px; text-decoration:none; padding:10px 20px; font-weight:bold; display:inline-block;" '
            f'href="#">{text} ➚</a>' # href="#" is placeholder, would be real link in future
            f'</div></div>'
        )
    
    enhanced_html = re.sub(cta_pattern, replace_cta, enhanced_html, flags=re.IGNORECASE)
    
    return enhanced_html

def publish_post(title, content_html, wp_url, user, password, status='draft', featured_media_id=None):
    """
    Publish post to WordPress via REST API.
    """
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # Basic Auth Header
    credentials = f"{user}:{password}"
    token = base64.b64encode(credentials.encode()).decode('utf-8')
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'title': title,
        'content': content_html,
        'status': status
    }
    
    if featured_media_id:
        data['featured_media'] = featured_media_id

    try:
        # verify=False is CRITICAL for LocalWP self-signed certs
        response = requests.post(api_url, headers=headers, json=data, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP Error: {err}")
        if response.text:
            logger.error(f"Response: {response.text}")
        sys.exit(1)
    except Exception as err:
        logger.error(f"Error publishing: {err}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Publish Markdown file to WordPress (LocalWP Compatible)")
    parser.add_argument("file", help="Path to the Markdown file")
    parser.add_argument("--url", default="http://localhost:10003", help="WordPress URL (check LocalWP for port)")
    parser.add_argument("--user", help="WordPress Username")
    parser.add_argument("--password", help="WordPress Application Password")
    parser.add_argument("--status", choices=['draft', 'publish', 'private'], default='draft', help="Post status")
    
    args = parser.parse_args()

    # Get Credentials
    user = args.user or os.getenv("WP_USER")
    password = args.password or os.getenv("WP_PASSWORD")

    if not user or not password:
        logger.error("Username and Password are required (via arguments or WP_USER/WP_PASSWORD env vars).")
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Read Content
    logger.info(f"Reading file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Extract Title and Frontmatter
    lines = md_content.splitlines()
    title = file_path.stem.replace("_", " ").title() # Default title
    body_md = md_content
    image_prompt = None

    # Robust Frontmatter Extraction
    # Look for the first line that is EXACTLY '---' (ignoring preliminary whitespace)
    start_idx = -1
    for i, line in enumerate(lines[:10]): # Only check top 10 lines
        if line.strip() == "---":
            start_idx = i
            break
            
    if start_idx != -1:
        try:
            # Find end of frontmatter
            end_idx = -1
            for i, line in enumerate(lines[start_idx+1:], start=start_idx+1):
                if line.strip() == "---":
                    end_idx = i
                    break
            
            if end_idx > start_idx:
                # Parse Frontmatter
                frontmatter_lines = lines[start_idx+1:end_idx]
                for line in frontmatter_lines:
                    if line.startswith("title:"):
                         val = line.split("title:", 1)[1].strip().replace('"', '')
                         if val: title = val
                    elif line.startswith("image_prompt:"):
                         val = line.split("image_prompt:", 1)[1].strip().replace('"', '')
                         if val: image_prompt = val
                
                # Strip Frontmatter from Body (everything after end_idx)
                body_md = "\n".join(lines[end_idx+1:]).strip()
                logger.info("Found and stripped YAML Frontmatter.")
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")

    # Fallback Title Extraction
    if not image_prompt and body_md.startswith("# "):
         # If no frontmatter title, check H1
         title_line = body_md.splitlines()[0]
         title = title_line[2:].strip()
         body_md = body_md[len(title_line):].strip()

    # Generate Schema
    logger.info("Generating SEO Schema...")
    schema_json = generate_schema(title, body_md)
    
    # Generate Feature Image
    logger.info("Generating Feature Image (Pollinations.ai)...")
    if image_prompt:
        logger.info(f"Using Custom Prompt: {image_prompt}")
        prompt = image_prompt
    else:
        logger.info("Using Default Prompt Template")
        prompt = f"photorealistic, cinematic lighting, 4k, {title}, minimalist, sleek design"
    
    image_url = generate_image_url(prompt)
    
    media_id = upload_media(image_url, title, args.url, user, password)

    # Convert
    logger.info("Converting Markdown to HTML...")
    html_content = convert_md_to_html(body_md)

    # Enhance (Affiliate Optimization)
    logger.info("Applying Affiliate Optimizations (Buttons, Disclosure, Schema)...")
    html_content = enhance_affiliate_content(html_content, schema_json=schema_json)

    # Publish
    logger.info(f"Uploading to {args.url} as {args.status} (SSL Verify Skipped)...")
    post = publish_post(title, html_content, args.url, user, password, args.status, featured_media_id=media_id)

    logger.info(f"✅ Successfully published!")
    logger.info(f"Link: {post.get('link')}")
    logger.info(f"ID: {post.get('id')}")

if __name__ == "__main__":
    main()
