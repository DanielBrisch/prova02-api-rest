import random
from fastapi import HTTPException
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import select

from src.config.database import get_session
from src.models.reservas_model import Reserva
from src.models.voos_model import Voo

reservas_router = APIRouter(prefix="/reservas")

@reservas_router.get("/{id_voo}")
def lista_reservas_voo(id_voo: int):
    with get_session() as session:
        statement = select(Reserva).where(Reserva.voo_id == id_voo)
        reservas = session.exec(statement).all()
        return reservas


@reservas_router.post("")
def cria_reserva(reserva: Reserva):
    with get_session() as session:
        existe_reserva = session.exec(select(Reserva).where(Reserva.documento == reserva.documento)).first()
        if existe_reserva:
            return JSONResponse(
                content={"message": f"Já existe uma reserva com este número de documento."},
                status_code=400,
            )

        voo = session.exec(select(Voo).where(Voo.id == reserva.voo_id)).first()
        if not voo:
            return JSONResponse(
                content={"message": f"Voo com id {reserva.voo_id} não encontrado."},
                status_code=404,
            )
        
        codigo_reserva = "".join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])
        reserva.codigo_reserva = codigo_reserva
        session.add(reserva)
        session.commit()
        session.refresh(reserva)
        return reserva

@reservas_router.post("/{codigo_reserva}/checkin/{num_poltrona}")
def faz_checkin(codigo_reserva: str, num_poltrona: int):
    with get_session() as session:
        reserva = session.exec(select(Reserva).where(Reserva.codigo_reserva == codigo_reserva)).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        voo = session.get(Voo, reserva.voo_id)
        if not voo:
            raise HTTPException(status_code=404, detail="Voo não encontrado.")
        
        nome_poltrona = f"poltrona_{num_poltrona}"
        if getattr(voo, nome_poltrona) is not None:
            raise HTTPException(status_code=400, detail="Poltrona já está ocupada.")

        setattr(voo, nome_poltrona, reserva.documento)  

        session.add(voo)
        session.commit()

        return {"message": "Check-in realizado com sucesso."}
    

@reservas_router.patch("/{codigo_reserva}/checkin/{num_poltrona}")
def atualiza_checkin(codigo_reserva: str, num_poltrona: int):
    with get_session() as session:
        reserva = session.exec(select(Reserva).where(Reserva.codigo_reserva == codigo_reserva)).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")
        
        voo = session.get(Voo, reserva.voo_id)
        if not voo:
            raise HTTPException(status_code=404, detail="Voo não encontrado.")
        
        nome_poltrona = f"poltrona_{num_poltrona}"
        if getattr(voo, nome_poltrona) is not None:
            raise HTTPException(status_code=400, detail="Poltrona já está ocupada.")
        
        poltrona_atual = [
            num for num in range(1, 10) if getattr(voo, f"poltrona_{num}") == reserva.documento
        ]
        
        if poltrona_atual:
            setattr(voo, f"poltrona_{poltrona_atual[0]}", None)
        
        setattr(voo, nome_poltrona, reserva.documento)

        session.add(voo)
        session.commit()

        return {"message": "Check-in atualizado com sucesso."}

