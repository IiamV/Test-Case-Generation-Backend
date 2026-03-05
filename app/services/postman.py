
from app.core.postman import postbot_generate, get_all_requestIds
from typing import Literal


def generate_test_script(
        collectionId: str,
        requestId: str,
        language: str,
        agentFramework: str
):
    all_requests = get_all_requestIds(collection_id=collectionId)

    # result = []
    for request in all_requests:

        generated = postbot_generate(
            collectionId=collectionId,
            requestId=request,
            language=language,
            agentFramework=agentFramework
        )

        # result.append(generated['data'])
    return generated


def generate_all_test_scripts(
        collectionId: str,
        language: str,
        agentFramework: str
):
    all_requests = get_all_requestIds(collection_id=collectionId)

    result = []
    for request in all_requests:

        generated = postbot_generate(
            collectionId=collectionId,
            requestId=request,
            language=language,
            agentFramework=agentFramework
        )

        result.append(generated['data']['text'])
    return result
