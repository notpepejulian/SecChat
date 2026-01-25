"""
Servicio para generar alias temporales anónimos.
Los alias cambian en cada chat y no revelan identidad.
"""
import hashlib
import random
import time


class AliasService:
    """Servicio para generar alias temporales"""
    
    # Listas para generar nombres aleatorios
    ADJECTIVES = [
        "Silent", "Swift", "Dark", "Bright", "Hidden", "Quick", "Calm", "Wild",
        "Gentle", "Fierce", "Mystic", "Noble", "Clever", "Bold", "Shy", "Wise",
        "Ancient", "Modern", "Frozen", "Burning", "Crystal", "Shadow", "Golden",
        "Silver", "Cosmic", "Quantum", "Digital", "Phantom", "Stealth", "Ghost"
    ]
    
    ANIMALS = [
        "Fox", "Wolf", "Eagle", "Raven", "Tiger", "Lion", "Bear", "Hawk",
        "Owl", "Falcon", "Panther", "Leopard", "Lynx", "Coyote", "Badger",
        "Otter", "Seal", "Whale", "Shark", "Dolphin", "Phoenix", "Dragon",
        "Cobra", "Viper", "Spider", "Scorpion", "Mantis", "Beetle", "Moth"
    ]
    
    @classmethod
    def generate_alias(cls, public_key: str, chat_id: str) -> str:
        """
        Genera un alias temporal basado en la llave pública y el chat.
        
        Args:
            public_key: Llave pública del usuario
            chat_id: ID del chat
            
        Returns:
            str: Alias en formato "AdjetivoAnimal1234"
        """
        # Crear hash único
        timestamp = str(time.time())
        random_salt = str(random.randint(0, 999999))
        
        hash_input = f"{public_key}{chat_id}{timestamp}{random_salt}"
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()
        
        # Usar hash para seleccionar palabras
        adj_index = int.from_bytes(hash_bytes[0:2], 'big') % len(cls.ADJECTIVES)
        animal_index = int.from_bytes(hash_bytes[2:4], 'big') % len(cls.ANIMALS)
        
        # Generar número de 4 dígitos
        number = int.from_bytes(hash_bytes[4:6], 'big') % 10000
        
        alias = f"{cls.ADJECTIVES[adj_index]}{cls.ANIMALS[animal_index]}{number:04d}"
        
        return alias
    
    @staticmethod
    def validate_alias(alias: str) -> bool:
        """
        Valida formato de alias.
        
        Args:
            alias: Alias a validar
            
        Returns:
            bool: True si el formato es válido
        """
        if not alias or len(alias) < 10:
            return False
        
        # Debe terminar en 4 dígitos
        if not alias[-4:].isdigit():
            return False
        
        # El resto debe ser alfabético
        if not alias[:-4].isalpha():
            return False
        
        return True
