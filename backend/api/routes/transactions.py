"""
Transaction Routes - CRUD, import, search, export
"""
import os
import csv
import io
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum

from api.middleware.auth import TokenData, require_roles, UserRole

router = APIRouter()

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"

class Channel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    POS = "pos"
    ATM = "atm"
    API = "api"

class RiskLabel(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    FRAUDULENT = "fraudulent"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"

class TransactionBase(BaseModel):
    transaction_id: str
    reference_number: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = None
    merchant_id: str
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    amount: Decimal
    currency: str = "USD"
    transaction_type: TransactionType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    channel: Channel
    transaction_timestamp: datetime

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    risk_score: Optional[float] = None
    risk_label: Optional[RiskLabel] = None
    model_id: Optional[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    review_notes: Optional[str] = None

class TransactionFilters(BaseModel):
    risk_label: Optional[RiskLabel] = None
    status: Optional[TransactionStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    customer_id: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_category: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Create a new transaction record.

    The transaction will be automatically scored if an active model exists.
    """
    supabase = request.app.state.supabase

    # Check for duplicate
    existing = supabase.table("transactions").select("id").eq("transaction_id", transaction.transaction_id).maybe_single().execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction with this ID already exists"
        )

    # Create transaction
    data = transaction.model_dump()
    data["user_id"] = token_data.user_id
    data["local_hour"] = transaction.transaction_timestamp.hour
    data["day_of_week"] = transaction.transaction_timestamp.weekday()

    result = supabase.table("transactions").insert(data).execute()

    # Trigger scoring (async)
    # In production, this would be a background task
    return result.data[0]

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_transactions(
    request: Request,
    file: UploadFile = File(...),
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Bulk upload transactions via CSV file.

    Required columns:
    - transaction_id, customer_id, merchant_id, amount, transaction_type, channel, transaction_timestamp

    Optional columns:
    - reference_number, customer_name, merchant_name, merchant_category, currency,
      latitude, longitude, country, city, ip_address, device_id, device_type
    """
    supabase = request.app.state.supabase

    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))

    transactions = []
    errors = []
    row_num = 0

    for row in csv_reader:
        row_num += 1
        try:
            ts = datetime.fromisoformat(row.get('transaction_timestamp', '').replace('Z', '+00:00'))
            transaction = {
                "transaction_id": row["transaction_id"],
                "customer_id": row["customer_id"],
                "merchant_id": row["merchant_id"],
                "amount": float(row["amount"]),
                "transaction_type": row.get("transaction_type", "purchase").lower(),
                "channel": row.get("channel", "web").lower(),
                "transaction_timestamp": ts.isoformat(),
                "user_id": token_data.user_id,
                "local_hour": ts.hour,
                "day_of_week": ts.weekday(),
                "currency": row.get("currency", "USD"),
                "reference_number": row.get("reference_number"),
                "customer_name": row.get("customer_name"),
                "merchant_name": row.get("merchant_name"),
                "merchant_category": row.get("merchant_category"),
                "country": row.get("country"),
                "city": row.get("city"),
                "ip_address": row.get("ip_address"),
                "device_id": row.get("device_id"),
                "device_type": row.get("device_type"),
            }
            transactions.append(transaction)
        except Exception as e:
            errors.append({"row": row_num, "error": str(e)})

    if transactions:
        # Batch insert (limit to 1000 at a time)
        batch_size = 1000
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i+batch_size]
            supabase.table("transactions").insert(batch).execute()

    return {
        "imported": len(transactions),
        "errors": errors,
        "message": f"Successfully imported {len(transactions)} transactions"
    }

