from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ..core.database import get_db
from ..models.subscriber import Subscriber

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.post("/subscribe")
def subscribe(request: SubscribeRequest, db: Session = Depends(get_db)):
    existing = db.query(Subscriber).filter(Subscriber.email == request.email).first()
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        else:
            existing.is_active = True
            db.commit()
            return {"message": "Welcome back! Subscription reactivated."}
    subscriber = Subscriber(email=request.email)
    db.add(subscriber)
    db.commit()
    return {"message": "Successfully subscribed to Daily AI Digest!"}


@router.delete("/unsubscribe")
def unsubscribe(email: EmailStr, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
    if not subscriber or not subscriber.is_active:
        raise HTTPException(status_code=404, detail="Email not found")
    subscriber.is_active = False
    db.commit()
    return {"message": "You have been unsubscribed from Daily AI Digest."}


@router.post("/trigger-digest")
def trigger_digest():
    from ..tasks.digest_tasks import run_daily_digest

    task = run_daily_digest.delay()
    return {"message": "Daily digest task triggered", "task_id": task.id}
