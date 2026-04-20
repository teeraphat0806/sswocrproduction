import os
import logging
import httpx
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# โหลดค่าคอนฟิกจาก .env ไฟล์ที่อยู่ในโฟลเดอร์หลักของโปรเจค (ขึ้นไป 3 ระดับจากไฟล์นี้) เพื่อให้สามารถใช้ตัวแปรสภาพแวดล้อมในการตั้งค่า OpenRouterClient ได้อย่างง่ายดาย
# หากไม่มี .env ไฟล์ หรือค่าที่จำเป็นไม่ถูกตั้งค่า จะมีการแจ้งเตือนผ่าน ValueError ในการสร้างอินสแตนซ์ของ OpenRouterClient และจะมีการล็อกข้อมูลที่เกี่ยวข้องเพื่อช่วยในการดีบักและตรวจสอบปัญหาในการเชื่อมต่อกับ OpenRouter API
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Client สำหรับเรียก OpenRouter API โดยเฉพาะ มีหน้าที่รับผิดชอบในการทำ HTTP requests ไปยัง OpenRouter เท่านั้น 
class OpenRouterClient:
    """
    Client for calling OpenRouter.ai API.
    Responsible ONLY for making HTTP requests to OpenRouter.
    """
    # การตั้งค่าเริ่มต้นจะถูกดึงมาจาก environment variables หรือสามารถส่งผ่านพารามิเตอร์ได้เมื่อสร้างอินสแตนซ์ของคลาสนี้ โดยมีการจัดการ fallback models ในกรณีที่โมเดลหลักไม่สามารถใช้งานได้ และมีการล็อกข้อมูลที่เกี่ยวข้องกับการเรียก API เพื่อช่วยในการดีบักและตรวจสอบปัญหาในการเชื่อมต่อกับ OpenRouter API
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        http_referer: Optional[str] = None,
        app_title: Optional[str] = None
    ):
        """
        Initialize OpenRouter client with configuration from env vars or parameters.
        
        Args:
            api_key: OpenRouter API key (defaults to env OPENROUTER_API_KEY)
            base_url: Base URL (defaults to env OPENROUTER_BASE_URL or https://openrouter.ai/api/v1)
            model: Default model to use (defaults to env OPENROUTER_MODEL)
            http_referer: HTTP referer header (defaults to env OPENROUTER_HTTP_REFERER)
            app_title: App title header (defaults to env OPENROUTER_APP_TITLE)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.http_referer = http_referer or os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.app_title = app_title or os.getenv("OPENROUTER_APP_TITLE", "Thai PDF OCR API")
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )
    
    # ฟังก์ชันหลักในการเรียก OpenRouter API โดยจะมีการจัดการ fallback models ในกรณีที่โมเดลหลักไม่สามารถใช้งานได้ และมีการล็อกข้อมูลที่เกี่ยวข้องกับการเรียก API เพื่อช่วยในการดีบักและตรวจสอบปัญหาในการเชื่อมต่อกับ OpenRouter API
    def call_openrouter(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 60
    ) -> str:
        """
        Call OpenRouter API with chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to instance default_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            
        Returns:
            Raw string response from the model
            
        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response format is unexpected
        """
        model = model or self.default_model
        
        # Fallback models if primary model fails
        fallback_models = [
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "deepseek/deepseek-chat-v3.1"
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # เพิ่ม HTTP headers สำหรับ referer และ app title ถ้ามีการตั้งค่าไว้ เพื่อให้สามารถส่งข้อมูลเหล่านี้ไปยัง OpenRouter API ได้ 
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title
        # รายละเอียดของ payload ที่จะส่งไปยัง OpenRouter API
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        # ถ้ามีการตั้งค่า max_tokens จะเพิ่มเข้าไปใน payload เพื่อจำกัดจำนวนโทเค็นในคำตอบจากโมเดล
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.base_url}/chat/completions"
        
        # ลองเรียก API ด้วยโมเดลหลักก่อน ถ้าเกิดข้อผิดพลาดที่บ่งชี้ว่าโมเดลไม่สามารถใช้งานได้ (เช่น 404 หรือข้อความแสดงว่า provider ไม่พร้อม) จะลองใช้โมเดลถัดไปใน fallback list จนกว่าจะสำเร็จหรือหมดตัวเลือก 
        models_to_try = [model] + [m for m in fallback_models if m != model]
        last_error = None
        
        for attempt_model in models_to_try:
            # อัปเดตโมเดลใน payload สำหรับแต่ละการลองเรียก API เพื่อให้แน่ใจว่าเรากำลังทดสอบโมเดลที่ถูกต้องในแต่ละรอบของการลอง
            payload["model"] = attempt_model
            
            # การล็อกข้อมูลที่เกี่ยวข้องกับการเรียก API เช่น URL, โมเดลที่กำลังพยายามใช้, และ API key ที่ถูกมาสก์เพื่อความปลอดภัย เพื่อช่วยในการดีบักและตรวจสอบปัญหาในการเชื่อมต่อกับ OpenRouter API
            masked_key = self.api_key[:10] + "..." + self.api_key[-4:] if len(self.api_key) > 14 else "***"
            logger.info(f"Calling OpenRouter API: {url}")
            logger.info(f"Attempting model: {attempt_model}, API Key: {masked_key}")
            logger.debug(f"Request payload: {payload}")
            
            try:
                # การใช้ httpx.Client เพื่อทำการส่ง HTTP POST request ไปยัง OpenRouter API ด้วย payload และ headers ที่เตรียมไว้ และมีการจัดการ timeout เพื่อป้องกันการรอคอยที่ยาวนานเกินไปในกรณีที่ API ไม่ตอบสนอง
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    
                    # Log response status
                    logger.info(f"OpenRouter response status: {response.status_code}")
                    
                    # If error, log response body before raising
                    if response.status_code != 200:
                        error_body = response.text
                        logger.error(f"OpenRouter API error response: {error_body}")
                        try:
                            error_json = response.json()
                            logger.error(f"Error JSON: {error_json}")
                        except:
                            pass
                    # ตรวจสอบสถานะของการตอบกลับจาก OpenRouter API และถ้าไม่ใช่ 200 OK จะมีการล็อกข้อมูลที่เกี่ยวข้องกับข้อผิดพลาดและพยายามใช้โมเดลถัดไปใน fallback list จนกว่าจะสำเร็จหรือหมดตัวเลือก
                    response.raise_for_status()
                    
                    result = response.json()
                    logger.debug(f"OpenRouter response: {result}")
                    
                    # ตรวจสอบรูปแบบของการตอบกลับจาก OpenRouter API ว่ามีข้อมูลที่คาดหวังหรือไม่ เช่น การมี "choices" และ "content" ในการตอบกลับ ถ้าไม่มีจะมีการแจ้งเตือนผ่าน ValueError และถ้ามีจะทำการดึงข้อมูลที่ต้องการออกมาและส่งกลับไปยังผู้เรียก
                    if "choices" not in result or len(result["choices"]) == 0:
                        raise ValueError("No choices in OpenRouter response")
                    
                    content = result["choices"][0].get("message", {}).get("content", "")
                    
                    # ตรวจสอบว่าข้อมูลที่ได้จาก OpenRouter API ไม่ว่างเปล่า ถ้าเป็นเช่นนั้นจะมีการแจ้งเตือนผ่าน ValueError และถ้าไม่ว่างเปล่าจะทำการส่งกลับไปยังผู้เรียก
                    if not content:
                        raise ValueError("Empty content in OpenRouter response")
                    
                    # การล็อกข้อมูลที่เกี่ยวข้องกับการเรียก API เช่น โมเดลที่ใช้ในการตอบกลับและจำนวนตัวอักษรที่ได้รับจาก OpenRouter API เพื่อช่วยในการดีบักและตรวจสอบปัญหาในการเชื่อมต่อกับ OpenRouter API และถ้าโมเดลที่สำเร็จไม่ใช่โมเดลหลักที่ตั้งไว้ จะมีการแจ้งเตือนผ่านการล็อกเพื่อให้ทราบว่าโมเดลหลักไม่สามารถใช้งานได้และมีการใช้โมเดล fallback แทน
                    if attempt_model != model:
                        logger.warning(f"Primary model '{model}' failed, used fallback: {attempt_model}")
                    logger.info(f"OpenRouter API call successful with {attempt_model}, received {len(content)} characters")
                    return content
            # การจัดการข้อผิดพลาดที่เกิดขึ้นระหว่างการเรียก API เช่น HTTP errors, timeouts, หรือข้อผิดพลาดอื่นๆ โดยจะมีการล็อกข้อมูลที่เกี่ยวข้องกับข้อผิดพลาดและพยายามใช้โมเดลถัดไปใน fallback list จนกว่าจะสำเร็จหรือหมดตัวเลือก และถ้าทุกโมเดลใน fallback list ล้มเหลว จะมีการแจ้งเตือนผ่านการล็อกและส่งกลับข้อผิดพลาดสุดท้ายที่เกิดขึ้น            
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_json = e.response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"]
                        if isinstance(error_detail, dict):
                            error_msg = f"{error_msg}: {error_detail.get('message', e.response.text)}"
                        else:
                            error_msg = f"{error_msg}: {error_detail}"
                    else:
                        error_msg = f"{error_msg}: {e.response.text}"
                except:
                    error_msg = f"{error_msg}: {e.response.text}"
                
                logger.error(f"Model {attempt_model} failed: {error_msg}")
                last_error = httpx.HTTPStatusError(
                    message=error_msg,
                    request=e.request,
                    response=e.response
                )
                
                # ตรวจสอบว่าข้อผิดพลาดที่เกิดขึ้นเป็นข้อผิดพลาดที่บ่งชี้ว่าโมเดลไม่สามารถใช้งานได้ (เช่น 404 หรือข้อความแสดงว่า provider ไม่พร้อม) ถ้าเป็นเช่นนั้นจะมีการล็อกข้อมูลที่เกี่ยวข้องและพยายามใช้โมเดลถัดไปใน fallback list จนกว่าจะสำเร็จหรือหมดตัวเลือก แต่ถ้าเป็นข้อผิดพลาดอื่นๆ จะไม่พยายามใช้โมเดลถัดไปและจะส่งกลับข้อผิดพลาดทันที
                if e.response.status_code == 404 or "provider" in error_msg.lower():
                    logger.warning(f"Model {attempt_model} not available, trying next fallback...")
                    continue
                else:
                    # ข้อผิดพลาดที่ไม่เกี่ยวข้องกับโมเดลไม่พร้อม เช่น ปัญหาในการเชื่อมต่อหรือข้อผิดพลาดอื่นๆ จะไม่พยายามใช้โมเดลถัดไปและจะส่งกลับข้อผิดพลาดทันที
                    raise last_error
                    
            except httpx.TimeoutException as e:
                logger.error(f"Model {attempt_model} timeout after {timeout}s")
                last_error = e
                continue
                
            except Exception as e:
                logger.error(f"Model {attempt_model} error: {str(e)}")
                last_error = e
                continue
        
        # ถ้าทุกโมเดลใน fallback list ล้มเหลว จะมีการแจ้งเตือนผ่านการล็อกและส่งกลับข้อผิดพลาดสุดท้ายที่เกิดขึ้น
        logger.error(f"All models failed. Last error: {last_error}")
        if last_error:
            raise last_error
        else:
            raise ValueError("All OpenRouter models failed")
