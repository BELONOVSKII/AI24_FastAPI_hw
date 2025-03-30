import json
import uuid
from datetime import datetime
from urllib.parse import unquote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.auth import current_active_user
from app.db import get_async_session
from app.models import Link, User
from app.services.redis_cache import (
    cache_link,
    cache_link_stats,
    get_cached_link,
    get_cached_link_stats,
    invalidate_cache,
    invalidate_cache_stats,
)

router = APIRouter()


async def remove_expired_links(db: AsyncSession):
    expired_links = await db.execute(
        select(Link).filter(Link.expires_at < datetime.utcnow())
    )
    expired_links = expired_links.scalars().all()

    for link in expired_links:
        await db.delete(link)
    await db.commit()


@router.post("/links/shorten")
async def create_short_link(
    original_url: str,
    user: User = Depends(current_active_user),
    custom_alias: str = None,
    expires_at: datetime = None,
    db: AsyncSession = Depends(get_async_session),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    if custom_alias:
        existing_link = await db.execute(
            select(Link).filter(Link.short_code == custom_alias)
        )
        if existing_link.scalar():
            raise HTTPException(status_code=400, detail="Alias already in use.")
        short_code = custom_alias
    else:
        short_code = str(uuid.uuid4())[:6]

    link = Link(
        original_url=unquote(original_url),
        short_code=short_code,
        user_id=user.id if user else None,
        expires_at=expires_at,
    )
    db.add(link)
    await db.commit()

    if expires_at:
        background_tasks.add_task(remove_expired_links, db)

    return {"short_code": short_code}


@router.get("/links/search")
async def search_link_by_url(
    original_url: str = Query(..., description="The original URL to search for"),
    db: AsyncSession = Depends(get_async_session),
):
    link = await db.execute(
        select(Link).filter(Link.original_url == unquote(original_url))
    )
    link = link.scalar()

    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    return {"short_code": link.short_code}


@router.get("/links/{short_code}", summary="Redirects to the old link")
async def redirect_to_original_url(
    short_code: str, db: AsyncSession = Depends(get_async_session)
):
    # Firstly try to find in cache
    cached_url = await get_cached_link(short_code)
    if cached_url:
        print("Cache works")
        return RedirectResponse(url=cached_url)

    link = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = link.scalar()

    if link is None or (link.expires_at and link.expires_at < datetime.utcnow()):
        raise HTTPException(status_code=404, detail="Link not found or expired")

    link.clicks += 1
    link.last_used_at = datetime.utcnow()
    db.add(link)
    await db.commit()

    # Cache the result
    await cache_link(short_code, link.original_url)

    return RedirectResponse(url=link.original_url)


@router.put("/links/{short_code}")
async def update_link(
    short_code: str,
    original_url: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    link = await db.execute(
        select(Link).filter(Link.short_code == short_code, Link.user_id == user.id)
    )
    link = link.scalar()

    if link is None:
        raise HTTPException(
            status_code=404, detail="Link not found or you are not authorized"
        )

    link.original_url = original_url
    db.add(link)
    await db.commit()

    # Delete from cache
    await invalidate_cache(short_code)
    await invalidate_cache_stats(short_code)

    return {"message": "Link updated successfully"}


@router.delete("/links/{short_code}")
async def delete_link(
    short_code: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    link = await db.execute(
        select(Link).filter(Link.short_code == short_code, Link.user_id == user.id)
    )
    link = link.scalar()

    if link is None:
        raise HTTPException(
            status_code=404, detail="Link not found or you are not authorized"
        )

    await db.delete(link)
    await db.commit()

    # Delete from cache
    await invalidate_cache(short_code)
    await invalidate_cache_stats(short_code)

    return {"message": "Link deleted successfully"}


@router.get("/links/{short_code}/stats")
async def get_link_stats(
    short_code: str, db: AsyncSession = Depends(get_async_session)
):
    # Firstly try to find in cache
    cached_stats = await get_cached_link_stats(short_code)
    if cached_stats:
        print("Cache works")
        return json.loads(cached_stats)
    link = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = link.scalar()

    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    stats = {
        "original_url": link.original_url,
        "created_at": link.created_at.isoformat(),
        "clicks": link.clicks,
        "last_used_at": link.last_used_at.isoformat(),
    }

    # Cache the result
    await cache_link_stats(short_code, json.dumps(stats))

    return stats
