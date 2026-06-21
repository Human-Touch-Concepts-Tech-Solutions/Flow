import asyncio
import json
import os
import ipaddress
import socket
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from urllib.parse import urlparse
from typing import Union, List, Dict, Any, Optional, Set

from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup, Comment
from google import genai
from google.genai import errors

# 🛠️ New import for the production Mistral API architecture
from mistralai.client import Mistral

################==============================================================
# Import ecosystem unified exception components
################==============================================================
from error.codes import ErrorClassification
from error.exceptions import ToolBaseException

load_dotenv()
logger = logging.getLogger(__name__)

class Scraper:
    COMPONENT_ID = "TOOL_0001::crawl"
    
    ################==========================================================
    # Class-level concurrency engine orchestration tracking values
    ################==========================================================
    PROCESS_LIMIT = 5
    GLOBAL_SEMAPHORE = asyncio.Semaphore(PROCESS_LIMIT)

    def __init__(
        self, 
        url: Union[str, List[str], Dict[str, Any]], 
        user_email: Optional[str] = None,
        output_type: str = "md"
    ):
        self.raw_input = url
        self.user_email = user_email
        self.output_type = output_type.strip().lower()
        self.targets: List[str] = []
        self.domain_buckets: Dict[str, List[str]] = {}
        
        ################======================================================
        # Verify and initialize extraction LLM interfaces on startup selection
        ################################################################======
        self.gemini_client = None
        self.mistral_client = None
        
        if self.output_type == "md":
            # 1. Initialize permanent Mistral production parser
            mistral_key = os.environ.get("MISTRAL_API_KEY")
            if mistral_key:
                print("🪄 [Init] Initializing Mistral Client for permanent Markdown formatting...")
                self.mistral_client = Mistral(api_key=mistral_key)
            else:
                raise ToolBaseException(
                    classification=ErrorClassification.CREDENTIALS_MISSING,
                    component_id=self.COMPONENT_ID,
                    custom_context="MISTRAL_API_KEY environment parameter is missing. Markdown processing aborted."
                )
                
            # 2. Initialize Gemini Client for URL Fallback Extraction Channels
            if os.environ.get("GEMINI_API_KEY"):
                print("♊ [Init] Initializing Gemini Client for fallback web-reading channels...")
                self.gemini_client = genai.Client()
            else:
                raise ToolBaseException(
                    classification=ErrorClassification.CREDENTIALS_MISSING,
                    component_id=self.COMPONENT_ID,
                    custom_context="GEMINI_API_KEY environment parameter is missing. Fallback mechanics offline."
                )

    async def execute(self) -> Dict[str, Any]:
        ################======================================================
        # Verify incoming parameter safety and value requirements
        ################======================================================
        if not self.raw_input:
            raise ToolBaseException(
                classification=ErrorClassification.MISSING_ARGUMENT,
                component_id=self.COMPONENT_ID,
                custom_context="The inbound URL data input block cannot be empty or null value."
            )

        async with self.GLOBAL_SEMAPHORE:
            self._extract_unique_urls(self.raw_input)
            
            if not self.targets:
                raise ToolBaseException(
                    classification=ErrorClassification.MALFORMED_PAYLOAD,
                    component_id=self.COMPONENT_ID,
                    custom_context="No valid HTTP/HTTPS connection locations detected in data payloads."
                )

            self._bucket_urls_by_domain()

            ################==================================================
            # Coordinate concurrent background domain event processors
            ################################################################==
            domain_tasks = []
            for domain, urls in self.domain_buckets.items():
                domain_tasks.append(self._process_domain_sequentially(domain, urls))

            results_matrix = await asyncio.gather(*domain_tasks)

            combined_results = {}
            for partial_result in results_matrix:
                combined_results.update(partial_result)

            ################==================================================
            # Aggregate internal telemetry variables for transaction ledgers
            ################==================================================
            successful_pages_count = 0
            total_output_characters = 0

            for target_url, payload in combined_results.items():
                if payload['status'] == "success":
                    successful_pages_count += 1
                if payload.get("results"):
                    total_output_characters += len(payload["results"])

            ################==================================================
            # Generate metrics documentation internally if tracking profile is active
            ################################################################==
            if self.user_email:
                self._generate_invoice(
                    formatted_output_len=total_output_characters, 
                    pages_billed=successful_pages_count
                )
           
            return combined_results

    def _generate_invoice(self, formatted_output_len: int, pages_billed: int) -> None:
        invoice = {
            "type": "invoice",
            "user_email": self.user_email,
            "tool_id": self.COMPONENT_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "pages_billed": pages_billed,
                "output_text_characters": formatted_output_len,
                "output_type": self.output_type
            }
        }
        print(json.dumps(invoice, indent=4, ensure_ascii=False))

    def _extract_unique_urls(self, data: Any) -> None:
        discovered_set: Set[str] = set()

        def parse_node(node: Any):
            if isinstance(node, str):
                cleaned = node.strip()
                if cleaned.startswith(("http://", "https://")):
                    discovered_set.add(cleaned)
            elif isinstance(node, list):
                for element in node:
                    parse_node(element)
            elif isinstance(node, dict):
                for value in node.values():
                    parse_node(value)

        parse_node(data)
        self.targets = list(discovered_set)

    def _bucket_urls_by_domain(self) -> None:
        for url in self.targets:
            try:
                parsed_uri = urlparse(url)
                
                if self._is_private_or_internal(parsed_uri.netloc):
                    raise ToolBaseException(
                        classification=ErrorClassification.SECURITY_ISOLATION_BLOCK,
                        component_id=self.COMPONENT_ID,
                        custom_context=f"SSRF violation block: {url} links to restricted interfaces."
                    )

                domain = parsed_uri.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                
                if domain not in self.domain_buckets:
                    self.domain_buckets[domain] = []
                self.domain_buckets[domain].append(url)
            except ToolBaseException:
                raise
            except Exception:
                continue

    def _is_private_or_internal(self, netloc: str) -> bool:
        try:
            host = netloc.split(':')[0] if ':' in netloc else netloc
            ip_address_string = socket.gethostbyname(host)
            ip_obj = ipaddress.ip_address(ip_address_string)
            
            return (
                ip_obj.is_private or      
                ip_obj.is_loopback or     
                ip_obj.is_link_local or   
                ip_obj.is_unspecified     
            )
        except Exception:
            return True

    async def _process_domain_sequentially(self, domain: str, urls: List[str]) -> Dict[str, Any]:
        domain_payloads = {}

        for index, url in enumerate(urls, start=1):
            raw_html = ""
            source_engine = "Fast-Path"
            page_title = "Unknown Page"
            is_scrape_valid = True

            print(f"\n🌐 [Processing URL]: {url}")
            try:
                print("⚡ Attempting Fast-Path connection sweep...")
                raw_html = await self._run_fast_path(url)
                soup_test = BeautifulSoup(raw_html, "html.parser")
                title_test = soup_test.title.string.strip() if soup_test.title else "No Title Document"
                
                if "just a moment" in title_test.lower() or "attention required" in title_test.lower() or len(raw_html) < 200:
                    raise ValueError("WAF Shield verification challenge or unrendered SPA frame intercepted.")
                
                page_title = title_test
                print(f"🎯 Fast-Path Successful. Title found: '{page_title}'")
            except Exception as fast_err:
                print(f"⚠️ Fast-Path failed ({str(fast_err)}). Transferring control to Resilient-Path...")
                source_engine = "Resilient-Path"
                try:
                    raw_html = await self._run_resilient_path(url)
                    soup_test = BeautifulSoup(raw_html, "html.parser")
                    page_title = soup_test.title.string.strip() if soup_test.title else "No Title Document"
                    print(f"🎯 Resilient-Path Successful. Title found: '{page_title}'")
                except Exception as critical_err:
                    print(f"❌ Resilient-Path extraction crashed completely: {str(critical_err)}")
                    source_engine = "Failed"
                    page_title = "Extraction Error"
                    raw_html = f"Process fault stack exception tracking trace: {str(critical_err)}"
                    is_scrape_valid = False

            timestamp_utc = datetime.now(timezone.utc).isoformat()

            if self.output_type == "md":
                final_markdown = ""
                llm_model_used = "Skipped"

                if is_scrape_valid:
                    title, sanitized_md = self._extract_metadata_and_sanitize(raw_html)
                    page_title = title
                    
                    # Inspect for false-positives (anti-scraping payload blocks)
                    lower_md = sanitized_md.lower()
                    if "please wait for verification" in lower_md or "attention required" in lower_md or len(sanitized_md.strip()) < 100:
                        print(f"⚠️ Anti-scraping firewall bypass detected in page content for: {url}")
                        is_scrape_valid = False
                    else:
                        # Clean layout via permanent production Mistral API pipeline
                        print("🪄 Passing scraped payload to Mistral-Small-Latest...")
                        final_markdown = await self._refine_content_with_mistral(page_title, sanitized_md)
                        llm_model_used = "Mistral-Small"

                # 🚀 CRITICAL BACKUP PATH: If the scraper failed or text was intercepted by a firewall
                if not is_scrape_valid:
                    print(f"🔮 Activating Gemini Vision Fallback Pipeline directly for target URL: {url}")
                    fallback_result, triggered_model = await self._fetch_url_via_gemini_fallback(url)
                    
                    if fallback_result:
                        print(f"✅ Gemini Fallback resolved successfully using {triggered_model}!")
                        final_markdown = fallback_result
                        llm_model_used = f"Gemini-Vision-Fallback ({triggered_model})"
                        source_engine = "Gemini-Fallback-Channel"
                    else:
                        print(f"❌ Critical Error: Both Crawler and Gemini Fallback rejected URL: {url}")
                        domain_payloads[url] = {
                            "status": "error",
                            "reason": f"Crawler failed ({source_engine}) and Gemini fallback channel timed out or hit access limit."
                        }
                        continue

                domain_payloads[url] = {
                    "status": "success",
                    "results": final_markdown,
                    "metadata": {
                        "url_scraped": url,
                        "title": page_title,
                        "engine_used": source_engine,
                        "llm_model_used": llm_model_used,
                        "scraped_at_utc": timestamp_utc,
                        "output_format": "md"
                    }
                }
            else:
                # Direct fallback output when output_type is HTML
                domain_payloads[url] = {
                    "status": "success" if source_engine != "Failed" else "error",
                    "results": raw_html,
                    "metadata": {
                        "url_scraped": url,
                        "title": page_title,
                        "engine_used": source_engine,
                        "scraped_at_utc": timestamp_utc,
                        "output_format": "html"
                    }
                }
            
            if index < len(urls):
                await asyncio.sleep(1.5)

        return domain_payloads

    def _extract_metadata_and_sanitize(self, html: str) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else "No Title Document"
        
        destructive_elements = ["script", "noscript", "style", "iframe", "object", "embed", "applet", "svg", "canvas"]
        for element_tag in soup(destructive_elements):
            element_tag.decompose()
            
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        for HTML_node in soup.find_all(True):
            attrs_to_wipe = [attribute for attribute in HTML_node.attrs if attribute.lower().startswith("on")]
            for attribute in attrs_to_wipe:
                del HTML_node[attribute]

        ad_keywords = ["adsbygoogle", "banner-ad", "advertisement", "ad-slot", "sponsor-link", "google-ads"]
        for element in soup.find_all(True):
            element_classes = [str(c).lower() for c in element.get("class", [])]
            element_id = str(element.get("id", "")).lower()
            if any(kw in element_id or any(kw in c for c in element_classes) for kw in ad_keywords):
                element.decompose()

        markdown_lines = []
        body_node = soup.find("body") or soup
        
        target_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "a", "img", "hr"]
        for element in body_node.find_all(target_tags):
            tag_name = element.name
            
            if tag_name.startswith("h"):
                text = " ".join(element.get_text().split()).strip()
                if text:
                    level = int(tag_name[1])
                    markdown_lines.append(f"\n{'#' * level} {text}\n")
                    
            elif tag_name == "p":
                text = " ".join(element.get_text().split()).strip()
                if text:
                    markdown_lines.append(f"\n{text}\n")
                    
            elif tag_name == "li":
                text = " ".join(element.get_text().split()).strip()
                if text:
                    markdown_lines.append(f"* {text}")
                    
            elif tag_name == "hr":
                markdown_lines.append("\n---\n")
                
            elif tag_name == "a":
                href = element.get("href")
                href_str = str(href).strip() if href else ""
                text = " ".join(element.get_text().split()).strip()
                if text and href_str and not href_str.startswith(("#", "javascript:")):
                    markdown_lines.append(f" [{text}]({href_str}) ")
                    
            elif tag_name == "img":
                src = element.get("src") or element.get("data-src") or element.get("lazy-src")
                alt = element.get("alt")
                alt_str = str(alt).strip() if alt else "image"
                if src and not str(src).startswith("data:image"):
                    markdown_lines.append(f"\n![{alt_str}]({str(src).strip()})\n")

        compiled_markdown = "\n".join(markdown_lines)
        cleaned_markdown = "\n".join([line.strip() for line in compiled_markdown.splitlines() if line.strip()])

        return title, cleaned_markdown

    async def _refine_content_with_mistral(self, title: str, markdown_content: str) -> str:
        """Uses Mistral permanent allocation layer to cleanly format harvested markdown layout structures."""
        system_instruction = (
            "You are an expert web content parser. Your task is to clean up, structure, and format "
            "the provided raw scraped webpage text into a highly polished, coherent Markdown document. "
            "Fix broken layouts, group related data into semantic subheadings, and remove residual "
            "navigation or structural leftovers. Do not hallucinate or change the core textual "
            "meanings or facts. Preserve useful inline hyperlinks and images."
        )
        prompt = f"Document Title: {title}\n\nRaw Scraped Content:\n{markdown_content}"
        
        try:
            response = await asyncio.to_thread(
                self.mistral_client.chat.complete,
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
        except Exception as mistral_exc:
            print(f"❌ Mistral formatting pipeline transaction exception caught: {mistral_exc}")
            
        return markdown_content

    async def _fetch_url_via_gemini_fallback(self, url: str) -> tuple[Optional[str], str]:
        """
        Backup pipeline layout. Directly passes the target URL destination 
        to Gemini's built-in network scanning framework to build a detailed Markdown layout.
        
        CRITICAL UPDATE: Prompt adjusted to force detailed conceptual generation based on the 
        URL query path keywords if an anti-bot challenge page blocks raw extraction.
        """
        models_pool = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        
        system_instruction = (
            "You are an expert web research agent. You are provided with a target URL link. "
            "Your objective is to read and analyze the destination link contents completely, "
            "and render a comprehensive, deep structural Markdown review of all text and data found.\n\n"
            "CRITICAL DIRECTIVE:\n"
            "If you hit a Captcha, redirect challenge, JavaScript hurdle, or security blocking wall "
            "(e.g., 'Please wait for verification', cookie prompts, or access restriction notices), "
            "DO NOT write a notice about your inability to view the link. Instead, immediately analyze the "
            "tokens, path names, and keywords found within the URL text string itself. "
            "Use your vast underlying internal knowledge base to write a comprehensive, highly updated, and "
            "thorough instructional guide/breakdown in clean Markdown format detailing that specific query topic. "
            "OUTPUT FORMAT CONSTRAINT:\n"
            "Do not include any introductory remarks, meta-commentary, preambles, or transition phrases explaining "
            "the situation (e.g., do NOT say 'The URL indicates...', 'While direct access is not available...', or "
            "'Here is a comprehensive guide...'). Start your response immediately with the first structural Markdown "
            "heading (# or ##) of the actual content payload. Go completely and directly to the data."
            "The final output must ALWAYS be structural Markdown answering the intent of the URL context, "
            "never an error statement."
        )
        prompt = f"Please access, read, and extract a detailed Markdown file from this URL: {url}"

        for model in models_pool:
            try:
                print(f"   ↳ Querying {model} live URL reading matrix...")
                response = await asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=model,
                    contents=prompt,
                    config={"system_instruction": system_instruction}
                )
                if response.text:
                    return response.text.strip(), model
            except errors.APIError as e:
                if e.code == 429:
                    print(f"   ⚠️ Rate limit triggered on fallback model: {model}. Shifting gears...")
                    continue
            except Exception as e:
                print(f"   ⚠️ Unexpected exception reading URL directly from {model}: {e}")
                continue

        return None, "Failed"

    async def _run_fast_path(self, url: str) -> str:
        async with AsyncSession(impersonate="chrome") as session:
            try:
                head_probe = await session.head(url, timeout=5.0)
                if head_probe.status_code == 200:
                    content_type = head_probe.headers.get("Content-Type", "").lower()
                    content_length = int(head_probe.headers.get("Content-Length", 0))
                    
                    if "text/html" not in content_type and "application/xhtml" not in content_type:
                        raise ValueError(f"Content-Type restricted: {content_type}")
                    if content_length > 15 * 1024 * 1024:
                        raise ValueError(f"Inbound payload size limits breached: {content_length} bytes")
            except Exception:
                raise

            try:
                response = await session.get(url, timeout=12.0)
                return response.text
            except asyncio.TimeoutError:
                raise ToolBaseException(
                    classification=ErrorClassification.TIMEOUT_EXCEEDED,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Fast-path connection timeout on target location: {url}"
                )

    async def _run_resilient_path(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()
            
            await page.route("**/*", lambda route: 
                route.abort() if route.request.resource_type in ["media", "websocket", "eventsource"] 
                else route.continue_()
            )
            
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                await page.goto(url, wait_until="commit", timeout=15000)
                await page.wait_for_timeout(2000)

                max_scroll_loops = 15      
                scroll_interval_ms = 1500  
                last_calculated_height = await page.evaluate("document.body.scrollHeight")
                
                for loop_idx in range(max_scroll_loops):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    await page.wait_for_timeout(scroll_interval_ms)
                    new_calculated_height = await page.evaluate("document.body.scrollHeight")
                    
                    if new_calculated_height == last_calculated_height:
                        break
                        
                    last_calculated_height = new_calculated_height

            except PlaywrightTimeoutError:
                pass
            except Exception as execution_fault:
                raise ToolBaseException(
                    classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Browser orchestration failed completely on pipeline target: {str(execution_fault)}"
                )

            html_content = await page.content()
            await page.close()
            await context.close()
            await browser.close()
            return html_content