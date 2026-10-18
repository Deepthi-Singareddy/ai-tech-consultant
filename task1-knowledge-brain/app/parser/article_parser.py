import re
import hashlib
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from app.schemas.models import ImageReference

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()

class ArticleParser:
    """
    Extracts structured knowledge from Brilliant Directories Solution Center HTML pages.
    Preserves section hierarchy, procedural lists, tables, and image/screenshot context.
    """

    @staticmethod
    def parse_html(html_content: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Title Extraction
        title_elem = soup.find('h1', class_='post-title') or soup.find('h1') or soup.title
        title = title_elem.get_text(strip=True) if title_elem else "Untitled Article"
        # Clean title encoding artifacts and extra whitespace
        title = re.sub(r'[\ufffd\x00-\x1f]+', '-', title)
        title = re.sub(r'\s+', ' ', title).strip()

        # 2. Category / Breadcrumb Extraction
        breadcrumbs = []
        bc_elem = soup.find('ul', class_='breadcrumb') or soup.find('div', class_='breadcrumbs')
        if bc_elem:
            breadcrumbs = [li.get_text(strip=True) for li in bc_elem.find_all(['li', 'a']) if li.get_text(strip=True)]
        category = " > ".join(breadcrumbs[1:-1]) if len(breadcrumbs) > 2 else "General"
        if not category or category == "":
            category = "General Knowledge"

        # 3. Target Article Body
        article_body = (
            soup.find('div', class_='article-body') or
            soup.find('div', class_='article-content') or
            soup.find('article') or
            soup.find('div', class_='content')
        )

        if not article_body:
            # Fallback to entire body if container not found
            article_body = soup.find('body') or soup

        # 4. Extract Images & Screenshots with Adjacent Context
        images: List[Dict[str, Any]] = []
        img_tags = article_body.find_all('img')
        for idx, img in enumerate(img_tags):
            src = img.get('src') or img.get('data-src') or ""
            if not src or 'avatar' in src.lower() or 'logo' in src.lower() and 'brilliantdirectories' in src.lower():
                continue
            
            alt = img.get('alt') or ""
            
            # Find surrounding text (previous paragraph or next paragraph)
            surrounding = []
            prev_p = img.find_previous(['p', 'h2', 'h3', 'li'])
            if prev_p:
                surrounding.append(prev_p.get_text(strip=True))
            next_p = img.find_next(['p', 'li'])
            if next_p:
                surrounding.append(next_p.get_text(strip=True))
            
            section_context = " ".join(surrounding[:2])
            
            # Synthesize screenshot visual description from alt and surrounding procedural text
            visual_desc = (
                f"Screenshot illustration for: '{section_context[:180]}'. "
                f"Visual interface elements depicting settings controls, form inputs, and configuration options."
            )

            images.append({
                "url": src,
                "alt_text": alt,
                "caption": alt if alt else f"Screenshot {idx+1} from {title}",
                "section_context": section_context[:300],
                "visual_description": visual_desc
            })

        # 5. Extract Text Sections by Heading
        sections: List[Dict[str, Any]] = []
        current_heading = "Overview"
        current_paragraphs: List[str] = []

        # Iterate over child elements
        for elem in article_body.descendants:
            if elem.name in ['h2', 'h3', 'h4']:
                h_text = elem.get_text(strip=True)
                if h_text and h_text != "Related Articles":
                    if current_paragraphs:
                        body_text = "\n".join(current_paragraphs).strip()
                        if len(body_text) > 20:
                            sections.append({
                                "heading": current_heading,
                                "content": body_text
                            })
                    current_heading = h_text
                    current_paragraphs = []
            elif elem.name in ['p', 'li', 'pre', 'code'] and elem.parent.name not in ['pre', 'code']:
                t = elem.get_text(strip=True)
                if t and t not in current_paragraphs and len(t) > 5:
                    current_paragraphs.append(t)

        # Flush final section
        if current_paragraphs:
            body_text = "\n".join(current_paragraphs).strip()
            if len(body_text) > 20:
                sections.append({
                    "heading": current_heading,
                    "content": body_text
                })

        # Full body clean text
        full_text = f"{title}\nCategory: {category}\n\n"
        for s in sections:
            full_text += f"## {s['heading']}\n{s['content']}\n\n"

        # If sections was empty, extract plain text directly
        if not sections:
            plain = article_body.get_text(separator="\n", strip=True)
            full_text = f"{title}\n\n{plain}"
            sections.append({"heading": "Content", "content": plain})

        # Article ID from URL
        match = re.search(r'/articles/(\d+)', url)
        article_id = match.group(1) if match else compute_hash(url)[:12]

        return {
            "article_id": article_id,
            "url": url,
            "title": title,
            "category": category,
            "sections": sections,
            "images": images,
            "full_text": full_text.strip(),
            "content_hash": compute_hash(full_text)
        }
