import json
import logging
from typing import Dict, Any
from pydantic import ValidationError
from app.models.po_schemas import OCRPOResult

logger = logging.getLogger(__name__)

# หน้าที่ของ TextStructurer คือการสร้าง prompt สำหรับ LLM และตรวจสอบความถูกต้องของข้อมูลที่ได้จาก LLM โดยจะมีการกำหนด schema ที่คาดหวังและกฎเกณฑ์ต่างๆ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้
class TextStructurer:
    """
    Service for building prompts and validating structured output.
    Responsible ONLY for prompt engineering and schema validation.
    """
    
    # กำหนด schema ที่คาดหวังสำหรับข้อมูลที่ได้จาก LLM โดยจะมีการอธิบายรายละเอียดของแต่ละฟิลด์ใน schema เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้
    SCHEMA_DESCRIPTION = """
{
  "header": {
    "poNumber": "string or null - PO number",
    "poDate": "string or null - PO date in ISO format YYYY-MM-DD",
    "deliveryDate": "string or null - Delivery date in ISO format YYYY-MM-DD",
    "yourRef": "string or null - Your reference",
    "customer": {
      "name": "string or null - Customer company name",
      "taxNumber": "string or null - Tax ID number",
      "tel": "string or null - Telephone number",
      "email": "string or null - Email address",
      "faxNumber": "string or null - Fax number",
      "address": "string or null - Full address",
      "code": "string or null - Customer code if found"
    }
  },
  "items": [
    {
      "codeSteel": "string or null - Steel code like RB12, SS400, H-Beam",
      "description": "string or null - Full description from PO",
      "shape": "square or line or null - Shape type",
      "width": "number or null - Width in mm (for square)",
      "length": "number or null - Length in mm",
      "thickness": "number or null - Thickness in mm",
      "quantity": "number or null - Quantity in pieces",
      "cuttingMethod": "normal or laser or plasma or gas or null - Cutting method",
      "job": "number or null - Job number",
      "notes": "string or null - Additional notes",
      "matchedSteelTypeId": "string or null - Matched steel type ID from system",
      "confidence": "number - Confidence score 0.0-1.0 for this item"
    }
  ],
  "meta": {
    "confidence": "number - Overall confidence score 0.0-1.0",
    "warnings": ["array of warning strings"],
    "rawText": "string - Original raw text for debugging",
    "fields": {
      "fieldName": "number - Confidence for specific field 0.0-1.0"
    }
  }
}
"""
    # ฟังก์ชันหลักที่ใช้ในการสร้าง prompt สำหรับ LLM โดยจะมีการกำหนดกฎเกณฑ์และ schema ที่คาดหวังเพื่อให้แน่ใจว่าข้อมูลที่ได้จาก LLM มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้
    def build_prompt(self, text: str) -> list:
        """
        Build chat messages for OpenRouter to extract structured data from text.
        
        Args:
            text: Raw extracted text from PDF (Thai language)
            
        Returns:
            List of message dicts for chat completion API
        """
        system_prompt = """You are an expert at extracting structured data from Thai purchase order (PO) documents for steel products.

Your task is to analyze the provided text and extract information into a specific JSON structure.

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Follow the exact schema structure provided
3. For missing fields: use null for optional fields, empty string "" for strings if unclear, 0 for numbers if unclear, [] for empty arrays
4. All dates must be in ISO format: YYYY-MM-DD
5. Numbers should be extracted as numbers, not strings
6. For steel items, look for dimension patterns:
   - "thickness x width x length" or "หนา x กว้าง x ยาว" (3 dimensions) → shape is "square"
   - "length x thickness" or "ยาว x หนา" (2 dimensions only) → shape is "line"
   - Look for Ø symbol which indicates cylindrical/line shape → shape is "line"
7. Steel codes are typically like: SS400, RB12, H-Beam, etc.
8. Shape classification rules:
   - "square" = sheet/plate with 3 dimensions (thickness, width, length)
   - "line" = bars/beams/rods with 2 dimensions OR has Ø symbol
9. Assign confidence scores (0.0-1.0) based on how clear the data is
10. Include warnings array if data is ambiguous or missing
11. If the dimensions are listed in separate columns under headers like T (thickness), W (width), L (length), map them to thickness, width, and length respectively. For example, 'SS400  19  475  545  1 PCS' maps to thickness=19, width=475, length=545, quantity=1, shape='square'.
12. Customer name can often be found at the very top of the document (e.g., top-left header), while our company (S.S.W.) is listed under 'เรียน' (Attention) or 'ชื่อ' as the recipient/seller. Always extract the other company name (the buyer, e.g., 'บริษัท เอ็ม.ซี.รุ่งเจริญ สตีลเพลท จำกัด') as customer.name.

IMPORTANT - COMPANY NAME EXCLUSION:
DO NOT use these company names as customer name (these are OUR company, not the customer):
- "บริษัท เอส.เอส.ดับบลิว.สตีลเซ็นเตอร์ จำกัด"
- "เอส.เอส.ดับบลิว.สตีลเซ็นเตอร์"
- "S.S.W. Steel Center"
- "S.S.W. Steelcenter"
- "SSW Steel Center"
- "SSW Steelcenter"
- Any variations of "S.S.W" or "SSW" with "Steel" or "Steelcenter"

If you find these names in the document, they are likely the seller/issuer, NOT the customer.
Look for OTHER company names to use as customer.name.

SCHEMA:
""" + self.SCHEMA_DESCRIPTION
        
        user_prompt = f"""Extract structured data from this Thai purchase order text and return as JSON following the schema:

--- TEXT FROM OCR ---
{text}
--- END TEXT ---

Remember: Return ONLY the JSON object, no other text."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages
# ฟังก์ชันที่ใช้ในการแปลงข้อมูลจาก LLM เป็น JSON และตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง   
    def parse_and_validate(self, json_text: str, include_raw_text: bool = True) -> Dict[str, Any]:
        """
        Parse JSON string and validate against Pydantic schema.
        
        Args:
            json_text: Raw JSON string from LLM
            include_raw_text: Whether to preserve raw text in meta.rawText
            
        Returns:
            Validated dict conforming to OCRPOResult schema
            
        Raises:
            ValueError: If JSON is invalid or doesn't parse
            ValidationError: If JSON doesn't match schema
        """
        # ทำความสะอาดข้อความ JSON ที่ได้รับจาก LLM โดยจะมีการลบช่องว่างส่วนเกินและตรวจสอบว่าข้อความที่ได้รับไม่ว่างเปล่า และถ้าข้อความที่ได้รับเริ่มต้นด้วย markdown code block จะมีการลบ markdown code block ออกเพื่อให้เหลือเฉพาะ JSON ที่ต้องการแปลง และถ้าข้อความที่ได้รับไม่สามารถแปลงเป็น JSON ได้ จะมีการแจ้งเตือนผ่านการล็อกและส่งกลับข้อผิดพลาดที่เกิดขึ้นในการแปลง JSON เพื่อให้สามารถดีบักได้ง่ายขึ้น
        cleaned_text = json_text.strip()
        
        # ลบช่องว่างส่วนเกินและตรวจสอบว่าข้อความที่ได้รับไม่ว่างเปล่า
        if cleaned_text.startswith("```"):
            # Remove ```json or ``` prefix
            lines = cleaned_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines)
        
        cleaned_text = cleaned_text.strip()
        
        # ตรวจ json_text ที่ได้รับไม่ว่างเปล่า
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            # Return first 300 chars for debugging
            snippet = cleaned_text[:300] + ("..." if len(cleaned_text) > 300 else "")
            raise ValueError(f"Invalid JSON from model. Error: {str(e)}. Snippet: {snippet}")
        
        # ตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ โดยจะมีการใช้ Pydantic ในการตรวจสอบความถูกต้องของข้อมูลและแปลงข้อมูลเป็น dict ที่สามารถนำไปใช้งานต่อได้อย่างถูกต้อง และถ้าข้อมูลที่ได้รับไม่ตรงกับ schema ที่กำหนดไว้ จะมีการแจ้งเตือนผ่านการล็อกและส่งกลับข้อผิดพลาดที่เกิดขึ้นในการตรวจสอบความถูกต้องของข้อมูลเพื่อให้สามารถดีบักได้ง่ายขึ้น และถ้าข้อมูลที่ได้รับมีความสอดคล้องกับ schema ที่กำหนดไว้ จะมีการส่งกลับข้อมูลในรูปแบบ dict ที่สามารถนำไปใช้งานต่อได้อย่างถูกต้อง และถ้า include_raw_text เป็น False จะมีการลบ rawText ออกจากผลลัพธ์เพื่อให้ขนาดของผลลัพธ์ลดลง
        try:
            validated = OCRPOResult(**data)
            result = validated.model_dump()
            
            # ถ้า include_raw_text เป็น False จะมีการลบ rawText ออกจากผลลัพธ์เพื่อให้ขนาดของผลลัพธ์ลดลง
            if not include_raw_text and result.get("meta", {}).get("rawText"):
                result["meta"]["rawText"] = None
            
            return result
            
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise
    
    # ฟังก์ชันหลักที่ใช้ในการสร้าง prompt สำหรับ LLM และตรวจสอบความถูกต้องของข้อมูลที่ได้จาก LLM โดยจะมีการกำหนดกฎเกณฑ์และ schema ที่คาดหวังเพื่อให้แน่ใจว่าข้อมูลที่ได้จาก LLM มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง โดยจะมีการจัดการกับข้อผิดพลาดที่อาจเกิดขึ้นในการแปลงข้อมูลจาก LLM เป็น JSON และการตรวจสอบความถูกต้องของข้อมูลตาม schema ที่กำหนดไว้ เพื่อให้แน่ใจว่าข้อมูลที่ได้มีความสอดคล้องกับความต้องการและสามารถนำไปใช้งานต่อได้อย่างถูกต้อง
    def structure_text(self, text: str, llm_callable, include_raw_text: bool = True) -> Dict[str, Any]:
        """
        High-level method to structure text using an LLM callable.
        
        Args:
            text: Raw text to structure
            llm_callable: Function that takes messages and returns string response
            include_raw_text: Whether to preserve raw text in response
            
        Returns:
            Validated structured data dict
            
        Raises:
            Various exceptions from LLM call or validation
        """
        # Build prompt
        messages = self.build_prompt(text)
        
        # Call LLM
        logger.info("Calling LLM to structure text")
        raw_response = llm_callable(messages)
        
        # Parse and validate
        logger.info("Parsing and validating LLM response")
        result = self.parse_and_validate(raw_response, include_raw_text=include_raw_text)
        
        return result
