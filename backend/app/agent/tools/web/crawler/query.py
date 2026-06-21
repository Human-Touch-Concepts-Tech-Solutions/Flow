import os
import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import httpx

################==============================================================
# Import ecosystem unified exception components
################==============================================================
from error.codes import ErrorClassification
from error.exceptions import ToolBaseException

class SearchApi:
    COMPONENT_ID = "TOOL_0001::query"

    def __init__(
        self, 
        query: str, 
        user_email: Optional[str] = None, 
        search_type: str = "search", 
        gl: Optional[str] = None,     
        hl: Optional[str] = None,    
        page: int = 1,                 
        num_results: int = 5,  
        tbs: Optional[str] = None,
        output_type: str = "json"  
    ):
        if not query or not query.strip():
            raise ToolBaseException(
                classification=ErrorClassification.MISSING_ARGUMENT,
                component_id=self.COMPONENT_ID,
                custom_context="Search query parameter input cannot be blank or empty strings."
            )

        self.query = query.strip()
        self.user_email = user_email
        self.search_type = search_type
        self.gl = gl
        self.hl = hl
        
        ################======================================================
        # Safeguard parameter type conversions and assignment boundaries
        ################======================================================
        try:
            self.page = max(1, int(page))
            self.num_results = max(1, int(num_results))
        except (ValueError, TypeError) as num_err:
            raise ToolBaseException(
                classification=ErrorClassification.MALFORMED_PAYLOAD,
                component_id=self.COMPONENT_ID,
                custom_context=f"Pagination settings 'page' and 'num_results' must be valid integers: {str(num_err)}"
            )
            
        self.tbs = tbs
        self.output_type = output_type.lower().strip() if output_type else "json"
        if self.output_type not in ["json", "md"]:
            self.output_type = "json"

        self.serper_api_key = os.getenv("SERPER_API_KEY")

    async def execute(self) -> Any:
        if not self.serper_api_key:
            raise ToolBaseException(
                classification=ErrorClassification.CREDENTIALS_MISSING,
                component_id=self.COMPONENT_ID,
                custom_context="SERPER_API_KEY could not be discovered inside active environment variables."
            )

        url = f"https://google.serper.dev/{self.search_type}"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }

        ################======================================================
        # Calculate pagination requirements to handle multi-page merges smoothly
        ################======================================================
        pages_needed = math.ceil(self.num_results / 10)
        payload_list = []
        
        for step in range(pages_needed):
            current_page_target = self.page + step
            page_payload: Dict[str, Any] = {
                "q": self.query,
                "page": current_page_target
            }
            if self.gl: page_payload["gl"] = self.gl
            if self.hl: page_payload["hl"] = self.hl
            if self.tbs: page_payload["tbs"] = self.tbs
            payload_list.append(page_payload)

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                final_payload = payload_list[0] if len(payload_list) == 1 else payload_list
                response = await client.post(url, headers=headers, json=final_payload)
            except httpx.TimeoutException:
                raise ToolBaseException(
                    classification=ErrorClassification.TIMEOUT_EXCEEDED,
                    component_id=self.COMPONENT_ID
                )
            except Exception as net_err:
                raise ToolBaseException(
                    classification=ErrorClassification.MALFORMED_PAYLOAD,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Underlying raw transport exception intercepted: {str(net_err)}"
                )

            if response.status_code == 403:
                raise ToolBaseException(
                    classification=ErrorClassification.PRIVILEGE_DENIED,
                    component_id=self.COMPONENT_ID,
                    custom_context="Serper transaction blocked. Verify API credit allowance limits or token accuracy."
                )
            elif response.status_code != 200:
                raise ToolBaseException(
                    classification=ErrorClassification.BAD_GATEWAY_RESPONSE,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Serper API bounced request back with server status signature: {response.status_code}"
                )
            
            try:
                raw_response_data = response.json()
            except Exception as json_err:
                raise ToolBaseException(
                    classification=ErrorClassification.MALFORMED_PAYLOAD,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Failed parsing server response as JSON payload data: {str(json_err)}"
                )
                
            unified_raw_data = self._merge_batch_payloads(raw_response_data)
            formatted_output = self._formatter(unified_raw_data)
            
            ################======================================================
            # Execute usage metrics invoicing generation trace if email tracking is active
            ################======================================================
            if self.user_email:
                try:
                    self._generate_invoice(formatted_output=formatted_output, pages_billed=pages_needed)
                except Exception as inv_err:
                    raise ToolBaseException(
                        classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                        component_id=self.COMPONENT_ID,
                        custom_context=f"Critical logging metrics failure writing invoice ledger context: {str(inv_err)}"
                    )
                
            return formatted_output

    def _merge_batch_payloads(self, raw_data: Any) -> Dict[str, Any]:
        try:
            if not raw_data:
                return {}

            if isinstance(raw_data, dict):
                if "organic" in raw_data:
                    raw_data["organic"] = raw_data["organic"][:self.num_results]
                return raw_data

            if not isinstance(raw_data, list) or len(raw_data) == 0:
                return {}

            unified_base = raw_data[0]
            aggregated_organic: List[Dict[str, Any]] = []

            for page_data in raw_data:
                if isinstance(page_data, dict) and "organic" in page_data:
                    aggregated_organic.extend(page_data["organic"])

            for position_index, item in enumerate(aggregated_organic, start=1):
                item["position"] = position_index

            unified_base["organic"] = aggregated_organic[:self.num_results]
            return unified_base
            
        except Exception as merge_err:
            raise ToolBaseException(
                classification=ErrorClassification.MALFORMED_PAYLOAD,
                component_id=self.COMPONENT_ID,
                custom_context=f"Array processing validation fault uniting pagination frames: {str(merge_err)}"
            )

    def _formatter(self, raw_data: Dict[str, Any]) -> Any:
        try:
            urls = [item.get("link") for item in raw_data.get("organic", []) if "link" in item]
            
            structured_data = {
                "status": "success",
                "search_metadata": {
                    "query": self.query,
                    "search_type": self.search_type,
                    "base_start_page": self.page,
                    "total_returned": len(urls),
                    "requested_limit": self.num_results
                },
                "extracted_links": urls,
                "direct_answer": raw_data.get("answerBox"),
                "knowledge_summary": raw_data.get("knowledgeGraph"),
                "search_results": [
                    {
                        "position": item.get("position"),
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet")
                    } for item in raw_data.get("organic", [])
                ],
                "people_also_ask": [item.get("question") for item in raw_data.get("peopleAlsoAsk", [])],
                "suggested_searches": [item.get("query") for item in raw_data.get("relatedSearches", [])]
            }

            ################======================================================
            # FIX: If mode is 'json', return the dynamic Python Dictionary interface 
            # directly so crawl.py can process 'extracted_links' natively without strings exceptions.
            ################======================================================
            if self.output_type == "json":
                return structured_data
            elif self.output_type == "md":
                return self._to_markdown(structured_data)

        except Exception as format_err:
            raise ToolBaseException(
                classification=ErrorClassification.MALFORMED_PAYLOAD,
                component_id=self.COMPONENT_ID,
                custom_context=f"Formatting layer structural failure processing response: {str(format_err)}"
            )

    def _to_markdown(self, data: Dict[str, Any]) -> str:
        meta = data["search_metadata"]
        md = []
        md.append(f"# 🔍 Web Search Report: `{meta['query']}`")
        md.append(f"*Type: {meta['search_type'].upper()} | Requested Limit: {meta['requested_limit']} | Total Aggregated Results: {meta['total_returned']}*\n")
        md.append("---")

        if data["direct_answer"]:
            ans = data["direct_answer"]
            md.append("\n## 💡 Direct Answer Box")
            md.append(f"> **{ans.get('snippet')}**")
            if ans.get('link'):
                md.append(f"> \n> *Source: [{ans.get('title')}]({ans.get('link')})*")
            md.append("\n---")

        if data["knowledge_summary"]:
            kg = data["knowledge_summary"]
            md.append(f"\n## 🧠 Knowledge Card: {kg.get('title', 'Entity Info')}")
            if kg.get('type'):
                md.append(f"**Classification:** {kg.get('type')}\n")
            if kg.get('description'):
                md.append(f"*{kg.get('description')}* (Source: [{kg.get('descriptionSource')}]({kg.get('descriptionLink')}))\n")
            
            if kg.get("attributes"):
                md.append("### Core Facts:")
                for attr, val in kg["attributes"].items():
                    md.append(f"* **{attr}:** {val}")
            md.append("\n---")

        md.append("\n## 🌐 Web Search Results")
        if not data["search_results"]:
            md.append("*No organic web listings returned for this specific search slice.*")
        else:
            for item in data["search_results"]:
                md.append(f"### {item['position']}. {item['title']}")
                md.append(f"🔗 **Link:** [{item['url']}]({item['url']})")
                md.append(f"📝 **Preview:** {item['snippet']}\n")

        if data["people_also_ask"]:
            md.append("\n---\n## ❓ People Also Ask")
            for question in data["people_also_ask"]:
                md.append(f"* {question}")

        if data["suggested_searches"]:
            md.append("\n---\n## 🔍 Related Queries")
            md.append(", ".join([f"`{q}`" for q in data["suggested_searches"]]))

        return "\n".join(md)

    def _generate_invoice(self, formatted_output: Any, pages_billed: int) -> None:
        ################======================================================
        # Safely extract processing length boundary traits if payload is standard dictionary
        ################======================================================
        if isinstance(formatted_output, dict):
            payload_len = len(json.dumps(formatted_output, ensure_ascii=False))
        else:
            payload_len = len(str(formatted_output))

        invoice = {
            "type": "invoice",
            "user_id": self.user_email,
            "tool_id": self.COMPONENT_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "third-party": pages_billed,
                "output_text": payload_len
            }
        }
        print(json.dumps(invoice, indent=4, ensure_ascii=False))