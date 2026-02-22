from fastapi import FastAPI

app = FastAPI(title="FlashApply Backend")


@app.get("/")
def root():
    return {
        "message": "Backend OK. Pour l'interface, lancez: streamlit run streamlit_app.py"
    }
