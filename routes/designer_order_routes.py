from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.order_modals import DesignerCakeOrder
from db import get_db
from routes.order_routes import get_current_user

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
