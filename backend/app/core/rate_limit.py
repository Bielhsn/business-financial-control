from slowapi import Limiter
from slowapi.util import get_remote_address

# Armazenamento em memória por padrão (suficiente para uma única instância).
# Para múltiplas instâncias, configurar storage_uri=settings.redis_url.
limiter = Limiter(key_func=get_remote_address)
