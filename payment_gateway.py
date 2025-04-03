import os
from novaerapayments import NovaEraPaymentsAPI, create_payment_api as create_novaera_api
from for4payments import For4PaymentsAPI, create_payment_api as create_for4_api
from typing import Union, Dict, Any
import requests
import json
from datetime import datetime, timedelta
import random
import string
import logging
import re

class GhostPaymentAPI:
    def __init__(self):
        self.api_key = os.environ.get("GHOST_API_KEY", "")
        self.api_url = os.environ.get("GHOST_API_URL", "https://api.ghostspaysv1.com/api/v1")
        self.logger = logging.getLogger('app')

    def _clean_phone(self, phone: str) -> str:
        """Remove todos os caracteres não numéricos do número de telefone"""
        if not phone:
            return ""
        return re.sub(r'\D', '', phone)

    def _get_headers(self) -> Dict[str, str]:
        # Lista de user agents comuns
        user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/95.0.4638.50 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # Lista de linguagens comuns
        languages = [
            'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'en-US,en;q=0.9,pt-BR;q=0.8',
            'pt-BR;q=0.9,en;q=0.8',
            'en-GB,en;q=0.9,pt;q=0.8'
        ]

        # Gerar um ID de dispositivo aleatório
        device_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        return {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': random.choice(user_agents),
            'Accept-Language': random.choice(languages),
            'X-Device-ID': device_id,
            'X-Request-ID': ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Ch-Ua-Platform': random.choice(['"Android"', '"iOS"', '"Windows"', '"macOS"']),
            'Sec-Ch-Ua-Mobile': '?1',
            'Origin': 'https://app.ghostspaysv1.com',
            'Referer': 'https://app.ghostspaysv1.com/',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
        }
    
    def create_payment(self, amount: float, description: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "amount": amount,
            "description": description,
            "currency": "BRL",
            **kwargs
        }
        
        response = requests.post(f"{self.api_url}/transaction.purchase", json=payload, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PIX payment request"""
        try:
            # Validação dos campos obrigatórios
            required_fields = ['name', 'email', 'cpf', 'amount']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")

            # Converter valor para centavos
            amount_in_cents = int(float(data['amount']) * 100)
            
            if amount_in_cents <= 0:
                raise ValueError("Valor do pagamento deve ser maior que zero")

            # Limpar número de telefone
            clean_phone = self._clean_phone(data.get('phone', ''))
            self.logger.info(f"Telefone original: {data.get('phone', '')}")
            self.logger.info(f"Telefone limpo: {clean_phone}")

            # Preparar payload para a API
            payload = {
                "name": data['name'],
                "email": data['email'],
                "cpf": data['cpf'],
                "phone": clean_phone,
                "paymentMethod": "PIX",
                "amount": amount_in_cents,
                "traceable": True,
                "items": [{
                    "unitPrice": amount_in_cents,
                    "title": "Inscrição 2025",
                    "quantity": 1,
                    "tangible": False
                }]
            }

            # Adicionar UTM parameters e metadata se presentes
            metadata = {}
            utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
            for field in utm_fields:
                if field in data:
                    metadata[field] = data[field]
            
            if data.get('metadata'):
                metadata.update(data['metadata'])
            
            if metadata:
                payload['metadata'] = metadata

            # Log detalhado da requisição
            headers = self._get_headers()
            masked_auth = f"{headers['Authorization'][:4]}...{headers['Authorization'][-4:]}" if len(headers['Authorization']) > 8 else "****"
            headers_log = headers.copy()
            headers_log['Authorization'] = masked_auth

            self.logger.info("=== Detalhes da Requisição PIX ===")
            self.logger.info(f"URL: {self.api_url}/transaction.purchase")
            self.logger.info(f"Headers: {json.dumps(headers_log, indent=2)}")
            self.logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            self.logger.info("================================")

            response = requests.post(
                f"{self.api_url}/transaction.purchase",
                json=payload,
                headers=headers
            )

            # Log da resposta
            self.logger.info("=== Detalhes da Resposta ===")
            self.logger.info(f"Status Code: {response.status_code}")
            self.logger.info(f"Response Headers: {dict(response.headers)}")
            self.logger.info(f"Response Body: {response.text}")
            self.logger.info("==========================")

            response.raise_for_status()
            response_data = response.json()

            # Retornar o ID da transação e os dados do PIX
            return {
                'id': response_data.get('id'),
                'pixCode': response_data.get('pixCode'),
                'pixQrCode': response_data.get('pixQrCode'),
                'expiresAt': response_data.get('expiresAt'),
                'status': response_data.get('status', 'pending')
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Detalhes do erro: {e.response.text}")
            raise ValueError(f"Erro na comunicação com a API: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro inesperado: {str(e)}")
            raise ValueError(f"Erro ao criar pagamento PIX: {str(e)}")
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Recupera detalhes de uma transação específica"""
        try:
            # Log da requisição
            headers = self._get_headers()
            masked_auth = f"{headers['Authorization'][:4]}...{headers['Authorization'][-4:]}" if len(headers['Authorization']) > 8 else "****"
            headers_log = headers.copy()
            headers_log['Authorization'] = masked_auth

            # Construir URL com query parameter
            url = f"{self.api_url}/transaction.getPayment?id={payment_id}"

            self.logger.info("=== Detalhes da Requisição de Status ===")
            self.logger.info(f"URL: {url}")
            self.logger.info(f"Headers: {json.dumps(headers_log, indent=2)}")
            self.logger.info("=====================================")

            # Fazer a requisição GET
            response = requests.get(url, headers=headers)

            # Log da resposta
            self.logger.info("=== Detalhes da Resposta de Status ===")
            self.logger.info(f"Status Code: {response.status_code}")
            self.logger.info(f"Response Headers: {dict(response.headers)}")
            self.logger.info(f"Response Body: {response.text}")
            self.logger.info("===================================")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Detalhes do erro: {e.response.text}")
            raise ValueError(f"Erro ao verificar status do pagamento: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao verificar status: {str(e)}")
            raise ValueError(f"Erro ao verificar status do pagamento: {str(e)}")

def create_ghost_api():
    return GhostPaymentAPI()

PaymentGatewayType = Union[NovaEraPaymentsAPI, For4PaymentsAPI, GhostPaymentAPI]

def get_payment_gateway() -> PaymentGatewayType:
    """Factory function to create the appropriate payment gateway instance based on PAYMENT_GATEWAY_CHOICE"""
    gateway_choice = os.environ.get("PAYMENT_GATEWAY_CHOICE", "GHOST").upper()
    
    gateway_map = {
        "GHOST": create_ghost_api,
        "NOVAERA": create_novaera_api,
        "FOR4": create_for4_api
    }
    
    if gateway_choice not in gateway_map:
        available_gateways = ", ".join(f"'{k}'" for k in gateway_map.keys())
        raise ValueError(f"PAYMENT_GATEWAY_CHOICE deve ser um dos seguintes: {available_gateways}")
    
    return gateway_map[gateway_choice]()
