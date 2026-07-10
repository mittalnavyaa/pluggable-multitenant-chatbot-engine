"""Structural Markdown parser to extract text blocks and map section headings."""

import re
import logging
from chunking.chunk_models import MarkdownElement

logger = logging.getLogger("markdown_parser")

class MarkdownParser:
    """Parses raw Markdown strings into structural elements containing parent heading contexts."""

    def parse(self, markdown_text: str) -> list[MarkdownElement]:
        """Splits Markdown text into blocks, preserving hierarchy mapping (H1/H2/H3)."""
        if not markdown_text or not markdown_text.strip():
            logger.warning("Empty markdown text provided to parser.")
            return []

        lines = markdown_text.splitlines()
        elements = []
        
        current_h1 = None
        current_h2 = None
        current_h3 = None
        
        in_code_block = False
        code_block_lines = []
        
        in_table = False
        table_lines = []
        
        in_list = False
        list_lines = []
        
        in_blockquote = False
        blockquote_lines = []
        
        paragraph_lines = []
        
        current_page_number = 1
        elem_page_start = 1
        
        def flush_all():
            nonlocal in_table, in_list, in_blockquote, elem_page_start
            if code_block_lines:
                elements.append(MarkdownElement(
                    type="code_block",
                    text="\n".join(code_block_lines),
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=elem_page_start,
                    page_end=current_page_number
                ))
                code_block_lines.clear()
            if table_lines:
                elements.append(MarkdownElement(
                    type="table",
                    text="\n".join(table_lines),
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=elem_page_start,
                    page_end=current_page_number
                ))
                table_lines.clear()
                in_table = False
            if list_lines:
                elements.append(MarkdownElement(
                    type="list",
                    text="\n".join(list_lines),
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=elem_page_start,
                    page_end=current_page_number
                ))
                list_lines.clear()
                in_list = False
            if blockquote_lines:
                elements.append(MarkdownElement(
                    type="blockquote",
                    text="\n".join(blockquote_lines),
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=elem_page_start,
                    page_end=current_page_number
                ))
                blockquote_lines.clear()
                in_blockquote = False
            if paragraph_lines:
                elements.append(MarkdownElement(
                    type="paragraph",
                    text="\n".join(paragraph_lines),
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=elem_page_start,
                    page_end=current_page_number
                ))
                paragraph_lines.clear()
            elem_page_start = current_page_number

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 0. Page boundary comments
            page_match = re.match(r"^<!--\s*PAGE_NUMBER:\s*(\d+)\s*-->$", stripped)
            if page_match:
                current_page_number = int(page_match.group(1))
                i += 1
                continue
            
            # 1. Code blocks
            if stripped.startswith("```"):
                if in_code_block:
                    code_block_lines.append(line)
                    in_code_block = False
                    elements.append(MarkdownElement(
                        type="code_block",
                        text="\n".join(code_block_lines),
                        h1=current_h1,
                        h2=current_h2,
                        h3=current_h3,
                        page_start=elem_page_start,
                        page_end=current_page_number
                    ))
                    code_block_lines.clear()
                    elem_page_start = current_page_number
                else:
                    flush_all()
                    in_code_block = True
                    code_block_lines.append(line)
                i += 1
                continue
                
            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue
                
            # 2. Headings
            h1_match = re.match(r"^#\s+(.*)$", stripped)
            h2_match = re.match(r"^##\s+(.*)$", stripped)
            h3_match = re.match(r"^###\s+(.*)$", stripped)
            
            if h1_match:
                flush_all()
                current_h1 = h1_match.group(1).strip()
                current_h2 = None
                current_h3 = None
                elements.append(MarkdownElement(
                    type="heading_1",
                    text=line,
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=current_page_number,
                    page_end=current_page_number
                ))
                elem_page_start = current_page_number
                i += 1
                continue
            elif h2_match:
                flush_all()
                current_h2 = h2_match.group(1).strip()
                current_h3 = None
                elements.append(MarkdownElement(
                    type="heading_2",
                    text=line,
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=current_page_number,
                    page_end=current_page_number
                ))
                elem_page_start = current_page_number
                i += 1
                continue
            elif h3_match:
                flush_all()
                current_h3 = h3_match.group(1).strip()
                elements.append(MarkdownElement(
                    type="heading_3",
                    text=line,
                    h1=current_h1,
                    h2=current_h2,
                    h3=current_h3,
                    page_start=current_page_number,
                    page_end=current_page_number
                ))
                elem_page_start = current_page_number
                i += 1
                continue
                
            # 3. Empty lines
            if not stripped:
                flush_all()
                i += 1
                continue
                
            # 4. Tables
            is_table_line = (
                stripped.startswith("|") or 
                stripped.endswith("|") or 
                ("|" in stripped and re.match(r"^[-|:\s]+$", stripped))
            )
            if is_table_line:
                if not in_table:
                    flush_all()
                    in_table = True
                table_lines.append(line)
                i += 1
                continue
            elif in_table:
                flush_all()
                
            # 5. Lists
            is_list_line = (
                re.match(r"^([\s\t]*)([-*+>]|\d+\.)\s+(.*)$", line) is not None and 
                not stripped.startswith(">")
            )
            if is_list_line:
                if not in_list:
                    flush_all()
                    in_list = True
                list_lines.append(line)
                i += 1
                continue
            elif in_list:
                if line.startswith(" ") or line.startswith("\t"):
                    list_lines.append(line)
                    i += 1
                    continue
                else:
                    flush_all()
                    
            # 6. Blockquotes
            is_blockquote_line = stripped.startswith(">")
            if is_blockquote_line:
                if not in_blockquote:
                    flush_all()
                    in_blockquote = True
                blockquote_lines.append(line)
                i += 1
                continue
            elif in_blockquote:
                flush_all()
                
            # 7. Paragraph continuation
            paragraph_lines.append(line)
            i += 1
            
        flush_all()
        return elements
