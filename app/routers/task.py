from fastapi import FastAPI, APIRouter
from fastapi import Depends, status, HTTPException
# Сессия БД
from sqlalchemy.orm import Session
# Функция подключения к БД
from app.backend.db_depends import get_db
# Аннотации, Модели БД и Pydantic.
from typing import Annotated
from app.models import Task, User
from app.schemas import CreateTask, UpdateTask
# Функции работы с записями.
from sqlalchemy import insert, select, update, delete

# Функция создания slug-строки
from slugify import slugify

router = APIRouter(prefix='/task', tags=['task'])


@router.get('/')
async def all_tasks(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Task)).scalars().all()
    return result


@router.get('/task_id')
async def task_by_id(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post('/create')
async def create_task(
        db: Annotated[Session, Depends(get_db)],
        create_task: CreateTask,
        user_id: int
):
    existing_user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User was not found")

    # Проверка существования задачи
    existing_task = db.execute(select(Task).where(Task.title == create_task.title)).scalar_one_or_none()
    if existing_task:
        raise HTTPException(status_code=400, detail="Task already exists")

    # Создание новой задачи с указанием user_id
    db.execute(insert(Task).values(
        title=create_task.title,
        content=create_task.content,  # проверка наличие в модели CreateTask
        priority=create_task.priority,  # проверка наличие в модели CreateTask
        completed=False,
        user_id=user_id  # связываем задачу с пользователем
    ))
    db.commit()

    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}


@router.put('/update')
async def update_task(task_id: int, update_task: UpdateTask, db: Annotated[Session, Depends(get_db)]):
    task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task was not found")

    db.execute(update(Task).where(Task.id == task_id).values(
        title=update_task.title,
        content=update_task.content,
        priority=update_task.priority
    ))
    db.commit()
    return {'status_code': status.HTTP_200_OK, 'transaction': 'Task update is successful!'}


@router.delete('/delete/{task_id}')
async def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task was not found")

    db.execute(delete(Task).where(Task.id == task_id))
    db.commit()
    return {'status_code': status.HTTP_200_OK, 'transaction': 'Task deleted successfully!'}
