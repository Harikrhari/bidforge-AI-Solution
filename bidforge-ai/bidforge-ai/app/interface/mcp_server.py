"""BidForge exposed as an MCP server so any MCP client/agent can search company evidence."""
from mcp.server.fastmcp import FastMCP

from app.container import build_retriever, get_pool

mcp = FastMCP("bidforge")


@mcp.tool()
async def search_company_evidence(tenant_id: str, query: str, k: int = 5) -> list[dict]:
    """Search a company's past proposals, CVs and case studies."""
    retriever = build_retriever(await get_pool())
    return [e.__dict__ for e in await retriever.search(tenant_id, query, k)]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