@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_label: Optional[RiskLabel] = None,
    status: Optional[TransactionStatus] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    customer_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    country: Optional[str] = None,
    min_risk_score: Optional[float] = None,
    max_risk_score: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|transaction_timestamp|amount|risk_score)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    List transactions with filtering, sorting, and pagination.

    Supports filtering by risk label, status, amount range, customer, merchant, country, and risk score.
    """
    supabase = request.app.state.supabase

    # Build query
    query = supabase.table("transactions").select("*", count="exact")

    # Apply filters
    if risk_label:
        query = query.eq("risk_label", risk_label.value)
    if status:
        query = query.eq("status", status.value)
    if customer_id:
        query = query.eq("customer_id", customer_id)
    if merchant_id:
        query = query.eq("merchant_id", merchant_id)
    if country:
        query = query.eq("country", country)
    if min_amount is not None:
        query = query.gte("amount", min_amount)
    if max_amount is not None:
        query = query.lte("amount", max_amount)
    if min_risk_score is not None:
        query = query.gte("risk_score", min_risk_score)
    if max_risk_score is not None:
        query = query.lte("risk_score", max_risk_score)
    if start_date:
        query = query.gte("transaction_timestamp", start_date)
    if end_date:
        query = query.lte("transaction_timestamp", end_date)

    # Calculate pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    query = query.order(sort_by, desc=(sort_order == "desc"))

    result = query.execute()

    total = result.count
    total_pages = (total + page_size - 1) // page_size

    return TransactionListResponse(
        transactions=result.data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get a specific transaction by ID or transaction_id."""
    supabase = request.app.state.supabase

    # Try by UUID first, then by transaction_id
    result = supabase.table("transactions").select("*").eq("id", transaction_id).maybe_single().execute()
    if not result.data:
        result = supabase.table("transactions").select("*").eq("transaction_id", transaction_id).maybe_single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return result.data

@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update: TransactionUpdate,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Update transaction status and add review notes.

    Managers can approve/reject/flag transactions.
    """
    supabase = request.app.state.supabase

    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        update_data["reviewed_by"] = token_data.user_id
        update_data["reviewed_at"] = datetime.utcnow().isoformat()

        result = supabase.table("transactions").update(update_data).eq("id", transaction_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        return result.data[0]

    # Return current state if no updates
    result = supabase.table("transactions").select("*").eq("id", transaction_id).maybe_single().execute()
    return result.data

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))
):
    """Delete a transaction (Admin only)."""
    supabase = request.app.state.supabase
    supabase.table("transactions").delete().eq("id", transaction_id).execute()

@router.get("/export/csv")
async def export_transactions(
    request: Request,
    risk_label: Optional[RiskLabel] = None,
    status: Optional[TransactionStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token_data: TokenData = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """Export transactions to CSV file."""
    supabase = request.app.state.supabase

    query = supabase.table("transactions").select("*")

    if risk_label:
        query = query.eq("risk_label", risk_label.value)
    if status:
        query = query.eq("status", status.value)
    if start_date:
        query = query.gte("transaction_timestamp", start_date)
    if end_date:
        query = query.lte("transaction_timestamp", end_date)

    result = query.limit(10000).execute()

    # Generate CSV
    output = io.StringIO()
    if result.data:
        fieldnames = result.data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result.data)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/stats/summary")
async def get_transaction_stats(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))
):
    """Get transaction statistics summary."""
    supabase = request.app.state.supabase

    query = supabase.table("transactions").select("amount, risk_score, risk_label, status")

    if start_date:
        query = query.gte("transaction_timestamp", start_date)
    if end_date:
        query = query.lte("transaction_timestamp", end_date)

    result = query.execute()

    if not result.data:
        return {
            "total_transactions": 0,
            "total_amount": 0,
            "avg_amount": 0,
            "avg_risk_score": 0,
            "risk_distribution": {},
            "status_distribution": {}
        }

    data = result.data
    total = len(data)
    total_amount = sum(float(t.get("amount", 0)) for t in data)
    risk_scores = [float(t.get("risk_score", 0)) for t in data if t.get("risk_score")] or [0]

    risk_dist = {}
    status_dist = {}
    for t in data:
        rl = t.get("risk_label")
        if rl:
            risk_dist[rl] = risk_dist.get(rl, 0) + 1
        st = t.get("status")
        if st:
            status_dist[st] = status_dist.get(st, 0) + 1

    return {
        "total_transactions": total,
        "total_amount": total_amount,
        "avg_amount": total_amount / total if total > 0 else 0,
        "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
        "risk_distribution": risk_dist,
        "status_distribution": status_dist
    }
