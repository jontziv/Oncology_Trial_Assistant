from fastapi import APIRouter

from copilot.domain.models import ParseProtocolRequest, ProtocolParseResult
from copilot.services.protocol_parser import parse_protocol

router = APIRouter(prefix="/v1/protocols", tags=["protocols"])


@router.post("/parse", response_model=ProtocolParseResult)
async def parse_protocol_text(request: ParseProtocolRequest) -> ProtocolParseResult:
    return parse_protocol(request.text)
