from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models.subscriber import Subscriber

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
    return {"message": "Subscription successful to Daily AI Digest!"}


@router.delete("/unsubscribe")
def unsubscribe(request: SubscribeRequest, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.email == request.email).first()
    if not subscriber or not subscriber.is_active:
        raise HTTPException(
            status_code=400, detail="Email not found or already unsubscribed"
        )
    subscriber.is_active = False
    db.commit()
    return {"message": "You have been unsubscribed from Daily AI Digest."}
