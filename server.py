from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import base64
import tenseal as ts
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ allow browser fetch requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DataIn(BaseModel):
    values: list  # list of numbers

def make_ckks_context():
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 60],
    )
    context.global_scale = 2**40
    context.generate_galois_keys()
    context.generate_relin_keys()
    return context

@app.post("/encrypt")
async def encrypt(data: DataIn):
    values = data.values
    if not values:
        raise HTTPException(status_code=400, detail="Provide a non-empty list of numbers.")

    arr = np.array(values, dtype=float).tolist()

    # build context and encrypt
    context = make_ckks_context()
    enc_vec = ts.ckks_vector(context, arr)

    # serialize
    enc_bytes = enc_vec.serialize()
    ctx_bytes = context.serialize(save_secret_key=True)  # ⚠ demo only

    # convert to base64 for JSON transport
    enc_b64 = base64.b64encode(enc_bytes).decode("utf-8")
    ctx_b64 = base64.b64encode(ctx_bytes).decode("utf-8")

    return {
        "encrypted_base64": enc_b64,
        "context_base64": ctx_b64,
        "length": len(arr),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
