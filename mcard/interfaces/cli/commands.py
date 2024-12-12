"""
CLI commands for MCard.
"""
import asyncio
from datetime import datetime
from typing import Optional
import click
from ...domain.models.card import MCard
from mcard.interfaces.api.mcard_api import api

def get_repository():
    """Alias for get_store to maintain compatibility."""
    return api.get_store()

@click.group()
def cli():
    """MCard command line interface."""
    pass

@cli.command()
@click.argument('content')
def create(content: str):
    """Create a new card with the given content."""
    async def _create():
        repo = await get_repository()
        card = MCard(content=content)
        await repo.save(card)
        click.echo(f"Created card with hash: {card.hash}")
        click.echo(f"Global time: {card.g_time}")
    
    asyncio.run(_create())

@cli.command()
@click.argument('hash_str')
def get(hash_str: str):
    """Get a card by its hash."""
    async def _get():
        repo = await get_repository()
        card = await repo.get(hash_str)
        if not card:
            click.echo("Card not found", err=True)
            return
        click.echo(f"Hash: {card.hash}")
        click.echo(f"Content: {card.content}")
        click.echo(f"Global time: {card.g_time}")
    
    asyncio.run(_get())

@cli.command()
@click.option('--start-time', type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%SZ"]), help='Start time filter (ISO format)')
@click.option('--end-time', type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%SZ"]), help='End time filter (ISO format)')
@click.option('--limit', type=int, help='Maximum number of cards to return')
@click.option('--offset', type=int, help='Number of cards to skip')
def list(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
):
    """List cards with optional time range and pagination."""
    async def _list():
        repo = await get_repository()
        if start_time or end_time:
            cards = await repo.get_by_time_range(start_time, end_time, limit, offset)
        else:
            cards = await repo.get_all(limit, offset)
        
        for card in cards:
            click.echo("-" * 40)
            click.echo(f"Hash: {card.hash}")
            click.echo(f"Content: {card.content}")
            click.echo(f"Global time: {card.g_time}")
    
    asyncio.run(_list())

if __name__ == '__main__':
    cli()
