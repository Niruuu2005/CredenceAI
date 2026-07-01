"""
Agent Output Parser for CredenceAI Iteration 0.4

Parses and validates LLM responses into structured agent outputs.
Handles JSON schema validation, malformed outputs, and fallback parsing.
"""

import json
import re
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ParsingError(Exception):
    """Raised when output parsing fails."""
    pass


class AgentOutputParser:
    """
    Parser for converting raw LLM outputs into structured agent responses.
    
    Features:
    - JSON schema validation using Pydantic models
    - Extraction of JSON from markdown code blocks
    - Fallback parsing for malformed outputs
    - Field validation and type coercion
    """
    
    @staticmethod
    def parse_json(raw_output: str, schema: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
        """
        Parse JSON from LLM output and optionally validate against schema.
        
        Args:
            raw_output: Raw text output from LLM
            schema: Optional Pydantic model for validation
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ParsingError: If JSON cannot be parsed or validated
        """
        try:
            # Try to extract JSON from the response
            json_str = AgentOutputParser._extract_json(raw_output)
            
            if not json_str:
                raise ParsingError("No JSON found in LLM output")
            
            # Parse JSON
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                repaired = AgentOutputParser._repair_json(json_str)
                if repaired != json_str:
                    logger.warning("JSON repair attempted after decode error: %s", e)
                    parsed_data = json.loads(repaired)
                else:
                    raise
            
            # Validate against schema if provided
            if schema:
                try:
                    validated = schema(**parsed_data)
                    return validated.model_dump()
                except ValidationError as e:
                    logger.error(f"Schema validation failed: {e}")
                    raise ParsingError(f"Invalid schema: {e}")
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ParsingError(f"Invalid JSON: {e}")
    
    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """
        Extract JSON from text, handling markdown code blocks.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON string or None
        """
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Case 1: JSON in markdown code block
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(code_block_pattern, text)
        if matches:
            return matches[0].strip()
        
        # Case 2: Direct JSON object/array
        # Look for { ... } or [ ... ]
        if text.startswith('{') or text.startswith('['):
            # Find matching closing bracket
            stack = []
            end_idx = -1
            for i, char in enumerate(text):
                if char in '{[':
                    stack.append(char)
                elif char in '}]':
                    if stack:
                        stack.pop()
                    if not stack:
                        end_idx = i + 1
                        break
            
            if end_idx > 0:
                return text[:end_idx]
        
        # Case 3: JSON embedded in text (look for first { or [)
        json_start = min(
            text.find('{') if text.find('{') != -1 else len(text),
            text.find('[') if text.find('[') != -1 else len(text)
        )
        
        if json_start < len(text):
            return AgentOutputParser._extract_json(text[json_start:])
        
        return None

    @staticmethod
    def _repair_json(text: str) -> str:
        """
        Best-effort repair of common LLM JSON mistakes before giving up.
        Handles trailing commas, Python literals, and single-quoted keys/strings.
        """
        repaired = text.strip()

        # Trailing commas before } or ]
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

        # Python booleans / None -> JSON
        repaired = re.sub(r"\bTrue\b", "true", repaired)
        repaired = re.sub(r"\bFalse\b", "false", repaired)
        repaired = re.sub(r"\bNone\b", "null", repaired)

        # Single-quoted keys: 'key': -> "key":
        repaired = re.sub(
            r"(?P<q>')(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P=q)\s*:",
            r'"\g<key>":',
            repaired,
        )

        # Single-quoted string values (simple cases): : 'value' -> : "value"
        repaired = re.sub(
            r":\s*'((?:\\'|[^'])*)'",
            lambda m: ': "' + m.group(1).replace('"', '\\"') + '"',
            repaired,
        )

        return repaired
    
    @staticmethod
    def parse_decision(raw_output: str) -> Dict[str, Any]:
        """
        Parse agent decision from LLM output.
        
        Expected format:
        {
            "decision": "approve|reject|review",
            "reasoning": "explanation",
            "confidence": 0.0-1.0,
            "factors": ["factor1", "factor2"]
        }
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Parsed decision dictionary
        """
        try:
            data = AgentOutputParser.parse_json(raw_output)
            
            # Validate required fields
            if "decision" not in data:
                raise ParsingError("Missing required field: decision")
            
            if "reasoning" not in data:
                data["reasoning"] = "No reasoning provided"
            
            if "confidence" not in data:
                data["confidence"] = 0.5  # Default moderate confidence
            
            # Normalize confidence to 0.0-1.0
            confidence = float(data["confidence"])
            if confidence > 1.0:
                confidence = confidence / 100.0  # Convert percentage to decimal
            data["confidence"] = max(0.0, min(1.0, confidence))
            
            # Normalize decision to lowercase
            data["decision"] = str(data["decision"]).lower()
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse decision: {e}")
            # Fallback parsing
            return AgentOutputParser._parse_decision_fallback(raw_output)
    
    @staticmethod
    def _parse_decision_fallback(raw_output: str) -> Dict[str, Any]:
        """
        Fallback parser for decision when JSON parsing fails.
        Uses keyword matching and heuristics.
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Best-effort parsed decision
        """
        text = raw_output.lower()
        
        # Detect decision keywords
        decision = "review"  # Default
        if "accept" in text or "approve" in text:
            decision = "accept"
        elif "reject" in text or "deny" in text:
            decision = "reject"
        
        # Extract confidence if mentioned
        confidence = 0.5
        confidence_patterns = [
            r'confidence[:\s]+([0-9.]+)',
            r'([0-9]+)%\s*confidence',
            r'confidence\s*=\s*([0-9.]+)'
        ]
        for pattern in confidence_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    conf_value = float(match.group(1))
                    if conf_value > 1.0:
                        conf_value = conf_value / 100.0
                    confidence = max(0.0, min(1.0, conf_value))
                    break
                except:
                    pass
        
        return {
            "decision": decision,
            "reasoning": raw_output[:500],  # First 500 chars as reasoning
            "confidence": confidence,
            "fallback_parsed": True
        }
    
    @staticmethod
    def parse_entity_disambiguation(raw_output: str) -> Dict[str, Any]:
        """
        Parse entity disambiguation from LLM output.
        
        Expected format:
        {
            "canonical_entity": "Entity Name",
            "entity_type": "person|organization|place|concept",
            "confidence": 0.0-1.0,
            "reasoning": "explanation",
            "alternatives": [{"name": "...", "confidence": 0.0-1.0}]
        }
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Parsed entity disambiguation
        """
        try:
            data = AgentOutputParser.parse_json(raw_output)
            
            # Validate required fields
            if "canonical_entity" not in data:
                raise ParsingError("Missing required field: canonical_entity")
            
            # Add defaults for optional fields
            data.setdefault("entity_type", "unknown")
            data.setdefault("confidence", 0.5)
            data.setdefault("reasoning", "")
            data.setdefault("alternatives", [])
            
            # Normalize confidence
            confidence = float(data["confidence"])
            if confidence > 1.0:
                confidence = confidence / 100.0
            data["confidence"] = max(0.0, min(1.0, confidence))
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse entity disambiguation: {e}")
            raise ParsingError(f"Could not parse entity disambiguation: {e}")
    
    @staticmethod
    def parse_extraction_validation(raw_output: str) -> Dict[str, Any]:
        """
        Parse extraction validation from LLM output.
        
        Expected format:
        {
            "status": "VALID|CAPTCHA|LOGIN_WALL|BOILERPLATE|SOFT_404|WRONG_LANGUAGE|PAYWALL",
            "reasoning": "explanation",
            "confidence": 0.0-1.0,
            "detected_issues": ["issue1", "issue2"]
        }
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Parsed extraction validation
        """
        try:
            data = AgentOutputParser.parse_json(raw_output)
            
            # Validate required fields
            if "status" not in data:
                raise ParsingError("Missing required field: status")
            
            # Normalize status to uppercase
            valid_statuses = ["VALID", "CAPTCHA", "LOGIN_WALL", "BOILERPLATE", "SOFT_404", "WRONG_LANGUAGE", "PAYWALL"]
            status = str(data["status"]).upper()
            if status not in valid_statuses:
                status = "VALID"  # Default to valid if unknown
            
            data["status"] = status
            data.setdefault("reasoning", "")
            data.setdefault("confidence", 0.5)
            data.setdefault("detected_issues", [])
            
            # Normalize confidence
            confidence = float(data["confidence"])
            if confidence > 1.0:
                confidence = confidence / 100.0
            data["confidence"] = max(0.0, min(1.0, confidence))
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse extraction validation: {e}")
            # Fallback: assume valid if parsing fails
            return {
                "status": "VALID",
                "reasoning": "Could not parse validation result, assuming valid",
                "confidence": 0.3,
                "detected_issues": [],
                "parsing_error": str(e)
            }
    
    @staticmethod
    def parse_source_recommendations(raw_output: str) -> Dict[str, Any]:
        """
        Parse source recommendations from LLM output.
        
        Expected format:
        {
            "recommended_sources": [
                {"name": "SearXNG", "priority": 1, "confidence": 0.9},
                {"name": "Wikidata", "priority": 2, "confidence": 0.8}
            ],
            "reasoning": "explanation"
        }
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Parsed source recommendations
        """
        try:
            data = AgentOutputParser.parse_json(raw_output)
            
            if "recommended_sources" not in data:
                raise ParsingError("Missing required field: recommended_sources")
            
            # Validate source entries
            for source in data["recommended_sources"]:
                if "name" not in source:
                    raise ParsingError("Source missing 'name' field")
                source.setdefault("priority", 1)
                source.setdefault("confidence", 0.5)
                
                # Normalize confidence
                confidence = float(source["confidence"])
                if confidence > 1.0:
                    confidence = confidence / 100.0
                source["confidence"] = max(0.0, min(1.0, confidence))
            
            # Sort by priority
            data["recommended_sources"].sort(key=lambda x: x.get("priority", 999))
            
            data.setdefault("reasoning", "")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse source recommendations: {e}")
            raise ParsingError(f"Could not parse source recommendations: {e}")
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present.
        
        Args:
            data: Parsed data dictionary
            required_fields: List of required field names
            
        Raises:
            ParsingError: If any required field is missing
        """
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ParsingError(f"Missing required fields: {', '.join(missing)}")
