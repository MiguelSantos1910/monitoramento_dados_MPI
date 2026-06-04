from pymongo import MongoClient
import plc_client as plc

MONGO_HOST = ""

def exportar():
    client = None
    try:
        client = MongoClient(MONGO_HOST)
        db = client.get_database('Cluster0')
        colecao = db['garra']

        vetores = plc.ler_vetores()  #lê os dados reais do CLP

        documento = {
            "db": plc.DB_NUMERO,
            "vetores": vetores
        }

        resultado = colecao.insert_one(documento)
        print(f"[MongoDB] Inserido com id: {resultado.inserted_id}")

    except Exception as e:
        raise Exception(f"Erro ao exportar: {e}")
    finally:
        if client:
            client.close()