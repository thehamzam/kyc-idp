"""Data models for document extraction."""
import base64
import json
import re
from dataclasses import dataclass, field
from typing import Optional

ALLOWED_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'}
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class ExtractionResult:
    """Extracted document information."""
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    document_number: Optional[str] = None
    document_type: Optional[str] = None
    expiry_date: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    sex: Optional[str] = None
    additional_fields: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'date_of_birth': self.date_of_birth,
            'document_number': self.document_number,
            'document_type': self.document_type,
            'expiry_date': self.expiry_date,
            'nationality': self.nationality,
            'address': self.address,
            'sex': self.sex,
            'additional_fields': self.additional_fields
        }

    @classmethod
    def from_response(cls, text: str) -> 'ExtractionResult':
        """Parse AI response into structured result."""
        if not text:
            return cls()
        try:
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            data = json.loads(match.group() if match else text)
        except json.JSONDecodeError:
            return cls()

        known = {'name', 'date_of_birth', 'document_number', 'document_type', 'expiry_date', 'nationality', 'address', 'sex'}
        additional = {k: v for k, v in data.items() if k not in known and v}

        return cls(
            name=data.get('name'),
            date_of_birth=data.get('date_of_birth'),
            document_number=data.get('document_number'),
            document_type=data.get('document_type'),
            expiry_date=data.get('expiry_date'),
            nationality=data.get('nationality'),
            address=data.get('address'),
            sex=data.get('sex'),
            additional_fields=additional
        )


@dataclass
class UploadedFile:
    """Uploaded document image."""
    filename: str
    content_type: str
    data: bytes

    def validate(self) -> tuple[bool, str]:
        """Validate file type and size."""
        if len(self.data) > MAX_FILE_SIZE:
            return False, f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        if self.content_type.lower() not in ALLOWED_TYPES:
            return False, "Invalid file type. Use JPEG, PNG, GIF, or WebP."
        if '.' in self.filename:
            ext = self.filename.rsplit('.', 1)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return False, "Invalid file extension."
        return True, ""

    def to_base64(self) -> str:
        return base64.b64encode(self.data).decode('utf-8')

    def to_data_url(self) -> str:
        return f"data:{self.content_type};base64,{self.to_base64()}"
