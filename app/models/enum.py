from enum import Enum

# ====================OLLAMA ENUM==============================================


class OllamaChatResponsePropertiesType(Enum):
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    SMOKE = "smoke"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"


class OllamaChatResponsePropertiesPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
