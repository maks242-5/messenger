from sqlalchemy import create_engine, String, Float, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import List

from flask_login import UserMixin 
import bcrypt 


engine = create_engine("postgresql+psycopg2://postgres@localhost/project", client_encoding='utf8')
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    def create_db(self):
        Base.metadata.create_all(engine)

    def drop_db(self):
        Base.metadata.drop_all(engine)

class Users(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname : Mapped[str] = mapped_column(String(100), unique=True)
    password : Mapped[str] = mapped_column(String(200))
    email : Mapped[str] = mapped_column(String(50), unique=True)

    # Зв'язки, які вимагають класи Friends та Messages через back_populates
    sent_requests: Mapped[List["Friends"]] = relationship("Friends", foreign_keys="Friends.sender", back_populates="sender_user")
    received_requests: Mapped[List["Friends"]] = relationship("Friends", foreign_keys="Friends.recipient", back_populates="recipient_user")
    
    sent_messages: Mapped[List["Messages"]] = relationship("Messages", foreign_keys="Messages.sender", back_populates="sender_user")
    received_messages: Mapped[List["Messages"]] = relationship("Messages", foreign_keys="Messages.recipient", back_populates="recipient_user")

    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Метод для перевірки пароля
    def check_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Friends(Base):
    __tablename__ = "friends"  # Виправлено: прибрано зайвий пробіл
    id: Mapped[int] = mapped_column(primary_key=True)
    sender : Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient : Mapped[int] = mapped_column(ForeignKey("users.id"))
    status : Mapped[bool] = mapped_column(Boolean, default=False)

    sender_user: Mapped["Users"] = relationship("Users", foreign_keys="Friends.sender", back_populates="sent_requests")
    recipient_user: Mapped["Users"] = relationship("Users", foreign_keys="Friends.recipient", back_populates="received_requests")


class Messages(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    sender: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_text: Mapped[str] = mapped_column(Text)
    status_check : Mapped[bool] = mapped_column(Boolean, default=False)

    sender_user: Mapped["Users"] = relationship("Users", foreign_keys="Messages.sender", back_populates="sent_messages")
    recipient_user: Mapped["Users"] = relationship("Users", foreign_keys="Messages.recipient", back_populates="received_messages")
    
base = Base()
base.create_db()