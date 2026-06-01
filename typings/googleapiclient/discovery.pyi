from typing import Any

HttpRequest = Any

def build(
    serviceName: Any,
    version: Any,
    http: Any | None = None,
    discoveryServiceUrl: Any | None = None,
    developerKey: Any | None = None,
    model: Any | None = None,
    requestBuilder: type[HttpRequest] = HttpRequest,
    credentials: Any | None = None,
    cache_discovery: bool = True,
    cache: Any | None = None,
    client_options: Any | None = None,
    adc_cert_path: Any | None = None,
    adc_key_path: Any | None = None,
    num_retries: int = 1,
    static_discovery: Any | None = None,
    always_use_jwt_access: bool = False,
) -> Any: ...
