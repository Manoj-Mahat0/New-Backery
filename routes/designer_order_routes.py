from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.order_modals import DesignerCakeOrder
from db import get_db
from fastapi import Form
from fastapi import File, UploadFile
from routes.order_routes import get_current_user
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter()

@router.post("/designer-cake/order")
def place_designer_cake_order(
    theme: str = Form(...),
    weight: float = Form(...),
    factory_id: int = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    message_on_cake: str = Form(None),
    design_image: UploadFile = File(...),
    print_image: UploadFile = File(...),
    instruction_audio: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["MAIN_STORE", "STORE"]:
        raise HTTPException(status_code=403, detail="Only stores can order designer cakes")

    factory = db.query(User).filter(User.id == factory_id, User.role == "FACTORY").first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")

    # Save uploaded files
    design_path = f"media/designs/{design_image.filename}"
    with open(design_path, "wb") as f:
        f.write(design_image.file.read())

    print_path = f"media/prints/{print_image.filename}"
    with open(print_path, "wb") as f:
        f.write(print_image.file.read())

    audio_path = None
    if instruction_audio:
        audio_path = f"media/audio/{instruction_audio.filename}"
        with open(audio_path, "wb") as f:
            f.write(instruction_audio.file.read())

    order = DesignerCakeOrder(
        user_id=current_user.id,
        factory_id=factory.id,
        theme=theme,
        weight=weight,
        price=price,
        quantity=quantity,
        message_on_cake=message_on_cake,
        image_url=design_path,
        print_image_url=print_path,
        audio_url=audio_path,
        created_at=datetime.now(IST),
        order_status="PLACED"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "designer_order_id": order.id,
        "theme": theme,
        "price": price,
        "quantity": quantity,
        "design_image": design_path,
        "print_image": print_path,
        "audio_instruction": audio_path,
        "message": "Designer cake order placed"
    }

@router.get("/designer-cake/orders")
def get_all_designer_cake_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    BASE_URL = "https://new-backery.onrender.com/"
    query = db.query(DesignerCakeOrder)
    if current_user.role == "STORE":
        query = query.filter(DesignerCakeOrder.user_id == current_user.id)
    orders = query.all()
    results = []
    for order in orders:
        results.append({
            "designer_order_id": order.id,
            "theme": order.theme,
            "weight": order.weight,
            "price": order.price,
            "quantity": order.quantity,
            "message_on_cake": order.message_on_cake,
            "design_image": BASE_URL + order.image_url if order.image_url else None,
            "print_image": BASE_URL + order.print_image_url if order.print_image_url else None,
            "audio_instruction": BASE_URL + order.audio_url if order.audio_url else None,
            "order_status": getattr(order, "order_status", "PLACED"),
            "factory_id": order.factory_id,
            "user_id": order.user_id,
            "created_at": order.created_at.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None

        })
    return results


@router.put("/designer-cake/orders/{designer_order_id}/update")
def update_designer_cake_order(
    designer_order_id: int,
    theme: str = Form(None),
    weight: float = Form(None),
    price: float = Form(None),
    quantity: int = Form(None),
    message_on_cake: str = Form(None),
    design_image: UploadFile = File(None),
    print_image: UploadFile = File(None),
    audio_instruction: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    BASE_URL = "https://new-backery.onrender.com/"
    order = db.query(DesignerCakeOrder).filter(DesignerCakeOrder.id == designer_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Designer cake order not found")

    # Only the user who placed the order or MAIN_STORE can update
    if current_user.role == "STORE" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")

    if theme is not None:
        order.theme = theme
    if weight is not None:
        order.weight = weight
    if price is not None:
        order.price = price
    if quantity is not None:
        order.quantity = quantity
    if message_on_cake is not None:
        order.message_on_cake = message_on_cake

    # Handle file updates
    if design_image:
        design_path = f"media/designs/{design_image.filename}"
        with open(design_path, "wb") as f:
            f.write(design_image.file.read())
        order.image_url = design_path
    if print_image:
        print_path = f"media/prints/{print_image.filename}"
        with open(print_path, "wb") as f:
            f.write(print_image.file.read())
        order.print_image_url = print_path
    if audio_instruction:
        audio_path = f"media/audio/{audio_instruction.filename}"
        with open(audio_path, "wb") as f:
            f.write(audio_instruction.file.read())
        order.audio_url = audio_path

    db.commit()
    db.refresh(order)

    return {
        "designer_order_id": order.id,
        "theme": order.theme,
        "weight": order.weight,
        "price": order.price,
        "quantity": order.quantity,
        "message_on_cake": order.message_on_cake,
        "design_image": BASE_URL + order.image_url if order.image_url else None,
        "print_image": BASE_URL + order.print_image_url if order.print_image_url else None,
        "audio_instruction": BASE_URL + order.audio_url if order.audio_url else None,
        "message": "Designer cake order updated"
    }

@router.put("/designer-cake/orders/{designer_order_id}/accept")
def accept_designer_cake_order(
    designer_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can accept orders")

    order = db.query(DesignerCakeOrder).filter(DesignerCakeOrder.id == designer_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Designer cake order not found")
    if order.factory_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this order")

    order.order_status = "ACCEPTED"
    db.commit()
    db.refresh(order)
    return {"designer_order_id": order.id, "status": order.order_status, "message": "Order accepted by factory"}

@router.put("/designer-cake/orders/{designer_order_id}/reject")
def reject_designer_cake_order(
    designer_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can reject orders")

    order = db.query(DesignerCakeOrder).filter(DesignerCakeOrder.id == designer_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Designer cake order not found")
    if order.factory_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reject this order")

    order.order_status = "REJECTED"
    db.commit()
    db.refresh(order)
    return {"designer_order_id": order.id, "status": order.order_status, "message": "Order rejected by factory"}

@router.put("/designer-cake/orders/{designer_order_id}/ship")
def ship_designer_cake_order(
    designer_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can ship orders")

    order = db.query(DesignerCakeOrder).filter(DesignerCakeOrder.id == designer_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Designer cake order not found")
    if order.factory_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to ship this order")
    if order.order_status != "ACCEPTED":
        raise HTTPException(status_code=400, detail="Order must be accepted before shipping")

    order.order_status = "SHIPPED"
    db.commit()
    db.refresh(order)
    return {"designer_order_id": order.id, "status": order.order_status, "message": "Order shipped by factory"}

@router.put("/designer-cake/orders/{designer_order_id}/receive")
def receive_designer_cake_order(
    designer_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["STORE", "MAIN_STORE"]:
        raise HTTPException(status_code=403, detail="Only STORE or MAIN_STORE can receive orders")

    order = db.query(DesignerCakeOrder).filter(DesignerCakeOrder.id == designer_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Designer cake order not found")

    # Only allow the user who placed the order or MAIN_STORE to receive
    if current_user.role == "STORE" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to receive this order")

    order.order_status = "RECEIVED"
    db.commit()
    db.refresh(order)
    return {
        "designer_order_id": order.id,
        "status": order.order_status,
        "message": "Designer cake order marked as received"
    }
