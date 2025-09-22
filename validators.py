import re
from typing import Optional
from interfaces import IValidator


class SecurityValidator(IValidator):
    
    MAX_MESSAGE_LENGTH = 1000
    MAX_USER_ID = 999999999999999
    MIN_USER_ID = 1
    REFERRAL_PARAM_PATTERN = re.compile(r'^friend_\d{1,15}$')
    SAFE_TEXT_PATTERN = re.compile(
        r'^[a-zA-Zа-яА-Я0-9\s\.,!?\-_@#$%&*()+=\[\]{}|\\:";\'<>\/\n\r\t]*$'
    )
    
    def validate_user_id(self, user_id: str) -> bool:
        try:
            user_id_int = int(user_id)
            if not (self.MIN_USER_ID <= user_id_int <= self.MAX_USER_ID):
                return False
            return True
        except (ValueError, TypeError) as e:
            return False
    
    def validate_referral_param(self, param: str) -> bool:
        if not isinstance(param, str):
            return False
        
        if len(param) > 50:
            return False
        
        if not self.REFERRAL_PARAM_PATTERN.match(param):
            return False
        
        try:
            user_id_str = param.split('_')[1]
            return self.validate_user_id(user_id_str)
        except (IndexError, ValueError) as e:
            return False
    
    def validate_message_text(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        
        if len(text) > self.MAX_MESSAGE_LENGTH:
            return False
        
        if not text.strip():
            return False
        
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        if not self.SAFE_TEXT_PATTERN.match(text):
            return False
        
        return True
    
    def sanitize_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        text = text[:self.MAX_MESSAGE_LENGTH]
        
        text = text.strip()
        
        return text
    
    def validate_telegram_init_data(self, init_data: str) -> bool:
        if not isinstance(init_data, str):
            return False
        
        if len(init_data) > 2000:
            return False
        
        if not re.match(r'^[a-zA-Z0-9+/=._-]+$', init_data):
            return False
        
        return True


def create_security_validator() -> SecurityValidator:
    return SecurityValidator()
