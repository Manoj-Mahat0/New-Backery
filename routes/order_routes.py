from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, Path, UploadFile, File
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from models.order_modals import Cake, CakeOrder, Order
from schemas.order_schemas import CakeOrderCreate, CakeOut, MultiCakeOrderCreate, CakeCreate
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import csv
from io import StringIO

router = APIRouter()
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

oauth2_scheme = HTTPBearer()

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        phone = payload.get("sub")
        if not phone:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.phone_number == phone).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/add-cake")
def add_cake(
    data: CakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MAIN_STORE":
        raise HTTPException(status_code=403, detail="Only MAIN_STORE can add cakes")
    cake = Cake(
        name=data.name,
        weight=data.weight,
        price=data.price
    )
    db.add(cake)
    db.commit()
    db.refresh(cake)
    return {"message": "Cake added successfully", "cake": cake.name}

@router.post("/get-cake-price")
def get_cake_price(data: CakeOrderCreate, db: Session = Depends(get_db)):
    cake = db.query(Cake).filter(
        Cake.name.ilike(data.cake_name),
        Cake.weight == data.weight
    ).first()
    if not cake:
        raise HTTPException(status_code=404, detail="Cake not found for the selected weight")

    return {
        "cake_name": cake.name,
        "weight": cake.weight,
        "price": cake.price
    }

@router.get("/cakes", response_model=List[CakeOut])
def get_all_cakes(db: Session = Depends(get_db)):
    return db.query(Cake).all()

@router.put("/cake/{cake_id}/update-price")
def update_cake_price(
    cake_id: int = Path(..., description="Cake ID"),
    new_price: float = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MAIN_STORE":
        raise HTTPException(status_code=403, detail="Only MAIN_STORE can update prices")

    cake = db.query(Cake).filter(Cake.id == cake_id).first()
    if not cake:
        raise HTTPException(status_code=404, detail="Cake not found")

    cake.price = new_price
    db.commit()
    db.refresh(cake)
    return {"message": "Cake price updated", "cake": cake.name, "weight": cake.weight, "new_price": cake.price}

@router.delete("/cake/{cake_id}/delete")
def delete_cake(
    cake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MAIN_STORE":
        raise HTTPException(status_code=403, detail="Only MAIN_STORE can delete cakes")

    cake = db.query(Cake).filter(Cake.id == cake_id).first()
    if not cake:
        raise HTTPException(status_code=404, detail="Cake not found")

    db.delete(cake)
    db.commit()
    return {"message": f"Cake '{cake.name}' (weight: {cake.weight} lb) deleted"}

@router.post("/bulk-upload-cakes")
def bulk_upload_cakes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MAIN_STORE":
        raise HTTPException(status_code=403, detail="Only MAIN_STORE can upload cakes")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))

    added = []
    for row in reader:
        name = row.get("name")
        weight = int(row.get("weight", 0))
        price = float(row.get("price", 0))

        if not name or weight not in [1, 2, 3] or price <= 0:
            continue  # Skip invalid rows

        existing = db.query(Cake).filter(Cake.name == name, Cake.weight == weight).first()
        if existing:
            continue  # Skip duplicates

        new_cake = Cake(name=name, weight=weight, price=price)
        db.add(new_cake)
        added.append(f"{name} ({weight} lb)")

    db.commit()
    return {
        "message": f"{len(added)} cakes added successfully",
        "cakes": added
    }

@router.post("/order-cake")
def place_cake_order(
    data: MultiCakeOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["MAIN_STORE", "STORE"]:
        raise HTTPException(status_code=403, detail="Only stores can order cakes")

    # Create the main order
    main_order = Order(user_id=current_user.id)
    db.add(main_order)
    db.commit()
    db.refresh(main_order)

    results = []
    for item in data.orders:
        factory = None
        if item.factory_id:
            factory = db.query(User).filter(User.id == item.factory_id, User.role == "FACTORY").first()
            if not factory:
                results.append({
                    "cake": item.cake_name,
                    "weight": item.weight,
                    "error": "Factory not found"
                })
                continue

        cake = db.query(Cake).filter(
            Cake.name.ilike(item.cake_name),
            Cake.weight == item.weight
        ).first()
        if not cake:
            results.append({
                "cake": item.cake_name,
                "weight": item.weight,
                "error": "Cake not found for selected weight"
            })
            continue

        cake_order = CakeOrder(
            order_id=main_order.id,  # Link to main order
            user_id=current_user.id,
            factory_id=factory.id if factory else None,
            cake_name=cake.name,
            weight=cake.weight,
            price=cake.price,
            quantity=item.quantity,
            order_status="PLACED"
        )
        db.add(cake_order)
        db.commit()
        db.refresh(cake_order)

        result = {
            "cake_order_id": cake_order.id,
            "cake": cake.name,
            "weight": cake.weight,
            "price": cake.price,
            "quantity": item.quantity,
            "order_status": cake_order.order_status
        }
        if factory:
            result["factory"] = factory.name
        results.append(result)

    return {
        "main_order_id": main_order.id,
        "orders": results
    }

@router.get("/orders")
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Remove role-based filtering so everyone can see all orders
    orders = db.query(Order).all()
    results = []
    for order in orders:
        cakes = []
        for cake_order in order.cake_orders:
            cakes.append({
                "cake_order_id": cake_order.id,
                "cake_name": cake_order.cake_name,
                "weight": cake_order.weight,
                "price": cake_order.price,
                "quantity": cake_order.quantity,
                "order_status": cake_order.order_status,
                "factory_id": cake_order.factory_id,
                "user_id": cake_order.user_id
            })
        results.append({
            "main_order_id": order.id,
            "created_at": order.created_at,
            "status": order.status,
            "cakes": cakes
        })
    return results


@router.put("/orders/{order_id}/update-quantity")
def update_order_quantity(
    order_id: int,
    new_quantity: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(CakeOrder).filter(CakeOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Only allow the user who placed the order or MAIN_STORE to update
    if current_user.role == "STORE" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    if current_user.role not in ["MAIN_STORE", "STORE"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    order.quantity = new_quantity
    db.commit()
    db.refresh(order)
    return {
        "order_id": order.id,
        "cake_name": order.cake_name,
        "quantity": order.quantity,
        "message": "Order quantity updated"
    }

@router.put("/orders/{cake_order_id}/accept")
def accept_cake_order(
    cake_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only FACTORY can accept orders
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can accept orders")

    cake_order = db.query(CakeOrder).filter(CakeOrder.id == cake_order_id).first()
    if not cake_order:
        raise HTTPException(status_code=404, detail="Cake order not found")

    # Only allow the factory assigned to this order to accept it
    if cake_order.factory_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this order")

    cake_order.order_status = "ACCEPTED"
    db.commit()
    db.refresh(cake_order)
    return {
        "main_order_id": cake_order.order_id,
        "cake_order_id": cake_order.id,
        "status": cake_order.order_status,
        "message": "Cake order accepted by factory"
    }

@router.put("/orders/{main_order_id}/accept-all")
def accept_all_cake_orders(
    main_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only FACTORY can accept orders
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can accept orders")

    # Get all cake orders for this main order assigned to this factory and not already accepted/rejected
    cake_orders = db.query(CakeOrder).filter(
        CakeOrder.order_id == main_order_id,
        CakeOrder.factory_id == current_user.id,
        CakeOrder.order_status == "PLACED"
    ).all()

    if not cake_orders:
        raise HTTPException(status_code=404, detail="No cake orders to accept for this main order and factory")

    accepted_ids = []
    for cake_order in cake_orders:
        cake_order.order_status = "ACCEPTED"
        db.commit()
        db.refresh(cake_order)
        accepted_ids.append(cake_order.id)

    return {
        "main_order_id": main_order_id,
        "accepted_orders": accepted_ids,
        "message": f"{len(accepted_ids)} cake orders accepted by factory"
    }

@router.put("/orders/{cake_order_id}/reject")
def reject_cake_order(
    cake_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only FACTORY can reject orders
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can reject orders")

    cake_order = db.query(CakeOrder).filter(CakeOrder.id == cake_order_id).first()
    if not cake_order:
        raise HTTPException(status_code=404, detail="Cake order not found")

    # Only allow the factory assigned to this order to reject it
    if cake_order.factory_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reject this order")

    cake_order.order_status = "REJECTED"
    db.commit()
    db.refresh(cake_order)
    return {
        "main_order_id": cake_order.order_id,
        "cake_order_id": cake_order.id,
        "status": cake_order.order_status,
        "message": "Cake order rejected by factory"
    }

@router.put("/orders/{main_order_id}/ship")
def ship_cake_orders(
    main_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only FACTORY can ship orders
    if current_user.role != "FACTORY":
        raise HTTPException(status_code=403, detail="Only FACTORY can ship orders")

    # Get all cake orders for this main order assigned to this factory
    cake_orders = db.query(CakeOrder).filter(
        CakeOrder.order_id == main_order_id,
        CakeOrder.factory_id == current_user.id,
        CakeOrder.order_status == "ACCEPTED"
    ).all()

    if not cake_orders:
        raise HTTPException(status_code=404, detail="No cake orders to ship for this main order and factory")

    for cake_order in cake_orders:
        cake_order.order_status = "SHIPPED"
        db.commit()
        db.refresh(cake_order)

    return {
        "main_order_id": main_order_id,
        "shipped_orders": [co.id for co in cake_orders],
        "message": f"{len(cake_orders)} cake orders shipped by factory"
    }

@router.put("/orders/{cake_order_id}/receive")
def receive_cake_order(
    cake_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only MAIN_STORE or STORE can receive orders
    if current_user.role not in ["MAIN_STORE", "STORE"]:
        raise HTTPException(status_code=403, detail="Only MAIN_STORE or STORE can receive orders")

    cake_order = db.query(CakeOrder).filter(CakeOrder.id == cake_order_id).first()
    if not cake_order:
        raise HTTPException(status_code=404, detail="Cake order not found")

    # Only allow the user who placed the order or MAIN_STORE to receive
    if current_user.role == "STORE" and cake_order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to receive this order")

    cake_order.order_status = "RECEIVED"
    db.commit()
    db.refresh(cake_order)
    return {
        "main_order_id": cake_order.order_id,
        "cake_order_id": cake_order.id,
        "status": cake_order.order_status,
        "message": "Cake order marked as received"
    }

@router.put("/orders/{cake_order_id}/receive-with-condition")
def receive_cake_order_with_condition(
    cake_order_id: int,
    new_quantity: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only MAIN_STORE or STORE can receive orders
    if current_user.role not in ["MAIN_STORE", "STORE"]:
        raise HTTPException(status_code=403, detail="Only MAIN_STORE or STORE can receive orders")

    cake_order = db.query(CakeOrder).filter(CakeOrder.id == cake_order_id).first()
    if not cake_order:
        raise HTTPException(status_code=404, detail="Cake order not found")

    # Only allow the user who placed the order or MAIN_STORE to receive
    if current_user.role == "STORE" and cake_order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to receive this order")

    cake_order.quantity = new_quantity
    cake_order.order_status = "RECEIVED_WITH_CONDITION"
    db.commit()
    db.refresh(cake_order)
    return {
        "main_order_id": cake_order.order_id,
        "cake_order_id": cake_order.id,
        "quantity": cake_order.quantity,
        "status": cake_order.order_status,
        "message": "Cake order marked as received with condition and quantity updated"
    }

@router.get("/analytics/store-orders-received")
def store_orders_received_analytics(
    store_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["STORE", "MAIN_STORE"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this analytics")

    now = datetime.utcnow()
    periods = {
        "1_day": now - timedelta(days=1),
        "3_days": now - timedelta(days=3),
        "1_week": now - timedelta(weeks=1),
        "1_month": now - timedelta(days=30),
        "1_year": now - timedelta(days=365),
    }

    results = []

    # If store_id is provided, MAIN_STORE can view analytics for any store
    if store_id is not None:
        store = db.query(User).filter(User.id == store_id, User.role.in_(["STORE", "MAIN_STORE"])).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        store_result = {"store_id": store.id, "store_name": store.name, "periods": {}}
        for label, start_time in periods.items():
            query = db.query(CakeOrder).filter(
                CakeOrder.user_id == store.id,
                CakeOrder.order_status.in_(["RECEIVED", "RECEIVED_WITH_CONDITION"]),
                CakeOrder.order.has(Order.created_at >= start_time)
            )
            count = query.count()
            earning = sum([co.price * co.quantity for co in query.all()])
            store_result["periods"][label] = {
                "orders_received": count,
                "total_earning": earning
            }
        results.append(store_result)
        return results

    # If STORE or MAIN_STORE wants to see their own analytics
    if current_user.role in ["STORE", "MAIN_STORE"]:
        store_id_self = current_user.id
        store_name = current_user.name
        store_result = {"store_id": store_id_self, "store_name": store_name, "periods": {}}
        for label, start_time in periods.items():
            query = db.query(CakeOrder).filter(
                CakeOrder.user_id == store_id_self,
                CakeOrder.order_status.in_(["RECEIVED", "RECEIVED_WITH_CONDITION"]),
                CakeOrder.order.has(Order.created_at >= start_time)
            )
            count = query.count()
            earning = sum([co.price * co.quantity for co in query.all()])
            store_result["periods"][label] = {
                "orders_received": count,
                "total_earning": earning
            }
        results.append(store_result)

    # If MAIN_STORE wants analytics for all stores (excluding itself)
    if current_user.role == "MAIN_STORE" and store_id is None:
        stores = db.query(User).filter(User.role.in_(["STORE", "MAIN_STORE"])).all()
        for store in stores:
            if store.id == current_user.id:
                continue
            store_result = {"store_id": store.id, "store_name": store.name, "periods": {}}
            for label, start_time in periods.items():
                query = db.query(CakeOrder).filter(
                    CakeOrder.user_id == store.id,
                    CakeOrder.order_status.in_(["RECEIVED", "RECEIVED_WITH_CONDITION"]),
                    CakeOrder.order.has(Order.created_at >= start_time)
                )
                count = query.count()
                earning = sum([co.price * co.quantity for co in query.all()])
                store_result["periods"][label] = {
                    "orders_received": count,
                    "total_earning": earning
                }
            results.append(store_result)

    return results