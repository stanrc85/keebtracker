from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .models import *
import os
from pathlib import Path
import shutil
from typing import List
from pydantic import BaseModel
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/media", StaticFiles(directory="data/media"), name="media")

templates = Jinja2Templates(directory="templates")

# Pydantic models for API
class CaseCreate(BaseModel):
    name: str
    color: str = None
    material: str = None
    acquired_date: str = None

class CaseResponse(CaseCreate):
    id: str

# Similar for others, but for brevity, I'll define as needed.

# API Endpoints

@app.get("/inventory/{category}")
def get_inventory_html(category: str, request: Request, db: Session = Depends(get_db)):
    if category == "cases":
        items = db.query(Case).all()
    elif category == "pcbs":
        items = db.query(PCB).all()
    elif category == "switches":
        items = db.query(Switch).all()
    elif category == "keycaps":
        items = db.query(Keycap).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
    return templates.TemplateResponse("inventory_list.html", {"request": request, "items": items, "category": category})

@app.post("/api/inventory/{category}")
def add_inventory_item(category: str, item: dict, db: Session = Depends(get_db)):
    if category == "cases":
        new_item = Case(**item)
    elif category == "pcbs":
        new_item = PCB(**item)
    elif category == "switches":
        new_item = Switch(**item)
    elif category == "keycaps":
        new_item = Keycap(**item)
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.put("/api/inventory/{category}/{id}")
def update_inventory_item(category: str, id: str, item: dict, db: Session = Depends(get_db)):
    if category == "cases":
        db_item = db.query(Case).filter(Case.id == id).first()
    # Similar for others
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.items():
        setattr(db_item, key, value)
    db.commit()
    return db_item

# Builds
@app.get("/api/builds")
def get_builds(db: Session = Depends(get_db)):
    builds = db.query(Build).all()
    return builds

@app.post("/api/builds")
def create_build(build: dict, db: Session = Depends(get_db)):
    new_build = Build(**build)
    db.add(new_build)
    db.commit()
    db.refresh(new_build)
    return new_build

@app.get("/api/builds/{id}")
def get_build_detail(id: str, request: Request, db: Session = Depends(get_db)):
    build = db.query(Build).filter(Build.id == id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return templates.TemplateResponse("build_detail.html", {"request": request, "build": build})

@app.put("/api/builds/{id}")
def update_build(id: str, build_update: dict, db: Session = Depends(get_db)):
    db_build = db.query(Build).filter(Build.id == id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    # Track changes for revisions
    changed_fields = ["case_id", "pcb_id", "switch_id", "keycap_id"]
    for field in changed_fields:
        if field in build_update and getattr(db_build, field) != build_update[field]:
            revision = BuildRevision(
                build_id=id,
                changed_component_type=field,
                old_component_id=getattr(db_build, field),
                new_component_id=build_update[field]
            )
            db.add(revision)
    
    for key, value in build_update.items():
        setattr(db_build, key, value)
    db.commit()
    return db_build

# Media
@app.post("/api/builds/{id}/media")
def upload_media(id: str, file: UploadFile = File(...), media_type: str = Form(...), db: Session = Depends(get_db)):
    upload_dir = Path(os.getenv("MEDIA_UPLOAD_DIR", "./data/media"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    media = Media(
        build_id=id,
        media_type=media_type,
        file_path=str(file_path.relative_to(upload_dir))
    )
    db.add(media)
    db.commit()
    return {"filename": file.filename}

@app.get("/api/media/{filename}")
def get_media(filename: str):
    # Served via static mount
    pass

@app.get("/builds/search")
def search_builds(q: str = "", db: Session = Depends(get_db)):
    if not q:
        builds = db.query(Build).all()
    else:
        builds = db.query(Build).join(Case, Build.case_id == Case.id, isouter=True)\
            .join(PCB, Build.pcb_id == PCB.id, isouter=True)\
            .join(Switch, Build.switch_id == Switch.id, isouter=True)\
            .join(Keycap, Build.keycap_id == Keycap.id, isouter=True)\
            .filter(
                (Build.name.ilike(f"%{q}%")) |
                (Case.name.ilike(f"%{q}%")) |
                (PCB.name.ilike(f"%{q}%")) |
                (Switch.name.ilike(f"%{q}%")) |
                (Keycap.name.ilike(f"%{q}%"))
            ).all()
    return templates.TemplateResponse("builds_table.html", {"builds": builds})

@app.post("/builds/add")
async def add_build(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    item_data = dict(form_data)
    new_build = Build(**item_data)
    db.add(new_build)
    db.commit()
    db.refresh(new_build)
    return templates.TemplateResponse("builds_list.html", {"request": request, "builds": db.query(Build).all()})

@app.post("/inventory/{category}/add")
async def add_inventory(category: str, request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    item_data = dict(form_data)
    # Convert checkboxes
    if 'lubed' in item_data:
        item_data['lubed'] = item_data['lubed'] == 'on'
    if 'filmed' in item_data:
        item_data['filmed'] = item_data['filmed'] == 'on'
    if category == "cases":
        new_item = Case(**item_data)
    elif category == "pcbs":
        new_item = PCB(**item_data)
    elif category == "switches":
        new_item = Switch(**item_data)
    elif category == "keycaps":
        new_item = Keycap(**item_data)
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    # Return updated list
    if category == "cases":
        items = db.query(Case).all()
    elif category == "pcbs":
        items = db.query(PCB).all()
    elif category == "switches":
        items = db.query(Switch).all()
    elif category == "keycaps":
        items = db.query(Keycap).all()
    return templates.TemplateResponse("inventory_list.html", {"request": request, "items": items, "category": category})