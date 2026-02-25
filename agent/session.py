from dataclasses import dataclass
import re

@dataclass
class CustomerProfile:
    name: str
    phone: str
    vehicle: str
    is_identified: bool = False

class SessionManager:
    def __init__(self):
        # Explicit State
        self.customer: CustomerProfile = None
        self.interaction_id: str = None
    
    def set_customer(self, data: dict):
        self.customer = CustomerProfile(
            name=data['name'],
            phone=data['phone'],
            vehicle=data['vehicle'],
            is_identified=True
        )

    def normalize_phone(self, raw_input: str) -> str:
        """
        Senior Signal: Robust input normalization.
        Strips non-digits. Handles basic parsing.
        """
        if not raw_input: return None
        # Remove spaces, dashes, parentheses
        clean = re.sub(r'\D', '', raw_input)
        # Basic check (adjust for your region)
        if len(clean) < 10: return None
        return clean

    @property
    def is_authenticated(self):
        return self.customer is not None and self.customer.is_identified