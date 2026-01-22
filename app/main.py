from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
import os

from app.database import get_session, init_db
from app.models import ReadingListItem, Settings
from app.safari_reader import extract_reading_list, get_default_bookmarks_path
from app.summarizer import fetch_webpage_content, summarize_with_llm
from pydantic import BaseModel

app = FastAPI(title="Reading List Processor")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup_event():
    await init_db()


class ProcessRequest(BaseModel):
    item_id: Optional[int] = None
    reprocess: bool = False
    custom_instructions: Optional[str] = None


class SettingsUpdate(BaseModel):
    custom_instructions: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("app/templates/index.html")


@app.get("/api/items")
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all reading list items from database"""
    result = await session.execute(select(ReadingListItem))
    items = result.scalars().all()
    return [item.to_dict() for item in items]


@app.post("/api/sync")
async def sync_reading_list(session: AsyncSession = Depends(get_session)):
    """Sync reading list from Safari bookmarks"""
    bookmarks_path = os.getenv('SAFARI_BOOKMARKS_PATH', get_default_bookmarks_path())

    try:
        reading_list = extract_reading_list(bookmarks_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading Safari bookmarks: {str(e)}")

    new_count = 0
    for item in reading_list:
        # Check if URL already exists
        result = await session.execute(
            select(ReadingListItem).where(ReadingListItem.url == item['url'])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            new_item = ReadingListItem(
                url=item['url'],
                title=item['title'] or item['url'],
                preview_text=item['preview_text'],
                added_date=item['added_date'] if item['added_date'] else datetime.utcnow()
            )
            session.add(new_item)
            new_count += 1

    await session.commit()

    return {"message": f"Synced {new_count} new items", "new_items": new_count}


@app.post("/api/process")
async def process_items(
    request: ProcessRequest,
    session: AsyncSession = Depends(get_session)
):
    """Process reading list items with Claude"""

    # Get custom instructions from settings if not provided
    custom_instructions = request.custom_instructions
    if not custom_instructions:
        result = await session.execute(
            select(Settings).where(Settings.key == 'custom_instructions')
        )
        settings = result.scalar_one_or_none()
        if settings:
            custom_instructions = settings.value

    if request.item_id:
        # Process single item
        result = await session.execute(
            select(ReadingListItem).where(ReadingListItem.id == request.item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        items_to_process = [item]
    else:
        # Process all unprocessed items (or all if reprocess=True)
        if request.reprocess:
            result = await session.execute(select(ReadingListItem))
        else:
            result = await session.execute(
                select(ReadingListItem).where(ReadingListItem.processed == False)
            )
        items_to_process = result.scalars().all()

    processed_count = 0
    errors = []

    for item in items_to_process:
        try:
            # Fetch content
            if not item.content or request.reprocess or request.item_id:
                content = fetch_webpage_content(item.url)
                if content:
                    item.content = content
                else:
                    errors.append(f"Failed to fetch content for {item.url}")
                    continue

            # Summarize
            summary = summarize_with_llm(item.content, custom_instructions)
            item.summary = summary
            item.processed = True
            item.processed_date = datetime.utcnow()
            processed_count += 1

        except Exception as e:
            errors.append(f"Error processing {item.url}: {str(e)}")

    await session.commit()

    return {
        "message": f"Processed {processed_count} items",
        "processed_count": processed_count,
        "errors": errors
    }


@app.get("/api/settings")
async def get_settings(session: AsyncSession = Depends(get_session)):
    """Get application settings"""
    result = await session.execute(
        select(Settings).where(Settings.key == 'custom_instructions')
    )
    settings = result.scalar_one_or_none()

    return {
        "custom_instructions": settings.value if settings else ""
    }


@app.post("/api/settings")
async def update_settings(
    settings_update: SettingsUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update application settings"""

    # Update or create custom instructions
    if settings_update.custom_instructions is not None:
        result = await session.execute(
            select(Settings).where(Settings.key == 'custom_instructions')
        )
        settings = result.scalar_one_or_none()

        if settings:
            settings.value = settings_update.custom_instructions
        else:
            settings = Settings(key='custom_instructions', value=settings_update.custom_instructions)
            session.add(settings)

    await session.commit()

    return {"message": "Settings updated"}


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a reading list item"""
    result = await session.execute(
        select(ReadingListItem).where(ReadingListItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.delete(item)
    await session.commit()

    return {"message": "Item deleted"}
