# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import base64
import tenseal as ts
import uvicorn

app = FastAPI()


class DataIn(BaseModel):
    values: list  # list of floats/ints


def make_ckks_context():
    # Demo parameters. You can tune poly_modulus_degree and coeff_mod_bit_sizes per your needs.
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 60],
    )
    context.global_scale = 2**40
    context.generate_galois_keys()
    context.generate_relin_keys()
    return context


@app.get("http://127.0.0.1:5501/src/")
async def root():
    return {"message": "API is running! Use POST /encrypt to encrypt data."}


@app.post("http://127.0.0.1:5501/src/")
async def encrypt(data: DataIn):
    values = data.values
    if not isinstance(values, list) or len(values) == 0:
        raise HTTPException(status_code=400, detail="Provide a non-empty list of numbers in 'values'.")

    # convert to numpy array of floats
    arr = np.array(values, dtype=float).tolist()

    # create context + encrypt
    context = make_ckks_context()
    enc_vec = ts.ckks_vector(context, arr)

    # serialize encrypted vector and context
    enc_bytes = enc_vec.serialize()
    try:
        ctx_bytes = context.serialize(save_secret_key=True)  # DEMO ONLY
    except TypeError:
        ctx_bytes = context.serialize()

    # Base64 outputs
    enc_b64 = base64.b64encode(enc_bytes).decode("utf-8")
    ctx_b64 = base64.b64encode(ctx_bytes).decode("utf-8")

    return {"encrypted_base64": enc_b64, "context_base64": ctx_b64, "length": len(arr)}


@app.post("/encrypt-and-store")
async def encrypt_and_store(data: DataIn):
    resp = await encrypt(data)
    enc_b64 = resp["encrypted_base64"]
    ctx_b64 = resp["context_base64"]

    # Save files (demo)
    with open("last_encrypted.b64", "w") as f:
        f.write(enc_b64)
    with open("last_context.b64", "w") as f:
        f.write(ctx_b64)

    return {"saved_files": ["last_encrypted.b64", "last_context.b64"]}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5501)
