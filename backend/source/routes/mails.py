from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from config_secrets import settings
from source.utils.mailer import send_mail


router = APIRouter(prefix="/api/v1/mails", tags=["mails"])


@router.post("/send-mail")
def send_mail_endpoint(req: dict, tasks: BackgroundTasks):
    # data = req.dict()
    tasks.add_task(send_mail, req)
    return {"status": 200, "message": "Email is being sent in the background"}